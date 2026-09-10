import { describe, expect, it } from "vitest";
import { decodeViewState, encodeViewState } from "./urlState";

describe("view URL state", () => {
  it("round-trips filters sorts and group", () => {
    const state = {
      filters: [{ field: "stage", operand: "is", value: "won" }],
      sort: [{ field: "name", dir: "asc" as const }],
      group: "stage",
      view: "mine",
    };
    const encoded = encodeViewState(state);
    expect(decodeViewState(encoded)).toEqual(state);
  });
});
