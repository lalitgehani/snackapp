from snackapp import page, ui


@page("/companies", title="Companies", nav=True, order=1)
def companies_index(ctx):
    rows = ctx.app.tables["companies"].list(expand="owner")
    ui.header("Companies")
    ui.view_bar([{"name": "All"}])
    ui.filter_bar([{"field": "industry", "operand": "is"}])
    ui.table(rows, ["name", "industry", "owner"], row_link="/companies/{id}")
