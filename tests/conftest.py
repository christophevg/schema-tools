import pytest

@pytest.fixture
def asset():
  from pathlib import Path
  def get_test_schema_path(schema, kind="schemas"):
    path = Path(__file__).parent / Path(kind) / Path(schema)
    return str(path.absolute())    
  return get_test_schema_path
