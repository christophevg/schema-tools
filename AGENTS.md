# AGENTS.md — schema-tools

Collection of tools to load, parse, query, dereference and map JSON/YAML
schemas, with UBL / Schematron / PEPPOL document validation on top. Ships a
CLI (`schema-tools`) and an optional Flask web viewer. Published to PyPI as
`schema-tools`, docs on ReadTheDocs.

## Module map (`src/schema_tools/`)

| Module | Role |
|--------|------|
| `ast.py` | line/column-preserving AST for JSON/YAML |
| `json.py`, `yaml.py` | schema loading (via `ast.py`) |
| `schema/__init__.py` | core schema object model: `$ref` resolving, dereferencing, selection, dependency extraction, mapping |
| `schema/json.py`, `schema/swagger.py` | schema-type support per flavor |
| `schema/schematron/` | Schematron validation engine (see below) |
| `schema/ubl.py`, `schema/xml.py` | UBL document validation (XSD + Schematron), XML loading |
| `peppol.py` | PEPPOL ruleset CLI entry (uses bundled rulesets) |
| `mapping.py` | value mapping on schema selections |
| `resources/` | bundled schematron rulesets (`PEPPOL-EN16931-UBL.sch`, `CEN-EN16931-UBL.sch`) + `UBL-2/` XSDs — packaged via hatch `packages = ["src/schema_tools"]` |
| `web/` | optional Flask viewer (`make web`, needs `API_KEY`) |
| `xml.py`, `utils.py` | shared helpers |

## Entry points

- CLI: `schema-tools` (`__main__.py`, Fire) with subcommands `ubl`,
  `schematron`, `peppol` — run via `make run` (see its `help`).
- Library: `schema_tools.validate(xml_root, schematrons)` is the top-level
  validation entry; `schema_tools.schema.schematron` is the engine.

## Schematron module (public API)

```python
from schema_tools.schema.schematron import Schematron

sch = Schematron(src)          # ElementTree | path | str | bytes | file-like
result = sch.validate(xml_root, strict=False)   # reusable across documents
# -> ValidationResult: .valid  .errors  .warnings  .unevaluated  .violations
# Violation: rule_id, flag, level, message, context, element, line
# strict=True propagates evaluator errors instead of recording Unevaluated
```

- `validate_schematron(xml_root, schematron) -> int` — legacy facade (logs,
  returns fatal-error count); kept for compatibility, delegates to
  `Schematron`. Its log output includes rule ids.
- `current()` (XSLT semantics: rule context node, not the dynamic predicate
  item) is injected by `functions.py` via a thread-local stash bound by
  `Schematron.validate()`.

## elementpath gotchas (verified empirically)

- the root Element passed to `select()` is the document node; relative
  paths select its CHILDREN (rule contexts must point inside the doc root)
- injected functions need `context=None` defaults (parse-time static calls
  pass no context) and must return *wrapped* nodes
  (`elementpath.xpath_nodes.EtreeElementNode`); raw Elements break path
  steps (XPTY0019); the context arg carries `.item` = wrapped node
- stdlib ElementTree tracks no sourcelines — `Violation.line` is always
  `None` unless a line-tracking parser produced the elements

## Conventions

- standard uv project: `make check` (format+lint+typecheck+test) is THE
  gate; `make test` accepts `TEST=tests/test_schematron.py::test_x`;
  `make publish` for releases (twine is a dev dep)
- **tags are bare versions** (`0.4.0`, not `v0.4.0`)
- version source of truth: `pyproject.toml` == `src/schema_tools/__init__.py`
- fully qualified imports: `from schema_tools.schema.schematron import ...`
- `ubl.validate` does NOT raise on invalid documents — it logs and returns