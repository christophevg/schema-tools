from schema_tools         import json, yaml
from schema_tools.utils   import ASTDumper

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
