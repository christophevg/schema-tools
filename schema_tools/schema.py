import requests
from requests_file import FileAdapter

from urllib.parse import urldefrag, urlparse
from pathlib import Path

from schema_tools.utils import ASTVisitor
from schema_tools       import json, yaml

def build(nodes):
  return NodesMapper().visit(nodes)

def load(path, parser=json):
  return build(parser.load(path))

def loads(src, parser=json):
  return build(parser.loads(src))


class Schema(object):
  args = {}

  def __init__(self, location=None, **kwargs):
    self.parent   = None
    self.location = location
    self.args     = kwargs   # catchall properties

  def __getattr__(self, key):
    try:
      return self.args[key]
    except KeyError:
      return None

  def select(self, *path, stack=[]):
    path = list(path)
    # print("select", path)
    # pop leading Nones
    while path and path[0] is None:
      path.pop(0)
    if not path: return None
    # ensure all parts in the path are strings
    for step in path:
      if not isinstance(step, str):
        raise ValueError("only string paths are selectable")
    # single path can be dotted string
    if len(path) == 1: path = path[0].split(".")
    return self._select(*path, stack=stack)

  def trace(self, *path):
    # print("trace", path)
    stack = []
    self.select(*path, stack=stack)
    return stack

  def _select(self, *path, stack=[]):
    # print(stack, "schema", path)
    return None # default

  def __repr__(self):
    props = { k: v for k, v in self.args.items() }  # TODO not "if v" ?
    props.update(self._more_repr())
    props["location"] = self.location
    return "{}({})".format(
      self.__class__.__name__,
      ", ".join( [ "{}={}".format(k, v) for k, v in props.items() ] )
    )

  def _more_repr(self):
    return {}

  def to_dict(self):
    items = {}
    for k, v in self.args.items():
      if isinstance(v, Schema):
        v = v.to_dict()
      items[k] = v
    return items

  def items(self):
    return self.args.items()

  def dependencies(self):
    return []

class ObjectSchema(Schema):
  def __init__(self, properties=[], definitions=[], **kwargs):
    super().__init__(**kwargs)
    if properties is None: properties = []
    self.properties = properties
    for prop in self.properties:
      prop.parent = self
    if definitions is None: definitions = []
    self.definitions = definitions
    for definition in self.definitions:
      definition.parent = self

  def definition(self, key, return_definition=True):
    for definition in self.definitions:
      if definition.name == key:
        return definition.definition if return_definition else definition
    raise KeyError("'{}' is not a known definition".format(key))

  def property(self, key, return_definition=True):
    for prop in self.properties:
      if prop.name == key:
        return prop.definition if return_definition else prop
    raise KeyError("'{}' is not a known property".format(key))

  def has_property(self, name):
    return any([ prop.name == name for prop in self.properties ])

  def _select(self, name, *remainder, stack=[]):
    # print(stack, "object", name, remainder)
    result = None
    try:
      result = self.property(name, return_definition=False)
      stack.append(result)
      if remainder:
        result = result._select(*remainder, stack=stack)
        if not result: stack.pop() # backtracking
    except KeyError:
      pass
    return result

  def _more_repr(self):
    return {
      "properties"  : len(self.properties),
      "definitions" : len(self.definitions)
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
    return out

  def dependencies(self):
    return list({
      dependency \
      for prop in self.properties \
      for dependency in prop.dependencies()
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

  def dependencies(self):
    return self._definition.dependencies()

class Property(Definition):
  pass

class ValueSchema(Schema):
  def _select(self, stack=[]): # no prop nor remainder accepted
    # print(stack, "value")
    return self

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

  def dependencies(self):
    if isinstance(self.items, Schema):
      return self.items.dependencies()
    else:
      return list({
        dependency \
        for item in self.items \
        for dependency in item.dependencies()
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
    for option in self.options:
      result = option._select(*path, stack=stack)
      if result: return result
    return None

  def dependencies(self):
    return list({
      dependency \
      for option in self.options \
      for dependency in option.dependencies()
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

  def dependencies(self):
    return  list(set( self.resolve().dependencies() + [ self ] ))

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


value_mapping = {
  "boolean": BooleanSchema,
  "integer": IntegerSchema,
  "null":    NullSchema,
  "number":  NumberSchema,
  "string":  StringSchema,
  "array":   ArraySchema
}

def defines_object(properties):
  return "type" in properties and \
       ( properties["type"] == "object" or \
         ( isinstance(properties["type"], list) and "object" in properties["type"] ) )

class NodesMapper(ASTVisitor):
  def visit_value(self, value_node):
    return value_node()

  def visit_object(self, object_node):
    properties = super().visit_object(object_node)
    properties["location"] = self.location(object_node)
    if defines_object(properties):
      # properties and definitions bubble up as Generic Schemas
      if "properties" in properties and properties["properties"]:
        properties["properties"] = [
          Property(name, definition) \
          for name, definition in properties["properties"].items()
        ]
      if "definitions" in properties and properties["definitions"]:
        properties["definitions"] = [
          Definition(name, definition) \
          for name, definition in properties["definitions"].items()
        ]
      return ObjectSchema(**properties)
    elif "type" in properties and properties["type"] in value_mapping:
      return value_mapping[properties["type"]](**properties)
    elif "allOf" in properties and isinstance(properties["allOf"], list):
      properties["options"] = properties.pop("allOf")
      return AllOf(**properties)
    elif "anyOf" in properties and isinstance(properties["anyOf"], list):
      properties["options"] = properties.pop("anyOf")
      return AnyOf(**properties)
    elif "oneOf" in properties and isinstance(properties["oneOf"], list):
      properties["options"] = properties.pop("oneOf")
      return OneOf(**properties)
    elif "$ref" in  properties and isinstance(properties["$ref"], str):
      properties["ref"] = properties.pop("$ref")
      return Reference(**properties)
    elif "enum" in properties and isinstance(properties["enum"], list):
      return Enum(**properties)
    else:
      return Schema(**properties)
