from snackapp import page, ui


@page("/opportunities", title="Opportunities", nav=True, order=3)
def opportunities_index(ctx):
    rows = ctx.app.tables["opportunities"].list(expand="company,owner")
    ui.header("Opportunities")
    ui.view_bar(
        [
            {"name": "All", "type": "table"},
            {"name": "My open", "type": "kanban"},
            {"name": "Closing this month", "type": "table"},
        ]
    )
    ui.kanban(
        rows,
        group_by="stage",
        groups=["lead", "qualified", "proposal", "won", "lost"],
        title_field="name",
        value_field="amount",
        on_move="move_opportunity",
        card_link="/opportunities/{id}",
    )
    ui.table(rows, ["name", "stage", "amount", "owner"], row_link="/opportunities/{id}")
