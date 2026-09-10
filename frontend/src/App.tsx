import { useEffect, useState } from "react";
import { renderNode, type Node } from "./render/registry";

type Meta = {
  title: string;
  nav: { path: string; title: string }[];
  user: { id: string; email: string } | null;
};

const script = document.querySelector("script[data-base]") as HTMLScriptElement | null;
const base = script?.dataset.base || "";

export function App() {
  const [meta, setMeta] = useState<Meta | null>(null);
  const [tree, setTree] = useState<Node | null>(null);
  const [path, setPath] = useState(window.location.pathname.replace(base, "") || "/");
  const [theme, setTheme] = useState<"light" | "dark">(
    window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light",
  );

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
  }, [theme]);

  useEffect(() => {
    fetch(`${base}/_sa/meta`, { credentials: "include" })
      .then((r) => r.json())
      .then(setMeta)
      .catch(() => setMeta({ title: "SnackApp", nav: [], user: null }));
  }, []);

  useEffect(() => {
    const qs = window.location.search;
    fetch(`${base}/_sa/view?path=${encodeURIComponent(path)}${qs ? "&" + qs.slice(1) : ""}`, {
      credentials: "include",
    })
      .then(async (r) => {
        if (r.status === 401) {
          setTree({ kind: "page", children: [{ kind: "header", title: "Log in" }] });
          return;
        }
        const data = await r.json();
        setTree(data.tree);
      })
      .catch(() => setTree({ kind: "page", children: [{ kind: "text", value: "offline" }] }));
  }, [path]);

  return (
    <div style={{ display: "flex", minHeight: "100vh" }}>
      <aside style={{ width: 220, borderRight: "1px solid var(--line)", padding: 16 }}>
        <strong>{meta?.title ?? "SnackApp"}</strong>
        <nav>
          {(meta?.nav || []).map((item) => (
            <a
              key={item.path}
              href={base + item.path}
              onClick={(e) => {
                e.preventDefault();
                history.pushState({}, "", base + item.path);
                setPath(item.path);
              }}
              style={{ display: "block", marginTop: 8 }}
            >
              {item.title}
            </a>
          ))}
        </nav>
        <button type="button" onClick={() => setTheme(theme === "dark" ? "light" : "dark")}>
          Theme
        </button>
      </aside>
      <main style={{ flex: 1, padding: 24 }}>{tree ? renderNode(tree) : <p>Loading…</p>}</main>
    </div>
  );
}
