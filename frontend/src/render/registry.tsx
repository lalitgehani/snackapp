import { type FormEvent, type ReactNode, useContext, useState } from "react";
import { ActionContext } from "../action";
import { FIELD_DISPLAY } from "../fields/FieldRenderer";

export type Node = {
  kind: string;
  children?: Node[];
  [key: string]: unknown;
};

export type Renderers = Record<string, (node: Node, render: (n: Node) => ReactNode) => ReactNode>;

function kids(node: Node, render: (n: Node) => ReactNode): ReactNode {
  return (node.children || []).map((child, i) => (
    <div key={i} className="sa-slot">
      {render(child)}
    </div>
  ));
}

function chip(value: unknown): ReactNode {
  if (value && typeof value === "object") {
    const rec = value as { email?: string; name?: string; id?: string };
    return (
      <span className="badge" data-kind="record-chip">
        {rec.email || rec.name || rec.id || FIELD_DISPLAY.user(value)}
      </span>
    );
  }
  return String(value ?? "");
}

export const registry: Renderers = {
  page: (n, r) => <div data-kind="page">{kids(n, r)}</div>,
  header: (n) => (
    <header>
      <h1>{String(n.title ?? "")}</h1>
      {n.subtitle ? <p>{String(n.subtitle)}</p> : null}
    </header>
  ),
  row: (n, r) => (
    <div data-kind="row">{kids(n, r)}</div>
  ),
  column: (n, r) => (
    <div data-kind="column">{kids(n, r)}</div>
  ),
  card: (n, r) => (
    <section data-kind="card">
      {n.title ? <h3>{String(n.title)}</h3> : null}
      {kids(n, r)}
    </section>
  ),
  tabs: (n, r) => <div data-kind="tabs">{kids(n, r)}</div>,
  tab: (n, r) => <div data-kind="tab" data-label={String(n.label)}>{kids(n, r)}</div>,
  fragment: (n, r) => (
    <div data-fragment={String(n.name)} data-deps={(n.deps as string[] | undefined)?.join(",")}>
      {kids(n, r)}
    </div>
  ),
  text: (n) => <p className={n.muted ? "muted" : undefined}>{String(n.value ?? "")}</p>,
  markdown: (n) => <div data-kind="markdown">{String(n.value ?? "")}</div>,
  stat: (n) => (
    <div data-kind="stat">
      <div>{String(n.label)}</div>
      <strong>{String(n.value)}</strong>
    </div>
  ),
  empty: (n) => <div className="empty">{String(n.message)}</div>,
  badge: (n) => <span className="badge">{String(n.value)}</span>,
  divider: () => <hr />,
  table: (n) => <DataTable node={n} />,
  fields: (n) => <FieldGrid node={n} />,
  kanban: (n) => <Kanban node={n} />,
  timeline: (n) => (
    <ol data-kind="timeline">
      {((n.items as { summary?: string; title?: string }[]) || []).map((item, i) => (
        <li key={i}>{item.summary || item.title || "entry"}</li>
      ))}
    </ol>
  ),
  bar_chart: (n) => <Chart node={n} kind="bar" />,
  form: (n) => <ActionForm node={n} />,
  filter_bar: (n) => <div data-kind="filter-bar">{JSON.stringify(n.items ?? [])}</div>,
  button: (n) => <ActionButton node={n} />,
  record: (n) => (
    <div data-kind="record" data-panel={n.panel ? "1" : "0"}>
      <div>{String(n.collection)} {String(n.id)}</div>
      <div data-kind="record-tabs">{((n.tabs as string[]) || []).join(" · ")}</div>
    </div>
  ),
  chart: (n) => <Chart node={n} kind={String(n.chart || "bar")} />,
  list: (n) => (
    <ul data-kind="list">
      {((n.rows as Record<string, unknown>[]) || []).map((row, i) => (
        <li key={String(row.id ?? i)}>{String(row[String(n.title_field || "name")] ?? "")}</li>
      ))}
    </ul>
  ),
  calendar: (n) => <Calendar node={n} />,
  view_bar: (n) => (
    <div data-kind="view-bar">
      {((n.views as { name: string }[]) || []).map((v) => (
        <button key={v.name} type="button">{v.name}</button>
      ))}
    </div>
  ),
};

