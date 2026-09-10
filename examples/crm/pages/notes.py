from snackapp import page, ui


@page("/notes", title="Notes", nav=True, order=4)
def notes_index(ctx):
    ui.header("Notes")
    ui.table(ctx.app.tables["notes"].list(expand="author"), ["body", "author", "target_type"])
