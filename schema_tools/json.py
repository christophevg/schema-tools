import jsoncfg

def load(path):
  return jsoncfg.load_config(path)

def loads(source):
  return jsoncfg.loads_config(source)

