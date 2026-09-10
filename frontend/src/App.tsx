import { FormEvent, useEffect, useMemo, useState } from "react";
import { renderNode, type Node } from "./render/registry";

type Meta = {
  title: string;
  nav: { path: string; title: string }[];
  user: { id: string; email: string } | null;
};

const script = document.querySelector("script[data-base]") as HTMLScriptElement | null;
const base = script?.dataset.base || "";

function LoginForm({ onDone }: { onDone: () => void }) {
  const [email, setEmail] = useState("admin@example.com");
  const [password, setPassword] = useState("");
  const [account, setAccount] = useState("");
  const [error, setError] = useState("");

  async function submit(event: FormEvent) {
    event.preventDefault();
    setError("");
    const response = await fetch(`${base}/_sa/login`, {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password, account }),
    });
    if (!response.ok) {
      setError("Could not sign in");
      return;
    }
    onDone();
  }

  return (
    <form data-kind="login" onSubmit={submit} style={{ maxWidth: 360 }}>
      <h1>Log in</h1>
      <label>
        Email
        <input name="email" value={email} onChange={(e) => setEmail(e.target.value)} />
      </label>
      <label>
        Password
        <input
          name="password"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />
      </label>
      <label>
        Account
        <input name="account" value={account} onChange={(e) => setAccount(e.target.value)} />
      </label>
      {error ? <p className="muted">{error}</p> : null}
      <button type="submit">Sign in</button>
    </form>
  );
}

export function App() {
  const [meta, setMeta] = useState<Meta | null>(null);
  const [tree, setTree] = useState<Node | null>(null);
  const [auth, setAuth] = useState<"ok" | "login" | "loading">("loading");
  const [path, setPath] = useState(window.location.pathname.replace(base, "") || "/");
  const [command, setCommand] = useState(false);
  const [query, setQuery] = useState("");
  const [theme, setTheme] = useState<"light" | "dark">(
    window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light",
  );

  const filteredNav = useMemo(
    () => (meta?.nav || []).filter((item) => item.title.toLowerCase().includes(query.toLowerCase())),
    [meta, query],
  );

  function loadMeta() {
    fetch(`${base}/_sa/meta`, { credentials: "include" })
      .then((r) => r.json())
      .then(setMeta)
      .catch(() => setMeta({ title: "SnackApp", nav: [], user: null }));
  }

  function loadView(next = path) {
    const qs = window.location.search;
    fetch(`${base}/_sa/view?path=${encodeURIComponent(next)}${qs ? "&" + qs.slice(1) : ""}`, {
      credentials: "include",
    })
      .then(async (r) => {
        if (r.status === 401) {
          setAuth("login");
          setTree(null);
          return;
        }
        const data = await r.json();
        setAuth("ok");
        setTree(data.tree);
      })
      .catch(() => setTree({ kind: "page", children: [{ kind: "text", value: "offline" }] }));
  }

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
  }, [theme]);

  useEffect(() => {
    loadMeta();
  }, []);

  useEffect(() => {
    loadView(path);
  }, [path]);

  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        setCommand((open) => !open);
      }
      if (event.key === "Escape") setCommand(false);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

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
      <main style={{ flex: 1, padding: 24 }}>
        {auth === "login" ? (
          <LoginForm
            onDone={() => {
              loadMeta();
              loadView(path);
            }}
          />
        ) : tree ? (
          renderNode(tree)
        ) : (
          <p>Loading…</p>
        )}
      </main>
      {command ? (
        <div data-kind="command" role="dialog" style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,.4)" }}>
          <div style={{ margin: "12vh auto", width: 420, background: "var(--panel)", padding: 16 }}>
            <input
              autoFocus
              placeholder="Jump to…"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            />
            <ul>
              {filteredNav.map((item) => (
                <li key={item.path}>
                  <button
                    type="button"
                    onClick={() => {
                      history.pushState({}, "", base + item.path);
                      setPath(item.path);
                      setCommand(false);
                    }}
                  >
                    {item.title}
                  </button>
                </li>
              ))}
            </ul>
          </div>
        </div>
      ) : null}
    </div>
  );
}
