from schema_tools.schema      import loads
from schema_tools.schema.json import Property

def test_selecting_into_all_of():
  src = """
{
  "type" : "object",
  "allOf" : [
    { "$ref" : "#/definitions/x" },
    { "$ref" : "#/definitions/y" },
    { "$ref" : "#/definitions/z" }
  ],
  "definitions" : {
    "x" : {
      "type" : "object",
      "properties" : {
        "a": {
          "type" : "string"
        }
      }
    },
    "y" : {
      "type" : "object",
      "properties" : {
        "b": {
          "type" : "string"
        }
      }
    },
    "z" : {
      "type" : "object",
      "properties" : {
        "c": {
          "type" : "string"
        }
      }
    }
  }
}
"""

  schema = loads(src)
  assert isinstance( schema.select("a"), Property )
  assert schema.select("a").name == "a"
  assert isinstance( schema.select("c"), Property )
  assert schema.select("c").name == "c"

def test_selecting_into_one_of():
  src = """
{
  "type" : "object",
  "oneOf" : [
    { "$ref" : "#/definitions/x" },
    { "$ref" : "#/definitions/y" },
    { "$ref" : "#/definitions/z" }
  ],
  "definitions" : {
    "x" : {
      "type" : "object",
      "properties" : {
        "a": {
          "type" : "string"
        }
      }
    },
    "y" : {
      "type" : "object",
      "properties" : {
        "b": {
          "type" : "string"
        }
      }
    },
    "z" : {
      "type" : "object",
      "properties" : {
        "c": {
          "type" : "string"
        }
      }
    }
  }
}
"""

  schema = loads(src)
  assert isinstance( schema.select("a"), Property )
  assert schema.select("a").name == "a"
  assert isinstance( schema.select("c"), Property )
  assert schema.select("c").name == "c"

def test_selecting_into_any_of():
  src = """
{
  "type" : "object",
  "anyOf" : [
    { "$ref" : "#/definitions/x" },
    { "$ref" : "#/definitions/y" },
    { "$ref" : "#/definitions/z" }
  ],
  "definitions" : {
    "x" : {
      "type" : "object",
      "properties" : {
        "a": {
          "type" : "string"
        }
      }
    },
    "y" : {
      "type" : "object",
      "properties" : {
        "b": {
          "type" : "string"
        }
      }
    },
    "z" : {
      "type" : "object",
      "properties" : {
        "c": {
          "type" : "string"
        }
      }
    }
  }
}
"""

  schema = loads(src)
  assert isinstance( schema.select("a"), Property )
  assert schema.select("a").name == "a"
  assert isinstance( schema.select("c"), Property )
  assert schema.select("c").name == "c"
