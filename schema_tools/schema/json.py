import requests
from requests_file import FileAdapter

from urllib.parse import urldefrag, urlparse
from pathlib import Path

from schema_tools import json, yaml
from schema_tools.schema import Schema, Mapper, loads, IdentifiedSchema, ConstantValueSchema

def log(*args):
  if False: print(*args)

class ObjectSchema(IdentifiedSchema):
  def __init__(self, properties=None, definitions=None,
                     allOf=None, anyOf=None, oneOf=None,
                    **kwargs):
    super().__init__(**kwargs)

    if properties is None: properties = []
    self.properties = properties
    if isinstance(self.properties, list):
      for prop in self.properties:
        prop.parent = self
    elif isinstance(self.properties, ConstantValueSchema):
      if self.properties.value is None:
        self.properties = []
    else:
      raise ValueError("can't handle properties", self.properties)

    if definitions is None: definitions = []
    self.definitions = definitions
    for definition in self.definitions:
      definition.parent = self

    self.allOf = allOf
    if self.allOf: self.allOf.parent = self
    self.anyOf = anyOf
    if self.anyOf: self.anyOf.parent = self
    self.oneOf = oneOf
    if self.oneOf: self.oneOf.parent = self

  def definition(self, key, return_definition=True):
    for definition in self.definitions:
      if definition.name == key:
        return definition.definition if return_definition else definition
    raise KeyError("'{}' is not a known definition".format(key))

  def _combinations(self):
    for combination in [ self.allOf, self.anyOf, self.oneOf ]:
      if isinstance(combination, Combination):
        for option in combination.options:
          yield option

  def property(self, key, return_definition=True):
    # local properties
    for prop in self.properties:
      if prop.name == key:
        return prop.definition if return_definition else prop
    # collected/combinations properties
    for candidate in self._combinations():
      if isinstance(candidate, Reference):
        candidate = candidate.resolve()
      try:
        return candidate.property(key, return_definition=return_definition)
      except:
        pass
    raise KeyError("'{}' is not a known property".format(key))

  def _select(self, name, *remainder, stack=None):
    if stack is None: stack = []
    log(stack, "object", name, remainder)
    result = None
    # TODO generalize this at schema level
    if name == "components" and remainder[0] == "schemas":
      try:
        remainder = list(remainder)
        stack.append("components")
        stack.append(remainder.pop(0))
        name = remainder.pop(0)
        result = self.definition(name, return_definition=False)
        stack.append(result)
        if remainder:
          result = result._select(*remainder, stack=stack)
      except KeyError:
        pass
    else:
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
      # "allOf"       : [ repr(candidate) for candidate in self.allOf.options ],
      # "oneOf"       : [ repr(candidate) for candidate in self.oneOf.options ],
      # "anyOf"       : [ repr(candidate) for candidate in self.anyOf.options ]
    }

  def to_dict(self, deref=False, prefix=None, stack=None):
    if stack is None: stack = []
    out = super().to_dict(deref=deref, prefix=prefix, stack=stack)
    if self.properties:
      out["properties"] = {
        p.name : p.to_dict(deref=deref, prefix=prefix, stack=stack+["properties"]) for p in self.properties 
      }
    if self.definitions:
      out["definitions"] = {
        d.name : d.to_dict(deref=deref, prefix=prefix, stack=stack+["definitions"]) for d in self.definitions 
      }
    if self.allOf:
      out["allOf"] = [
         a.to_dict(deref=deref, prefix=prefix, stack=stack) for a in self.allOf.options
      ]
    if self.oneOf:
      out["oneOf"] = [
         a.to_dict(deref=deref, prefix=prefix, stack=stack) for a in self.oneOf.options
      ]
    if self.anyOf:
      out["anyOf"] = [
         a.to_dict(deref=deref, prefix=prefix, stack=stack) for a in self.anyOf.options
      ]
    return out

  def dependencies(self, external=False, visited=None):
    return list({
      dependency \
      for prop in self.properties + list(self._combinations()) \
      for dependency in prop.dependencies(external=external, visited=visited)
    })

class Definition(IdentifiedSchema):
  def __init__(self, name, definition):
    self.name              = name
    self._definition       = definition
    if isinstance(self._definition, Schema):
      self._definition.parent = self
      self._location = self._definition._location
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

  def to_dict(self, deref=False, prefix=None, stack=None):
    if stack is None: stack = []
    if isinstance(self._definition, Schema):
      return self._definition.to_dict(deref=deref, prefix=prefix, stack=stack + [self.name])
    else:
      return self._definition

  def _select(self, *path, stack=None):
    log(stack, "definition/property", path)
    return self.definition._select(*path, stack=stack)

  def dependencies(self, external=False, visited=None):
    return self._definition.dependencies(external=external, visited=visited)

