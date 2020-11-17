import json as native_json
import difflib

def diff(expected, actual):
  expected = expected.splitlines(1)
  actual = actual.splitlines(1)
  diff = difflib.unified_diff(expected, actual)
  return ''.join(diff)

from schema_tools import model
from schema_tools import json

def test_round_trip_spec(schema):
  original_file = schema("json-schema-draft-07.json")
  with open(original_file) as fp:
    original = native_json.load(fp)

  # load, parse and generate
  ast    = json.load(original_file)
  schema = model.load(ast)
  gen    = schema.to_dict()

  original_dump = json.dumps(original)
  gen_dump      = json.dumps(gen)
  
  print(diff(original_dump, gen_dump))
  assert original == gen
