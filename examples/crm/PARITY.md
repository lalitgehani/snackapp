# Parity with Twenty CRM

Comparison of this SnackApp clone against Twenty across data model, views,
record surfaces, search, and dashboards.

| Area | Twenty | SnackApp clone | Classification |
|------|--------|----------------|----------------|
| Companies / people / opportunities | Yes | Yes | — |
| Notes / tasks polymorphic targets | note-target / task-target | target_type + target_id | deliberate divergence: simpler public API |
| Attachments | Yes | files field | — |
| Timeline | Yes | ui.timeline | — |
| Favorites | Yes, per user | access=private | — |
| Kanban by stage | Yes | ui.kanban | — |
| Saved views | Yes | declared views | — |
| Command menu | Yes | shell ⌘K | example scope: search uses list contains |
| Side panel | Yes | ui.record(panel=True) | — |
| Aggregates | Yes | ui.stat / ui.chart | — |
| Workflows / AI / email sync | Yes | No | example scope |
| Pixel-perfect Twenty CSS | — | No | deliberate divergence |

Line count method: `find examples/crm -name '*.py' | xargs wc -l`.
Twenty frontend TypeScript is hundreds of thousands of lines; this clone is
under 1,200 Python lines.

Open framework defects: none.
