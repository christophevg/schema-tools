from schema_tools import json, model

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
  
  ast    = json.loads(json_src)
  schema = model.load(ast)
  
  assert isinstance(schema,                    model.ObjectSchema)
  assert isinstance(schema.select("home"),     model.StringSchema)
  assert isinstance(schema.select("business"), model.StringSchema)

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
  
  ast    = json.loads(json_src)
  schema = model.load(ast)
  
  assert isinstance(schema,                                model.ObjectSchema)
  assert isinstance(schema.select("home"),                 model.ObjectSchema)
  assert isinstance(schema.select("home.address"),         model.ObjectSchema)
  assert isinstance(schema.select("home.address.street"),  model.StringSchema)
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
  
  ast    = json.loads(json_src)
  schema = model.load(ast)
  
  assert isinstance(schema,                                model.ObjectSchema)
  assert isinstance(schema.select("home"),                 model.ObjectSchema)
  assert isinstance(schema.select("home.address"),         model.ObjectSchema)
  assert isinstance(schema.select("home.address.street"),  model.StringSchema)

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

  ast    = json.loads(json_src)
  schema = model.load(ast)

  home     = schema.select("home.url")
  business = schema.select("business.url")

  assert isinstance(home, model.StringSchema)
  assert isinstance(business, model.StringSchema)

  # home = string <- property <- object <- definition
  assert isinstance(home.parent.parent.parent, model.Definition)
  assert home.parent.parent.parent.name == "address"
  assert isinstance(business.parent.parent.parent, model.Definition)
  assert business.parent.parent.parent.name == "address"

  assert home is business

def test_external_reference_with_fragment(schema):
  json_src = """{
    "type": "object",
    "properties" : {
      "foreign" : {
        "$ref" : "file:%%%%"
      }
    }
  }
  """.replace("%%%%", schema("money.json"))

  ast    = json.loads(json_src)
  schema = model.load(ast)
  
  assert( isinstance(schema.select("foreign.currency"), model.StringSchema) )
