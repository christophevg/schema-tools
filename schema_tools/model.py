from schema_tools.utils import ASTVisitor


def load(node):
  return NodesMapper().visit(node)


class NodesMapper(ASTVisitor):
  def visit_value(self, value_node):
    return value_node()

  def visit_object(self, object_node):
    properties = super().visit_object(object_node)
    if "type" in properties:
      type = properties.pop("type")
      properties["location"] = self.location(object_node)
      for p in [ "schema", "id", "comment" ]:
        properties[p] = properties.pop("$"+p, None)
      if type == "object":
        if "properties" in properties:
          properties["properties"] = [
            Property(name, definition) \
            for name, definition in properties["properties"].items()
          ]
        if "definitions" in properties:
          properties["definitions"] = [
            Definition(name, definition) \
            for name, definition in properties["definitions"].items()
          ]
        return ObjectSchema(**properties)
      else:
        return {
          "boolean": BooleanSchema,
          "integer": IntegerSchema,
          "null":    NullSchema,
          "number":  NumberSchema,
          "string":  StringSchema,
          "array":   ArraySchema
        }[type](**properties)
    elif "allOf" in properties and isinstance(properties["allOf"], list):
      properties["options"] = properties.pop("allOf")
      return AllOf(**properties)
    elif "anyOf" in properties and isinstance(properties["anyOf"], list):
      properties["options"] = properties.pop("anyOf")
      return AnyOf(**properties)
    elif "oneOf" in properties and isinstance(properties["oneOf"], list):
      properties["options"] = properties.pop("oneOf")
      return OneOf(**properties)
    elif "$ref" in  properties:
      properties["ref"] = properties.pop("$ref")
      return Reference(**properties)
    else:
      return properties


class Schema(object):
  def __init__(self, location=None, schema=None, id=None, comment=None, title=None, description=None, version=None, definitions=[]):
    self.parent      = None
    self.location    = location
    self.schema      = schema
    self.id          = id
    self.title       = title
    self.description = description
    self.version     = version
    self.definitions = definitions
    for definition in self.definitions:
      definition.parent = self

  def definition(self, key):
    for definition in self.definitions:
      if definition.name == key: return definition
    raise KeyError("'{}' is not a known definition".format(key))

class ObjectSchema(Schema):
  def __init__(self, properties=[], minProperties=0, maxProperties=None, required=[], additionalProperties=True, **kwargs):
    super().__init__(**kwargs)
    self.properties            = properties
    self.min_properties        = minProperties
    self.max_properties        = maxProperties
    self.required              = required
    self.additional_properties = additionalProperties
    for prop in self.properties:
      prop.parent = self

  def __repr__(self):
    return "ObjectSchema(properties={})".format(
      len(self.properties)
    )

  def property(self, key):
    for prop in self.properties:
      if prop.name == key: return prop
    raise KeyError("'{}' is not a known property".format(key))

class Definition(Schema):
  def __init__(self, name, definition):
    self.name              = name
    self.definition        = definition
    self.definition.parent = self

  def __repr__(self):
    return "{}(name={}, definition={})".format(
      self.__class__.__name__, self.name, repr(self.definition)
    )

class Property(Definition):
  pass

class ValueSchema(Schema):
  def __init__(self, const=None, default=None, **kwargs):
    super().__init__(**kwargs)
    self.const   = const
    self.default = default

  def __repr__(self):
    return "{}(const={}, default={})".format(
      self.__class__.__name__, self.const, self.default
    )

class StringSchema(ValueSchema):
  def __init__(self, format=None, **kwargs):
    super().__init__(**kwargs)
    self.format = format

  def __repr__(self):
    return "{}(format={}, const={}, default={})".format(
      self.__class__.__name__, self.format, self.const, self.default
    )

class IntegerSchema(ValueSchema):
  pass

class NullSchema(ValueSchema):
  pass

class NumberSchema(ValueSchema):
  pass

class BooleanSchema(ValueSchema):
  pass

class ArraySchema(Schema):
  def __init__(self, items=None, minItems=0, maxItems=None, uniqueItems=False, **kwargs):
    super().__init__(**kwargs)
    self.items        = items
    self.min_items    = minItems
    self.max_items    = maxItems
    self.unique_items = uniqueItems
    for item in self.items:
      item.parent = self

  def __repr__(self):
    return "ArraySchema(items={}, min_items={}, max_items={}, unique_items={})".format(
      len(self.properties), self.min_items, self.max_items, self.unique_items
    )

class Combination(Schema):
  def __init__(self, options=[], **kwargs):
    super().__init__(**kwargs)
    self.options = options
    for option in self.options:
      option.parent = self
  
  def __repr__(self):
    return "{}(options={})".format(
      self.__class__.__name__, len(self.options)
    )

class AllOf(Combination):
  pass

class AnyOf(Combination):
  pass

class OneOf(Combination):
  pass

class Reference(Schema):
  def __init__(self, ref=None, **kwargs):
    super().__init__(**kwargs)
    self.ref = ref

  def __repr__(self):
    return "Reference(ref={})".format(
      self.ref
    )

  @property
  def root(self):
    p = self.parent
    while not p.parent is None:
      p = p.parent
    return p

  def resolve(self):
    if self.ref.startswith("#/definitions/"):
      name = self.ref.replace("#/definitions/", "")
      return self.root.definition(name).definition
    else:
      raise NotImplementedError
