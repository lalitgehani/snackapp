from snackapp.discovery import action


@action
def move_opportunity(ctx, id, stage):
    ctx.app.tables["opportunities"].update(id, stage=stage)
    ctx.toast("Stage updated")


@action
def save_company(ctx, id, **fields):
    ctx.app.tables["companies"].update(id, **fields)


@action
def save_opportunity(ctx, id, **fields):
    ctx.app.tables["opportunities"].update(id, **fields)


@action(command=True)
def new_company(ctx):
    ctx.go("/companies")
