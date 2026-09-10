from snackapp import page, ui


@page("/", title="Dashboard", nav=True, order=0)
def dashboard(ctx):
    opps = ctx.app.tables["opportunities"]
    acts = ctx.app.tables["activities"]
    open_n = opps.count("stage != 'won' and stage != 'lost'")
    won_n = opps.count("stage = 'won'")
    all_n = opps.count()
    win_rate = f"{(won_n / all_n * 100):.0f}%" if all_n else "—"
    by_stage = opps.aggregate(functions="count()", group_by="stage")
    won_over_time = opps.aggregate(
        functions="count()", group_by="close_date", filter="stage = 'won'"
    )
    volume = acts.count()
    ui.header("Pipeline")
    with ui.row():
        ui.stat("Open", open_n)
        ui.stat("Win rate", win_rate)
        ui.stat("Won", won_n)
        ui.stat("Activity", volume)
    stage_rows = by_stage.get("results") if isinstance(by_stage, dict) else []
    won_rows = won_over_time.get("results") if isinstance(won_over_time, dict) else []
    ui.chart("bar", data=stage_rows, collection="opportunities")
    ui.chart("line", data=won_rows)
