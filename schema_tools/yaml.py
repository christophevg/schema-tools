import yaml
from yaml.loader import SafeLoader

from schema_tools.ast import ValueNode, ListNode, ObjectNode

def load(path):
  with open(path, "r") as file:
    return yaml.load(file, Loader=YamlSchemaLoader)

def loads(src):
  return yaml.load(src, Loader=YamlSchemaLoader)

class YamlSchemaLoader(yaml.SafeLoader):
  pass

def scalar_constructor(type=None):
  def constructor(loader, node):
    value = loader.construct_scalar(node)
    value = type(value) if type else None
    return ValueNode(value, node.start_mark.line+1, node.start_mark.column+1)      
  return constructor
yaml.add_constructor("tag:yaml.org,2002:timestamp",  scalar_constructor(str),   YamlSchemaLoader)
yaml.add_constructor("tag:yaml.org,2002:str",        scalar_constructor(str),   YamlSchemaLoader)
yaml.add_constructor("tag:yaml.org,2002:int",        scalar_constructor(int),   YamlSchemaLoader)
yaml.add_constructor("tag:yaml.org,2002:float",      scalar_constructor(float), YamlSchemaLoader)
yaml.add_constructor("tag:yaml.org,2002:bool",       scalar_constructor(bool),  YamlSchemaLoader)
yaml.add_constructor("tag:yaml.org,2002:null",       scalar_constructor(),      YamlSchemaLoader)

def list_constructor(loader, node):
  items = loader.construct_sequence(node)
  return ListNode(items, node.start_mark.line, node.start_mark.column+1)
yaml.add_constructor(yaml.resolver.BaseResolver.DEFAULT_SEQUENCE_TAG, list_constructor,  YamlSchemaLoader)

def dict_constructor(loader, node):
  mapping = loader.construct_mapping(node)
  mapping = { k() : v  for k, v in mapping.items() }
  return ObjectNode(mapping, node.start_mark.line, node.start_mark.column+1)
yaml.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, dict_constructor,  YamlSchemaLoader)
