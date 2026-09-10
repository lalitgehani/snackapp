import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "examples" / "crm"


def _py_files():
    return list(ROOT.rglob("*.py"))


def test_models_under_150_lines():
    text = (ROOT / "models.py").read_text().splitlines()
    assert len(text) < 150


def test_clone_under_1200_lines():
    total = sum(len(p.read_text().splitlines()) for p in _py_files())
    assert total < 1200


def test_all_26_types_used():
    from snackapp.fields.registry import FIELD_REGISTRY

    text = (ROOT / "models.py").read_text()
    used = {name for name in FIELD_REGISTRY if f"Field.{name}(" in text}
    assert set(FIELD_REGISTRY) <= used


def test_no_rules_escape_hatch():
    for path in _py_files():
        assert "rules=" not in path.read_text()


def test_public_imports_only():
    allowed = {"snackapp", "examples"}
    for path in _py_files():
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.level:
                    continue
                if not node.module:
                    continue
                root = node.module.split(".")[0]
                if node.module.startswith("snackapp."):
                    rest = node.module.split(".")[1]
                    assert rest not in {"embedded", "provision"}, path
                assert root in allowed or node.module.startswith("snackapp"), path
