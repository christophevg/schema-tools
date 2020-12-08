from schema_tools         import json, yaml
from schema_tools.utils   import ASTDumper
from schema_tools.ast     import ValueNode

def test_comparable_parsing():
  dumper = ASTDumper()
  
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
  json_txt = dumper.dump(json_ast)

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
  yaml_txt = dumper.dump(yaml_ast)

  assert(json_ast == yaml_ast)

def test_parse_dates():
  src = """
something:
  example: 2021-01-01
"""

  ast = yaml.loads(src)
  assert isinstance(ast["something"]["example"], ValueNode)
