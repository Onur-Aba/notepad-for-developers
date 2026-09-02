from __future__ import annotations

import ast
from pathlib import Path


def _catalog() -> dict[str, dict[str, str]]:
    source = Path("app/i18n.py").read_text(encoding="utf-8")
    module = ast.parse(source)
    for node in module.body:
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and node.target.id == "_TRANSLATIONS":
            return ast.literal_eval(node.value)
    raise AssertionError("_TRANSLATIONS catalog not found")


def test_english_and_turkish_catalogs_have_identical_key_coverage() -> None:
    catalog = _catalog()
    assert set(catalog) == {"en", "tr"}
    assert set(catalog["en"]) == set(catalog["tr"])
    assert all(str(value).strip() for table in catalog.values() for value in table.values())
