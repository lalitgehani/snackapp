// SnackApp renderer. Vanilla, no build step.
// Renders the tree from /_sa/view and posts interactions to /_sa/action/*.
const BASE = (document.currentScript && document.currentScript.dataset.base) || '';
const P = p => BASE + p;                       // API path
const R = () => location.pathname.slice(BASE.length) || '/';  // route within the app
const $ = (t, c, x) => { const e = document.createElement(t); if (c) e.className = c;
  if (x != null) e.textContent = x; return e; };
const api = async (u, o) => (await fetch(u, { credentials: 'same-origin', ...o })).json();
const post = (u, b) => api(u, { method: 'POST', headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(b || {}) });

let META = null, TREE = null;

const money = v => v == null || v === '' ? '' :
  '$' + Number(v).toLocaleString(undefined, { maximumFractionDigits: 0 });

// dotted paths: "company.name" -> row.company.name (expand replaces in place)
function dig(row, path) {
  return String(path).split('.').reduce((o, k) => (o == null ? undefined : o[k]), row);
}
function fmt(row, col) {
  const v = dig(row, col.field);
  if (v == null || v === '') return '';
  if (col.type === 'money') return money(v);
  if (col.type === 'number') return Number(v).toLocaleString();
  if (v && typeof v === 'object') return v.name || v.title || v.id || '';
  return String(v);
}
function subst(tpl, row) {
  return tpl.replace(/\{(\w+)\}/g, (_, k) => {
    const v = row[k]; return (v && typeof v === 'object') ? v.id : (v ?? '');
  });
}
function toast(msg, err) {
  const t = $('div', 'toast' + (err ? ' err' : ''), msg);
  document.body.appendChild(t); setTimeout(() => t.remove(), 3200);
}

// ---- navigation: the URL is the state -------------------------------------
function go(path) { history.pushState({}, '', BASE + path); render(); }
addEventListener('popstate', () => render());

function setQuery(k, v) {
  const u = new URL(location.href);
  if (v === '' || v == null) u.searchParams.delete(k); else u.searchParams.set(k, v);
  go(u.pathname.slice(BASE.length) + (u.search || ''));
}

// ---- actions ---------------------------------------------------------------
async function runAction(name, params, confirmMsg) {
  if (confirmMsg && !window.confirm(confirmMsg)) return;
  const r = await post(P('/_sa/action/' + name), params);
  if (!r.ok) { toast(typeof r.error === 'string' ? r.error : JSON.stringify(r.error), true); return; }
  if (r.toast) toast(r.toast);
  if (r.redirect) return go(r.redirect);
  // Refresh anything the author named, PLUS every fragment whose recorded data
  // dependencies intersect the collections this action actually wrote.
  const names = new Set(r.refresh || []);
  if (r.wrote && r.wrote.length && TREE) {
    (function walk(n) {
      if (n.kind === 'fragment' && (n.deps || []).some(d => r.wrote.includes(d)))
        names.add(n.name);
      (n.children || []).forEach(walk);
    })(TREE);
  }
  if (names.size) return refreshFragments([...names]);
  render();
}

// Re-fetch the view but swap ONLY the named fragments -- the rest of the DOM,
// including scroll position and any open widget, is left alone.
async function refreshFragments(names) {
  const d = await api(P('/_sa/view?path=') + encodeURIComponent(R()) +
                      (location.search ? '&' + location.search.slice(1) : ''));
  if (d.error) return render();
  const fresh = {};
  (function walk(n) {
    if (n.kind === 'fragment' && names.includes(n.name)) fresh[n.name] = n;
    (n.children || []).forEach(walk);
  })(d.tree);
  for (const name of names) {
    const host = document.querySelector(`[data-fragment="${name}"]`);
    if (host && fresh[name]) { host.replaceChildren(); (fresh[name].children || [])
      .forEach(c => host.appendChild(node(c))); }
  }
}

