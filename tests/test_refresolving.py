from schema_tools import json, model

def test_simple_local_ref_to_definition():
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

  assert isinstance(schema.property("home").options[1], model.Reference)
  resolved = schema.property("home").options[1].resolve()
  assert isinstance(resolved, model.StringSchema)
  assert resolved is schema.definition("id")

def test_external_references(schema):
  json_src = """{
    "type": "object",
    "properties" : {
      "home" : {
        "$ref" : "file:%%%%"
      },
      "business" : {
        "$ref" : "https://example.com/schemas/unknown.json"
      }
    }
  }
  """.replace("%%%%", schema("guid.json"))

  ast    = json.loads(json_src)
  schema = model.load(ast)
  
  assert( isinstance(schema,                            model.ObjectSchema) )
  assert( isinstance(schema.property("home"),           model.Reference)    )
  assert( isinstance(schema.property("home").resolve(), model.StringSchema) )

  try:
    schema.property("business").resolve()
    assert False
  except ValueError:
    pass

def test_external_reference_with_fragment(schema):
  json_src = """{
    "type": "object",
    "properties" : {
      "foreign" : {
        "$ref" : "file:%%%%"
      }
    }
  }
  """.replace("%%%%", schema("money.json#/properties/currency"))

  ast    = json.loads(json_src)
  schema = model.load(ast)
  
  assert( isinstance(schema,                               model.ObjectSchema) )
  assert( isinstance(schema.property("foreign"),           model.Reference)    )
  assert( isinstance(schema.property("foreign").resolve(), model.StringSchema) )
