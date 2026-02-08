import os

from flask import Flask, render_template, request

from pathlib import Path

import json

from schema_tools        import xml
from schema_tools        import peppol
from schema_tools.schema import ubl

import xmltodict
from jinja2 import BaseLoader, Undefined
from jinja2.sandbox import SandboxedEnvironment

from markdown import markdown

from rich.logging import RichHandler
from rich.console import Console

import logging

from .defaults import markdown_template, xml_example

console = Console(record=True, force_terminal=True, width=150)

LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
FORMAT = "%(message)s"
logging.basicConfig(
  level=LOG_LEVEL, format=FORMAT, datefmt="[%X]",
  handlers=[RichHandler(console=console, show_path=False)]
)
logger = logging.getLogger(__name__)

HERE      = Path(__file__).parent
TEMPLATES = HERE / "templates"
STATIC    = TEMPLATES / "static"

API_KEY = os.environ.get("API_KEY", None)
if API_KEY is None:
  raise ValueError("can't run without an API key")

app = Flask(
  "schema-tools",
  template_folder= TEMPLATES,
  static_folder= STATIC
)
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.jinja_env.add_extension("jinja2_highlight.HighlightExtension")

def ensure_list(dl):
  if not isinstance(dl, list):
    return [ dl ]
  return dl

def check_api_key():
  api_key = request.form.get("api-key")
  if api_key != API_KEY:
    raise ValueError("please provide an API key to use this service")

def protected(func):
  def wrapper():
    try:
      check_api_key()
      return func()
    except Exception as ex:
      logger.debug(ex, exc_info=1)
      logger.error(f"[bold red]Whoops:[/bold red] {ex} ({ex.__class__.__module__}.{ex.__class__.__qualname__})", extra={"markup": True})
      return console.export_html()
  return wrapper

class SilentUndefined(Undefined):
  def _fail_with_undefined_error(self, *args, **kwargs):
    return "&nbsp;"

def return_console(func):
  def wrapper():
    result = func()
    if result:
      logger.info(result)
    return console.export_html()
  return wrapper


@app.route("/")
def home():
  return render_template(
    "index.html", markdown=markdown_template, xml=xml_example
  )

@app.route("/peppol/validate", methods=["POST"], endpoint="validate")
@protected
@return_console
def validate():
  src      = request.form.get("ubl")
  doctype  = request.form.get("doctype", "Invoice")
  xml_root = xml.parse(src)
  return ubl.validate(xml_root, doctype=doctype)

@app.route("/peppol/check", methods=["POST"], endpoint="check")
@protected
@return_console
def check():
  participant = request.form.get("participant")
  return json.dumps(peppol.check(participant), indent=2)

@app.route("/xml/view", methods=["POST"], endpoint="view")
@protected
def view():
  src           = request.form.get("xml").strip()
  meta_template = request.form.get("markdown", "# 4 Ooh 4 Missing Markdown")

  # collect namespaces, to strip later
  xml  = xmltodict.parse(src)
  root = list(xml.keys())[0]
  namespaces = {
    uri : None for key, uri in xml[root].items() if key.startswith("@xmlns")
  }
  logger.debug({"namespaces": namespaces})

  # parse xml again to dict, now omitting namespaces
  xml = xmltodict.parse(src, process_namespaces=True, namespaces=namespaces)
  logger.debug(json.dumps(xml,indent=2))

  # construct template and render html
  template = SandboxedEnvironment(
    loader=BaseLoader(),undefined=SilentUndefined
  ).from_string(meta_template)
  html = markdown(
    template.render(xml=xml, ensure_list=ensure_list),
    extensions=["tables", "attr_list"]
  )
  return render_template(
    "render.html",
    body=html, debug=json.dumps(xml, indent=2)
  )
