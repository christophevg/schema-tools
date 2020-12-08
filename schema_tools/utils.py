from collections import namedtuple

from schema_tools.ast import ValueNode, ListNode, ObjectNode

location = namedtuple("NodeLocation", "line column")

def node_location(node):
  try:
    return location(node._line, node._column)
  except AttributeError:
    raise TypeError("Expected a config node but received a {}.".format(
      node.__class__.__name__
    ))

class VisitorException(Exception): pass

class Visitor(object):
  def __init__(self, value_class, list_class, object_class):
    self.value_class  = value_class
    self.list_class   = list_class
    self.object_class = object_class

  def visit(self, obj):
    try:
      if isinstance(obj, self.object_class):
        return self.visit_object(obj)
      elif isinstance(obj, self.list_class):
        return self.visit_list(obj)
      elif isinstance(obj, self.value_class):
        return self.visit_value(obj)
      else:
        raise TypeError("Node type '{}' is not supported by '{}'".format(
          obj.__class__.__name__, self.__class__.__name__
        ))
    except VisitorException as e:
      raise e
    except Exception as e:
      raise VisitorException("Failed to visit '{}', due to '{}'".format(
        repr(obj),
        str(e)
      ))

  def visit_value(self, value_node):
    raise NotImplementedError

  def visit_list(self, list_node):
    raise NotImplementedError

  def visit_object(self, object_node):
    raise NotImplementedError

class ASTVisitor(Visitor):
  def __init__(self):
    super().__init__(ValueNode, ListNode, ObjectNode)
    self.level = 0

  def location(self, node):
    return node_location(node)
  
  def visit_value(self, value_node):
    raise NotImplementedError

  def visit_list(self, list_node):
    self.level += 1
    children = [ self.visit(item) for item in list_node ]
    self.level -= 1
    return children

  def visit_object(self, object_node):
    self.level += 1
    children = { str(key) : self.visit(child) for key, child in object_node.items() }
    self.level -= 1
    return children

class ASTDumper(ASTVisitor):
  def dump(self, node):
    return "\n".join(self.visit(node))

  def indent(self):
    return "  " * self.level

  def location(self, node):
    location = super().location(node)
    # don't take into account column ;-)
    return "[{},{}]{} ".format(*location, self.indent())

  def visit_value(self, value_node):
    return "{}{}".format(self.location(value_node), value_node())

  def visit_object(self, object_node):
    children = []
    for key, child in super().visit_object(object_node).items():
      # reuse location of child for key
      children.append("{}{}".format(self.location(object_node[key]), key))
      if isinstance(child, list):
        children.extend(child)
      else:
        children.append(child)
    return children
