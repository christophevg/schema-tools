from schema_tools.schema import load, loads

def test_deref_to_dict(asset):
  original_file = asset("invoice.json")
  d = load(original_file).to_dict(deref=True)

  # undereferenced top-level definition and 1st level dereferenced definition 
  items = d["properties"]["lines"]["items"]
  assert items["properties"]["type"]["$ref"] == "#/definitions/type"
  assert items["properties"]["price"]["properties"]["taxed"]["$ref"] ==  \
    "#/properties/lines/properties/price/definitions/taxed"


  # simple included type and 2nd-level dereferenced definition
  product = items["properties"]["product"]
  assert product["properties"]["id"]["type"] == "string"
  assert product["properties"]["cost"]["properties"]["taxed"]["$ref"] == \
    "#/properties/lines/properties/product/properties/cost/definitions/taxed"
