import xmlschema
import logging

logger = logging.getLogger(__name__)

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
