from schema_tools        import yaml
from schema_tools.schema import loads

from schema_tools.schema.json import StringSchema, ObjectSchema

def test_swagger_component_definitions():
  src = """
type: object
properties:
  something:
    $ref: "#/components/schemas/sometype"
  someotherthing:
    $ref: "#/components/schemas/someothertype"
components:
  schemas:
    sometype:
      type: string
    someothertype:
      type: object
      properties:
        foo:
          type: string
"""

  schema = loads(src, parser=yaml)

  assert isinstance(schema.property("something"), StringSchema)
  assert isinstance(schema.property("someotherthing"), ObjectSchema)
  assert isinstance(schema.select("someotherthing.foo").definition, StringSchema)

def test_swagger_select_components():
  src = """
components:
  schemas:
    sometype:
      type: string
    someothertype:
      type: object
      properties:
        foo:
          type: string
"""

  schema = loads(src, parser=yaml)
  assert isinstance(schema.definition("sometype"), StringSchema)
  assert isinstance(schema.select("components.schemas.sometype").definition, StringSchema)

def test_swagger_structure():
  yaml_src = """
openapi: 3.0.0
info:
  description: "deposits endpoint"
  version: "1.0.0"
  title: "vouchers"
paths:
  /make/deposit:
    post:
      summary: "make a deposit"
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: file:tests/schemas/money.json
      responses:
        '200':
          description: success
          content:
            application/json:
              schema:
                type: boolean
        '400':
          description: failure
          content:
            application/json:
              schema:
                type: string
"""
  schema = loads(yaml_src, parser=yaml)
  print(schema.to_dict())
