import os
import sys
import logging

import fire

from schema_tools        import xml
from schema_tools.schema import ubl
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

def validate(xml_filename, doctype="Invoice"):
  xml_root = xml.load(xml_filename)
  ubl.validate(xml_root, doctype=doctype)

def cli():
  fire.Fire({
    "validate"           : validate,
    "query"              : schematron.query,
    "generate_functions" : schematron.generate_functions
  })

if __name__ == "__main__":
  cli()
