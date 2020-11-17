from schema_tools import json, model

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

  ast    = json.loads(json_src)
  schema = model.load(ast)
  
  assert isinstance(schema, model.StringSchema)

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

  ast    = json.loads(json_src)
  schema = model.load(ast)
  
  assert isinstance(schema, model.ObjectSchema)
  assert len(schema.properties) == 1
  assert schema.properties[0].name == "url"
  assert isinstance(schema.properties[0].definition, model.StringSchema)

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

  ast    = json.loads(json_src)
  schema = model.load(ast)
  
  assert isinstance(schema, model.ObjectSchema)
  assert len(schema.properties) == 1
  assert schema.properties[0].name == "address"
  assert isinstance(schema.properties[0].definition, model.ObjectSchema)
  assert len(schema.properties[0].definition.properties) == 1
  assert schema.properties[0].definition.properties[0].name == "url"
  assert isinstance(schema.properties[0].definition.properties[0].definition, model.StringSchema)

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

  ast    = json.loads(json_src)
  schema = model.load(ast)
  
  assert isinstance(schema, model.ObjectSchema)
  assert len(schema.definitions) == 1
  assert schema.definitions[0].name == "address"
  assert isinstance(schema.definitions[0].definition, model.ObjectSchema)
  assert len(schema.definitions[0].definition.properties) == 1
  assert schema.definitions[0].definition.properties[0].name == "url"
  assert isinstance(schema.definitions[0].definition.properties[0].definition, model.StringSchema)

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

  ast    = json.loads(json_src)
  schema = model.load(ast)
  
  assert isinstance(schema, model.ObjectSchema)
  assert len(schema.properties) == 1
  assert schema.properties[0].name == "home"
  assert isinstance(schema.properties[0].definition, model.Reference)

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
  
  ast    = json.loads(json_src)
  schema = model.load(ast)
  
  assert isinstance(schema, model.ObjectSchema)
  assert len(schema.properties) == 1
  assert schema.properties[0].name == "home"
  assert isinstance(schema.properties[0].definition, model.AnyOf)
  assert len(schema.properties[0].definition.options) == 2
  assert isinstance(schema.properties[0].definition.options[0], model.Reference)
  assert isinstance(schema.properties[0].definition.options[1], model.Reference)
