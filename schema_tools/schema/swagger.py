from schema_tools.schema import Schema, Mapper

class Components(Schema):
  def __init__(self, schemas=[], **kwargs):
    super().__init__(**kwargs)
    self.schemas = schemas
    for schema in self.schemas:
      schema.parent = self

  def schema(self, key, return_definition=True):
    for schema in self.schemas:
      if schema.name == key:
        return schema.definition if return_definition else schema
    raise KeyError("'{}' is not a known schema".format(key))

  # def _select(self, name, *remainder, stack=[]):
  #   # print(stack, "components", name, remainder)
  #   result = None
  #   try:
  #     result = self.property(name, return_definition=False)
  #     stack.append(result)
  #     if remainder:
  #       result = result._select(*remainder, stack=stack)
  #   except KeyError:
  #     pass
  #   return result

  def _more_repr(self):
    return {
      "schemas" : len(self.schemas)
    }

  def to_dict(self):
    out = super().to_dict()
    if self.schemas:
      out["schemas"] = {
        s.name : s.to_dict() for p in self.schemas
      }
    return out

  # def dependencies(self, resolve=False):
  #   return list({
  #     dependency \
  #     for prop in self.properties \
  #     for dependency in prop.dependencies(resolve=resolve)
  #   })

class SwaggerMapper(Mapper):
  
  def map_components(self, properties):
    if self.has( properties, "schemas" ) and
      schemas = properties["schemas"]
      properties["schemas"] = [
          Property(name, definition) \
          for name, definition in properties["properties"].items()
        ]
      if self.has(properties, "definitions"):
        properties["definitions"] = [
          Definition(name, definition) \
          for name, definition in properties["definitions"].items()
        ]
      return ObjectSchema(**properties)

  def map_value(self, properties):
    value_mapping = {
      "boolean": BooleanSchema,
      "integer": IntegerSchema,
      "null":    NullSchema,
      "number":  NumberSchema,
      "string":  StringSchema,
      "array":   ArraySchema
    }
    if self.has(properties, "type", value_mapping):
      return value_mapping[properties["type"]](**properties)
    
  def map_all_of(self, properties):
    if self.has(properties, "allOf", list):
      properties["options"] = properties.pop("allOf")
      return AllOf(**properties)

  def map_any_of(self, properties):
    if self.has(properties, "anyOf", list):
      properties["options"] = properties.pop("anyOf")
      return AnyOf(**properties)

  def map_one_of(self, properties):
    if self.has(properties, "oneOf", list):
      properties["options"] = properties.pop("oneOf")
      return OneOf(**properties)

  def map_reference(self, properties):
    if self.has(properties, "$ref", str):
      properties["ref"] = properties.pop("$ref")
      return Reference(**properties)

  def map_enum(self, properties):
    if self.has(properties, "enum", list):
      return Enum(**properties)

