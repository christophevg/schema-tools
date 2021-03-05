from schema_tools.schema import load, loads

def test_deref_to_dict(asset):
  original_file = asset("invoice.json")
  d = load(original_file).to_dict(deref=True)

  # undereferenced top-level definition and 1st level dereferenced definition 
  items = d["properties"]["lines"]["items"]
  assert items["properties"]["type"]["$ref"] == "#/definitions/type"
  assert items["properties"]["price"]["properties"]["taxed"]["$ref"] ==  \
    "#/properties/lines/items/properties/price/definitions/taxed"


  # simple included type and 2nd-level dereferenced definition
  product = items["properties"]["product"]
  assert product["properties"]["id"]["type"] == "string"
  assert product["properties"]["cost"]["properties"]["taxed"]["$ref"] == \
    "#/properties/lines/items/properties/product/properties/cost/definitions/taxed"

def test_ensure_derereferenced_schemas_drop_local_ids(asset):
  original_file = asset("invoice.json")
  d = load(original_file).to_dict(deref=True)

  assert "$id" not in d["properties"]["lines"]["items"]["properties"]["product"]

def test_ensure_dereferenced_combinations_generate_correct_ref_path(asset):
  original_file = asset("combination.json")
  d = load(original_file).to_dict(deref=True)

  assert d["properties"]["lines"]["anyOf"][1]["properties"]["subproduct"]["$ref"] == \
    "#/properties/lines/anyOf/1"
  