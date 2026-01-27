import os

from flask import Flask, render_template, request

from pathlib import Path

from importlib.resources import files, as_file

from schema_tools import xml

from schema_tools.schema import schematron
from schema_tools import resources

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

@app.route("/")
def home():
  return render_template("index.html")

@app.route("/validate", methods=["POST"])
def validate():
  try:
    api_key = request.form.get("api-key")
    if api_key != API_KEY:
      raise ValueError("please provide an API key to use this service")
    ubl = request.form.get("ubl")
    xml_root = xml.parse(ubl)

    doctype = request.form.get("doctype")

    # running from package, setup files context
    with as_file(files(resources)) as resource_root:
      if xml.validate(
        xml_root,
        resource_root / f"UBL-2/xsd/maindoc/UBL-{doctype}-2.1.xsd"
      ):
        schematron.validate(xml_root, [
          resource_root / "CEN-EN16931-UBL.sch",
          resource_root / "PEPPOL-EN16931-UBL.sch"
        ])
  except Exception as ex:
    # logger.exception(ex)
    logger.error(f"[bold red]Whoops:[/bold red] {ex}", extra={"markup": True})

  return console.export_html()
