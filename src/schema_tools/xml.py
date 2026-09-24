from xml.etree import ElementTree

from pathlib import Path

from schema_tools.schema import xml as xml_schema

import logging
logger = logging.getLogger(__name__)

def parse(src):
  try:
    return ElementTree.XML(src)
  except ElementTree.ParseError as ex:
    logger.error(f"[red][XML] {ex}", extra={"markup": True})
  return None

def load(xml_filename, xsd_filename=None):
  """
  optionally performs XSD schema validation, loads an XML file, returning a parsed ElementTree
  """

  xml_root = parse(Path(xml_filename).read_text())
  if  xml_root is None:
    return None

  if xsd_filename:
    if not xml_schema.validate(xml_root, xsd_filename):
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
