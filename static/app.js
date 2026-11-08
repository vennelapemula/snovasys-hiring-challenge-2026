"use strict";

/* =====================================
   TRUSTVAULT - DOCUMENT MANAGEMENT
   Purple & White Professional Edition
===================================== */

const $ = (id) => document.getElementById(id);

const JSONH = {
  "Content-Type": "application/json"
};

let me = null;
let currentDocument = null;
let loadingDocuments = false;

/* =====================================
   DESIGN STYLING
===================================== */

const style = document.createElement("style");

style.textContent = `
  :root {
    --tv-primary: #635bdb;
    --tv-dark: #39327f;
    --tv-light: #f1efff;
  }

  #appBox button {
    border-radius: 9px;
    transition: all .2s ease;
  }

  #appBox button:disabled,
  #loginBox button:disabled {
    opacity: .6;
    cursor: wait;
    transform: none;
  }

  #docs table,
  #adminOut table {
    border-radius: 10px;
    overflow: hidden;
  }

  #docs td button,
  #grants button {
    margin: 3px;
    padding: 8px 12px;
    font-size: 12px;
    background: #635bdb;
    border-radius: 7px;
  }

  #docs td button:hover,
  #grants button:hover {
    background: #39327f;
  }

  #docs td button.tv-delete {
    background: #dc3545;
  }

  #docs td button.tv-delete:hover {
    background: #a91e2c;
  }

  #docs td a {
    display: inline-block;
    padding: 7px 10px;
    background: #eeedff;
    border-radius: 7px;
    text-decoration: none;
  }

  #docs td a:hover {
    background: #ddd9ff;
  }

  #grants {
    line-height: 1.8;
  }

  #grants p {
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 10px;
  }

  #adminOut {
    overflow-x: auto;
  }

  #msg {
    font-weight: 600;
  }

  .tv-empty {
    padding: 25px;
    text-align: center;
    color: #777d94;
  }

  .tv-loading {
    opacity: .65;
    pointer-events: none;
  }
`;

document.head.appendChild(style);

/* =====================================
   BASIC FUNCTIONS
===================================== */

function el(tag, text) {
  const element = document.createElement(tag);

  if (text !== undefined && text !== null) {
    element.textContent = String(text);
  }

  return element;
}

function msg(message) {
  const box = $("msg");

  if (box) {
    box.textContent = message || "";
  }
}

function setBusy(button, busy, originalText) {
  if (!button) return;

  if (busy) {
    button.dataset.originalText = button.textContent;
    button.disabled = true;
    button.textContent = "Please wait...";
  } else {
    button.disabled = false;
    button.textContent =
      originalText || button.dataset.originalText || "Submit";
  }
}

function addBtn(parent, label, fn, className) {
  const button = el("button", label);

  button.type = "button";

  if (className) {
    button.className = className;
  }

  button.addEventListener("click", fn);

  parent.appendChild(button);

  return button;
}

/* =====================================
   API CONNECTION
===================================== */

async function api(path, opts = {}) {
  try {
    const response = await fetch(path, {
      credentials: "same-origin",
      ...opts
    });

    let data = null;

    const contentType =
      response.headers.get("content-type") || "";

    if (contentType.includes("application/json")) {
      data = await response.json();
    } else {
      const text = await response.text();

      if (text) {
        data = { message: text };
      }
    }

    return {
      ok: response.ok,
      status: response.status,
      data
    };

  } catch (error) {
    console.error("API Error:", error);

    return {
      ok: false,
      status: 0,
      data: {
        error: "Server connection failed. Check your internet or server."
      }
    };
  }
}

function errorMessage(result, fallback) {
  return (
    result.data?.error ||
    result.data?.message ||
    fallback
  );
}

/* =====================================
   LOGIN AND SESSION
===================================== */

async function start() {
  const result = await api("/me");

  if (!result.ok) {
    me = null;

    $("loginBox").hidden = false;
    $("appBox").hidden = true;

    if (result.status !== 401 && result.status !== 403) {
      msg(errorMessage(result, "Could not connect to server."));
    }

    return;
  }

  me = result.data;

  if (!me || !me.username) {
    msg("Invalid user session.");
    return;
  }

  $("loginBox").hidden = true;
  $("appBox").hidden = false;

  $("who").textContent =
    me.username + " (" + me.role + ")";

  $("adminBox").hidden =
    me.role !== "admin";

  const uploadBox = $("uploadBox");

  if (uploadBox) {
    uploadBox.hidden =
      me.role === "viewer1";
  }

  msg("");

  await loadDocs();
}

/* LOGIN */

