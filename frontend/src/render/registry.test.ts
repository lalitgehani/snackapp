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

  it("bounds table rows", () => {
    const node = {
      kind: "table",
      rows: Array.from({ length: 80 }, (_, i) => ({ id: String(i), name: "n" })),
      columns: [{ field: "name", label: "Name" }],
    };
    const el = registry.table(node, () => null) as { props: { node: typeof node } };
    expect(el).toBeTruthy();
  });
});
