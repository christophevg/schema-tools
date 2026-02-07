"""
Schematron support for validating XML documents against rules that check semantics on top of basic XSD validation.

Schematron rules are using XSLT Patterns, which require some XSLT engine, which is not really readily available. BUT... XSLT Patters are essentially a sub set of XPath, and XPath queries _are_ supported by e.g. the `elementpath` package.

So: this Schematron validation IS NOT perfect, yet good enough to handle a lot and while YMMV, I try to apply more and more fixes, making it more robust ;-)
"""

from typing import List, Union

from pathlib import Path

import json

import elementpath

from elementpath.xpath3 import XPath3Parser

# this injects custom functions in the parser
import schema_tools.schema.schematron.functions # noqa: F401

from schema_tools import xml

from rich.console import Console

import logging

logger = logging.getLogger(__name__)

console = Console()

def select(
  root, query,
  namespaces={"":"http://purl.oclc.org/dsdl/schematron"},
  context=None,
  variables=None,
  return_list=True,
  return_node=False,
  debug=False
) -> Union[bool,List,str]:
  """
  utility function wrapping `elementpath.select` with some sensible defaults and error handling
  """
  try:
    logger.debug(f"root={root}")
    logger.debug(f"query={query}")
    logger.debug(f"context={context}")
    result = elementpath.select(
      root, query, namespaces=namespaces, item=context, variables=variables,
      parser=XPath3Parser
    )
    logger.debug(f"result={result}")
    # return first value in list
    if not return_list and isinstance(result, list):
      logger.debug("UNWRAPPING LIST")
      result = result[0] if len(result) else None

    # try opportunistic unwrapping of text node
    if not return_node:
      try:
        return result.text
      except AttributeError:
        pass
    return result

  except elementpath.exceptions.ElementPathValueError as ex:
    logger.error(ex)
    return False
  except (
    elementpath.exceptions.ElementPathNameError, elementpath.exceptions.ElementPathTypeError
  ) as ex:
    logger.warning(f"for query '{query}':")
    logger.warning(f"can't perform select: {ex}")
    logger.warning(json.dumps(variables, indent=2, default=str))
    return [] if return_list else True

def select_find(*args, **kwargs) -> List:
  """
  wrapper utility function for `select`, ensuring that a list if returned
  """
  result = select(*args, **kwargs)
  return result if isinstance(result,list) else []

def select_query(*args, **kwargs) -> Union[bool,List,str]:
  """
  wrapper utility function for `select`, ensuring that a value is returned, not a list.
  """
  return select(*args, **kwargs, return_list=False)

def schema_namespaces(root):
  """
  detects namespaces in "ns" tags from a Schematron ElementTree
  """
  return {
    element.get("prefix") : element.get("uri")
    for element in select_find(root, "ns")
  }

def schema_variables(xml_root, context_root, namespaces=None):
  """
  discover variables in context and evaluate those variables within the scope of the xml
  """
  variables = {}
  for let in select_find(context_root, "let"):
    name  = let.get("name")
    query = let.get("value")
    value = select_find(
      xml_root, query, namespaces=namespaces, variables=variables
    )
    variables[name] = value
    logger.debug(f"discovered variable {name}={value}")
  return variables

