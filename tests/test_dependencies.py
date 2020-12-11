from schema_tools.schema import load, loads

def test_dependency_discovery(asset):
  original_file = asset("invoice.json")
  schema = load(original_file)
  # invoice
  #   product
  #     guid
  #     money
  #       currencies
  #   money
  #     currencies
  # ----------
  # product, guid, money
  assert len(schema.dependencies()) == 2                # product and money
  assert len(schema.dependencies(external=True)) == 4   # + guid and currencies

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


def test_dependencies_in_combination(asset):
  src = """
{
  "type" : "object",
  "allOf" : [
    { "$ref" : "#/definitions/x" },
    { "$ref" : "#/definitions/y" },
    { "$ref" : "#/definitions/z" }
  ],
  "definitions" : {
    "x" : {
      "type" : "object",
      "properties" : {
        "a": {
          "type" : "string"
        }
      }
    },
    "y" : {
      "type" : "object",
      "properties" : {
        "b": {
          "type" : "string"
        }
      }
    },
    "z" : {
      "type" : "object",
      "properties" : {
        "c": {
          "$ref" : "file:%%%%"
        }
      }
    }
  }
}
""".replace("%%%%", asset("money.json"))

  schema = loads(src)
  assert len(schema.dependencies()) == 1

def test_dependencies_in_tuple(asset):
  src = """
{
  "type" : "array",
  "items" : [
    {
      "type" : "string"
    },
    {
      "$ref" : "file:%%%%"
    }
  ]
}
""".replace("%%%%", asset("money.json"))

  schema = loads(src)
  assert len(schema.dependencies()) == 1
