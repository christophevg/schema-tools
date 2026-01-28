from xml.etree import ElementTree

from pathlib import Path

from importlib.resources import as_file, files

from schema_tools        import resources
from schema_tools        import xml
from schema_tools.schema import xml as xml_schema
from schema_tools.schema import schematron

def validate(src, doctype="Invoice"):
  """
  Accepts and ElementTree or filepath or string
  """
  if isinstance(src, ElementTree.Element):
    xml_root = src
  elif Path(src).is_file():
    xml_root = xml.load(src)
  elif isinstance(src, str):
    xml_root = xml.parse(src)
  else:
    raise ValueError(f"unsupported XML src type: {type(src)}")

  # running from package, setup files context
  with as_file(files(resources)) as resource_root:
    if xml_schema.validate(
      xml_root,
      resource_root / f"UBL-2/xsd/maindoc/UBL-{doctype}-2.1.xsd"
    ):
      schematron.validate(xml_root, [
        resource_root / "CEN-EN16931-UBL.sch",
        resource_root / "PEPPOL-EN16931-UBL.sch"
      ])

# expose cli-enabled functions
cli = {
  "validate" : validate
}
