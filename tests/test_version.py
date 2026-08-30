from app.constants import VERSION


def test_version_is_single_source() -> None:
    assert VERSION == "1.2.3"
