from schema_tools import model

class Mapping(object):
  def __init__(self, source, target):
    self.source     = source
    self.target     = target
    self.validation = []

  @property
  def is_valid(self):
    return self._validate()
  
  @property
  def status(self):
    if not self.is_valid:
      return "\n".join([str(self)] + self.validation)
    return None
  
  def __str__(self):
    return "source:{}\ntarget:{}".format(repr(self.source), repr(self.target))
  
  def _validate(self):
    self.validation = []
    if isinstance(self.source, model.ValueSchema) and  \
       isinstance(self.target, model.ValueSchema):
     return self._validate_value_schemas()
    self.validation.append(
      "can't compare source '{}' with target '{}'".format(
      self.source.__class__.__name__, self.target.__class__.__name__
    ))
    return False

  def _validate_value_schemas(self):
    if not self.source.__class__ is self.target.__class__:
      self.validation.append(
        "source type '{}' doesn't match target type '{}'".format(
        self.source.__class__.__name__, self.target.__class__.__name__
      ))
      return False
    
    return True
