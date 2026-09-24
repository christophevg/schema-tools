"""
Schematron support for validating XML documents against rules that check semantics on top of basic XSD validation.

Schematron rules are using XSLT Patterns, which require some XSLT engine, which is not really readily available. BUT... XSLT Patters are essentially a sub set of XPath, and XPath queries _are_ supported by e.g. the `elementpath` package.

So: this Schematron validation IS NOT perfect, yet good enough to handle a lot and while YMMV, I try to apply more and more fixes, making it more robust ;-)
"""

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from xml.etree import ElementTree

import elementpath
from elementpath.xpath3 import XPath3Parser
from rich.console import Console

# this injects custom functions in the parser
import schema_tools.schema.schematron.functions  # noqa: F401
from schema_tools import xml

logger = logging.getLogger(__name__)

console = Console()


def select(
  root,
  query,
  namespaces=None,
  context=None,
  variables=None,
  return_list=True,
  return_node=False,
  debug=False,
  strict=False,
) -> bool | list | str:
  """
  utility function wrapping `elementpath.select` with some sensible defaults and error handling

  strict=True propagates evaluator errors (unsupported functions, unparsable
  patterns) instead of returning a neutral result that would let an assert
  silently pass.
  """
  if namespaces is None:
    namespaces = {"": "http://purl.oclc.org/dsdl/schematron"}
  try:
    logger.debug(f"root={root}")
    logger.debug(f"query={query}")
    logger.debug(f"context={context}")
    result = elementpath.select(
      root, query, namespaces=namespaces, item=context, variables=variables, parser=XPath3Parser
    )
    logger.debug(f"result={result}")
    # return first value in list
    if not return_list and isinstance(result, list):
      logger.debug("UNWRAPPING LIST")
      result = result[0] if len(result) else None

    # try opportunistic unwrapping of text node
    if not return_node:
      try:
        return str(result.text)
      except AttributeError:
        pass
    return result  # type: ignore[no-any-return]

  except elementpath.exceptions.ElementPathValueError as ex:
    if strict:
      raise
    logger.error(ex)
    return False
  except (
    elementpath.exceptions.ElementPathNameError,
    elementpath.exceptions.ElementPathTypeError,
  ) as ex:
    if strict:
      raise
    logger.warning(f"for query '{query}':")
    logger.warning(f"can't perform select: {ex}")
    logger.warning(json.dumps(variables, indent=2, default=str))
    return [] if return_list else True


def select_find(*args, **kwargs) -> list:
  """
  wrapper utility function for `select`, ensuring that a list if returned
  """
  result = select(*args, **kwargs)
  return result if isinstance(result, list) else []


def select_query(*args, **kwargs) -> bool | list | str:
  """
  wrapper utility function for `select`, ensuring that a value is returned, not a list.
  """
  kwargs.pop("return_list", None)  # this wrapper overrides return_list
  return select(*args, **kwargs, return_list=False)  # type: ignore[misc]


def schema_namespaces(root):
  """
  detects namespaces in "ns" tags from a Schematron ElementTree
  """
  return {element.get("prefix"): element.get("uri") for element in select_find(root, "ns")}


def schema_variables(xml_root, context_root, namespaces=None):
  """
  discover variables in context and evaluate those variables within the scope of the xml
  """
  variables = {}
  for let in select_find(context_root, "let"):
    name = let.get("name")
    query = let.get("value")
    value = select_find(xml_root, query, namespaces=namespaces, variables=variables)
    variables[name] = value
    logger.debug(f"discovered variable {name}={value}")
  return variables


def load_schematron(src):
  """
  loads a Schematron from a file path, string, bytes or file-like object,
  returning a parsed ElementTree (see also `schema_tools.schema.ubl.validate`
  for the same source-sniffing approach on the XML side)
  """
  if isinstance(src, ElementTree.Element):
    return src
  if isinstance(src, bytes):
    return xml.parse(src.decode("utf-8"))
  if isinstance(src, Path):
    return xml.load(src)
  if isinstance(src, str):
    return xml.load(src) if Path(src).is_file() else xml.parse(src)
  if hasattr(src, "read"):
    return xml.parse(src.read())
  raise ValueError(f"unsupported schematron src type: {type(src)}")


@dataclass
class Violation:
  """a failed Schematron assert, with everything needed for reporting"""

  rule_id: str | None  # assert @id (absent in many rulesets)
  flag: str | None  # assert @flag as authored ("fatal", "warning", ...)
  level: str  # derived: "error" if flag == "fatal", else "warning"
  message: str  # assert text, raw — no value substitution
  context: str  # rule @context XPath, as authored
  element: ElementTree.Element  # the matched context node
  line: int | None  # element.sourceline; None with stdlib ElementTree (no
  # line tracking), populated when elements come from a parser that records it


@dataclass
class Unevaluated:
  """an XPath the evaluator could not evaluate — a potential silent pass"""

  context: str  # rule @context ("" for schema-level lets)
  query: str  # the XPath that could not be evaluated
  reason: str  # exception class + message