def validate_schematron(xml_root, schematron_filename) -> int:
  """
  validates an ElementTree against a Schematron
  """
  schematron_root = xml.load(schematron_filename)
  namespaces      = schema_namespaces(schematron_root)
  variables       = schema_variables(xml_root, schematron_root, namespaces)

  logger.info(
    f"validating against schematron '{schematron_filename.name}'",
    extra={"markup": True}
  )
  logger.debug("with variables:")
  logger.debug(json.dumps(variables, indent=2, default=str))

  errors   = 0
  warnings = 0
  # for every pattern in the schematron
  for pattern in select_find(schematron_root, "pattern"):
    pattern_variables = schema_variables(xml_root, pattern, namespaces)
    logger.debug("pattern variables:")
    logger.debug(json.dumps(pattern_variables, indent=2, default=str))

    # for every rule in the schematron/pattern
    for rule in select_find(pattern, "rule"):
      rule_variables = schema_variables(xml_root, rule, namespaces)
      logger.debug("rule variables:")
      logger.debug(json.dumps(rule_variables, indent=2, default=str))
      context_query = rule.get("context")

      # for every context in the schematron/pattern/rule
      contexts = select_find(
        xml_root, context_query, namespaces=namespaces,
        variables=variables | pattern_variables | rule_variables
      )
      for context in contexts:
        # perform every assertion in the schematron/pattern/rule given context
        for assertion in select_find(rule, "assert"):
          assertion_query = assertion.get("test")
          fatal           = assertion.get("flag") == "fatal"
          logger.debug(assertion_query)
          logger.debug(json.dumps(
            variables | pattern_variables | rule_variables,
            indent=2, default=str
          ))
          result = select_query(
            xml_root, assertion_query,
            namespaces=namespaces,
            context=context,
            variables=variables | pattern_variables | rule_variables
          )
          if not result:
            if fatal:
              errors += 1
              logger_func = logger.error
              color = "red"
            else:
              warnings += 1
              logger_func = logger.warning
              color = "yellow"
            logger_func(f"""[{color}]{assertion.text}[/{color}]
  [blue]context[/blue]: {context_query}
  [blue]query[/blue]  : {assertion_query}""",
                extra={"markup": True}
              )
  if errors:
    logger.debug(f"schematron errors={errors}")
  if warnings:
    logger.debug(f"schematron warnings={warnings}")
  return errors

def validate(xml_root, schematrons):
  """
  validates a given XML file against a given XSD and Schematron, or if omitted, the UBL 2.1 XSD and Peppol Schematron.
  example:
    % schema-tools validate invoice.xml
  """
  # check all provided files _are_ files
  for filename in schematrons:
    if filename and not Path(filename).is_file():
      logger.error(f"unknown file: {filename}")
      return

  errors = 0
  for schematron_filename in schematrons:
    errors += validate_schematron(xml_root, schematron_filename)

  if not errors:
    logger.info(
      "[bold green]✅ XML is valid[/bold green]",
      extra={"markup": True}
    )
    return True
  return False

def query(query, xml_filename, context=None):
  """
  performs an XPath query on a provided XML file, optionally given a 'context'
  example:
    % schema-tools schematron query "@schemeID" tests/examples/invoice.xml  "cac:AccountingSupplierParty/cac:Party/cbc:EndpointID"
    0088
  """
  xml_root   = xml.load(xml_filename)
  logger.debug(xml_root)
  namespaces = xml.namespaces(xml_filename)
  logger.debug(namespaces)
  if context:
    context = select_query(xml_root, context, namespaces=namespaces, return_node=True)
    logger.debug(f"CONTEXT={context}")
  return select_find(xml_root, query, namespaces=namespaces, context=context)

def _gen(name, retval, args):
  """
  utility function to generate stubs for functions
  """
  fname = name.replace("-", "_")
  params = [ f"'{arg}'" for arg in args.values() ] + [ f"'{retval}'"]
  vars = []
  for varname, type in args.items():
    default, cls = {
      "xs:string"         : ("''", "str"),
      "xs:string?"        : ("''", "str"),
      "xs:decimal"        : ("0.0", "(float,int)"),
      "xs:integer"        : ("0", "int"),
      "xs:anyAtomicType?" : ("''", "str")
    }[type]
    vars.append(
      f"  {varname} = self.get_argument(context, default={default}, cls={cls})"
    )
  nl = "\n"
  return f"""
@method(function("{name}", nargs={len(params)-1},
  sequence_types=({ ', '.join(params)})))
def evaluate_{fname}_function(self, context):
  if self.context is not None:
      context = self.context
{nl.join(vars)}
  logger.warning("function '{name}' hasn't been implemented yet!")
  return True
"""

def generate_functions(schematron_filename):
  """
  generate function stubs for function definitions found in Schematron
  """
  schematron_root = xml.load(schematron_filename)
  namespaces      = xml.namespaces(schematron_filename)

  for function in select_find(
    schematron_root, "function", namespaces=namespaces
  ):
    name = function.get("name").replace("fn:","").strip()
    retval = function.get("as").strip()
    args = {}
    for arg in select_find(function, "param", namespaces=namespaces):
      args[arg.get("name")] = arg.get("as", "xs:anyAtomicType?").strip()
    console.print(_gen(name, retval, args))

# expose cli-enabled functions
cli = {
  "query"              : query,
  "generate_functions" : generate_functions
}