// ---- node rendering --------------------------------------------------------
function button(b) {
  const el = $('button', b.tone === 'primary' ? 'primary' : b.tone === 'danger' ? 'danger' : '', b.label);
  el.onclick = e => {
    e.stopPropagation();
    if (b.link) return go(b.link);
    if (b.opens) { const m = document.querySelector(`[data-modal="${b.opens}"]`);
      if (m) m.style.display = 'flex'; return; }
    if (b.action) runAction(b.action, b.params || {}, b.confirm);
  };
  return el;
}

function kids(n, host) { (n.children || []).forEach(c => host.appendChild(node(c))); return host; }

function node(n) {
  switch (n.kind) {
    case 'page': return kids(n, $('div'));

    case 'header': {
      const w = $('div', 'hdr'), l = $('div');
      l.appendChild($('h1', null, n.title));
      if (n.subtitle) l.appendChild($('div', 'sub', n.subtitle));
      const r = $('div'); r.style.display = 'flex'; r.style.gap = '8px';
      (n.actions || []).forEach(b => r.appendChild(button(b)));
      w.append(l, r); return w;
    }

    case 'row': return kids(n, $('div', 'row'));
    case 'column': {
      const c = $('div', 'col');
      if (n.width) { c.style.flex = `${n.width} 1 0`; }
      return kids(n, c);
    }
    case 'card': {
      const c = $('div', 'card');
      if (n.title) c.appendChild($('h3', null, n.title));
      return kids(n, c);
    }
    case 'fragment': { const f = $('div'); f.dataset.fragment = n.name; return kids(n, f); }
    case 'divider': { const d = $('div'); d.style.borderTop = '1px solid var(--line)';
      d.style.margin = '14px 0'; return d; }
    case 'text': return $('div', n.muted ? 'muted' : '', n.value);
    case 'markdown': { const d = $('div'); d.innerHTML = n.value
      .replace(/&/g, '&amp;').replace(/</g, '&lt;')
      .replace(/\*\*(.+?)\*\*/g, '<b>$1</b>').replace(/\n/g, '<br>'); return d; }
    case 'badge': { const b = $('span', 'badge ' + (n.value || ''), n.value); return b; }
    case 'stat': {
      const c = $('div', 'card stat' + (n.tone === 'good' ? ' good' : ''));
      c.append($('div', 'l', n.label), $('div', 'v', String(n.value)));
      if (n.delta) c.appendChild($('div', 'muted', n.delta));
      return c;
    }
    case 'empty': {
      const e = $('div', 'empty'); e.appendChild($('div', null, n.message));
      if (n.action) { const w = $('div'); w.style.marginTop = '10px';
        w.appendChild(button(n.action)); e.appendChild(w); }
      return e;
    }

    case 'table': return tableNode(n);
    case 'fields': return fieldsNode(n);
    case 'kanban': return kanbanNode(n);
    case 'timeline': {
      const ul = $('ul', 'tl');
      (n.items || []).forEach(it => {
        const li = $('li');
        li.appendChild($('div', null, dig(it, n.title_field)));
        const meta = [n.body_field && dig(it, n.body_field), dig(it, n.time_field)]
          .filter(Boolean).join(' · ');
        li.appendChild($('div', 'm', meta));
        ul.appendChild(li);
      });
      return ul;
    }
    case 'bar_chart': {
      const w = $('div'), bars = $('div', 'bars');
      bars.style.height = (n.height || 180) + 'px';
      const max = Math.max(...n.data.map(d => Number(dig(d, n.value_field)) || 0), 1);
      n.data.forEach(d => {
        const col = $('div'); col.style.flex = '1';
        const b = $('div', 'b');
        b.style.height = ((Number(dig(d, n.value_field)) || 0) / max * 100) + '%';
        col.append(b, $('div', 'lab', String(dig(d, n.label_field))));
        col.style.display = 'flex'; col.style.flexDirection = 'column';
        col.style.justifyContent = 'flex-end'; bars.appendChild(col);
      });
      w.appendChild(bars); return w;
    }

    case 'tabs': {
      const w = $('div'), bar = $('div', 'tabs'), body = $('div');
      const tabs = (n.children || []).filter(c => c.kind === 'tab');
      tabs.forEach((t, i) => {
        const b = $('button', i === 0 ? 'on' : '', t.label);
        b.onclick = () => {
          [...bar.children].forEach(x => x.classList.remove('on'));
          b.classList.add('on'); body.replaceChildren(kids(t, $('div')));
        };
        bar.appendChild(b);
      });
      if (tabs[0]) body.appendChild(kids(tabs[0], $('div')));
      w.append(bar, body); return w;
    }

    case 'form': return formNode(n);
    case 'filter_bar': {
      const w = $('div', 'tbar'); w.style.marginBottom = '14px';
      w.style.border = '1px solid var(--line)'; w.style.borderRadius = 'var(--radius)';
      (n.items || []).forEach(it => {
        const box = $('div'); box.style.maxWidth = '220px';
        const sel = $('select');
        (it.options || []).forEach(o => {
          const op = $('option', null, o === '' ? `All ${it.field}` : o);
          op.value = o; sel.appendChild(op);
        });
        sel.value = (n.values || {})[it.field] || '';
        sel.onchange = () => setQuery(it.field, sel.value);
        box.appendChild(sel); w.appendChild(box);
      });
      return w;
    }
    default: { const d = $('div', 'err', 'unknown node: ' + n.kind); return d; }
  }
}

