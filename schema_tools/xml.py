import xmlschema
from xml.etree import ElementTree

from pathlib import Path

import logging
logger = logging.getLogger(__name__)

def parse(src):
  try:
    return ElementTree.XML(src)
  except ElementTree.ParseError as ex:
    logger.error(f"[red][XML] {ex}", extra={"markup": True})
  return None

def validate(xml_root, xsd_filename):
  logger.info(
    f"validating against XSD '{xsd_filename.name}'",
    extra={"markup": True}
  )
  # XSD validation
  try:
    xmlschema.validate(xml_root, xsd_filename)
    return True
  except xmlschema.validators.exceptions.XMLSchemaValidationError as ex:
    logger.error(f"[red][XSD][/red] {ex}", extra={"markup": True})
  except xmlschema.exceptions.XMLResourceParseError as ex:
    logger.error(f"[red][XSD] {ex}[/red]", extra={"markup": True})
  except xmlschema.validators.exceptions.XMLSchemaChildrenValidationError as ex:
    logger.error(f"[red][XSD] {ex.reason}[/red]", extra={"markup": True})
    logger.debug(str(ex)) # full exception with schema and instance excerpts
  return False

def load(xml_filename, xsd_filename=None):
  """
  optionally performs XSD schema validation, loads an XML file, returning a parsed ElementTree
  """

  xml_root = parse(Path(xml_filename).read_text())
  if  xml_root is None:
    return None

  if xsd_filename:
    if not validate(xml_root, xsd_filename):
      return None

  return xml_root

def namespaces(filename):
  """
  extracts namespaces in use in the XML document
  """
  # Source - https://stackoverflow.com/a
  # Posted by Davide Brunato, modified by community. See post 'Timeline' for change history
  # Retrieved 2026-01-08, License - CC BY-SA 3.0
  with Path(filename).open() as fp:
    return dict([
      node for _, node in ElementTree.iterparse(fp, events=['start-ns'])
    ])
