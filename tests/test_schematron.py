"""
tests for Schematron validation: in-memory source handling (FR-1), the
Schematron class + structured ValidationResult (FR-2), the unevaluated
query bug fix (strict select) and `current()` support (FR-3).

note: elementpath treats the root Element passed to select() as the document
node, so rule contexts are evaluated relative to it; the test documents below
use a synthetic <doc> root element to keep rule contexts simple.
"""

import io
import logging
from xml.etree import ElementTree

import elementpath
import pytest

from schema_tools.schema import schematron
from schema_tools.schema.schematron import Schematron

SCHEMATRON = """<schema xmlns="http://purl.oclc.org/dsdl/schematron">
  <ns prefix="t" uri="http://example.com/test"/>
  <pattern>
    <rule context="t:root">
      <assert id="T1" test="t:child" flag="fatal">root must have a child</assert>
      <assert id="T2" test="@id" flag="warning">root should have an id</assert>
    </rule>
  </pattern>
</schema>"""

XML = """<doc xmlns:t="http://example.com/test">
  <t:root/>
</doc>"""


@pytest.fixture
def xml_root():
  return ElementTree.fromstring(XML)


@pytest.fixture
def schematron_file(tmp_path):
  path = tmp_path / "conventions.sch"
  path.write_text(SCHEMATRON, encoding="utf-8")
  return path


# ---------------------------------------------------------------------------
# FR-1: schematron source types (legacy facade)


def test_schematron_from_path(xml_root, schematron_file):
  assert schematron.validate_schematron(xml_root, schematron_file) == 1


def test_schematron_from_path_as_string(xml_root, schematron_file):
  assert schematron.validate_schematron(xml_root, str(schematron_file)) == 1


def test_schematron_from_string(xml_root):
  assert schematron.validate_schematron(xml_root, SCHEMATRON) == 1


def test_schematron_from_bytes(xml_root):
  assert schematron.validate_schematron(xml_root, SCHEMATRON.encode("utf-8")) == 1


def test_schematron_from_file_like(xml_root):
  assert schematron.validate_schematron(xml_root, io.StringIO(SCHEMATRON)) == 1


def test_schematron_from_elementtree(xml_root):
  root = ElementTree.fromstring(SCHEMATRON)
  assert schematron.validate_schematron(xml_root, root) == 1


def test_unsupported_source_type(xml_root):
  with pytest.raises(ValueError):
    schematron.validate_schematron(xml_root, 123)


def test_load_schematron_passthrough():
  root = ElementTree.fromstring(SCHEMATRON)
  assert schematron.load_schematron(root) is root


def test_load_schematron_invalid_xml_string():
  assert schematron.load_schematron("<not-xml") is None


# ---------------------------------------------------------------------------
# FR-2: Schematron class + ValidationResult


def test_validate_result_violations(xml_root):
  result = Schematron(SCHEMATRON).validate(xml_root)
  assert not result.valid
  assert len(result.violations) == 2
  assert len(result.errors) == 1
  assert len(result.warnings) == 1

  error = result.errors[0]
  assert error.rule_id == "T1"
  assert error.flag == "fatal"
  assert error.level == "error"
  assert error.message == "root must have a child"
  assert error.context == "t:root"
  assert error.element.tag == "{http://example.com/test}root"
  assert error.line is None  # stdlib ElementTree does not track sourcelines


def test_validate_result_valid_document(xml_root):
  xml_root[0].append(ElementTree.fromstring('<t:child xmlns:t="http://example.com/test"/>'))
  result = Schematron(SCHEMATRON).validate(xml_root)
  assert result.valid
  assert result.errors == []
  assert result.unevaluated == []


def test_validate_result_non_fatal_failure_is_no_error(xml_root):
  xml_root[0].append(ElementTree.fromstring('<t:child xmlns:t="http://example.com/test"/>'))
  result = Schematron(SCHEMATRON).validate(xml_root)
  assert result.valid  # warnings do not invalidate
  assert len(result.errors) == 0
  assert len(result.warnings) == 1


def test_validate_result_missing_rule_id_is_none(xml_root):
  no_id = SCHEMATRON.replace(' id="T1"', "").replace(' id="T2"', "")
  result = Schematron(no_id).validate(xml_root)
  assert all(v.rule_id is None for v in result.violations)


def test_schematron_class_from_path(schematron_file, xml_root):
  result = Schematron(schematron_file).validate(xml_root)
  assert len(result.errors) == 1


def test_schematron_class_reusable(schematron_file, xml_root):
  sch = Schematron(schematron_file)
  assert len(sch.validate(xml_root).errors) == 1
  assert len(sch.validate(xml_root).errors) == 1


# ---------------------------------------------------------------------------
# bug fix: unevaluated queries no longer silently pass


def test_unevaluated_assert_is_recorded_not_silent(xml_root):
  unsupported = SCHEMATRON.replace('test="t:child"', "test='unknown:func(t:child)'")
  result = Schematron(unsupported).validate(xml_root)
  assert not result.valid
  assert len(result.unevaluated) == 1
  entry = result.unevaluated[0]
  assert entry.context == "t:root"
  assert entry.query == "unknown:func(t:child)"
  assert "ElementPathNameError" in entry.reason