function tableNode(n) {
  const wrap = $('div', 'tbl');
  let rows = n.rows.slice(), sortKey = null, asc = true, page = 0, term = '';
  const bar = $('div', 'tbar'), tbl = $('table'), thead = $('thead'), tbody = $('tbody');
  const foot = $('div', 'tbar');

  if (n.search && n.search.length) {
    const inp = $('input'); inp.placeholder = 'Search…'; inp.style.maxWidth = '260px';
    inp.oninput = () => { term = inp.value.toLowerCase(); page = 0; draw(); };
    bar.appendChild(inp); wrap.appendChild(bar);
  }
  const htr = $('tr');
  n.columns.forEach(c => {
    const th = $('th', null, c.label);
    th.onclick = () => { asc = sortKey === c.field ? !asc : true; sortKey = c.field; draw(); };
    htr.appendChild(th);
  });
  if (n.row_actions && n.row_actions.length) htr.appendChild($('th', null, ''));
  thead.appendChild(htr); tbl.append(thead, tbody); wrap.append(tbl, foot);

  function view() {
    let r = rows;
    if (term) r = r.filter(x => n.search.some(f =>
      String(dig(x, f) ?? '').toLowerCase().includes(term)));
    if (sortKey) r = r.slice().sort((a, b) => {
      const A = dig(a, sortKey), B = dig(b, sortKey);
      if (A == null) return 1; if (B == null) return -1;
      return (A > B ? 1 : A < B ? -1 : 0) * (asc ? 1 : -1);
    });
    return r;
  }
  function draw() {
    const all = view(), size = n.page_size || 25;
    const slice = all.slice(page * size, (page + 1) * size);
    tbody.replaceChildren();
    if (!all.length) {
      const tr = $('tr'), td = $('td', 'muted', n.empty_message);
      td.colSpan = n.columns.length + 1; tr.appendChild(td); tbody.appendChild(tr);
    }
    slice.forEach(row => {
      const tr = $('tr');
      n.columns.forEach(c => {
        const td = $('td');
        if (c.type === 'badge') { const v = fmt(row, c); if (v) td.appendChild($('span', 'badge ' + v, v)); }
        else if (c.type === 'link' && dig(row, c.field)) {
          const a = $('a', null, fmt(row, c)); a.href = dig(row, c.field);
          a.target = '_blank'; a.onclick = e => e.stopPropagation(); td.appendChild(a);
        } else td.textContent = fmt(row, c);
        tr.appendChild(td);
      });
      if (n.row_actions && n.row_actions.length) {
        const td = $('td');
        n.row_actions.forEach(b => td.appendChild(button({ ...b, params: { ...(b.params || {}), id: row.id } })));
        tr.appendChild(td);
      }
      if (n.row_link) { tr.dataset.link = '1'; tr.onclick = () => go(subst(n.row_link, row)); }
      tbody.appendChild(tr);
    });
    foot.replaceChildren();
    const pages = Math.ceil(all.length / size);
    if (pages > 1) {
      const prev = $('button', null, '‹'), next = $('button', null, '›');
      prev.onclick = () => { if (page > 0) { page--; draw(); } };
      next.onclick = () => { if (page < pages - 1) { page++; draw(); } };
      foot.append(prev, $('span', 'muted', ` ${page + 1} / ${pages} · ${all.length} rows `), next);
    } else foot.appendChild($('span', 'muted', `${all.length} rows`));
  }
  draw(); return wrap;
}

