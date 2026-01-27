from pathlib import Path

from schema_tools        import xml
from schema_tools.schema import ubl

def test_good_validation():
  xml_root = xml.load(Path(__file__).parent / "examples" / "invoice.xml")
  try:
    ubl.validate(xml_root)
  except Exception:
    assert False, "should not throw a validation exception"

def test_bad_xml_validation():
  xml_root = xml.load(Path(__file__).parent / "examples" / "invoice.bad.xml")
  try:
    ubl.validate(xml_root)
    assert False, "should throw an XML schema validation exception"
  except Exception:
    pass
