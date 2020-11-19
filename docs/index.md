# Schema Tools

> Collection of tools to parse, query, map,... Json/Yaml schemas

[![Latest Version on PyPI](https://img.shields.io/pypi/v/schema-tools.svg)](https://pypi.python.org/pypi/schema-tools/)
[![Supported Implementations](https://img.shields.io/pypi/pyversions/schema-tools.svg)](https://pypi.python.org/pypi/schema-tools/)
[![Build Status](https://secure.travis-ci.org/christophevg/schema-tools.svg?branch=master)](http://travis-ci.org/christophevg/schema-tools)
[![Documentation Status](https://readthedocs.org/projects/schema-tools/badge/?version=latest)](https://schema-tools.readthedocs.io/en/latest/?badge=latest)
[![Coverage Status](https://coveralls.io/repos/github/christophevg/schema-tools/badge.svg?branch=master)](https://coveralls.io/github/christophevg/schema-tools?branch=master)
[![Built with PyPi Template](https://img.shields.io/badge/PyPi_Template-v0.1.4-blue.svg)](https://github.com/christophevg/pypi-template)

## Features at a Glance

- support for (loading of) Json and Yaml schemas with additional access to line and column information as an Abstract Syntax Tree (AST)

```pycon
>>> from schema_tools import json
>>> j = json.loads('''{
...   "hello" : "world",
...   "count" : [
...     1,
...     2,
...     3
...   ]
... }''')
>>> j
ObjectNode(len=2, line=1, column=1)
>>> j()
{'hello': 'world', 'count': [1, 2, 3]}

>>> from schema_tools import yaml
>>> y = yaml.loads('''
... hello : world
... count :
... - 1
... - 2
... - 3
... ''')
>>> y
ObjectNode(len=2, line=1, column=1)
>>> y()
{'hello': 'world', 'count': [1, 2, 3]}

>>> for k, v in y:
...   print(k, v)
... 
hello ValueNode(value=world, line=2, column=9)
count ListNode(len=3, line=3, column=1)

>>> from schema_tools.utils import node_location
>>> l = node_location(j.count)
>>> l.line
3
>>> l.column
13
>>> node_location(y.count)
NodeLocation(3, 0)
>>> node_location(j["count"])
NodeLocation(3, 13)
>>> node_location(y["count"])
NodeLocation(3, 0)
```

- a schema oriented object model

<!---
from schema_tools.schema import loads
json_src = '''
{
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
}'''
schema = loads(json_src)
schema
schema.properties[0]
schema.properties[0].definition.options[1]
schema.properties[0].definition.options[1].resolve()
schema.properties[0].definition.options[1].resolve().parent.name
-->

```pycon
>>> from schema_tools.schema import loads
>>> json_src = '''
... {
...   "$schema": "http://json-schema.org/draft-07/schema#",
...   "$id": "test",
...   "title": "a title",
...   "description": "a description",
...   "version": "123",
...   "type": "object",
...   "properties" : {
...     "home" : {
...       "anyOf" : [
...         { "$ref" : "#/definitions/address" },
...         { "$ref" : "#/definitions/id"      }
...       ]
...     }
...   },
...   "definitions" : {
...     "id" : {
...       "type" : "string"
...     },
...     "address" : {
...       "type" : "object",
...       "properties" : {
...         "url": {
...           "type": "string",
...           "format": "uri-reference"
...         }
...       },
...       "additionalProperties" : false,
...       "required" : [
...         "url"
...       ]
...     } 
...   }
... }'''
>>> schema = loads(json_src)
>>> schema
ObjectSchema($schema=http://json-schema.org/draft-07/schema#, $id=test, title=a title, description=a description, version=123, type=object, properties=1, definitions=2, location=NodeLocation(line=2, column=1))
>>> schema.properties[0]
Property(name=home, definition=AnyOf(options=2, location=NodeLocation(line=10, column=14)), location=None)
>>> schema.properties[0].definition.options[1]
Reference(ref=#/definitions/id)
>>> schema.properties[0].definition.options[1].resolve()
StringSchema(type=string, location=NodeLocation(line=18, column=12))
>>> schema.properties[0].definition.options[1].resolve().parent.name
'id'
```

- (re) generate dict/textual representation

<!---
import json
from schema_tools.schema import load
schema = load("tests/schemas/json-schema-draft-07.json")
d = schema.to_dict()
s = json.dumps(d, indent=2, sort_keys=True)
print(s[:150], "{}\n...\n{}".format(s[:147], s[-83:]))
-->

```pycon
>>> import json
>>> from schema_tools.schema import load
>>> schema = load("tests/schemas/json-schema-draft-07.json")
>>> d = schema.to_dict()
>>> s = json.dumps(d, indent=2, sort_keys=True)
>>> print(s[:150], "{}\n...\n{}".format(s[:147], s[-83:]))
{
  "$id": "http://json-schema.org/draft-07/schema#",
  "$schema": "http://json-schema.org/draft-07/schema#",
  "default": true,
  "definitions": {
   {
  "$id": "http://json-schema.org/draft-07/schema#",
  "$schema": "http://json-schema.org/draft-07/schema#",
  "default": true,
  "definitions": {
...
  "title": "Core schema meta-schema",
  "type": [
    "object",
    "boolean"
  ]
}
```

- use property selectors - across schema boundaries ;-)

<!---
from schema_tools.schema import load
schema = load("tests/schemas/invoice.json")
amount = schema.select("lines.price.amount")
amount.parent.parent
-->

```pycon
>>> from schema_tools.schema import load
>>> schema = load("tests/schemas/invoice.json")
>>> amount = schema.select("lines.price.amount")
>>> amount.parent.parent
ObjectSchema($schema=http://json-schema.org/draft-07/schema#, $id=file:tests/schemas/money.json, type=object, version=1, additionalProperties=False, required=['amount', 'currency'], properties=2, definitions=0, location=NodeLocation(line=1, column=1))
```

- define mapping between schemas with mapping validation

<!---
from schema_tools.schema import load
source = load("tests/schemas/product.json").select("cost.amount")
target = load("tests/schemas/invoice.json").select("lines.price.amount")
from schema_tools.mapping import Mapping
m = Mapping(source, target)
m.is_valid
target = load("tests/schemas/invoice.json").select("lines.price.currency")
m = Mapping(source, target)
m.is_valid
False
print(m.status)
-->

```pycon
>>> from schema_tools.schema import load
>>> source = load("tests/schemas/product.json").select("cost.amount")
>>> target = load("tests/schemas/invoice.json").select("lines.price.amount")
>>> from schema_tools.mapping import Mapping
>>> m = Mapping(source, target)
>>> m.is_valid
True
>>> target = load("tests/schemas/invoice.json").select("lines.price.currency")
>>> m = Mapping(source, target)
>>> m.is_valid
False
>>> False
False
>>> print(m.status)
source:IntegerSchema(type=integer, location=NodeLocation(line=7, column=15))
target:StringSchema(type=string, location=NodeLocation(line=10, column=17))
source type 'IntegerSchema' doesn't match target type 'StringSchema'
```

## Contents

* [What is in the Box](whats-in-the-box.md)
* [Getting Started](getting-started.md)
* [Contributing](contributing.md)
