export const FIELD_DISPLAY: Record<string, (value: unknown) => string> = {
  text: String,
  long_text: String,
  rich_text: (v) => JSON.stringify(v),
  number: String,
  currency: (v) => {
    const o = v as { amount?: number; code?: string };
    return `${o?.amount ?? ""} ${o?.code ?? ""}`.trim();
  },
  percent: (v) => `${v}%`,
  rating: String,
  boolean: (v) => (v ? "yes" : "no"),
  date: String,
  datetime: String,
  select: String,
  multi_select: (v) => (Array.isArray(v) ? v.join(", ") : String(v)),
  email: String,
  emails: (v) => JSON.stringify(v),
  phone: String,
  phones: (v) => JSON.stringify(v),
  url: String,
  links: (v) => JSON.stringify(v),
  full_name: (v) => {
    const o = v as { first?: string; last?: string };
    return `${o?.first ?? ""} ${o?.last ?? ""}`.trim();
  },
  address: (v) => JSON.stringify(v),
  json: (v) => JSON.stringify(v),
  array: (v) => JSON.stringify(v),
  file: (v) => JSON.stringify(v),
  files: (v) => JSON.stringify(v),
  relation: String,
  user: (v) => {
    if (v && typeof v === "object" && "email" in (v as object)) {
      return String((v as { email: string }).email);
    }
    return String(v ?? "");
  },
};
