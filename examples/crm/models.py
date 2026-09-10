from snackapp import Field

COMPANIES = [
    Field.text("name", required=True),
    Field.computed("label", "concat(name, '')", "text"),
    Field.full_name("legal_name"),
    Field.emails("emails"),
    Field.phones("phones"),
    Field.links("links"),
    Field.address("address"),
    Field.url("domain"),
    Field.email("billing_email"),
    Field.phone("switchboard"),
    Field.number("employees"),
    Field.multi_select("tags", ["vip", "partner"]),
    Field.user("owner"),
    Field.select("industry", ["saas", "agency", "other"]),
    Field.rating("health"),
    Field.json("meta"),
]

PEOPLE = [
    Field.full_name("name"),
    Field.emails("emails"),
    Field.phones("phones"),
    Field.relation("company", to="companies"),
    Field.user("owner"),
    Field.select("role", ["champion", "buyer", "user"]),
]

OPPORTUNITIES = [
    Field.text("name", required=True),
    Field.relation("company", to="companies"),
    Field.relation("person", to="people"),
    Field.currency("amount"),
    Field.percent("probability"),
    Field.select("stage", ["lead", "qualified", "proposal", "won", "lost"]),
    Field.date("close_date"),
    Field.user("owner"),
    Field.rating("fit"),
]

NOTES = [
    Field.rich_text("body"),
    Field.user("author"),
    Field.select("target_type", ["companies", "people", "opportunities"]),
    Field.text("target_id"),
]

TASKS = [
    Field.text("title", required=True),
    Field.long_text("description"),
    Field.select("status", ["open", "done"]),
    Field.date("due"),
    Field.datetime("remind_at"),
    Field.user("assignee"),
    Field.select("target_type", ["companies", "people", "opportunities"]),
    Field.text("target_id"),
    Field.boolean("done"),
]

ATTACHMENTS = [
    Field.files("files"),
    Field.file("primary"),
    Field.relation("company", to="companies"),
    Field.array("tags"),
]

ACTIVITIES = [
    Field.text("summary"),
    Field.datetime("occurred_at"),
    Field.user("actor"),
    Field.select("kind", ["create", "update", "comment"]),
    Field.json("payload"),
    Field.text("target_id"),
]

FAVORITES = [
    Field.relation("company", to="companies"),
    Field.user("owner"),
    Field.boolean("pinned", default=True),
]