const VIRTUAL_BOUND = 60;

function DataTable({ node }: { node: Node }) {
  const { go, run } = useContext(ActionContext);
  const rows = (node.rows as Record<string, unknown>[]) || [];
  const columns = (node.columns as { field: string; label: string }[]) || [];
  const actions = (node.row_actions as { label: string; action?: string; params?: Record<string, unknown> }[]) || [];
  const visible = rows.slice(0, VIRTUAL_BOUND);
  const link = node.row_link ? String(node.row_link) : "";
  return (
    <table data-kind="table" data-virtual-bound={VIRTUAL_BOUND} data-row-count={rows.length}>
      <thead>
        <tr>
          {columns.map((c) => (
            <th key={c.field}>{c.label}</th>
          ))}
          {actions.length ? <th>Actions</th> : null}
        </tr>
      </thead>
      <tbody>
        {visible.map((row, i) => (
          <tr
            key={String(row.id ?? i)}
            onClick={
              link
                ? () => go(link.replace("{id}", String(row.id ?? "")))
                : undefined
            }
            style={link ? { cursor: "pointer" } : undefined}
          >
            {columns.map((c) => (
              <td key={c.field}>{cell(row[c.field], c.field)}</td>
            ))}
            {actions.length ? (
              <td onClick={(event) => event.stopPropagation()}>
                {actions.map((item) => (
                  <button
                    key={item.label}
                    type="button"
                    onClick={() =>
                      run(String(item.action), {
                        ...(item.params || {}),
                        id: row.id,
                      })
                    }
                  >
                    {item.label}
                  </button>
                ))}
              </td>
            ) : null}
          </tr>
        ))}
      </tbody>
    </table>
  );
}

type FormItem = {
  field: string;
  label: string;
  type?: string;
  options?: string[];
};

function ActionForm({ node }: { node: Node }) {
  const { run } = useContext(ActionContext);
  const items = (node.items as FormItem[]) || [];
  const values = (node.values as Record<string, unknown>) || {};
  const extra = (node.params as Record<string, unknown>) || {};
  const [error, setError] = useState("");
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    const form = event.currentTarget;
    const data = new FormData(form);
    const params: Record<string, unknown> = { ...extra, ...values };
    for (const [key, value] of data.entries()) {
      params[key] = value;
    }
    const result = await run(String(node.action), params);
    if (result.ok === false || result.error) {
      setError(result.error || "Could not save");
      return;
    }
    form.reset();
  }
  return (
    <form data-kind="form" className="sa-form" onSubmit={submit}>
      {node.title ? <h3>{String(node.title)}</h3> : null}
      {items.map((item) => (
        <label key={item.field}>
          {item.label}
          {item.type === "select" ? (
            <select name={item.field} defaultValue={String(values[item.field] ?? "")}>
              {(item.options || []).map((option) => (
                <option key={option} value={option}>
                  {option}
                </option>
              ))}
            </select>
          ) : item.type === "long_text" ? (
            <textarea name={item.field} defaultValue={String(values[item.field] ?? "")} rows={3} />
          ) : (
            <input
              name={item.field}
              type={item.type === "date" ? "date" : "text"}
              defaultValue={String(values[item.field] ?? "")}
              required={Boolean((item as { required?: boolean }).required)}
            />
          )}
        </label>
      ))}
      {error ? <p className="muted">{error}</p> : null}
      <button type="submit">{String(node.submit_label || "Save")}</button>
    </form>
  );
}

function ActionButton({ node }: { node: Node }) {
  const { run, go } = useContext(ActionContext);
  const label = String(node.label ?? "");
  return (
    <button
      type="button"
      data-tone={String(node.tone || "default")}
      onClick={() => {
        if (node.confirm && !window.confirm(String(node.confirm))) {
          return;
        }
        if (node.link) {
          go(String(node.link));
          return;
        }
        if (node.action) {
          void run(String(node.action), (node.params as Record<string, unknown>) || {});
        }
      }}
    >
      {label}
    </button>
  );
}

