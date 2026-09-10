"""UI primitives.

The page function runs ONCE PER NAVIGATION on the server, with real data in
hand -- so you write ordinary Python and can branch on values. What it produces
is a tree, not HTML. Interactions afterwards are one of two things:

  * client-local (typing, sorting a loaded table, opening a modal, tab switch)
    -- these never call Python at all; or
  * an @action -- ordinary Python that mutates through SnackBase and names the
    fragments to refresh.

That is the whole state model. There is deliberately no session_state:
    data state      -> SnackBase collections
    navigation state-> the URL
    ephemeral state -> owned by the widget in the browser
"""
from __future__ import annotations

import contextvars
from contextlib import contextmanager
from typing import Any

_stack: contextvars.ContextVar[list] = contextvars.ContextVar("ui_stack")
# names of the fragments currently being built, outermost first
_frags: contextvars.ContextVar[list] = contextvars.ContextVar("ui_frags", default=[])


def active_fragments() -> list[str]:
    return list(_frags.get())


def _node(kind: str, **props: Any) -> dict:
    n = {"kind": kind, **{k: v for k, v in props.items() if v is not None}}
    stack = _stack.get(None)
    if stack:
        stack[-1].setdefault("children", []).append(n)
    return n


@contextmanager
def _container(kind: str, **props: Any):
    n = _node(kind, **props)
    n.setdefault("children", [])
    stack = _stack.get()
    stack.append(n)
    try:
        yield n
    finally:
        stack.pop()


def new_tree() -> tuple[dict, contextvars.Token]:
    root = {"kind": "page", "children": []}
    token = _stack.set([root])
    return root, token


def end_tree(token: contextvars.Token) -> None:
    _stack.reset(token)


# --- layout -----------------------------------------------------------------
def header(title: str, subtitle: str | None = None, actions: list | None = None):
    return _node("header", title=title, subtitle=subtitle, actions=actions or [])


@contextmanager
def row(gap: str = "md", align: str = "stretch"):
    with _container("row", gap=gap, align=align) as n:
        yield n


@contextmanager
def column(width: str | None = None):
    with _container("column", width=width) as n:
        yield n


@contextmanager
def card(title: str | None = None, actions: list | None = None):
    with _container("card", title=title, actions=actions or []) as n:
        yield n


@contextmanager
def tabs():
    with _container("tabs") as n:
        yield n


@contextmanager
def tab(label: str):
    with _container("tab", label=label) as n:
        yield n


@contextmanager
def fragment(name: str):
    """A named region that an action can refresh on its own.

    This is what replaces the whole-script rerun: an action says
    `refresh("pipeline")` and only this subtree is rebuilt.
    """
    n_deps: set[str] = set()
    prev = _frags.get()
    _frags.set(prev + [name])
    try:
        with _container("fragment", name=name, deps=[]) as n:
            n["_deps"] = n_deps
            yield n
    finally:
        _frags.set(prev)
        # deps are filled in by the runtime from what this fragment read
        n["deps"] = sorted(n_deps)
        n.pop("_deps", None)


# --- display ----------------------------------------------------------------
def text(value: str, muted: bool = False):
    return _node("text", value=value, muted=muted or None)


def markdown(value: str):
    return _node("markdown", value=value)


def stat(label: str, value: Any, delta: str | None = None, tone: str = "neutral"):
    return _node("stat", label=label, value=value, delta=delta, tone=tone)


def empty(message: str, action: dict | None = None):
    return _node("empty", message=message, action=action)


def badge(value: str, tone: str = "neutral"):
    return _node("badge", value=value, tone=tone)


def divider():
    return _node("divider")


# --- data display -----------------------------------------------------------
def table(rows: list[dict], columns: list, row_link: str | None = None,
          search: list[str] | None = None, empty_message: str = "Nothing here yet.",
          row_actions: list | None = None, page_size: int = 25):
    """Columns are names, or {'field','label','type','width'} dicts."""
    cols = []
    for c in columns:
        c = {"field": c} if isinstance(c, str) else dict(c)
        c.setdefault("label", c["field"].split(".")[-1].replace("_", " ").title())
        cols.append(c)
    return _node("table", rows=rows, columns=cols, row_link=row_link,
                 search=search, empty_message=empty_message,
                 row_actions=row_actions or [], page_size=page_size)


