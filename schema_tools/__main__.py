import os
import sys
import logging

import fire

from schema_tools        import peppol
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

def cli():
  fire.Fire({
    "ubl"       : ubl.cli,
    "schematron": schematron.cli,
    "peppol"    : peppol.cli
  })

if __name__ == "__main__":
  cli()
