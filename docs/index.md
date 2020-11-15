# Schema Tools

> Collection of tools to parse, query, map,... Json/Yaml schemas

[![Latest Version on PyPI](https://img.shields.io/pypi/v/schema-tools.svg)](https://pypi.python.org/pypi/schema-tools/)
[![Supported Implementations](https://img.shields.io/pypi/pyversions/schema-tools.svg)](https://pypi.python.org/pypi/schema-tools/)
[![Build Status](https://secure.travis-ci.org/christophevg/schema-tools.svg?branch=master)](http://travis-ci.org/christophevg/schema-tools)
[![Documentation Status](https://readthedocs.org/projects/schema-tools/badge/?version=latest)](https://schema-tools.readthedocs.io/en/latest/?badge=latest)
[![Coverage Status](https://coveralls.io/repos/github/christophevg/schema-tools/badge.svg?branch=master)](https://coveralls.io/github/christophevg/schema-tools?branch=master)
[![Built with PyPi Template](https://img.shields.io/badge/PyPi_Template-v0.1.4-blue.svg)](https://github.com/christophevg/pypi-template)

## Features at a Glance

- support for (loading of) Json and Yaml schemas with additional access to line and column information

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
ConfigJSONObject(len=2, line=1, column=1)
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
ConfigYamlObject(len=2, line=1, column=0)
>>> y()
{'hello': 'world', 'count': [1, 2, 3]}

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

- access using ref-like selectors (e.g. "properties.some_object.some_property")

**TODO: add example**

- define mapping between schemas with mapping validation

**TODO: add example**

## Contents

* [What is in the Box](whats-in-the-box.md)
* [Getting Started](getting-started.md)
* [Contributing](contributing.md)
