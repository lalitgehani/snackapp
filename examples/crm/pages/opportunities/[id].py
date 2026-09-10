from snackapp import page, ui


@page(title="Opportunity")
def opportunity_detail(id, ctx):
    rec = ctx.app.tables["opportunities"].get(id, expand="company,person,owner")
    ui.record("opportunities", id, fields=["name", "stage", "amount", "owner"], panel=False)
    ui.fields(rec, ["name", "stage", "amount", "probability"], editable=True, action="save_opportunity")
