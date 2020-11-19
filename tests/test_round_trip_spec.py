import json
import difflib

def diff(expected, actual):
  expected = expected.splitlines(1)
  actual = actual.splitlines(1)
  diff = difflib.unified_diff(expected, actual)
  return ''.join(diff)

from schema_tools.schema import load

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
