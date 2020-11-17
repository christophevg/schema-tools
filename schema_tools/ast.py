class SchemaNode(object):
  def __init__(self, line, column):
    self._line   = line
    self._column = column
  

class ValueNode(SchemaNode):
  def __init__(self, value, line, column):
    super().__init__(line, column)
    self._value  = value

  def replace(self, find, replace_by):
    return self._value.replace(find, replace_by)

  def __repr__(self):
    return "ValueNode(value={}, line={}, column={})".format(
      self._value, self._line, self._column
    )
  
  def __call__(self):
    return self._value

  def __eq__(self, other):
    if not isinstance(other, self.__class__): return NotImplemented
    return self._value == other._value

  def __hash__(self):
    return hash( (self._value, self._line, self._column) )

class ListNode(SchemaNode):
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
    return "ListNode(len={}, line={}, column={})".format(
      len(self._items), self._line, self._column
    )

  def __call__(self):
    return [ v() for v in self ]

  def __eq__(self, other):
    if not isinstance(other, self.__class__): return NotImplemented
    for index, _ in enumerate(self._items):
      if self._items[index] != other._items[index]: return False
    return True

class ObjectNode(SchemaNode):
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
    return "ObjectNode(len={}, line={}, column={})".format(
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

  def __eq__(self, other):
    if not isinstance(other, self.__class__): return NotImplemented
    for key in self._items.keys():
      if self._items[key] != other._items[key]: return False
    return True