function fieldsNode(n) {
  const wrap = $('div'), g = $('div', 'grid'), inputs = {};
  const rec = n.record || {};
  n.items.forEach(it => {
    g.appendChild($('div', 'k', it.label));
    const raw = dig(rec, it.field);
    if (n.editable) {
      const i = $('input'); i.value = raw == null ? '' : (typeof raw === 'object' ? (raw.name || raw.id) : raw);
      inputs[it.field] = { el: i, was: i.value }; g.appendChild(i);
    } else if (it.type === 'badge' && raw) g.appendChild($('span', 'badge ' + raw, String(raw)));
    else if (it.type === 'money') g.appendChild($('div', null, money(raw)));
    else g.appendChild($('div', null, raw == null ? '' :
      (typeof raw === 'object' ? (raw.name || raw.id) : String(raw))));
  });
  wrap.appendChild(g);
  if (n.editable && n.action) {
    const bar = $('div', 'acts'), save = $('button', 'primary', 'Save');
    save.onclick = () => {
      const changed = { id: rec.id };
      let any = false;
      for (const [f, o] of Object.entries(inputs))
        if (o.el.value !== o.was) { changed[f] = o.el.value; any = true; }
      if (!any) return toast('No changes');
      runAction(n.action, changed);
    };
    bar.appendChild(save); wrap.appendChild(bar);
  }
  return wrap;
}

function kanbanNode(n) {
  const board = $('div', 'kan');
  n.groups.forEach(gname => {
    const col = $('div', 'kcol');
    const items = n.rows.filter(r => String(dig(r, n.group_by)) === gname);
    col.appendChild($('h4', null, `${gname} · ${items.length}`));
    items.forEach(r => {
      const c = $('div', 'kc'); c.draggable = true;
      c.ondragstart = e => e.dataTransfer.setData('text/plain', r.id);
      c.appendChild($('div', 't', String(dig(r, n.title_field) ?? '')));
      if (n.subtitle_field) {
        const s = dig(r, n.subtitle_field);
        if (s) c.appendChild($('div', 's', String(s)));
      }
      if (n.value_field) c.appendChild($('div', 'v', money(dig(r, n.value_field))));
      if (n.card_link) c.onclick = () => go(subst(n.card_link, r));
      col.appendChild(c);
    });
    col.ondragover = e => { e.preventDefault(); col.classList.add('over'); };
    col.ondragleave = () => col.classList.remove('over');
    col.ondrop = e => {
      e.preventDefault(); col.classList.remove('over');
      const id = e.dataTransfer.getData('text/plain');
      if (id && n.on_move) runAction(n.on_move, { id, stage: gname });
    };
    board.appendChild(col);
  });
  return board;
}