@dataclass
class ValidationResult:
  """outcome of validating one document against one Schematron"""

  violations: list[Violation] = field(default_factory=list)
  unevaluated: list[Unevaluated] = field(default_factory=list)

  @property
  def valid(self) -> bool:
    # warnings do not invalidate (legacy error-count semantics), but
    # unevaluated queries do: validity cannot be claimed for a ruleset
    # that was only partially evaluated
    return not self.errors and not self.unevaluated

  @property
  def errors(self) -> list[Violation]:
    return [v for v in self.violations if v.level == "error"]

  @property
  def warnings(self) -> list[Violation]:
    return [v for v in self.violations if v.level == "warning"]


class Schematron:
  """
  a Schematron loaded once (ElementTree, path, string, bytes or file-like),
  reusable across documents via `validate`
  """

  def __init__(self, src):
    self.root = load_schematron(src)
    self.namespaces = schema_namespaces(self.root)

  def validate(self, xml_root, strict=False) -> ValidationResult:
    """validates an ElementTree against this Schematron"""
    result = ValidationResult()
    variables = schema_variables(xml_root, self.root, self.namespaces)

    # for every pattern in the schematron
    for pattern in select_find(self.root, "pattern"):
      pattern_variables = schema_variables(xml_root, pattern, self.namespaces)

      # for every rule in the schematron/pattern
      for rule in select_find(pattern, "rule"):
        rule_variables = schema_variables(xml_root, rule, self.namespaces)
        context_query = rule.get("context")
        merged = variables | pattern_variables | rule_variables

        # for every context matched by the schematron/pattern/rule; under
        # strict, evaluator errors propagate instead of being recorded
        try:
          contexts = select_find(
            xml_root, context_query, namespaces=self.namespaces, variables=merged, strict=True
          )
        except elementpath.exceptions.ElementPathError as ex:
          if strict:
            raise
          result.unevaluated.append(Unevaluated(context_query, context_query, _reason(ex)))
          continue

        for context in contexts:
          # perform every assertion in the schematron/pattern/rule given context
          for assertion in select_find(rule, "assert"):
            assertion_query = assertion.get("test")
            try:
              result_ok = select_query(
                xml_root,
                assertion_query,
                namespaces=self.namespaces,
                context=context,
                variables=merged,
                strict=True,
              )
            except elementpath.exceptions.ElementPathError as ex:
              if strict:
                raise
              result.unevaluated.append(Unevaluated(context_query, assertion_query, _reason(ex)))
              continue
            if not result_ok:
              flag = assertion.get("flag")
              result.violations.append(
                Violation(
                  rule_id=assertion.get("id"),
                  flag=flag,
                  level="error" if flag == "fatal" else "warning",
                  message=assertion.text or "",
                  context=context_query,
                  element=context,
                  line=getattr(context, "sourceline", None),
                )
              )
    return result


def _reason(ex) -> str:
  return f"{type(ex).__module__}.{type(ex).__qualname__}: {ex}"


def validate_schematron(xml_root, schematron) -> int:
  """
  validates an ElementTree against a Schematron, given as an ElementTree,
  file path, string, bytes or file-like object; returns the number of fatal
  errors and logs all findings (legacy interface — prefer `Schematron`)
  """
  schematron_label = (
    Path(schematron).name if isinstance(schematron, (str, Path)) else "in-memory schematron"
  )
  logger.info(f"validating against schematron '{schematron_label}'", extra={"markup": True})

  result = Schematron(schematron).validate(xml_root)
  for unevaluated in result.unevaluated:
    logger.warning(f"unevaluated query '{unevaluated.query}': {unevaluated.reason}")
  for violation in result.violations:
    logger_func = logger.error if violation.level == "error" else logger.warning
    color = "red" if violation.level == "error" else "yellow"
    logger_func(
      f"""[{color}]{violation.message}[/{color}]
  [blue]context[/blue]: {violation.context}
  [blue]rule id[/blue]: {violation.rule_id}""",
      extra={"markup": True},
    )
  return len(result.errors)


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
    logger.info("[bold green]✅ XML is valid[/bold green]", extra={"markup": True})
    return True
  return False


def query(query, xml_filename, context=None):
  """
  performs an XPath query on a provided XML file, optionally given a 'context'
  example:
    % schema-tools schematron query "@schemeID" tests/examples/invoice.xml  "cac:AccountingSupplierParty/cac:Party/cbc:EndpointID"
    0088
  """
  xml_root = xml.load(xml_filename)
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
  params = [f"'{arg}'" for arg in args.values()] + [f"'{retval}'"]
  vars = []
  for varname, type in args.items():
    default, cls = {
      "xs:string": ("''", "str"),
      "xs:string?": ("''", "str"),
      "xs:decimal": ("0.0", "(float,int)"),
      "xs:integer": ("0", "int"),
      "xs:anyAtomicType?": ("''", "str"),
    }[type]
    vars.append(f"  {varname} = self.get_argument(context, default={default}, cls={cls})")
  nl = "\n"
  return f"""
@method(function("{name}", nargs={len(params) - 1},
  sequence_types=({", ".join(params)})))
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
  namespaces = xml.namespaces(schematron_filename)

  for function in select_find(schematron_root, "function", namespaces=namespaces):
    name = function.get("name").replace("fn:", "").strip()
    retval = function.get("as").strip()
    args = {}
    for arg in select_find(function, "param", namespaces=namespaces):
      args[arg.get("name")] = arg.get("as", "xs:anyAtomicType?").strip()
    console.print(_gen(name, retval, args))


# expose cli-enabled functions
cli = {"query": query, "generate_functions": generate_functions}
