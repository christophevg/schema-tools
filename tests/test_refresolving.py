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

  assert isinstance(schema.property("home").definition.options[1], model.Reference)
  resolved = schema.property("home").definition.options[1].resolve()
  assert isinstance(resolved, model.StringSchema)
  assert resolved is schema.definition("id").definition
