import type { ReactNode } from "react";

export type Node = {
  kind: string;
  children?: Node[];
  [key: string]: unknown;
};

export type Renderers = Record<string, (node: Node, render: (n: Node) => ReactNode) => ReactNode>;

function kids(node: Node, render: (n: Node) => ReactNode): ReactNode {
  return (node.children || []).map((child, i) => <span key={i}>{render(child)}</span>);
}

export const registry: Renderers = {
  page: (n, r) => <div data-kind="page">{kids(n, r)}</div>,
  header: (n) => (
    <header>
      <h1>{String(n.title ?? "")}</h1>
      {n.subtitle ? <p>{String(n.subtitle)}</p> : null}
    </header>
  ),
  row: (n, r) => <div style={{ display: "flex", gap: 12 }}>{kids(n, r)}</div>,
  column: (n, r) => <div style={{ flex: 1 }}>{kids(n, r)}</div>,
  card: (n, r) => (
    <section style={{ background: "var(--panel)", border: "1px solid var(--line)", borderRadius: 10, padding: 16 }}>
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
  fields: (n) => <pre>{JSON.stringify(n.record)}</pre>,
  kanban: (n) => <Kanban node={n} />,
  timeline: (n) => <ol data-kind="timeline">{((n.items as object[]) || []).length} entries</ol>,
  bar_chart: (n) => <div data-kind="chart-bar">{JSON.stringify(n.data)}</div>,
  form: (n) => <form data-kind="form">{String(n.title ?? n.name)}</form>,
  filter_bar: (n) => <div data-kind="filter-bar" />,
  button: (n) => <button type="button">{String(n.label)}</button>,
  record: (n) => <div data-kind="record" data-panel={n.panel ? "1" : "0"}>{String(n.id)}</div>,
  chart: (n) => <div data-kind={`chart-${n.chart}`}>{JSON.stringify(n.data)}</div>,
  list: (n) => <ul data-kind="list">{((n.rows as object[]) || []).length}</ul>,
  calendar: (n) => <div data-kind="calendar" data-field={String(n.date_field)} />,
  view_bar: (n) => <div data-kind="view-bar" />,
};

function DataTable({ node }: { node: Node }) {
  const rows = (node.rows as Record<string, unknown>[]) || [];
  const columns = (node.columns as { field: string; label: string }[]) || [];
  const visible = rows.slice(0, 60);
  return (
    <table data-kind="table">
      <thead>
        <tr>
          {columns.map((c) => (
            <th key={c.field}>{c.label}</th>
          ))}
        </tr>
      </thead>
      <tbody>
        {visible.map((row, i) => (
          <tr key={String(row.id ?? i)}>
            {columns.map((c) => (
              <td key={c.field}>{String(row[c.field] ?? "")}</td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function Kanban({ node }: { node: Node }) {
  const groups = (node.groups as string[]) || [];
  return (
    <div data-kind="kanban" style={{ display: "flex", gap: 12 }}>
      {groups.map((g) => (
        <div key={g} data-group={g}>
          <h4>{g}</h4>
        </div>
      ))}
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
