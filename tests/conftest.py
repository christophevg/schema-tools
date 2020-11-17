import pytest

@pytest.fixture
def schema():
  from pathlib import Path
  def get_test_schema_path(schema):
    path = Path(__file__).parent / Path("schemas") / Path(schema)
    return str(path.absolute())    
  return get_test_schema_path
