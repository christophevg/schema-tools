from schema_tools import json, yaml

def test_comparable_parsing():
  json_src = """{
    "a" : 1,
    "b" : [ 
      2,
      3,
    ],
    "c" : {
      "i1" : true,
      "i2" : "a",
      "i3" : null
    }
  }"""

  json_ast = json.loads(json_src)
  json_txt = dump(json_ast)

  yaml_src = """
  a : 1
  b :
    - 2
    - 3

  c :
    i1 : true
    i2 : "a"
    i3 : null
  """

  yaml_ast = yaml.loads(yaml_src)
  yaml_txt = dump(yaml_ast)

  assert(json_txt == yaml_txt)


from jsoncfg.config_classes import ConfigJSONObject, ConfigJSONArray, ConfigJSONScalar
from schema_tools.nodes     import ObjectNode, ListNode, ValueNode

def dump(ast, indent=0):
  txt = ""
  if isinstance(ast, (ObjectNode, ConfigJSONObject)):
    for key, value in ast:
      txt += "  " * indent + "@{}".format(value._line) + " " + key + "\n"
      # expect key to be on same line as value
      txt += dump(value, indent+1)
  elif isinstance(ast, (ListNode, ConfigJSONArray)):
    for item in ast:
      txt += dump(item, indent+1)
  elif isinstance(ast, (ValueNode, ConfigJSONScalar)):
    txt += "  " * indent + "@{}".format(ast._line) + " " + str(ast()) + "\n"
  return txt
