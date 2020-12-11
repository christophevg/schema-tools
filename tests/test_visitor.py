from schema_tools             import yaml
from schema_tools.schema      import build
from schema_tools.schema.json import IntegerSchema, StringSchema, TupleItem

def test_allow_for_empty_properties():
  # empty properties shouldn't fail building object schema from AST
  ast = yaml.loads("""
  something:
    type: object
    properties:  
  """)
  schema = build(ast)
  assert len(schema.something.properties) == 0

def test_allow_for_no_items():
  # empty properties shouldn't fail building object schema from AST
  ast = yaml.loads("""
  something:
    type: array
  """)
  schema = build(ast)
  assert schema.something.items is None

def test_allow_for_tuple_items():
  # tuple properties shouldn't fail building object schema from AST
  ast = yaml.loads("""
  something:
    type: array
    items:
      - type: integer
      - type: string
  """)
  schema = build(ast)
  assert isinstance(schema.something.items, list)
  assert len(schema.something.items) == 2
  assert isinstance(schema.something.items[0], TupleItem)
  assert isinstance(schema.something.items[0].definition, IntegerSchema)
  assert isinstance(schema.something.items[1].definition, StringSchema)
