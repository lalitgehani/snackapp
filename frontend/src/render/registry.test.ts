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
});
