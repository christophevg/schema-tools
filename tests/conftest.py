import pytest


@pytest.fixture
def asset():
  from pathlib import Path

  class AssetPath(str):
    """
    filesystem path to a test asset; .uri is the same location as a
    proper file:// URI, for embedding in JSON "$ref" values (raw Windows
    paths contain invalid escape sequences)
    """

    @property
    def uri(self):
      # fragment (e.g. "money.json#/properties/currency") must stay
      # delimiter-separated, not percent-encoded
      path, _, fragment = Path(self).absolute().as_posix().partition("#")
      return Path(path).as_uri() + ("#" + fragment if fragment else "")

  def get_test_schema_path(schema, kind="schemas"):
    return AssetPath(Path(__file__).parent / kind / schema)

  return get_test_schema_path
