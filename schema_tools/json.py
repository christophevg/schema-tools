import json
import jsoncfg
from jsoncfg.config_classes import ConfigJSONObject, ConfigJSONArray, ConfigJSONScalar

from schema_tools.utils import node_location, Visitor
from schema_tools.ast   import ValueNode, ListNode, ObjectNode

def load(path):
  return JsonConfigMapper().visit(jsoncfg.load_config(path))

def loads(source):
  return JsonConfigMapper().visit(jsoncfg.loads_config(source))

def dumps(obj, indent=2, sort_keys=True):
  return json.dumps(obj, indent=indent, sort_keys=sort_keys)


class JsonConfigMapper(Visitor):
  def __init__(self):
    super().__init__(ConfigJSONScalar, ConfigJSONArray, ConfigJSONObject)
  
  def visit_value(self, value_node):
    return ValueNode(value_node(), *node_location(value_node))

  def visit_list(self, list_node):
    children = [ self.visit(child) for child in list_node ]
    return ListNode(children, *node_location(list_node))

  def visit_object(self, object_node):
    children = { key : self.visit(child) for key, child in object_node }
    return ObjectNode(children, *node_location(object_node))
