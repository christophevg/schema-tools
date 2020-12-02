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
    if self.has( properties, "components" ) and \
       self.has( properties["components"], "schemas" ):
      schemas = [
        Definition(name, definition) \
        for name, definition in properties["components"]["schemas"].items()
      ]
      return 

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
