from schema_tools.schema import load

def test_dependency_discovery_while_loading(asset):
  original_file = asset("invoice.json")
  schema = load(original_file)
  # invoice
  #   product
  #     guid
  #     money
  #   money
  # ----------
  # product, guid, money
  assert len(schema.dependencies()) == 3
