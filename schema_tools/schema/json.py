import requests
from requests_file import FileAdapter

from urllib.parse import urldefrag, urlparse
from pathlib import Path

from schema_tools import json, yaml
from schema_tools.schema import Schema, Mapper, loads

class ObjectSchema(Schema):
  def __init__(self, properties=[], definitions=[], allof=[], **kwargs):
    super().__init__(**kwargs)
    if properties is None: properties = []
    self.properties = properties
    for prop in self.properties:
      prop.parent = self
    if definitions is None: definitions = []
    self.definitions = definitions
    for definition in self.definitions:
      definition.parent = self
    if allof is None: allof = []
    self.allof = allof
    for allof in self.allof:
      allof.parent = self

  def definition(self, key, return_definition=True):
    for definition in self.definitions:
      if definition.name == key:
        return definition.definition if return_definition else definition
    raise KeyError("'{}' is not a known definition".format(key))

  def property(self, key, return_definition=True):
    # local properties
    for prop in self.properties:
      if prop.name == key:
        return prop.definition if return_definition else prop
    # collected/all-of properties
    for candidate in self.allof:
      if isinstance(candidate, Reference):
        candidate = candidate.resolve()
      try:
        return candidate.property(key, return_definition=return_definition)
      except:
        pass
    raise KeyError("'{}' is not a known property".format(key))

  def _select(self, name, *remainder, stack=[]):
    # print(stack, "object", name, remainder)
    result = None
    try:
      result = self.property(name, return_definition=False)
      stack.append(result)
      if remainder:
        result = result._select(*remainder, stack=stack)
    except KeyError:
      pass
    return result

  def _more_repr(self):
    return {
      "properties"  : [ prop.name for prop in self.properties ],
      "definitions" : [ definition.name for definition in self.definitions ],
      "allof"       : [ repr(candidate) for candidate in self.allof ]
    }

  def to_dict(self):
    out = super().to_dict()
    if self.properties:
      out["properties"] = {
        p.name : p.to_dict() for p in self.properties 
      }
    if self.definitions:
      out["definitions"] = {
        d.name : d.to_dict() for d in self.definitions 
      }
    if self.allof:
      out["allof"] = [
         a.to_dict() for a in self.allof
      ]
    return out

  def dependencies(self, resolve=False):
    return list({
      dependency \
      for prop in self.properties + self.allof \
      for dependency in prop.dependencies(resolve=resolve)
    })

class Definition(Schema):
  def __init__(self, name, definition):
    self.name              = name
    self._definition       = definition
    if isinstance(self._definition, Schema):
      self._definition.parent = self
    elif isinstance(self._definition, bool):
      pass
    else:
      raise ValueError("unsupported items type: '{}'".format(
        self.items.__class__.__type__)
      )

  def is_ref(self):
    return isinstance(self._definition, Reference)

  @property
  def definition(self):
    d = self._definition
    while isinstance(d, Reference):
      d = d.resolve()
    return d

  def _more_repr(self):
    return {
      "name"       : self.name,
      "definition" : repr(self._definition)
    }

  def to_dict(self):
    if isinstance(self._definition, Schema):
      return self._definition.to_dict()
    else:
      return self._definition

  def _select(self, *path, stack=[]):
    # print(stack, "definition/property", path)
    return self.definition._select(*path, stack=stack)

  def dependencies(self, resolve=False):
    return self._definition.dependencies(resolve=resolve)

class Property(Definition):       pass

class ValueSchema(Schema):        pass

class StringSchema(ValueSchema):  pass
class IntegerSchema(ValueSchema): pass
class NullSchema(ValueSchema):    pass
class NumberSchema(ValueSchema):  pass
class BooleanSchema(ValueSchema): pass

class ArraySchema(Schema):
  def __init__(self, items=None, **kwargs):
    super().__init__(**kwargs)
    self.items = items
    if isinstance(self.items, Schema):
      self.items.parent = self
    elif isinstance(self.items, (list, bool)) or self.items is None:
      pass
    else:
      raise ValueError("unsupported items type: '{}'".format(
        self.items.__class__.__name__)
      )

  def _more_repr(self):
    return {
      "items" : repr(self.items)
    }

  def to_dict(self):
    out = super().to_dict()
    if isinstance(self.items, Schema):
      out["items"] = self.items.to_dict()
    else:
      out["items"] = self.items
    return out

  def _select(self, *path, stack=[]):
    # TODO in case of (list, bool, None)
    # print(stack, "array", path)
    return self.items._select(*path, stack=stack)

  def dependencies(self, resolve=False):
    if isinstance(self.items, Schema):
      return self.items.dependencies(resolve=resolve)
    else:
      return list({
        dependency \
        for item in self.items \
        for dependency in item.dependencies(resolve=resolve)
      })

