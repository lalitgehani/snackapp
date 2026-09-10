from snackapp import App

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
