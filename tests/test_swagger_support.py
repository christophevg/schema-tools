from schema_tools        import yaml
from schema_tools.schema import loads


def test_swagger_component_definitions():
  src = """
type: object
properties:
  something:
    $ref: "#/components/schemas/something"
components:
  schemas:
    sometype:
      type: string
"""

  schema = loads(src, parser=yaml)
  print(schema)
  # assert False

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