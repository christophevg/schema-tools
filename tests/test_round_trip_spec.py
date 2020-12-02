import json
import difflib

def diff(expected, actual):
  expected = expected.splitlines(1)
  actual = actual.splitlines(1)
  diff = difflib.unified_diff(expected, actual)
  return ''.join(diff)

from schema_tools.schema import load, loads
from schema_tools.schema.json import ObjectSchema, AnyOf, Reference, Property, Enum

def test_round_trip_spec(asset):
  original_file = asset("json-schema-draft-07.json")
  with open(original_file) as fp:
    original = json.load(fp)

  # load, parse and generate
  schema = load(original_file).to_dict()

  original_dump = json.dumps(original)
  gen_dump      = json.dumps(schema)
  
  print(diff(original_dump, gen_dump))
  assert original == schema

def test_untyped_object():
  src = """
{
  "type": "object",
  "properties": {
    "properties": {
      "type": "object",
      "additionalProperties": { "$ref": "#" },
    },
    "something" : {
      "properties" : {
        "a" : {
          "type" : "object"
        },
        "properties" : {
          "$ref" : "#"
        }
      }
    },
    "somethingelse" : {
      "properties" : {
        "properties" : {
          "type" : "string"
        }
      }
    },
    "type": {
      "anyOf": [
        { "type" : "string" },
        {
          "type": "array",
          "items": { "type" : "string" }
        }
      ]
    }
  },
  "format": { "type": "string" },
  "definitions" : {
    "properties" : {
      "enum" : [
        "a",
        "b"
      ]
    }
  }
}
"""
  schema = loads(src)
  assert isinstance(schema.property("properties"), ObjectSchema)
  assert isinstance(schema.property("type"), AnyOf)
  assert isinstance(schema.property("something"), ObjectSchema)
  assert isinstance(schema.select("something.properties"), Property)
  assert isinstance(schema.select("somethingelse.properties"), Property)
  assert isinstance(schema.definition("properties"), Enum)