class Property(Definition):          pass

class ValueSchema(IdentifiedSchema): pass

class StringSchema(ValueSchema):     pass
class IntegerSchema(ValueSchema):    pass
class NullSchema(ValueSchema):       pass
class NumberSchema(ValueSchema):     pass
class BooleanSchema(ValueSchema):    pass

class ArraySchema(IdentifiedSchema):
  def __init__(self, items=None, **kwargs):
    super().__init__(**kwargs)
    self.items = items
    if isinstance(self.items, Schema):
      self.items.parent = self
    elif self.items is None:
      self.items = []
    else:
      raise ValueError("unsupported items type: '{}'".format(
        self.items.__class__.__name__)
      )

  def _more_repr(self):
    return {
      "items" : repr(self.items)
    }

  def to_dict(self, deref=False, prefix=None, stack=None):
    if stack is None: stack = []
    out = super().to_dict(deref=deref, prefix=prefix, stack=stack)
    if isinstance(self.items, Schema):
      out["items"] = self.items.to_dict(deref=deref, prefix=prefix, stack=stack)
    else:
      out["items"] = self.items
    return out

  def _select(self, index, *path, stack=None):
    # TODO in case of (None)
    log(stack, "array", index, path)
    if isinstance(self.items, Schema):
      return self.items._select(index, *path, stack=stack)

  def dependencies(self, external=False, visited=None):
    if isinstance(self.items, Schema):
      return self.items.dependencies(external=external, visited=visited)
    else:
      return list({
        dependency \
        for item in self.items \
        for dependency in item.dependencies(external=external, visited=visited)
      })

class TupleItem(Definition):
  def _more_repr(self):
    return {
      "index"      : self.name,
      "definition" : repr(self._definition)
    }

class TupleSchema(IdentifiedSchema):
  def __init__(self, items=None, **kwargs):
    super().__init__(**kwargs)
    self.items = items
    if not isinstance(self.items, list):
      raise ValueError("tuple items should be list, not: '{}'".format(
        self.items.__class__.__name__)
      )
    for item in self.items:
      item.parent = self

  def _more_repr(self):
    return {
      "items" : repr(self.items)
    }

  def item(self, index):
    return self[index].definition

  def __getitem__(self, index):
    if not isinstance(index, int):
      raise TypeError("tuple access only with numeric indices")
    return self.items[index]


  def to_dict(self, deref=False, prefix=None, stack=None):
    if stack is None: stack = []
    out = super().to_dict(deref=deref, prefix=prefix, stack=stack)
    out["items"] = [ item.to_dict(deref=deref, prefix=prefix, stack=stack) for item in self.items ]
    return out

  def _select(self, index, *path, stack=None):
    log(stack, "tuple", index, path)
    if path:
      return self[int(index)]._select(*path, stack=stack)
    else:
      return self[int(index)]

  def dependencies(self, external=False, visited=None):
    return list({
      dependency \
      for item in self.items \
      for dependency in item.dependencies(external=external, visited=visited)
    })

class Combination(IdentifiedSchema):
  def __init__(self, options=None, **kwargs):
    super().__init__(**kwargs)
    self.options = options if options else []
    for option in self.options:
      option.parent = self
  
  def _more_repr(self):
    return {
      "options"  : len(self.options)
    }

  def to_dict(self, deref=False, prefix=None, stack=None):
    if stack is None: stack = []
    out = super().to_dict(deref=deref, prefix=prefix, stack=stack)
    name = self.__class__.__name__
    name = name[0].lower() + name[1:]
    out[name] = [ o.to_dict(deref=deref, prefix=prefix, stack=stack) for o in self.options ]
    return out

  def _select(self, *path, stack=None):
    log(stack, "combination", path)
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

  def dependencies(self, external=False, visited=None):
    return list({
      dependency \
      for option in self.options \
      for dependency in option.dependencies(external=external, visited=visited)
    })

class AllOf(Combination): pass
class AnyOf(Combination): pass
class OneOf(Combination): pass