def fields(record: dict, spec: list, editable: bool = False, action: str | None = None):
    """Render a record as a label/value grid, optionally inline-editable."""
    items = []
    for f in spec:
        f = {"field": f} if isinstance(f, str) else dict(f)
        f.setdefault("label", f["field"].replace("_", " ").title())
        items.append(f)
    return _node("fields", record=record, items=items,
                 editable=editable or None, action=action)


def kanban(rows: list[dict], group_by: str, groups: list[str], title_field: str,
           subtitle_field: str | None = None, value_field: str | None = None,
           on_move: str | None = None, card_link: str | None = None):
    return _node("kanban", rows=rows, group_by=group_by, groups=groups,
                 title_field=title_field, subtitle_field=subtitle_field,
                 value_field=value_field, on_move=on_move, card_link=card_link)


def timeline(items: list[dict], title_field: str, time_field: str,
             body_field: str | None = None):
    return _node("timeline", items=items, title_field=title_field,
                 time_field=time_field, body_field=body_field)


def bar_chart(data: list[dict], label_field: str, value_field: str, height: int = 180):
    return _node("bar_chart", data=data, label_field=label_field,
                 value_field=value_field, height=height)


# --- input ------------------------------------------------------------------
def button(label: str, action: str | None = None, params: dict | None = None,
           link: str | None = None, opens: str | None = None,
           tone: str = "default", confirm: str | None = None):
    return {"kind": "button", "label": label, "action": action,
            "params": params or {}, "link": link, "opens": opens,
            "tone": tone, "confirm": confirm}


def form(name: str, action: str, spec: list, values: dict | None = None,
         submit_label: str = "Save", title: str | None = None,
         params: dict | None = None):
    """A form is a declaration: fields, the action it submits to, and defaults.

    Draft state lives in the browser. Python never sees a keystroke.
    """
    items = []
    for f in spec:
        if isinstance(f, str):
            items.append({"field": f, "label": f.replace("_", " ").title(), "type": "text"})
        else:
            f = dict(f)
            f.setdefault("label", f["field"].replace("_", " ").title())
            f.setdefault("type", "text")
            items.append(f)
    return _node("form", name=name, action=action, items=items,
                 values=values or {}, submit_label=submit_label,
                 title=title, params=params or {})


def modal_form(name: str, action: str, spec: list, values: dict | None = None,
               submit_label: str = "Save", title: str | None = None,
               params: dict | None = None):
    n = form(name, action, spec, values, submit_label, title, params)
    n["modal"] = True
    return n


def record(collection: str, id: str, fields: list | None = None, tabs: list | None = None,
           panel: bool = False):
    return _node(
        "record",
        collection=collection,
        id=id,
        fields=fields or [],
        tabs=tabs or [],
        panel=panel or None,
    )


def chart(kind: str, data: list[dict] | None = None, collection: str | None = None,
          x: str | None = None, y: str | None = None, aggregate: str | None = None):
    return _node(
        "chart",
        chart=kind,
        data=data or [],
        collection=collection,
        x=x,
        y=y,
        aggregate=aggregate,
    )


def list_view(rows: list[dict], title_field: str, subtitle_field: str | None = None):
    return _node("list", rows=rows, title_field=title_field, subtitle_field=subtitle_field)


def calendar(rows: list[dict], date_field: str):
    if not date_field:
        raise ValueError("calendar view requires a date field")
    return _node("calendar", rows=rows, date_field=date_field)


def view_bar(views: list[dict], current: str | None = None):
    return _node("view_bar", views=views, current=current)


def filter_bar(spec: list, values: dict | None = None):
    """Filters bind to the URL query string, not to hidden server state.

    Changing one is a navigation, which means it is shareable and back-button
    correct for free -- the thing session_state can never give you.
    """
    return _node("filter_bar", items=spec, values=values or {})
