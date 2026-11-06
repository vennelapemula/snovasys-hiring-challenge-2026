const $ = (id) => document.getElementById(id);
const JSONH = { "Content-Type": "application/json" };
let me = null;

function el(tag, text) {
  const e = document.createElement(tag);
  if (text !== undefined) e.textContent = text;
  return e;
}
function msg(t) { $("msg").textContent = t || ""; }

async function api(path, opts) {
  const r = await fetch(path, Object.assign({ credentials: "same-origin" }, opts || {}));
  let data = null;
  try { data = await r.json(); } catch (e) { data = null; }
  return { ok: r.ok, status: r.status, data: data };
}

function addBtn(parent, label, fn) {
  const b = el("button", label);
  b.onclick = fn;
  parent.appendChild(b);
}

function table(box, cols, rows) {
  box.replaceChildren();
  const t = el("table");
  const h = el("tr");
  cols.forEach((c) => h.appendChild(el("th", c)));
  t.appendChild(h);
  rows.forEach((r) => {
    const tr = el("tr");
    cols.forEach((c) => tr.appendChild(el("td", r[c] == null ? "" : String(r[c]))));
    t.appendChild(tr);
  });
  box.appendChild(t);
}

async function start() {
  const ub = $("uploadBox");
if (ub) ub.hidden = me.role === "viewer";
  const r = await api("/me");
  if (!r.ok) {
    $("loginBox").hidden = false;
    $("appBox").hidden = true;
    return;
    msg("");
  }
  me = r.data;
  $("loginBox").hidden = true;
  $("appBox").hidden = false;
  $("who").textContent = me.username + " (" + me.role + ")";
  $("adminBox").hidden = me.role !== "admin";
  $("uploadBox").hidden = me.role === "viewer";
  loadDocs();
}

$("loginBtn").onclick = async () => {
  const r = await api("/login", {
    method: "POST", headers: JSONH,
    body: JSON.stringify({ username: $("u").value, password: $("p").value }),
  });
  if (!r.ok) { msg((r.data && r.data.error) || "login failed"); return; }
  $("p").value = "";
  msg("");
  start();
};

$("logoutBtn").onclick = async () => { await api("/logout", { method: "POST" }); me = null; start(); };

async function loadDocs() {
  const p = new URLSearchParams();
  if ($("q").value) p.set("q", $("q").value);
  if ($("cat").value) p.set("category", $("cat").value);
  if ($("own").value) p.set("owner", $("own").value);
  if ($("since").value) p.set("since", $("since").value);
  const r = await api("/documents?" + p.toString());
  if (!r.ok) { msg("could not load documents"); return; }

  const box = $("docs");
  box.replaceChildren();
  const t = el("table");
  const h = el("tr");
  ["id", "name", "category", "owner", "created", "actions"].forEach((c) => h.appendChild(el("th", c)));
  t.appendChild(h);
  r.data.forEach((d) => {
    const tr = el("tr");
    [d.id, d.name, d.category, d.owner, d.created_at].forEach((v) =>
      tr.appendChild(el("td", v == null ? "" : String(v))));
    const td = el("td");
    const dl = el("a", "Download");
    dl.href = "/documents/" + d.id + "/download";
    td.appendChild(dl);
    if (d.owner === me.username) {
      addBtn(td, "Share", () => share(d));
      addBtn(td, "Access", () => access(d));
      addBtn(td, "Delete", () => del(d));
    }
    tr.appendChild(td);
    t.appendChild(tr);
  });
  box.appendChild(t);
}
$("searchBtn").onclick = loadDocs;

$("upBtn").onclick = async () => {
  const f = $("file").files[0];
  if (!f) { msg("choose a file"); return; }
  const fd = new FormData();
  fd.append("file", f);
  fd.append("category", $("upcat").value);
  const r = await api("/documents", { method: "POST", body: fd });
  msg(r.ok ? "uploaded" : (r.data && r.data.error) || "upload failed");
  loadDocs();
};

async function share(d) {
  const username = prompt("Share with which username?");
  if (!username) return;
  const level = prompt("Level: read or edit", "read");
  const r = await api("/documents/" + d.id + "/grants", {
    method: "POST", headers: JSONH, body: JSON.stringify({ username: username, level: level }),
  });
  msg(r.ok ? "granted" : (r.data && r.data.error) || "failed");
  access(d);
}

async function access(d) {
  const r = await api("/documents/" + d.id + "/grants");
  const box = $("grants");
  box.replaceChildren();
  if (!r.ok) { msg("not allowed"); return; }
  box.appendChild(el("h3", "Access to: " + d.name));
  if (r.data.length === 0) box.appendChild(el("p", "Nobody else has access."));
  r.data.forEach((g) => {
    const row = el("p", g.username + " (" + g.level + ") ");
    addBtn(row, "Revoke", async () => {
      const x = await api("/documents/" + d.id + "/grants/" + encodeURIComponent(g.username), { method: "DELETE" });
      msg(x.ok ? "revoked" : "failed");
      access(d);
    });
    box.appendChild(row);
  });
}

async function del(d) {
  if (!confirm("Delete " + d.name + "?")) return;
  const r = await api("/documents/" + d.id, { method: "DELETE" });
  msg(r.ok ? "deleted" : "not allowed");
  $("grants").replaceChildren();
  loadDocs();
}

document.querySelectorAll("#adminBox button").forEach((b) => {
  b.onclick = async () => {
    const r = await api(b.dataset.p);
    const out = $("adminOut");
    if (!r.ok) { out.textContent = "error " + r.status; return; }
    if (Array.isArray(r.data)) {
      const cols = r.data.length ? Object.keys(r.data[0]) : [];
      table(out, cols, r.data);
    } else {
      out.textContent = JSON.stringify(r.data);
    }
  };
});

start();