from schema_tools.schema  import load, IntegerSchema, StringSchema
from schema_tools.mapping import Mapping

def test_simple_string_mapping(asset):
  source = load(asset("product.json")).select("cost.amount")
  target = load(asset("invoice.json")).select("lines.price.amount")

  assert isinstance(source, IntegerSchema)
  assert isinstance(target, IntegerSchema)

  m = Mapping(source, target)

  assert m.is_valid
  assert not m.errors

def test_different_value_schemas(asset):
  source = load(asset("product.json")).select("cost.amount")
  target = load(asset("invoice.json")).select("lines.price.currency")

  assert isinstance(source, IntegerSchema)
  assert isinstance(target, StringSchema)

  m = Mapping(source, target)

  assert not m.is_valid
  assert m.errors
