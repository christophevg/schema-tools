# TODO

Backlog of things to do. Completed items are checked off and kept visible.

## Migration to uv-based standard (in progress — Phase 2: code-quality remediation)

- [x] pypi-template project management removed from Makefile, `.pypi-template` deleted
- [x] `pyproject.toml` (hatchling, src-layout, docs/web extras, dev group, tool config)
- [x] `Makefile` replaced with standard uv target set (+ `local-schema`, `web` preserved)
- [x] src/ layout (`schema_tools/` → `src/schema_tools/`), `py.typed` added
- [x] CI workflow: 4 jobs (test matrix 3.10–3.13 × 3 OS, lint, typecheck, build)
- [x] `.readthedocs.yaml` → Python 3.12 + `docs` extra
- [x] root `README.md` per standard (incl. agentic badge), `.github/README.md` removed
- [x] legacy files removed (`setup.py`, `tox.ini`, `requirements*.txt`, `MANIFEST.in`)
- [x] `env-dev` + `test` (58 passed) + `docs` verified locally
- [x] code-quality remediation: ruff 82 findings, 30 files unformatted, mypy 10 errors
- [x] `make check` fully green (pre-publish/CI gate for all future work) — 58 tests, mypy clean, ruff clean
- [x] CI green on GitHub — full matrix (3 OS × 4 Python) + lint + typecheck + build (run 35977142946)
- [x] Windows compatibility: proper `file:///` URIs in refs (`url2pathname` + `as_uri`), explicit `encoding="utf-8"` on text reads, `asset` fixture emits URIs
- [ ] RTD build green on `docs` extra (+ `docs/code.md` toctree decision)

## Loading

- add tests to check column/line parsing
- add tests to check __eq__

## Selector Support

## Mapping Support

- MappingCollection