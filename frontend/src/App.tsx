import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";
import { ActionContext, type ActionResult } from "./action";
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
    <div className="login-screen">
      <form data-kind="login" className="login-card" onSubmit={submit}>
        <div className="login-kicker">SnackApp</div>
        <h1>Open the ledger.</h1>
        <p className="muted">Sign in with the credentials printed on first boot.</p>
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
          <input
            name="account"
            placeholder="AA0001"
            value={account}
            onChange={(e) => setAccount(e.target.value)}
          />
        </label>
        {error ? <p className="muted">{error}</p> : null}
        <button type="submit">Enter</button>
      </form>
    </div>
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
  const [toast, setToast] = useState("");

  const filteredNav = useMemo(
    () => (meta?.nav || []).filter((item) => item.title.toLowerCase().includes(query.toLowerCase())),
    [meta, query],
  );

  const go = useCallback((next: string) => {
    history.pushState({}, "", base + next);
    setPath(next);
  }, []);

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

  const runAction = useCallback(
    async (name: string, params: Record<string, unknown> = {}): Promise<ActionResult> => {
      const response = await fetch(`${base}/_sa/action/${encodeURIComponent(name)}`, {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(params),
      });
      const data = (await response.json().catch(() => ({}))) as ActionResult;
      if (!response.ok) {
        return { ok: false, error: data.error || "Could not run action" };
      }
      if (data.toast) {
        setToast(data.toast);
        window.setTimeout(() => setToast(""), 2400);
      }
      if (data.redirect) {
        go(data.redirect);
      } else {
        loadView(path);
      }
      return data;
    },
    [go, path],
  );

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
    const onPop = () => setPath(window.location.pathname.replace(base, "") || "/");
    window.addEventListener("popstate", onPop);
    return () => window.removeEventListener("popstate", onPop);
  }, []);

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

  const actionApi = useMemo(() => ({ run: runAction, go }), [runAction, go]);

  if (auth === "login") {
    return (
      <LoginForm
        onDone={() => {
          loadMeta();
          loadView(path);
        }}
      />
    );
  }

  return (
    <ActionContext.Provider value={actionApi}>
      <div className="shell">
        <aside className="rail">
          <div className="brand">
            <span className="mark" aria-hidden="true" />
            <span className="wordmark">{meta?.title ?? "SnackApp"}</span>
          </div>
          <nav>
            {(meta?.nav || []).map((item) => (
              <a
                key={item.path}
                href={base + item.path}
                className={path === item.path ? "active" : undefined}
                onClick={(e) => {
                  e.preventDefault();
                  go(item.path);
                }}
              >
                {item.title}
              </a>
            ))}
          </nav>
          <div className="rail-foot">
            <span>{meta?.user?.email}</span>
            <button type="button" onClick={() => setTheme(theme === "dark" ? "light" : "dark")}>
              {theme === "dark" ? "Day paper" : "Night ink"}
            </button>
            <button
              type="button"
              onClick={async () => {
                await fetch(`${base}/_sa/logout`, { method: "POST", credentials: "include" });
                setAuth("login");
                setTree(null);
              }}
            >
              Sign out
            </button>
            <span className="muted">⌘K to jump</span>
          </div>
        </aside>
        <main className="stage">
          {toast ? (
            <div className="toast" role="status">
              {toast}
            </div>
          ) : null}
          {tree ? renderNode(tree) : <p className="muted">Setting the desk…</p>}
        </main>
        {command ? (
          <div className="command" data-kind="command" role="dialog">
            <div className="command-panel">
              <input
                autoFocus
                placeholder="Jump to a page…"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
              />
              <ul>
                {filteredNav.map((item) => (
                  <li key={item.path}>
                    <button
                      type="button"
                      onClick={() => {
                        go(item.path);
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
    </ActionContext.Provider>
  );
}
