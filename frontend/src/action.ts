import { createContext } from "react";

export type ActionResult = {
  ok?: boolean;
  error?: string;
  redirect?: string | null;
  toast?: string | null;
};

export type ActionApi = {
  run: (name: string, params?: Record<string, unknown>) => Promise<ActionResult>;
  go: (path: string) => void;
};

export const ActionContext = createContext<ActionApi>({
  run: async () => ({ ok: false, error: "no action runtime" }),
  go: () => undefined,
});
