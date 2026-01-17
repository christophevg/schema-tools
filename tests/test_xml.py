from pathlib import Path

from importlib.resources import files, as_file

from schema_tools        import xml
from schema_tools        import resources
from schema_tools.schema import schematron

def validate(xml_filename):
  with as_file(files(resources)) as resource_root:
    xml_root = xml.load(xml_filename)
    if xml.validate(
      xml_root, resource_root / "UBL-2/xsd/maindoc/UBL-Invoice-2.1.xsd"
    ):
      return schematron.validate(xml_root, [
        resource_root / "CEN-EN16931-UBL.sch",
        resource_root / "PEPPOL-EN16931-UBL.sch"
      ])
  return False

def test_validation():
  assert validate(Path(__file__).parent / "examples" / "invoice.xml")
