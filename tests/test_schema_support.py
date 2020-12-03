from schema_tools             import json, yaml
from schema_tools.schema      import loads, load
from schema_tools.schema.json import StringSchema, IntegerSchema
from schema_tools.schema.json import ObjectSchema, Reference, AnyOf, Property

def test_string_schema():
  json_src = """{
    "$schema": "http://json-schema.org/draft-07/schema#",
    "$id": "test",
    "title": "a title",
    "description": "a description",
    "version": "123",
    "type": "string",
    "format": "uri-reference"
  }
  """

  schema = loads(json_src)
  
  assert isinstance(schema, StringSchema)

def test_object_schema():
  json_src = """{
    "$schema": "http://json-schema.org/draft-07/schema#",
    "$id": "test",
    "title": "a title",
    "description": "a description",
    "version": "123",
    "type": "object",
    "properties": {
      "url": {
        "type": "string",
        "format": "uri-reference"
      }
    }
  }
  """

  schema = loads(json_src)
  
  assert isinstance(schema, ObjectSchema)
  assert len(schema.properties) == 1
  assert schema.properties[0].name == "url"
  assert isinstance(schema.properties[0].definition, StringSchema)

def test_nested_object_schema():
  json_src = """{
    "$schema": "http://json-schema.org/draft-07/schema#",
    "$id": "test",
    "title": "a title",
    "description": "a description",
    "version": "123",
    "type": "object",
    "properties": {
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
  
  assert isinstance(schema, ObjectSchema)
  assert len(schema.properties) == 1
  assert schema.properties[0].name == "address"
  assert isinstance(schema.properties[0].definition, ObjectSchema)
  assert len(schema.properties[0].definition.properties) == 1
  assert schema.properties[0].definition.properties[0].name == "url"
  assert isinstance(schema.properties[0].definition.properties[0].definition, StringSchema)

def test_definitions():
  json_src = """{
    "$schema": "http://json-schema.org/draft-07/schema#",
    "$id": "test",
    "title": "a title",
    "description": "a description",
    "version": "123",
    "type": "object",
    "definitions" : {
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
  
  assert isinstance(schema, ObjectSchema)
  assert len(schema.definitions) == 1
  assert schema.definitions[0].name == "address"
  assert isinstance(schema.definitions[0].definition, ObjectSchema)
  assert len(schema.definitions[0].definition.properties) == 1
  assert schema.definitions[0].definition.properties[0].name == "url"
  assert isinstance(schema.definitions[0].definition.properties[0].definition, StringSchema)

def test_ref():
  json_src = """{
    "$schema": "http://json-schema.org/draft-07/schema#",
    "$id": "test",
    "title": "a title",
    "description": "a description",
    "version": "123",
    "type": "object",
    "properties" : {
      "home" : {
        "$ref" : "#/definitions/address"
      }
    },
    "definitions" : {
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
  
  assert isinstance(schema, ObjectSchema)
  assert len(schema.properties) == 1
  assert schema.properties[0].name == "home"
  assert schema.properties[0].is_ref()
  assert isinstance(schema.properties[0]._definition, Reference)

def test_anyof():
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
  
  assert isinstance(schema, ObjectSchema)
  assert len(schema.properties) == 1
  assert schema.properties[0].name == "home"
  assert isinstance(schema.properties[0].definition, AnyOf)
  assert len(schema.properties[0].definition.options) == 2
  assert isinstance(schema.properties[0].definition.options[0], Reference)
  assert isinstance(schema.properties[0].definition.options[1], Reference)

def test_all_of_properties():
  src = """
type: object
properties:
allof:
  - $ref: "#/definitions/something"
  - $ref: "#/definitions/somethingelse"
definitions:
  something:
    type: object
    properties:
      x:
        type: string
  somethingelse:
    type: object
    properties:
      y:
        type: integer        
"""
  schema = loads(src, parser=yaml)
  assert isinstance(schema.property("x"), StringSchema)
  assert isinstance(schema.property("y"), IntegerSchema)
  assert isinstance(schema.select("x"), Property)
  assert isinstance(schema.select("x").definition, StringSchema)

def test_combination_with_schema_dumping():
  src="""
{
  "type": "object",
  "properties": {
    "x" : {
      "type" : "string"
    },
    "y" : {
      "type" : "string"
    }
  },
  "oneOf": [
    {
      "required": [
        "x"
      ]
    },
    {
      "required": [
        "y"
      ]
    }
  ]
}
"""
  schema = loads(src)
  d = schema.to_dict()
  s = json.dumps(d)
  