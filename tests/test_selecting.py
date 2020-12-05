from schema_tools.schema      import loads, load
from schema_tools.schema.json import StringSchema, ObjectSchema, ArraySchema, IntegerSchema
from schema_tools.schema.json import Definition, Property, Enum

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
  
  assert isinstance(schema,                               ObjectSchema)
  home = schema.select("home")
  assert isinstance(home, Property)
  assert isinstance(home.definition, StringSchema)

  assert isinstance(schema.select("business").definition, StringSchema)

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
  assert isinstance(schema.select("home").definition,                 ObjectSchema)
  assert isinstance(schema.select("home.address").definition,         ObjectSchema)
  assert isinstance(schema.select("home.address.street").definition,  StringSchema)
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

  assert isinstance(schema,                                           ObjectSchema)
  assert isinstance(schema.select("home").definition,                 ObjectSchema)
  assert isinstance(schema.select("home.address").definition,         ObjectSchema)
  assert isinstance(schema.select("home.address.street").definition,  StringSchema)

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

  home     = schema.select("home.url").definition
  business = schema.select("business.url").definition

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

  assert( isinstance(schema.select("foreign.currency").definition, Enum) )

def test_tracing(asset):
  schema = load(asset("invoice.json"))
  trace  = schema.trace("lines.price.amount")

  assert len(trace) == 3
  assert trace[0].name == "lines"  and isinstance(trace[0].definition, ArraySchema)
  assert trace[1].name == "price"  and isinstance(trace[1].definition, ObjectSchema)
  assert trace[2].name == "amount" and isinstance(trace[2].definition, IntegerSchema)

def test_none_selectors(asset):
  schema = load(asset("invoice.json"))
  assert schema.select(None) is None
  assert schema.select() is None
  assert schema.trace(None) == []
  trace = schema.trace(None, "lines")
  assert len(trace) == 0

def test_none_string_selectors(asset):
  schema = load(asset("invoice.json"))
  try:
    schema.select(1)
    assert False
  except ValueError:
    pass
  try:
    schema.select("lines", 1)
    assert False
  except ValueError:
    pass

def test_incomplete_trace(asset):
  schema = load(asset("invoice.json"))
  trace  = schema.trace("lines.price.amount2")

  assert len(trace) == 3
  assert trace[0].name == "lines"   and isinstance(trace[0].definition, ArraySchema)
  assert trace[1].name == "price"   and isinstance(trace[1].definition, ObjectSchema)
  assert trace[2].name == "amount2" and trace[2].definition is None

def test_overlapping_paths():
  src = """
{
  "type": "object",
  "properties": {
    "collection": {
      "type": "array",
      "items": {
        "oneOf" : [
          {
            "type" : "object",
            "properties" : {
              "product" : {
                "tag" : 1,
                "type" : "object",
                "properties" : {
                  "name" : {
                    "type" : "string"
                  }
                }
              }
            }
          },
          {
            "type" : "object",
            "properties" : {
              "product" : {
                "tag" : 2,
                "type" : "object",
                "properties" : {
                  "label" : {
                    "type" : "string"
                  }
                }
              }
            }
          },
          {
            "type" : "object",
            "properties" : {
              "product" : {
                "tag" : 3,
                "type" : "object",
                "properties" : {
                  "label" : {
                    "type" : "object",
                    "properties" : {
                      "nl" : {
                        "type" : "string"
                      }
                    }
                  }
                }
              }
            }
          }
        ]
      }
    }
  }
}
"""

  schema = loads(src)
  trace = schema.trace("collection.product.label")
  assert len(trace) == 3
  assert trace[1].definition.tag == 2

  trace = schema.trace("collection.product.label.nl")
  assert len(trace) == 4
  assert trace[1].definition.tag == 3
