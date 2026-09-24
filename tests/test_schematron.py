"""
tests for Schematron validation, in particular the in-memory source
handling (FR-1: schematron as ElementTree, path, string, bytes or file-like)

note: elementpath treats the root Element passed to select() as the document
node, so rule contexts are evaluated relative to it; the test documents below
use a synthetic <doc> root element to keep rule contexts simple.
"""

import io
from xml.etree import ElementTree

import pytest

from schema_tools.schema import schematron

SCHEMATRON = """<schema xmlns="http://purl.oclc.org/dsdl/schematron">
  <ns prefix="t" uri="http://example.com/test"/>
  <pattern>
    <rule context="t:root">
      <assert test="t:child" flag="fatal">root must have a child</assert>
      <assert test="@id" flag="warning">root should have an id</assert>
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


def test_valid_document_passes(xml_root):
  xml_root[0].append(ElementTree.fromstring('<t:child xmlns:t="http://example.com/test"/>'))
  assert schematron.validate_schematron(xml_root, SCHEMATRON) == 0


def test_non_fatal_failure_is_no_error(xml_root):
  xml_root[0].append(ElementTree.fromstring('<t:child xmlns:t="http://example.com/test"/>'))
  root = ElementTree.fromstring(SCHEMATRON)
  assert schematron.validate_schematron(xml_root, root) == 0


def test_unsupported_source_type(xml_root):
  with pytest.raises(ValueError):
    schematron.validate_schematron(xml_root, 123)


def test_load_schematron_passthrough():
  root = ElementTree.fromstring(SCHEMATRON)
  assert schematron.load_schematron(root) is root


def test_load_schematron_invalid_xml_string():
  assert schematron.load_schematron("<not-xml") is None
