import os
import sys
import logging

import fire

from importlib.resources import files

from schema_tools        import xml
from schema_tools        import resources
from schema_tools.schema import schematron

from rich.logging import RichHandler

# setup logging infrastructure

if os.environ.get("FORCE_LOG", False) or sys.stdout.isatty():
  LOG_LEVEL = os.environ.get("LOG_LEVEL") or "INFO"
else:
  LOG_LEVEL = "ERROR"

FORMAT = "%(message)s"
logging.basicConfig(
  level=LOG_LEVEL, format=FORMAT, datefmt="[%X]",
  handlers=[RichHandler()]
)

def validate(xml_filename):
  with files(resources) as resource_root:
    xml_root = xml.load(xml_filename)
    if xml.validate(
      xml_root, resource_root / "UBL-2/xsd/maindoc/UBL-Invoice-2.1.xsd"
    ):
      schematron.validate(xml_root, [
        resource_root / "CEN-EN16931-UBL.sch",
        resource_root / "PEPPOL-EN16931-UBL.sch"
      ])

def cli():
  fire.Fire({
    "validate"           : validate,
    "query"              : schematron.query,
    "generate_functions" : schematron.generate_functions
  })

if __name__ == "__main__":
  cli()
