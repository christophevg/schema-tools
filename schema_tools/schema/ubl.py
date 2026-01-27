from importlib.resources import as_file, files

from schema_tools        import resources
from schema_tools.schema import xml
from schema_tools.schema import schematron

def validate(xml_root, doctype="Invoice"):
  # running from package, setup files context
  with as_file(files(resources)) as resource_root:
    if xml.validate(
      xml_root,
      resource_root / f"UBL-2/xsd/maindoc/UBL-{doctype}-2.1.xsd"
    ):
      schematron.validate(xml_root, [
        resource_root / "CEN-EN16931-UBL.sch",
        resource_root / "PEPPOL-EN16931-UBL.sch"
      ])
