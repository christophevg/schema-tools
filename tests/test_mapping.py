from schema_tools         import json, model
from schema_tools.mapping import Mapping

def test_simple_string_mapping(schema):
  source = model.load(json.load(schema("product.json"))).select("cost.amount")
  target = model.load(json.load(schema("invoice.json"))).select("lines.price.amount")

  assert isinstance(source, model.IntegerSchema)
  assert isinstance(target, model.IntegerSchema)

  m = Mapping(source, target)

  assert m.is_valid
  assert not m.status

def test_different_value_schemas(schema):
  source = model.load(json.load(schema("product.json"))).select("cost.amount")
  target = model.load(json.load(schema("invoice.json"))).select("lines.price.currency")

  assert isinstance(source, model.IntegerSchema)
  assert isinstance(target, model.StringSchema)

  m = Mapping(source, target)

  assert not m.is_valid
  assert m.status
