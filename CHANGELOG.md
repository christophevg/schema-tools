# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.4.0] - 2026-09-24

### Added

- `Schematron` class (`schema_tools.schema.schematron`): load a Schematron
  once from an ElementTree, file path, string, bytes or file-like object and
  validate any number of documents against it.
- `ValidationResult` with structured `Violation` entries (`rule_id`, `flag`,
  `level`, `message`, `context`, `element`, `line`) and `Unevaluated` entries
  for queries the evaluator could not run; `.valid`, `.errors`, `.warnings`
  properties. `validate(strict=True)` propagates evaluator errors instead of
  recording them.
- `current()` support in Schematron assert expressions — XSLT semantics
  (the rule context node, not the dynamic context item), enabling
  cross-element joins such as a `bpmn:messageFlow` joining back to the
  process containing the node its `targetRef` names.
- First test coverage for the Schematron module (29 tests; suite total 87).

### Fixed

- Schematron asserts no longer silently pass when the XPath evaluator cannot
  evaluate a query (unsupported functions, unparsable patterns): such
  queries are now reported as `Unevaluated` and mark the result invalid
  (`strict=True` raises instead).
- Latent `AttributeError` in `validate_schematron` when the schematron
  argument was not a path.
- Windows compatibility: proper `file:///` URIs in JSON `$ref`s,
  `url2pathname` + `Path.as_uri()` for reference fetching, explicit
  `encoding="utf-8"` on all text reads.

### Changed

- Project migrated to the uv-based standard tooling (hatchling, src layout,
  Makefile targets, CI matrix 3 OS × Python 3.10–3.13, ReadTheDocs config).
- Legacy `validate_schematron` violation log output now includes the rule id.