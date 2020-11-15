import yaml
from yaml.loader import SafeLoader

def load(path):
  return yaml.load(path, Loader=ConfigYamlLoader)

def loads(src):
  return yaml.load(src, Loader=ConfigYamlLoader)


class ConfigNode(object):
  def __init__(self, line, column):
    self._line   = line
    self._column = column
  

class ConfigYamlScalar(ConfigNode):
  def __init__(self, value, line, column):
    super().__init__(line, column)
    self._value  = value

  def replace(self, find, replace_by):
    return self._value.replace(find, replace_by)

  def __repr__(self):
    return "ConfigYamlScalar(value={}, line={}, column={})".format(
      self._value, self._line, self._column
    )
  
  def __call__(self):
    return self._value

class ConfigYamlArray(ConfigNode):
  def __init__(self, items, line, column):
    super().__init__(line, column)
    self._items   = items
    self.current = -1

  def __iter__(self):
    return iter(self._items)

  def __setitem__(self, key, item):
      self._items[key] = item

  def __getitem__(self, key):
      return self._items[key]
  
  def __repr__(self):
    return "ConfigYamlArray(len={}, line={}, column={})".format(
      len(self._items), self._line, self._column
    )

  def __call__(self):
    return [ v() for v in self ]

class ConfigYamlObject(ConfigNode):
  def __init__(self, items, line, column):
    super().__init__(line, column)
    self._items  = items

  def __iter__(self):
    return iter(self._items.items())

  def __setitem__(self, key, item):
    self._items[key] = item

  def __getitem__(self, key):
    return self._items[key]

  def __getattr__(self, key):
    return self._items[key]

  def __repr__(self):
    return "ConfigYamlObject(len={}, line={}, column={})".format(
      len(self._items), self._line, self._column
    )

  def __len__(self):
      return len(self._items)

  def __delitem__(self, key):
      del self._items[key]

  def clear(self):
      return self._items.clear()

  def copy(self):
      return self._items.copy()

  def has_key(self, k):
      return k in self._items

  def __contains__(self, k):
    return k in self._items

  def update(self, *args, **kwargs):
      return self._items.update(*args, **kwargs)

  def keys(self):
      return self._items.keys()

  def values(self):
      return self._items.values()

  def items(self):
    return self._items.items()

  def __call__(self):
    return {
      k : v() for k, v in self.items()
    }

class ConfigYamlLoader(yaml.SafeLoader):
  pass

def scalar_constructor(type=None):
  def constructor(loader, node):
    value = loader.construct_scalar(node)
    value = type(value) if type else None
    return ConfigYamlScalar(value, node.start_mark.line+1, node.start_mark.column)      
  return constructor
yaml.add_constructor("tag:yaml.org,2002:str",   scalar_constructor(str),   ConfigYamlLoader)
yaml.add_constructor("tag:yaml.org,2002:int",   scalar_constructor(int),   ConfigYamlLoader)
yaml.add_constructor("tag:yaml.org,2002:float", scalar_constructor(float), ConfigYamlLoader)
yaml.add_constructor("tag:yaml.org,2002:bool",  scalar_constructor(bool),  ConfigYamlLoader)
yaml.add_constructor("tag:yaml.org,2002:null",  scalar_constructor(),      ConfigYamlLoader)

def list_constructor(loader, node):
  items = loader.construct_sequence(node)
  return ConfigYamlArray(items, node.start_mark.line, node.start_mark.column)
yaml.add_constructor(yaml.resolver.BaseResolver.DEFAULT_SEQUENCE_TAG, list_constructor,  ConfigYamlLoader)

def dict_constructor(loader, node):
  mapping = loader.construct_mapping(node)
  mapping = { k() : v  for k, v in mapping.items() }
  return ConfigYamlObject(mapping, node.start_mark.line, node.start_mark.column)
yaml.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, dict_constructor,  ConfigYamlLoader)
