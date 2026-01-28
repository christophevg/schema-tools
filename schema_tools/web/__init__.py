import os

from flask import Flask, render_template, request

from pathlib import Path

import json

from schema_tools        import xml
from schema_tools        import peppol
from schema_tools.schema import ubl

from rich.logging import RichHandler
from rich.console import Console

import logging

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

def check_api_key():
  api_key = request.form.get("api-key")
  if api_key != API_KEY:
    raise ValueError("please provide an API key to use this service")

def protected(func):
  def wrapper():
    try:
      check_api_key()
      result = func()
      if result:
        logger.info(result)
    except Exception as ex:
      # logger.exception(ex)
      logger.error(f"[bold red]Whoops:[/bold red] {ex}", extra={"markup": True})
    return console.export_html()
  return wrapper

@app.route("/")
def home():
  return render_template("index.html")

@app.route("/peppol/validate", methods=["POST"], endpoint="validate")
@protected
def validate():
  src      = request.form.get("ubl")
  doctype  = request.form.get("doctype")
  xml_root = xml.parse(src)
  return ubl.validate(xml_root, doctype=doctype)

@app.route("/peppol/check", methods=["POST"], endpoint="check")
@protected
def check():
  participant = request.form.get("participant")
  return json.dumps(peppol.check(participant), indent=2)
