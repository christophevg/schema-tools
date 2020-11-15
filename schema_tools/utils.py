from collections import namedtuple

location = namedtuple("NodeLocation", "line column")

def node_location(node):
  try:
    return location(node._line, node._column)
  except AttributeError:
    raise TypeError("Expected a config node but received a {}.".format(
      node.__class__.__name__
    ))