$("loginBtn").addEventListener("click", async () => {
  const username = $("u").value.trim();
  const password = $("p").value;

  if (!username || !password) {
    msg("Please enter username and password.");
    return;
  }

  const button = $("loginBtn");

  setBusy(button, true);

  const result = await api("/login", {
    method: "POST",
    headers: JSONH,
    body: JSON.stringify({
      username,
      password
    })
  });

  setBusy(button, false, "Login to TrustVault →");

  if (!result.ok) {
    msg(errorMessage(result, "Login failed."));
    return;
  }

  $("p").value = "";

  msg("Login successful!");

  await start();
});

/* ENTER KEY LOGIN */

$("p").addEventListener("keydown", (event) => {
  if (event.key === "Enter") {
    $("loginBtn").click();
  }
});

/* LOGOUT */

$("logoutBtn").addEventListener("click", async () => {
  const button = $("logoutBtn");

  setBusy(button, true);

  const result = await api("/logout", {
    method: "POST"
  });

  setBusy(button, false, "Logout");

  if (!result.ok) {
    msg(errorMessage(result, "Logout failed."));
    return;
  }

  me = null;
  currentDocument = null;

  $("appBox").hidden = true;
  $("loginBox").hidden = false;

  $("u").value = "";
  $("p").value = "";

  $("docs").replaceChildren();
  $("grants").replaceChildren();
  $("adminOut").replaceChildren();

  msg("Logged out successfully.");
});

/* =====================================
   DOCUMENT SEARCH AND FILTER
===================================== */

async function loadDocs() {
  if (!me || loadingDocuments) return;

  loadingDocuments = true;

  const box = $("docs");

  box.classList.add("tv-loading");

  const params = new URLSearchParams();

  const search = $("q").value.trim();
  const category = $("cat").value.trim();
  const owner = $("own").value.trim();
  const since = $("since").value;

  if (search) params.set("q", search);
  if (category) params.set("category", category);
  if (owner) params.set("owner", owner);
  if (since) params.set("since", since);

  try {
    const result = await api(
      "/documents?" + params.toString()
    );

    if (!result.ok) {
      msg(errorMessage(result, "Could not load documents."));
      return;
    }

    if (!Array.isArray(result.data)) {
      msg("Invalid document response from server.");
      return;
    }

    renderDocuments(result.data);

    msg(result.data.length + " document(s) found.");

  } finally {
    loadingDocuments = false;
    box.classList.remove("tv-loading");
  }
}

/* RENDER DOCUMENT TABLE */

function renderDocuments(documents) {
  const box = $("docs");

  box.replaceChildren();

  if (documents.length === 0) {
    box.appendChild(
      el("p", "No documents found.")
    ).className = "tv-empty";

    return;
  }

  const table = el("table");

  const header = el("tr");

  [
    "ID",
    "Name",
    "Category",
    "Owner",
    "Created",
    "Actions"
  ].forEach((column) => {
    header.appendChild(el("th", column));
  });

  table.appendChild(header);

  documents.forEach((document) => {
    const row = el("tr");

    [
      document.id,
      document.name,
      document.category,
      document.owner,
      document.created_at
    ].forEach((value) => {
      row.appendChild(
        el("td", value ?? "")
      );
    });

    const actions = el("td");

    /* DOWNLOAD */

    const download = el("a", "⬇ Download");

    download.href =
      "/documents/" +
      encodeURIComponent(document.id) +
      "/download";

    download.setAttribute(
      "aria-label",
      "Download " + document.name
    );

    actions.appendChild(download);

    /* OWNER ACTIONS */

    if (document.owner === me.username) {

      addBtn(actions, "Share", () => {
        share(document);
      });

      addBtn(actions, "Access", () => {
        access(document);
      });

      addBtn(
        actions,
        "Delete",
        () => del(document),
        "tv-delete"
      );
    }

    row.appendChild(actions);

    table.appendChild(row);
  });

  box.appendChild(table);
}

/* SEARCH BUTTON */

$("searchBtn").addEventListener("click", loadDocs);

/* ENTER KEY SEARCH */

$("q").addEventListener("keydown", (event) => {
  if (event.key === "Enter") loadDocs();
});

["cat", "own", "since"].forEach((id) => {
  $(id).addEventListener("keydown", (event) => {
    if (event.key === "Enter") loadDocs();
  });
});

/* =====================================
   DOCUMENT UPLOAD
===================================== */

$("upBtn").addEventListener("click", async () => {
  if (!me) {
    msg("Please login first.");
    return;
  }

  const file = $("file").files[0];

  const category = $("upcat").value.trim();

  if (!file) {
    msg("Please choose a document.");
    return;
  }

  if (!category) {
    msg("Please enter document category.");
    return;
  }

  const formData = new FormData();

  formData.append("file", file);
  formData.append("category", category);

  const button = $("upBtn");

  setBusy(button, true);

  const result = await api("/documents", {
    method: "POST",
    body: formData
  });

  setBusy(button, false, "⬆ Upload Document");

  if (!result.ok) {
    msg(errorMessage(result, "Upload failed."));
    return;
  }

  $("file").value = "";
  $("upcat").value = "";

  msg("Document uploaded successfully!");

  await loadDocs();
});