def test_strict_validate_raises_on_unsupported_query(xml_root):
  unsupported = SCHEMATRON.replace('test="t:child"', "test='unknown:func(t:child)'")
  with pytest.raises(elementpath.exceptions.ElementPathNameError):
    Schematron(unsupported).validate(xml_root, strict=True)


def test_select_neutral_behavior_without_strict():
  # legacy behavior preserved: error -> [], query -> True
  root = ElementTree.fromstring("<doc/>")
  assert schematron.select_find(root, "unknown:func()") == []
  assert schematron.select_query(root, "unknown:func()") is True


def test_select_strict_raises():
  root = ElementTree.fromstring("<doc/>")
  with pytest.raises(elementpath.exceptions.ElementPathNameError):
    schematron.select(root, "unknown:func()", strict=True)


def test_validate_schematron_logs_unevaluated(xml_root, caplog):
  unsupported = SCHEMATRON.replace('test="t:child"', "test='unknown:func(t:child)'")
  with caplog.at_level(logging.WARNING):
    errors = schematron.validate_schematron(xml_root, unsupported)
  assert errors == 0  # unevaluated is not counted as a fatal error
  assert any("unevaluated" in record.message for record in caplog.records)


def test_validate_schematron_returns_error_count(xml_root):
  assert schematron.validate_schematron(xml_root, SCHEMATRON) == 1


def test_validate_schematron_logs_violations(xml_root, caplog):
  with caplog.at_level(logging.INFO):
    schematron.validate_schematron(xml_root, SCHEMATRON)
  messages = [record.message for record in caplog.records]
  assert any("root must have a child" in message for message in messages)
  assert any("root should have an id" in message for message in messages)


# ---------------------------------------------------------------------------
# legacy facade behavior


def test_valid_document_passes(xml_root):
  xml_root[0].append(ElementTree.fromstring('<t:child xmlns:t="http://example.com/test"/>'))
  assert Schematron(SCHEMATRON).validate(xml_root).valid


def test_non_fatal_failure_is_no_error(xml_root):
  xml_root[0].append(ElementTree.fromstring('<t:child xmlns:t="http://example.com/test"/>'))
  result = Schematron(SCHEMATRON).validate(xml_root)
  assert len(result.errors) == 0


def test_load_schematron_invalid_xml_string_is_none():
  assert schematron.load_schematron("<not-xml") is None


# ---------------------------------------------------------------------------
# FR-3: current() support (cross-element joins)


BPMN_XML = """<doc xmlns:b="http://example.com/bpmn">
  <b:process id="p1">
    <b:startEvent id="s1"/>
  </b:process>
  <b:process id="p2">
    <b:startEvent id="s2"/>
  </b:process>
  <b:messageFlow id="m1" targetRef="s1"/>
  <b:messageFlow id="m2" targetRef="unknown"/>
</doc>"""

BPMN_SCHEMATRON = """<schema xmlns="http://purl.oclc.org/dsdl/schematron">
  <ns prefix="b" uri="http://example.com/bpmn"/>
  <pattern>
    <rule context="b:messageFlow">
      <assert id="M1" test="//b:process[b:startEvent/@id = current()/@targetRef]"
              flag="fatal">message flow target must be a start event in a process</assert>
    </rule>
  </pattern>
</schema>"""


def test_current_joins_to_context_node():
  # m1 targets s1, which lives in process p1 -> valid; m2 targets 'unknown'
  # -> violates M1. current() must resolve to each messageFlow itself.
  result = Schematron(BPMN_SCHEMATRON).validate(ElementTree.fromstring(BPMN_XML))
  assert not result.valid
  assert len(result.errors) == 1
  violation = result.errors[0]
  assert violation.rule_id == "M1"
  assert violation.element.get("id") == "m2"


def test_current_inside_function_module():
  # direct elementpath use, no stash bound: current() falls back to the
  # evaluation context item (equivalent to `.` at the top level)
  import elementpath
  from elementpath.xpath3 import XPath3Parser

  import schema_tools.schema.schematron.functions  # noqa: F401

  root = ElementTree.fromstring('<doc><child id="c1"/><other id="x"/></doc>')
  matched = elementpath.select(
    root, "child[@id = current()/@id]", namespaces={}, parser=XPath3Parser
  )
  assert len(matched) == 1
  assert matched[0].get("id") == "c1"


def test_current_bare_call_is_harmless():
  # no stash bound: current() falls back to the evaluation context item,
  # which at the top level is the document root (current() == `.`)
  import elementpath
  from elementpath.xpath3 import XPath3Parser

  import schema_tools.schema.schematron.functions  # noqa: F401

  root = ElementTree.fromstring("<doc/>")
  assert elementpath.select(root, "current()", namespaces={}, parser=XPath3Parser) == [root]


def test_current_falls_back_to_context_item():
  # without a stash-bound node, current() mirrors the dynamic context item
  import elementpath
  from elementpath.xpath3 import XPath3Parser

  from schema_tools.schema.schematron.functions import _current, set_current_context

  set_current_context(None)
  root = ElementTree.fromstring('<doc><child id="c1"/><other id="x"/></doc>')
  # inside child's predicate, current() == child (the context item)
  matched = elementpath.select(
    root,
    "child[@id = current()/@id and current()/self::child]",
    namespaces={},
    parser=XPath3Parser,
  )
  assert _current.node is None
  assert len(matched) == 1
