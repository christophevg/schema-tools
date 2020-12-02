from schema_tools.schema      import load
from schema_tools.schema.json import IntegerSchema, StringSchema
from schema_tools.mapping     import Mapping

def test_simple_string_mapping(asset):
  source = load(asset("product.json")).select("cost.amount").definition
  target = load(asset("invoice.json")).select("lines.price.amount").definition

  assert isinstance(source, IntegerSchema)
  assert isinstance(target, IntegerSchema)

  m = Mapping(source, target)

  assert m.is_valid
  assert not m.errors

def test_different_value_schemas(asset):
  source = load(asset("product.json")).select("cost.amount").definition
  target = load(asset("invoice.json")).select("lines.price.currency").definition

  assert isinstance(source, IntegerSchema)
  assert isinstance(target, StringSchema)

  m = Mapping(source, target)

  assert not m.is_valid
  assert m.errors
