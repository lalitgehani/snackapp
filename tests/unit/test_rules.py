from snackapp.schema import rules_for


def test_private_rules():
    rules = rules_for("private", "owner")
    assert rules["list_rule"] == "owner = @request.auth.id"
    assert rules["view_rule"] == "owner = @request.auth.id"
    assert rules["update_rule"] == "owner = @request.auth.id"
    assert rules["delete_rule"] == "owner = @request.auth.id"
    assert rules["create_rule"] == ""


def test_team_rules_are_open():
    rules = rules_for("team")
    assert set(rules.values()) == {""}


def test_readonly_locks_writes():
    rules = rules_for("readonly")
    assert rules["list_rule"] == ""
    assert rules["create_rule"] is None
    assert rules["update_rule"] is None
    assert rules["delete_rule"] is None
