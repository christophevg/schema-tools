import collections

import inspect

UnknownProperty = collections.namedtuple("UnknownProperty", "name definition")

from schema_tools        import json
from schema_tools.utils  import ASTVisitor

def load(path, parser=json):
  return build(parser.load(path), origin=path)

def loads(src, parser=json, origin=None):
  return build(parser.loads(src), origin=origin)

def build(nodes, origin=None):
  from schema_tools.schema.json import SchemaMapper
  schema = NodesMapper(SchemaMapper()).visit(nodes)
  schema._origin = origin
  return schema

class NodesMapper(ASTVisitor):
  def __init__(self, *mappers):
    super().__init__()
    self.mappers = [
      func \
      for mapper in mappers \
      for func in inspect.getmembers(mapper, predicate=callable) \
      if func[0].startswith("map_")
    ]

  def visit_value(self, value_node):
    return ConstantValueSchema(value=value_node(), _location=self.location(value_node))

  def visit_object(self, object_node):
    properties = super().visit_object(object_node)
    properties["_location"] = self.location(object_node)

    for name, mapper in self.mappers:
      result = mapper(properties)
      if result: return result

    return Schema(**properties)

class Mapper(object):
  def has(self, properties, name, of_type=None, containing=None):
    if not name in properties: return False
    value = properties[name]
    if isinstance(value, ConstantValueSchema):
      value = value.value
    if of_type:
      if isinstance(of_type, str):
        return value == of_type      
      elif isinstance(of_type, dict):
        return value in of_type
      else:
        if isinstance(value, of_type):
          if not containing or containing in value:
            return True
        return False
    return bool(value)

class Schema(object):
  args = {}
  _location = None
  _origin   = None

  def __init__(self, **kwargs):
    self.parent    = None
    self._location = None
    self._origin   = None
    if "_location" in kwargs:
      self._location = kwargs.pop("_location")
    self.args     = kwargs   # catchall properties
    # drop examples
    if "examples" in kwargs and not isinstance(kwargs["examples"], IdentifiedSchema):
      kwargs.pop("examples")

  def __getattr__(self, key):
    try:
      return self.args[key]
    except KeyError:
      return None

  def select(self, *path, stack=None):
    path = self._clean(path)
    if not path: return None
    # print("select", path)
    return self._select(*path, stack=stack)

  def trace(self, *path):
    path = self._clean(path)
    if not path: return []
    # print("trace", path)
    stack = []
    self.select(*path, stack=stack)
    # add UnknownProperties for not returned items in stack
    for missing in path[len(stack):]:
      stack.append(UnknownProperty(missing, None))
    return stack

  def _clean(self, path):
    if not path or path[0] is None: return None
    # ensure all parts in the path are strings
    for step in path:
      if not isinstance(step, str):
        raise ValueError("only string paths are selectable")
    # single path can be dotted string
    if len(path) == 1: path = path[0].split(".")
    return path

  def _select(self, *path, stack=None):
    # print(stack, "schema", path)
    return None # default

  def __repr__(self):
    props = { k: v for k, v in self.args.items() }  # TODO not "if v" ?
    props.update(self._more_repr())
    props["<location>"] = self._location
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
      elif isinstance(v, list):
        vv = []
        for i in v:
          vv.append(i.to_dict() if isinstance(i, Schema) else i)
        v = vv
      elif v is None or isinstance(v, (str, int, float)):
        pass
      else:
        print(v.__class__.__name__, v)
        raise NotImplementedError
      items[k] = v
    return items

  def items(self):
    return self.args.items()

  def dependencies(self, external=False, visited=None):
    return []

  @property
  def root(self):
    if not self.parent: return self
    p = self.parent
    while not p.parent is None:
      p = p.parent
    return p

  @property
  def origin(self):
    return self.root._origin

class IdentifiedSchema(Schema): pass

class ConstantValueSchema(IdentifiedSchema):
  def to_dict(self):
    return self.value