function formNode(n) {
  const inner = $('div', n.modal ? 'dlg' : '');
  if (n.title) inner.appendChild($('h3', null, n.title));
  const vals = {};
  n.items.forEach(it => {
    const f = $('div', 'fld');
    f.appendChild($('label', null, it.label + (it.required ? ' *' : '')));
    let el;
    if (it.type === 'select') {
      el = $('select');
      (it.options || []).forEach(o => {
        const val = (o && typeof o === 'object') ? o.value : o;
        const lab = (o && typeof o === 'object') ? o.label : o;
        const op = $('option', null, lab); op.value = val; el.appendChild(op);
      });
    } else if (it.type === 'textarea') { el = $('textarea'); el.rows = 3; }
    else { el = $('input'); el.type = ['number', 'date', 'email', 'url'].includes(it.type) ? it.type : 'text'; }
    const pre = (n.values || {})[it.field];
    if (pre != null) el.value = pre;
    vals[it.field] = el; f.appendChild(el); inner.appendChild(f);
  });
  const acts = $('div', 'acts');
  if (n.modal) {
    const cancel = $('button', null, 'Cancel');
    cancel.onclick = () => { host.style.display = 'none'; };
    acts.appendChild(cancel);
  }
  const submit = $('button', 'primary', n.submit_label || 'Save');
  submit.onclick = async () => {
    const body = { ...(n.params || {}) };
    for (const [f, el] of Object.entries(vals)) if (el.value !== '') body[f] = el.value;
    const missing = n.items.filter(i => i.required && !body[i.field]).map(i => i.label);
    if (missing.length) return toast('Required: ' + missing.join(', '), true);
    if (n.modal) host.style.display = 'none';
    Object.values(vals).forEach(el => { el.value = ''; });
    await runAction(n.action, body);
  };
  acts.appendChild(submit); inner.appendChild(acts);

  let host;
  if (n.modal) {
    host = $('div', 'ovl'); host.dataset.modal = n.name; host.style.display = 'none';
    host.onclick = e => { if (e.target === host) host.style.display = 'none'; };
    host.appendChild(inner);
  } else { host = $('div', 'card'); host.appendChild(inner); }
  return host;
}

// ---- shell -----------------------------------------------------------------
function loginScreen() {
  const root = document.getElementById('root');
  root.replaceChildren();
  const box = $('div', 'card login');
  box.appendChild($('h3', null, (META && META.title) || 'Sign in'));
  const mk = (label, type, val) => {
    const f = $('div', 'fld'); f.appendChild($('label', null, label));
    const i = $('input'); i.type = type; if (val) i.value = val;
    f.appendChild(i); box.appendChild(f); return i;
  };
  const e = mk('Email', 'text'), p = mk('Password', 'password'), a = mk('Account', 'text');
  const b = $('button', 'primary', 'Sign in'); b.style.width = '100%';
  b.onclick = async () => {
    const r = await post(P('/_sa/login'), { email: e.value, password: p.value, account: a.value });
    if (r.ok) location.reload(); else toast('Login failed', true);
  };
  p.onkeydown = ev => { if (ev.key === 'Enter') b.click(); };
  box.appendChild(b); root.appendChild(box);
}

function shell() {
  const root = document.getElementById('root');
  root.replaceChildren();
  const side = $('div', 'side');
  side.appendChild($('div', 'brand', META.title));
  const nav = $('div', 'nav');
  META.nav.forEach(it => {
    const a = $('a', R() === it.path ? 'on' : '', it.title);
    a.href = BASE + it.path;
    a.onclick = e => { e.preventDefault(); go(it.path); };
    nav.appendChild(a);
  });
  side.appendChild(nav);
  const main = $('div', 'main'), top = $('div', 'top');
  top.appendChild($('span', null, META.user.email));
  const out = $('button', null, 'Logout');
  out.onclick = async () => { await post(P('/_sa/logout')); location.reload(); };
  top.appendChild(out);
  const body = $('div', 'body'); body.id = 'view';
  main.append(top, body); root.append(side, main);
  return body;
}

async function render() {
  if (!META) META = await api(P('/_sa/meta'));
  if (!META.user) return loginScreen();
  const body = shell();
  const d = await api(P('/_sa/view?path=') + encodeURIComponent(R()) +
                      (location.search ? '&' + location.search.slice(1) : ''));
  if (d.error) {
    body.appendChild($('div', 'err',
      `${d.error}: ${JSON.stringify(d.detail, null, 2)}\n\n${d.trace || ''}`));
    return;
  }
  document.title = d.title + ' · ' + META.title;
  TREE = d.tree;
  body.appendChild(node(d.tree));
}

render();