class Reference(IdentifiedSchema):
  def __init__(self, ref=None, **kwargs):
    super().__init__(**kwargs)
    self.ref = ref.value

  def __repr__(self):
    return "Reference(ref={})".format( self.ref )

  def _more_repr(self):
    return {
      "$ref" : self.ref
    }

  def to_dict(self, deref=False, prefix=None, stack=None):
    if stack is None: stack = []
    if prefix is None: prefix = "#"
    if deref: 
      if self.is_remote:
        prefix = "#/" + "/".join(stack)
        return self.resolve().to_dict(deref=deref, prefix=prefix, stack=stack)
      else:
        return { "$ref" : prefix + self.ref[1:] }
    return { "$ref" : self.ref }

  def resolve(self, return_definition=True):
    url, fragment = urldefrag(self.ref)
    if url:
      doc = self._fetch(url)
    else:
      doc = self.root

    if fragment:
      if fragment.startswith("/definitions/"):
        name = fragment.replace("/definitions/", "")
        if not doc.definition:
          raise ValueError("doc " + repr(doc) + " has no definitions ?!")
        return doc.definition(name, return_definition=return_definition)
      elif fragment.startswith("/properties/"):
        name = fragment.replace("/properties/", "")
        return doc.property(name, return_definition=return_definition)
      elif fragment.startswith("/components/schemas/"):
        name = fragment.replace("/components/schemas/", "")
        return doc.definition(name, return_definition=return_definition)
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
      return loads(src, origin=url)
    except:
      try:
        return loads(src, parser=yaml)
      except Exception as e:
        raise ValueError("unable to parse '{}', due to '{}'".format(url, str(e)))

  def _select(self, *path, stack=None):
    log(self._stack, "ref", path)
    return self.resolve()._select(*path, stack=stack)

  @property
  def is_remote(self):
    return not self.ref.startswith("#")

  def dependencies(self, external=False, visited=None):
    if not visited: visited = []
    if self in visited:
      return []
    visited.append(self)
    if self.is_remote:
      if external:
        return list(set( self.resolve(return_definition=False).dependencies(external=external, visited=visited) + [ self ] ))
      else:
        return [ self ]
    else:
      return list(set( self.resolve(return_definition=False).dependencies(external=external, visited=visited) ))

  def __hash__(self):
    return hash(self.ref)

  def __eq__(self, other):
    if isinstance(other, self.__class__):
      return self.ref == other.ref
    else:
      return False

class Enum(IdentifiedSchema):
  def __init__(self, enum=None, **kwargs):
    super().__init__(**kwargs)
    self.values = []
    if enum:
      for e in enum:
        if not isinstance(e, ConstantValueSchema):
          raise ValueError("not constant value", e)
        else:
          self.values.append(e.value)
  
  def _more_repr(self):
    return {
      "enum"  : self.values
    }

  def to_dict(self, deref=False, prefix=None, stack=None):
    return { "enum" : self.values }


class SchemaMapper(Mapper):
  
  def map_object(self, properties):
    if self.has( properties, "type", "object" ) or \
       self.has( properties, "type", list, containing="object") or \
       ( self.has(properties, "properties") and \
         not isinstance(properties["properties"], IdentifiedSchema) ) or \
       ( self.has(properties, "components") and \
         not isinstance(properties["components"], IdentifiedSchema) ):
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
      # extract combinations
      for combination, cls in { "allOf" : AllOf, "oneOf" : OneOf, "anyOf": AnyOf }.items():
        options = self._combine_options(properties, combination, combination.lower())
        if options:
          properties[combination] = cls(options=options)
      return ObjectSchema(**properties)

  def map_value(self, properties):
    value_mapping = {
      "boolean": BooleanSchema,
      "integer": IntegerSchema,
      "null":    NullSchema,
      "number":  NumberSchema,
      "string":  StringSchema
    }
    if self.has(properties, "type", value_mapping):
      return value_mapping[properties["type"].value](**properties)

  def map_array(self, properties):
    if not self.has(properties, "type", "array"): return
    if self.has(properties, "items", list):
      properties["items"] = [
        TupleItem(index, value) \
        for index, value in enumerate(properties["items"])
      ]
      return TupleSchema(**properties)
    return ArraySchema(**properties)

  def _combine_options(self, properties, *keys):
    combined = []
    for key in keys:
      if self.has(properties, key):
        combined += properties.pop(key, {})
    return combined

  def map_all_of(self, properties):
    if "type" in properties: return
    options = self._combine_options(properties, "allOf", "allof")
    if options:
      properties["options"] = options
      return AllOf(**properties)

  def map_any_of(self, properties):
    if "type" in properties: return
    options = self._combine_options(properties, "anyOf", "anyof")
    if options:
      properties["options"] = options
      return AnyOf(**properties)

  def map_one_of(self, properties):
    if "type" in properties: return
    options = self._combine_options(properties, "oneOf", "oneof")
    if options:
      properties["options"] = options
      return OneOf(**properties)

  def map_reference(self, properties):
    if self.has(properties, "$ref", str):
      properties["ref"] = properties.pop("$ref")
      return Reference(**properties)

  def map_enum(self, properties):
    if self.has(properties, "enum", list):
      return Enum(**properties)
