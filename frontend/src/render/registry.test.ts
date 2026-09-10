import { createElement, type ReactElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import { registry } from "./registry";

const kinds = [
  "page", "header", "row", "column", "card", "tabs", "tab", "fragment",
  "text", "markdown", "stat", "empty", "badge", "divider", "table", "fields",
  "kanban", "timeline", "bar_chart", "form", "filter_bar", "button",
  "record", "chart", "list", "calendar", "view_bar",
];

describe("node registry", () => {
  it("resolves every emitted kind", () => {
    for (const kind of kinds) {
      expect(registry[kind], kind).toBeTypeOf("function");
    }
  });

  it("keeps a 10000-row table to a bounded tbody", () => {
    const node = {
      kind: "table",
      rows: Array.from({ length: 10_000 }, (_, i) => ({ id: String(i), name: `n${i}` })),
      columns: [{ field: "name", label: "Name" }],
    };
    const el = registry.table(node, () => null) as ReactElement;
    const html = renderToStaticMarkup(createElement("div", null, el));
    expect(html).toContain('data-kind="table"');
    expect(html).toContain('data-row-count="10000"');
    expect(html).toContain('data-virtual-bound="60"');
    const body = html.match(/<tbody>([\s\S]*)<\/tbody>/)?.[1] ?? "";
    const rowCount = (body.match(/<tr\b/g) ?? []).length;
    expect(rowCount).toBe(60);
    expect(body).toContain(">n0<");
    expect(body).toContain(">n59<");
    expect(body).not.toContain(">n60<");
    expect(body).not.toContain(">n9999<");
  });

  it("renders a form with a submit control", () => {
    const node = {
      kind: "form",
      name: "new",
      action: "add_todo",
      title: "Add",
      items: [{ field: "title", label: "Title", type: "text" }],
      values: {},
      params: {},
      submit_label: "Add task",
    };
    const el = registry.form(node, () => null) as ReactElement;
    const html = renderToStaticMarkup(createElement("div", null, el));
    expect(html).toContain('data-kind="form"');
    expect(html).toContain('name="title"');
    expect(html).toContain("Add task");
  });
});
