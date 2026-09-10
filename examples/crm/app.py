from snackapp import App, page, ui

from .models import (
    ACTIVITIES,
    ATTACHMENTS,
    COMPANIES,
    FAVORITES,
    NOTES,
    OPPORTUNITIES,
    PEOPLE,
    TASKS,
)

app = App("SnackCRM")

companies = app.collection("companies", *COMPANIES, access="team")
people = app.collection("people", *PEOPLE, access="team")
opportunities = app.collection(
    "opportunities",
    *OPPORTUNITIES,
    access="team",
    views=[
        {"name": "All", "type": "table"},
        {"name": "My open", "type": "kanban", "group": "stage"},
        {"name": "Closing this month", "type": "table"},
    ],
)
notes = app.collection("notes", *NOTES, access="team")
tasks = app.collection("tasks", *TASKS, access="team")
attachments = app.collection("attachments", *ATTACHMENTS, access="team")
activities = app.collection("activities", *ACTIVITIES, access="team")
favorites = app.collection("favorites", *FAVORITES, access="private")


@page("/", title="Dashboard", nav=True, order=0)
def dashboard(ctx):
    ui.header("Pipeline")
    with ui.row():
        ui.stat("Open", opportunities.count("stage != 'won' and stage != 'lost'"))
        ui.chart("bar", collection="opportunities", x="stage", y="amount", aggregate="sum")
        ui.chart("line", collection="opportunities", x="close_date", y="amount", aggregate="sum")


@page("/companies", title="Companies", nav=True, order=1)
def companies_index(ctx):
    ui.header("Companies")
    ui.view_bar([{"name": "All"}])
    ui.table(companies.list(), ["name", "industry", "owner"])


@page("/people", title="People", nav=True, order=2)
def people_index(ctx):
    ui.header("People")
    ui.table(people.list(expand="company"), ["name", "company", "role"])


@page("/opportunities", title="Opportunities", nav=True, order=3)
def opportunities_index(ctx):
    ui.header("Opportunities")
    ui.view_bar([{"name": "All"}, {"name": "My open"}, {"name": "Closing this month"}])
    ui.kanban(
        opportunities.list(),
        group_by="stage",
        groups=["lead", "qualified", "proposal", "won", "lost"],
        title_field="name",
        value_field="amount",
    )
    ui.table(opportunities.list(), ["name", "stage", "amount", "owner"])


@page("/notes", title="Notes", nav=True, order=4)
def notes_index(ctx):
    ui.header("Notes")
    ui.table(notes.list(), ["body", "author"])


@page("/tasks", title="Tasks", nav=True, order=5)
def tasks_index(ctx):
    ui.header("Tasks")
    ui.table(tasks.list(), ["title", "status", "assignee"])


@page("/companies/{id}", title="Company")
def company_detail(id, ctx):
    ui.record("companies", id, fields=["name", "emails", "phones", "address"], tabs=["people", "opportunities", "notes", "tasks", "attachments"])
    ui.timeline(activities.list(filter=f"target_id = '{id}'"), "summary", "occurred_at")
