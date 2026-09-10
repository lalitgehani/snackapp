import { describe, expect, it } from "vitest";
import { FIELD_DISPLAY } from "./FieldRenderer";

describe("field display", () => {
  it("covers every registry type", () => {
    const types = [
      "text", "long_text", "rich_text", "number", "currency", "percent", "rating",
      "boolean", "date", "datetime", "select", "multi_select", "email", "emails",
      "phone", "phones", "url", "links", "full_name", "address", "json", "array",
      "file", "files", "relation", "user",
    ];
    for (const t of types) {
      expect(FIELD_DISPLAY[t]("x")).toBeTypeOf("string");
    }
  });
});
