from schema_tools.schema.json import ValueSchema, Enum, StringSchema

class ValidationIssue(object):
  def __init__(self, msg):
    self.msg = msg

  def __str__(self):
    return "{}: {}".format(self.__class__.__name__, self.msg)
  
  def __repr__(self):
    return str(self)

class Warning(ValidationIssue): pass
class Error(ValidationIssue): pass

class Mapping(object):
  def __init__(self, source, target):
    self.source     = source
    self.target     = target
    self.validation = []

  @property
  def is_valid(self):
    return self._validate()
  
  @property
  def issues(self):
    self._validate()
    return self.validation

  @property
  def errors(self):
    self._validate()
    return [ e for e in self.validation if isinstance(e, Error) ]

  @property
  def warnings(self):
    self._validate()
    return [ w for w in self.validation if isinstance(w, Warning) ]

  def warn(self, msg, *args):
    self.validation.append(Warning(msg.format(*args)))
    return True

  def error(self, msg, *args):
    self.validation.append(Error(msg.format(*args)))
    return False

  def __str__(self):
    return "source:{}\ntarget:{}".format(repr(self.source), repr(self.target))
  
  # TODO make this more generic and easier to simply add checks

  def _validate(self):
    self.validation = []
    if isinstance(self.source, ValueSchema) and isinstance(self.target, ValueSchema):
     return self._validate_value_schemas()

    if isinstance(self.source, Enum) and isinstance(self.target, Enum):
     return self._validate_enum_schemas()

    if isinstance(self.source, Enum) and isinstance(self.target, StringSchema):
      return self.warn(
        "target type, 'StringSchema', accepts '{}' with cast",
        self.source.__class__.__name__
      )
    return self.error(
      "can't compare source '{}' with target '{}'",
      self.source.__class__.__name__, self.target.__class__.__name__
    )

  def _validate_value_schemas(self):
    if self.source.__class__ is self.target.__class__: return True
    if self.target.__class__ is StringSchema:
      return self.warn(
        "target type, 'StringSchema', accepts '{}' with cast",
        self.source.__class__.__name__
      )
    else:
      return self.error(
        "source type '{}' doesn't match target type '{}'",
        self.source.__class__.__name__, self.target.__class__.__name__
      )

  def _validate_enum_schemas(self):
    if not self.source.__class__ is self.target.__class__:
      return self.error(
        "source type '{}' doesn't match target type '{}'",
          self.source.__class__.__name__, self.target.__class__.__name__
      )
    if not self.source.values == self.target.values:
      return self.error(
        "source enum values () don't match target enum values ()",
        ", ".join(self.source.values), ", ".join(self.target.values)
      )
    return True
