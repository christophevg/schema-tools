from pathlib import Path

import pytest

from schema_tools import xml
from schema_tools.schema import ubl


def test_good_validation():
  xml_root = xml.load(Path(__file__).parent / "examples" / "invoice.xml")
  try:
    ubl.validate(xml_root)
  except Exception:
    pytest.fail("should not throw a validation exception")


def test_bad_xml_validation():
  # invalid documents are reported/logged, ubl.validate does not raise
  xml_root = xml.load(Path(__file__).parent / "examples" / "invoice.bad.xml")
  try:
    ubl.validate(xml_root)
  except Exception:
    pytest.fail("invalid document should be reported, not raise")