class Combination(Schema):
  def __init__(self, options=[], **kwargs):
    super().__init__(**kwargs)
    self.options = options
    for option in self.options:
      option.parent = self
  
  def _more_repr(self):
    return {
      "options"  : len(self.options)
    }

  def to_dict(self):
    out = super().to_dict()
    name = self.__class__.__name__
    name = name[0].lower() + name[1:]
    out[name] = [ o.to_dict() for o in self.options ]
    return out

  def _select(self, *path, stack=[]):
    # print(stack, "combination", path)
    best_stack = []
    result     = None
    for option in self.options:
      local_stack = []
      result = option._select(*path, stack=local_stack)
      if len(local_stack) > len(best_stack):
        best_stack = local_stack
      if result: break
    stack.extend(local_stack)
    return result

  def dependencies(self, resolve=False):
    return list({
      dependency \
      for option in self.options \
      for dependency in option.dependencies(resolve=resolve)
    })

class AllOf(Combination): pass
class AnyOf(Combination): pass
class OneOf(Combination): pass

class Reference(Schema):
  def __init__(self, ref=None, **kwargs):
    super().__init__(**kwargs)
    self.ref = ref

  def __repr__(self):
    return "Reference(ref={})".format( self.ref )

  def _more_repr(self):
    return {
      "$ref" : self.ref
    }

  def to_dict(self):
    return { "$ref" : self.ref }

  @property
  def root(self):
    p = self.parent
    while not p.parent is None:
      p = p.parent
    return p

  def resolve(self):
    url, fragment = urldefrag(self.ref)
    if url:
      doc = self._fetch(url)
    else:
      doc = self.root

    if fragment:
      if fragment.startswith("/definitions/"):
        name = fragment.replace("/definitions/", "")
        return doc.definition(name)
      elif fragment.startswith("/properties/"):
        name = fragment.replace("/properties/", "")
        return doc.property(name)
      elif fragment.startswith("/components/schemas/"):
        name = fragment.replace("/components/schemas/", "")
        return doc.definition(name)        
      else:
        raise NotImplementedError

    return doc

  def _fetch(self, url):
    s = requests.Session()
    s.mount("file:", FileAdapter())
    # make sure file url is absolute
    u = urlparse(url)
    if u.scheme == "file":
      u = u._replace(path=str(Path(u.path).absolute()))
      url = u.geturl()

    try:
      doc = s.get(url)
    except Exception as e:
      raise ValueError("unable to fetch '{}', due to '{}'".format(url, str(e)))

    src = doc.text
    try:
      return loads(src)
    except:
      try:
        return loads(src, parser=yaml)
      except Exception as e:
        raise ValueError("unable to parse '{}', due to '{}'".format(url, str(e)))

  def _select(self, *path, stack=[]):
    # print(self._stack, "ref", path)
    return self.resolve()._select(*path, stack=stack)

  def dependencies(self, resolve=False):
    if resolve:
      return  list(set( self.resolve().dependencies(resolve=resolve) + [ self ] ))
    else:
      return [ self ]

  def __hash__(self):
    return hash(self.ref)

  def __eq__(self, other):
    if isinstance(other, self.__class__):
      return self.ref == other.ref
    else:
      return False

class Enum(Schema):
  def __init__(self, enum=[], **kwargs):
    super().__init__(**kwargs)
    self.values = enum
  
  def _more_repr(self):
    return {
      "enum"  : self.values
    }

  def to_dict(self):
    return { "enum" : self.values }


class SchemaMapper(Mapper):
  
  def map_object(self, properties):
    if self.has( properties, "type", "object" ) or \
       self.has( properties, "type", list, containing="object"):
      # properties and definitions bubble up as Generic Schemas
      if self.has(properties, "properties"):
        properties["properties"] = [
          Property(name, definition) \
          for name, definition in properties["properties"].items()
        ]
      if self.has(properties, "definitions"):
        properties["definitions"] = [
          Definition(name, definition) \
          for name, definition in properties["definitions"].items()
        ]
      if self.has(properties, "components") and properties["components"].schemas:
        components = properties.pop("components")
        if not "definitions" in properties: properties["definitions"] = []
        properties["definitions"] += [
          Definition(name, definition) \
          for name, definition in components.schemas.items()
        ]
      return ObjectSchema(**properties)

  def map_value(self, properties):
    value_mapping = {
      "boolean": BooleanSchema,
      "integer": IntegerSchema,
      "null":    NullSchema,
      "number":  NumberSchema,
      "string":  StringSchema,
      "array":   ArraySchema
    }
    if self.has(properties, "type", value_mapping):
      return value_mapping[properties["type"]](**properties)
    
  def map_all_of(self, properties):
    if self.has(properties, "allOf", list):
      properties["options"] = properties.pop("allOf")
      return AllOf(**properties)

  def map_any_of(self, properties):
    if self.has(properties, "anyOf", list):
      properties["options"] = properties.pop("anyOf")
      return AnyOf(**properties)

  def map_one_of(self, properties):
    if self.has(properties, "oneOf", list):
      properties["options"] = properties.pop("oneOf")
      return OneOf(**properties)

  def map_reference(self, properties):
    if self.has(properties, "$ref", str):
      properties["ref"] = properties.pop("$ref")
      return Reference(**properties)

  def map_enum(self, properties):
    if self.has(properties, "enum", list):
      return Enum(**properties)

