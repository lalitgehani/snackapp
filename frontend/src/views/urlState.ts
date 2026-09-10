export type ViewState = {
  filters: { field: string; operand: string; value: string }[];
  sort: { field: string; dir: "asc" | "desc" }[];
  group?: string;
  view?: string;
};

export function encodeViewState(state: ViewState): string {
  const params = new URLSearchParams();
  if (state.filters.length) params.set("f", JSON.stringify(state.filters));
  if (state.sort.length) params.set("s", JSON.stringify(state.sort));
  if (state.group) params.set("g", state.group);
  if (state.view) params.set("v", state.view);
  return params.toString();
}

export function decodeViewState(search: string): ViewState {
  const params = new URLSearchParams(search.startsWith("?") ? search.slice(1) : search);
  const parse = <T,>(key: string, fallback: T): T => {
    const raw = params.get(key);
    if (!raw) return fallback;
    try {
      return JSON.parse(raw) as T;
    } catch {
      return fallback;
    }
  };
  return {
    filters: parse("f", [] as ViewState["filters"]),
    sort: parse("s", [] as ViewState["sort"]),
    group: params.get("g") || undefined,
    view: params.get("v") || undefined,
  };
}
