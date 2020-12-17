from schema_tools.schema import loads

def test_nested_selections():
  src = """{
    "type": "object",
    "properties" : {
      "home" : {
        "type" : "object",
        "properties" : {
          "address" : {
            "type" : "object",
            "properties" : {
              "street" : {
                "type" : "string"
              }
            }
          }
        }
      }
    }
  }
  """

  schema = loads(src)
  assert schema.select("home")._location.line == 4
  assert schema.select("home.address")._location.line == 7
