from snackapp import page, ui


@page(title="Company")
def company_detail(id, ctx):
    rec = ctx.app.tables["companies"].get(id, expand="owner")
    people = ctx.app.tables["people"].list(filter=f"company = '{id}'")
    opps = ctx.app.tables["opportunities"].list(filter=f"company = '{id}'")
    notes = ctx.app.tables["notes"].list(filter=f"target_id = '{id}'")
    tasks = ctx.app.tables["tasks"].list(filter=f"target_id = '{id}'")
    files = ctx.app.tables["attachments"].list(filter=f"company = '{id}'")
    ui.record(
        "companies",
        id,
        fields=["name", "emails", "phones", "address", "owner"],
        tabs=[
            f"People ({len(people)})",
            f"Opportunities ({len(opps)})",
            f"Notes ({len(notes)})",
            f"Tasks ({len(tasks)})",
            f"Attachments ({len(files)})",
        ],
    )
    ui.fields(rec, ["name", "industry", "domain"], editable=True, action="save_company")
    ui.timeline(
        ctx.app.tables["activities"].list(filter=f"target_id = '{id}'"),
        "summary",
        "occurred_at",
        body_field="payload",
    )
