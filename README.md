# Schema Tools

> Collection of tools to parse, query, map,... Json/Yaml schemas

[![PyPI version](https://img.shields.io/pypi/v/schema-tools.svg)](https://pypi.org/project/schema-tools/)
[![Python versions](https://img.shields.io/pypi/pyversions/schema-tools.svg)](https://pypi.org/project/schema-tools/)
[![License](https://img.shields.io/github/license/christophevg/schema-tools.svg)](https://github.com/christophevg/schema-tools/blob/master/LICENSE.txt)
[![CI](https://github.com/christophevg/schema-tools/actions/workflows/test.yaml/badge.svg)](https://github.com/christophevg/schema-tools/actions/workflows/test.yaml)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-blue.svg)](https://github.com/astral-sh/ruff)
[![Type checked: mypy](https://img.shields.io/badge/type%20checked-mypy-blue.svg)](https://mypy.readthedocs.io/)
[![Documentation Status](https://readthedocs.org/projects/schema-tools/badge/?version=latest)](https://schema-tools.readthedocs.org/en/latest/?badge=latest)
[![Coverage Status](https://coveralls.io/repos/github/christophevg/schema-tools/badge.svg?branch=master)](https://coveralls.io/github/christophevg/schema-tools?branch=master)
[![Agentic](https://img.shields.io/badge/workflow-agentic-blueviolet?style=flat-square)](https://christophe.vg/about/Agentic-Workflow)

Schema Tools is a collection of utilities to load, parse, query, dereference
and map Json and Yaml schemas, with support for UBL / Schematron / PEPPOL
document validation on top. It ships a CLI (`schema-tools`) and an optional
web-based schema viewer.

## Features

- (loading of) Json and Yaml schemas with line/column-preserving Abstract
  Syntax Tree access
- a schema-oriented object model with `$ref` resolving, dereferencing and
  mapping
- selection, dependency extraction and round-trip (de)serialization
- UBL document validation (XSD + Schematron) with PEPPOL billing rules

## Installation

Using pip:

```bash
pip install schema-tools
```

Using uv:

```bash
uv add schema-tools
```

## Quick Start

```pycon
>>> from schema_tools import json
>>> j = json.loads('''{
...   "hello" : "world",
...   "count" : [ 1, 2, 3 ]
... }''')
>>> j
ObjectNode(len=2, line=1, column=1)
>>> j()
{'hello': 'world', 'count': [1, 2, 3]}
```

## Documentation

Full documentation available at [schema-tools.readthedocs.io](https://schema-tools.readthedocs.io/).

## Development

```bash
make env-dev    # Install all dependencies
make test       # Run tests
make lint       # Run linter
make typecheck  # Run type checker
make check      # Run all quality checks
make docs       # Build documentation
```

## License

MIT License - see [LICENSE](LICENSE.txt) for details.