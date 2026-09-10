import ast
import importlib.util
from pathlib import Path

from snackapp.schema import Schema

ROOT = Path(__file__).resolve().parents[2] / "examples" / "crm"


def _models():
    spec = importlib.util.spec_from_file_location("crm_models", ROOT / "models.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


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


def test_crm_storage_fields_pass_collection_validator():
    from snackbase.domain.services.collection_validator import CollectionValidator

    models = _models()
    schema = Schema()
    schema.collection("companies", *models.COMPANIES, access="team")
    schema.collection("people", *models.PEOPLE, access="team")
    schema.collection("opportunities", *models.OPPORTUNITIES, access="team")
    schema.collection("notes", *models.NOTES, access="team")
    schema.collection("tasks", *models.TASKS, access="team")
    schema.collection("attachments", *models.ATTACHMENTS, access="team")
    schema.collection("activities", *models.ACTIVITIES, access="team")
    schema.collection("favorites", *models.FAVORITES, access="private")
    for name, cd in schema.defs.items():
        errors = CollectionValidator.validate(name, cd.storage_fields())
        assert errors == [], (name, [(e.code, e.message) for e in errors])


def test_dashboard_uses_aggregates_not_row_loads():
    text = (ROOT / "pages" / "index.py").read_text()
    assert ".list(" not in text
    assert ".count(" in text
    assert ".aggregate(" in text


def test_pages_directory_exists():
    assert (ROOT / "pages" / "index.py").exists()
    assert (ROOT / "pages" / "companies.py").exists()
    assert (ROOT / "pages" / "opportunities.py").exists()
    assert (ROOT / "pages" / "companies" / "[id].py").exists()


def test_favorites_are_private():
    text = (ROOT / "app.py").read_text()
    assert 'access="private"' in text
    assert "favorites" in text


def test_index_pages_under_60_lines():
    for name in ("companies.py", "people.py", "opportunities.py", "notes.py", "tasks.py", "index.py"):
        lines = (ROOT / "pages" / name).read_text().splitlines()
        assert len(lines) < 60, name


def test_detail_pages_under_80_lines():
    for rel in ("pages/companies/[id].py", "pages/people/[id].py", "pages/opportunities/[id].py"):
        lines = (ROOT / rel).read_text().splitlines()
        assert len(lines) < 80, rel


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
