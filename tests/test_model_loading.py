from schema_tools             import yaml
from schema_tools.schema      import loads
from schema_tools.schema.json import StringSchema, ObjectSchema, Reference, AnyOf

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


def test_swagger_style_definitions():
  yaml_src = """
components:
  schemas:
    something:
      type: object
      properties:
      allOf:
        - $ref: '#/components/schemas/somethingElse'
      discriminator:
        propertyName: 'type'
"""

  schema = loads(yaml_src, parser=yaml)
  print(schema.to_dict())
  # assert False

def test_swagger_structure():
  yaml_src = """
openapi: 3.0.0
info:
  description: "deposits endpoint"
  version: "1.0.0"
  title: "vouchers"
paths:
  /make/deposit:
    post:
      summary: "make a deposit"
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: file:tests/schemas/money.json
      responses:
        '200':
          description: success
          content:
            application/json:
              schema:
                type: boolean
        '400':
          description: failure
          content:
            application/json:
              schema:
                type: string
"""
  schema = loads(yaml_src, yaml)
  print(schema.to_dict())
