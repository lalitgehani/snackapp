from snackapp import page, ui


@page("/tasks", title="Tasks", nav=True, order=5)
def tasks_index(ctx):
    rows = ctx.app.tables["tasks"].list(expand="assignee")
    ui.header("Tasks")
    ui.table(rows, ["title", "status", "assignee"])
    ui.calendar(rows, "due")
