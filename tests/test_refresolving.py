from schema_tools.schema      import loads
from schema_tools.schema.json import StringSchema, ObjectSchema, Reference, Enum
from schema_tools.schema.json import ArraySchema

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
  
  schema = loads(json_src)

  assert isinstance(schema.property("home").options[1], Reference)
  resolved = schema.property("home").options[1].resolve()
  assert isinstance(resolved, StringSchema)
  assert resolved is schema.definition("id")

def test_external_references(asset):
  json_src = """{
    "type": "object",
    "properties" : {
      "home" : {
        "$ref" : "file:%%%%"
      },
      "business" : {
        "$ref" : "https://localhost/schemas/unknown.json"
      }
    }
  }
  """.replace("%%%%", asset("guid.json"))

  schema = loads(json_src)
  
  assert isinstance(schema,                   ObjectSchema)
  home = schema.property("home", return_definition=False)
  assert home.is_ref()
  assert isinstance(home._definition,         Reference)
  assert isinstance(schema.property("home"),  StringSchema)

  try:
    schema.property("business").resolve()
    assert False
  except ValueError:
    pass

def test_external_reference_with_fragment(asset):
  json_src = """{
    "type": "object",
    "properties" : {
      "foreign" : {
        "$ref" : "file:%%%%"
      }
    }
  }
  """.replace("%%%%", asset("money.json#/properties/currency"))

  schema = loads(json_src)
  
  assert isinstance(schema, ObjectSchema)
  foreign = schema.property("foreign", return_definition=False)
  assert foreign.is_ref()
  assert isinstance(foreign._definition, Reference)
  assert isinstance(schema.property("foreign"), Enum)

def test_origin_of_external_reference(asset):
  json_src = """{
    "type": "object",
    "properties" : {
      "foreign" : {
        "$ref" : "file:%%%%"
      }
    }
  }
  """.replace("%%%%", asset("money.json#/properties/currency"))

  schema = loads(json_src)
  
  assert isinstance(schema.property("foreign"), Enum)
  assert isinstance(schema.property("foreign"), Enum)
  assert schema.property("foreign").origin.endswith("currencies.json")

def test_avoiding_recursing():
  src = """
{
  "type" : "object",
  "properties" : {
    "person" : {
      "$ref" : "#/definitions/human"
    }
  },
  "definitions" : {
    "human" : {
      "type" : "object",
      "properties" : {
        "parent" : {
          "$ref" : "#/definitions/human"
        }
      }
    }
  }
}
"""
  schema = loads(src)
  dependencies = schema.dependencies()
  assert True

def test_array_items_byref():
  src = """
{
  "type" : "object",
  "properties" : {
    "humanity" : {
      "type" : "array",
      "items" : {
        "$ref" : "#/definitions/human"
      }
    }
  },
  "definitions" : {
    "human" : {
      "type" : "object",
      "properties" : {
        "name" : {
          "type" : "string"
        }
      }
    }
  }
}
"""
  schema = loads(src)
  humanity = schema.property("humanity")
  assert isinstance(humanity.items, Reference)
  assert isinstance(humanity.items.resolve(), ObjectSchema)
  assert isinstance(humanity.items.resolve().property("name"), StringSchema)

