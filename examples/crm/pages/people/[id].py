from snackapp import page, ui


@page(title="Person")
def person_detail(id, ctx):
    ui.record("people", id, fields=["name", "emails", "phones", "role", "company"])
    ui.timeline(
        ctx.app.tables["activities"].list(filter=f"target_id = '{id}'"),
        "summary",
        "occurred_at",
    )
