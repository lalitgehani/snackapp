import { describe, expect, it } from "vitest";
import { primitives } from "./index";

describe("primitives", () => {
  it("lists thirty-eight names", () => {
    expect(primitives).toHaveLength(38);
  });
});
