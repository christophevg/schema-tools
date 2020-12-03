from schema_tools.schema import load, loads

def test_dependency_discovery(asset):
  original_file = asset("invoice.json")
  schema = load(original_file)
  # invoice
  #   product
  #     guid
  #     money
  #   money
  # ----------
  # product, guid, money
  assert len(schema.dependencies()) == 2                # product and money
  assert len(schema.dependencies(external=True)) == 3   # guid in addition

def test_dependencies_within_references(asset):
  src = """
{
  "type": "object",
  "properties" : {
    "a" : {
      "$ref" : "#/definitions/aType"
    }
  },
  "definitions" : {
    "aType" : {
      "$ref" : "file:%%%%"
    }
  }
}
""".replace("%%%%", asset("money.json"))

  schema = loads(src)
  assert len(schema.dependencies()) == 1

def test_dependencies_within_references(asset):
  src = """
{
  "type": "object",
  "properties" : {
    "a" : {
      "$ref" : "#/definitions/aType"
    }
  },
  "definitions" : {
    "aType" : {
      "type" : "object",
      "properties" : {
        "b" : {
          "$ref" : "file:%%%%"
        }
      }
    }
  }
}
""".replace("%%%%", asset("money.json"))

  schema = loads(src)
  assert len(schema.dependencies()) == 1