function cell(value: unknown, field?: string): ReactNode {
  if (value && typeof value === "object") return chip(value);
  const text = String(value ?? "");
  if (field === "status" && ["todo", "doing", "done"].includes(text)) {
    return <span className={`badge status-pill status-${text}`}>{text}</span>;
  }
  if (!text) return <span className="muted">—</span>;
  return text;
}

function FieldGrid({ node }: { node: Node }) {
  const record = (node.record as Record<string, unknown>) || {};
  const items = (node.items as { field: string; label: string }[]) || [];
  return (
    <dl data-kind="fields">
      {items.map((item) => (
        <div key={item.field}>
          <dt>{item.label}</dt>
          <dd>{cell(record[item.field])}</dd>
        </div>
      ))}
    </dl>
  );
}

function Kanban({ node }: { node: Node }) {
  const { go } = useContext(ActionContext);
  const groups = (node.groups as string[]) || [];
  const rows = (node.rows as Record<string, unknown>[]) || [];
  const groupBy = String(node.group_by || "stage");
  const titleField = String(node.title_field || "name");
  const subtitleField = node.subtitle_field ? String(node.subtitle_field) : "";
  const link = node.card_link ? String(node.card_link) : "";
  return (
    <div data-kind="kanban">
      {groups.map((g) => {
        const cards = rows.filter((row) => String(row[groupBy] ?? "") === g);
        return (
          <div key={g} data-group={g}>
            <h4>
              {g} · {cards.length}
            </h4>
            {cards.map((row, i) => (
              <article
                key={String(row.id ?? i)}
                draggable
                onClick={link ? () => go(link.replace("{id}", String(row.id ?? ""))) : undefined}
              >
                <strong>{String(row[titleField] ?? "")}</strong>
                {subtitleField ? <small>{String(row[subtitleField] ?? "no date")}</small> : null}
              </article>
            ))}
          </div>
        );
      })}
    </div>
  );
}

function Calendar({ node }: { node: Node }) {
  const { go } = useContext(ActionContext);
  const rows = (node.rows as Record<string, unknown>[]) || [];
  const field = String(node.date_field || "due");
  const now = new Date();
  const year = now.getFullYear();
  const month = now.getMonth();
  const daysInMonth = new Date(year, month + 1, 0).getDate();
  const pad = new Date(year, month, 1).getDay();
  const byDay = new Map<number, Record<string, unknown>[]>();
  for (const row of rows) {
    const raw = String(row[field] ?? "");
    const day = Number(raw.slice(8, 10));
    if (!day || raw.slice(0, 7) !== `${year}-${String(month + 1).padStart(2, "0")}`) continue;
    byDay.set(day, [...(byDay.get(day) || []), row]);
  }
  const heads = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
  const cells: ReactNode[] = [];
  for (let i = 0; i < pad; i++) cells.push(<div key={`p${i}`} className="cal-cell" />);
  for (let d = 1; d <= daysInMonth; d++) {
    const items = byDay.get(d) || [];
    cells.push(
      <div key={d} className="cal-cell">
        <div className="cal-day">{d}</div>
        {items.map((row) => (
          <span
            key={String(row.id)}
            className="cal-item"
            onClick={
              node.card_link
                ? () => go(String(node.card_link).replace("{id}", String(row.id ?? "")))
                : undefined
            }
          >
            {String(row.title || row.name || "")}
          </span>
        ))}
      </div>,
    );
  }
  return (
    <div data-kind="calendar" data-field={field}>
      {heads.map((h) => (
        <div key={h} className="cal-head">
          {h}
        </div>
      ))}
      {cells}
    </div>
  );
}

function Chart({ node, kind }: { node: Node; kind: string }) {
  const data = (node.data as object[]) || [];
  return (
    <div data-kind={`chart-${kind}`}>
      <table>
        <tbody>
          {data.map((row, i) => (
            <tr key={i}>
              <td>{JSON.stringify(row)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function renderNode(node: Node): ReactNode {
  const fn = registry[node.kind];
  if (!fn) {
    return <div data-kind="unknown">Unknown node kind: {node.kind}</div>;
  }
  return fn(node, renderNode);
}
