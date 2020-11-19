from schema_tools.schema import loads, StringSchema, ObjectSchema, Definition

def test_simple_selections():
  json_src = """{
    "type": "object",
    "properties" : {
      "home" : {
        "type" : "string"
      },
      "business" : {
        "type" : "string"
      }
    }
  }
  """
  
  schema = loads(json_src)
  
  assert isinstance(schema,                    ObjectSchema)
  assert isinstance(schema.select("home"),     StringSchema)
  assert isinstance(schema.select("business"), StringSchema)

def test_nested_selections():
  json_src = """{
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
  
  schema = loads(json_src)
  
  assert isinstance(schema,                                ObjectSchema)
  assert isinstance(schema.select("home"),                 ObjectSchema)
  assert isinstance(schema.select("home.address"),         ObjectSchema)
  assert isinstance(schema.select("home.address.street"),  StringSchema)
  assert schema.select("home.address.phone") is None

def test_reference_to_definition_selections():
  json_src = """{
    "type": "object",
    "properties" : {
      "home" : {
        "type" : "object",
        "properties" : {
          "address" : {
            "$ref" : "#/definitions/address"
          }
        }
      }
    },
    "definitions" : {
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
  """
  
  schema = loads(json_src)
  
  assert isinstance(schema,                                ObjectSchema)
  assert isinstance(schema.select("home"),                 ObjectSchema)
  assert isinstance(schema.select("home.address"),         ObjectSchema)
  assert isinstance(schema.select("home.address.street"),  StringSchema)

def test_anyof_refs():
  json_src = """{
    "$schema": "http://json-schema.org/draft-07/schema#",
    "$id": "test",
    "title": "a title",
    "description": "a description",
    "version": "123",
    "type": "object",
    "properties" : {
      "home" : {
        "anyOf" : [
          { "$ref" : "#/definitions/address" },
          { "$ref" : "#/definitions/id"      }
        ]
      },
      "business" : {
        "anyOf" : [
          { "$ref" : "#/definitions/address" },
          { "$ref" : "#/definitions/id"      }
        ]
      }
    },
    "definitions" : {
      "id" : {
        "type" : "string"
      },
      "address" : {
        "type" : "object",
        "properties" : {
          "url": {
            "type": "string",
            "format": "uri-reference"
          }
        },
        "additionalProperties" : false,
        "required" : [
          "url"
        ]
      }
    }
  }
  """

  schema = loads(json_src)

  home     = schema.select("home.url")
  business = schema.select("business.url")

  assert isinstance(home, StringSchema)
  assert isinstance(business, StringSchema)

  # home = string <- property <- object <- definition
  assert isinstance(home.parent.parent.parent, Definition)
  assert home.parent.parent.parent.name == "address"
  assert isinstance(business.parent.parent.parent, Definition)
  assert business.parent.parent.parent.name == "address"

  assert home is business

def test_external_reference_with_fragment(asset):
  json_src = """{
    "type": "object",
    "properties" : {
      "foreign" : {
        "$ref" : "file:%%%%"
      }
    }
  }
  """.replace("%%%%", asset("money.json"))

  schema = loads(json_src)
  
  assert( isinstance(schema.select("foreign.currency"), StringSchema) )