/* =====================================
   SHARE DOCUMENT
===================================== */

async function share(document) {
  if (!me) return;

  const username = prompt(
    "Enter username to share document:"
  );

  if (!username || !username.trim()) return;

  const level = prompt(
    "Enter permission: read or edit",
    "read"
  );

  if (!level) return;

  const permission = level.trim().toLowerCase();

  if (!["read", "edit"].includes(permission)) {
    msg("Permission must be read or edit.");
    return;
  }

  const result = await api(
    "/documents/" +
    encodeURIComponent(document.id) +
    "/grants",
    {
      method: "POST",
      headers: JSONH,
      body: JSON.stringify({
        username: username.trim(),
        level: permission
      })
    }
  );

  if (!result.ok) {
    msg(errorMessage(result, "Sharing failed."));
    return;
  }

  msg("Document shared successfully!");

  await access(document);
}

/* =====================================
   ACCESS MANAGEMENT
===================================== */

async function access(document) {
  if (!me) return;

  currentDocument = document;

  const box = $("grants");

  box.replaceChildren();

  const result = await api(
    "/documents/" +
    encodeURIComponent(document.id) +
    "/grants"
  );

  if (!result.ok) {
    msg(errorMessage(result, "Could not load permissions."));
    return;
  }

  if (!Array.isArray(result.data)) {
    msg("Invalid permission response.");
    return;
  }

  box.appendChild(
    el("h3", "🔑 Access to: " + document.name)
  );

  if (result.data.length === 0) {
    box.appendChild(
      el("p", "Nobody else has access.")
    );

    return;
  }

  result.data.forEach((grant) => {
    const row = el(
      "p",
      grant.username + " (" + grant.level + ")"
    );

    addBtn(row, "Revoke Access", async () => {
      const confirmed = confirm(
        "Revoke access for " +
        grant.username +
        "?"
      );

      if (!confirmed) return;

      const revoke = await api(
        "/documents/" +
        encodeURIComponent(document.id) +
        "/grants/" +
        encodeURIComponent(grant.username),
        {
          method: "DELETE"
        }
      );

      if (!revoke.ok) {
        msg(errorMessage(revoke, "Revoke failed."));
        return;
      }

      msg("Access revoked successfully.");

      await access(document);
    });

    box.appendChild(row);
  });
}

/* =====================================
   DELETE DOCUMENT
===================================== */

async function del(document) {
  if (!me) return;

  const confirmed = confirm(
    "Are you sure you want to delete " +
    document.name +
    "?"
  );

  if (!confirmed) return;

  const result = await api(
    "/documents/" +
    encodeURIComponent(document.id),
    {
      method: "DELETE"
    }
  );

  if (!result.ok) {
    msg(errorMessage(result, "Delete failed."));
    return;
  }

  msg("Document deleted successfully.");

  $("grants").replaceChildren();

  await loadDocs();
}

/* =====================================
   ADMIN DASHBOARD
===================================== */

const adminBox = $("adminBox");

adminBox.addEventListener("click", async (event) => {

  const button = event.target.closest("button[data-p]");

  if (!button || !adminBox.contains(button)) return;

  if (!me || me.role !== "admin") {
    msg("Admin access required.");
    return;
  }

  const output = $("adminOut");

  output.replaceChildren();

  setBusy(button, true);

  const result = await api(button.dataset.p);

  setBusy(button, false);

  if (!result.ok) {
    output.textContent =
      errorMessage(result, "Admin request failed. HTTP " + result.status);

    return;
  }

  /* ARRAY RESPONSE */

  if (Array.isArray(result.data)) {

    if (result.data.length === 0) {
      output.appendChild(
        el("p", "No records available.")
      );

      return;
    }

    const columns = Object.keys(result.data[0]);

    const table = el("table");

    const header = el("tr");

    columns.forEach((column) => {
      header.appendChild(el("th", column));
    });

    table.appendChild(header);

    result.data.forEach((item) => {
      const row = el("tr");

      columns.forEach((column) => {
        row.appendChild(
          el("td", item[column] ?? "")
        );
      });

      table.appendChild(row);
    });

    output.appendChild(table);

  } else {

    /* OBJECT RESPONSE */

    const pre = el("pre");

    pre.textContent =
      JSON.stringify(result.data, null, 2);

    pre.style.whiteSpace = "pre-wrap";
    pre.style.overflowWrap = "anywhere";
    pre.style.padding = "15px";
    pre.style.background = "#f1efff";
    pre.style.borderRadius = "10px";

    output.appendChild(pre);
  }

  msg("Admin data loaded successfully.");
});

/* =====================================
   APPLICATION START
===================================== */

start();
