from snackapp import page, ui


@page("/people", title="People", nav=True, order=2)
def people_index(ctx):
    rows = ctx.app.tables["people"].list(expand="company,owner")
    ui.header("People")
    ui.table(rows, ["name", "company", "role"], row_link="/people/{id}")
    ui.list_view(rows, "name", "role")
