// Rate — a small demo frontend for the Rate API.
// Plain JavaScript, no build step: a hash router (#/post/3, #/me...) that
// renders each view into <main id="app">.

const API = (window.RATE_API || "http://localhost:8000").replace(/\/$/, "");

const storage = {
  get(k) { try { return localStorage.getItem(k); } catch { return null; } },
  set(k, v) { try { localStorage.setItem(k, v); } catch {} },
  del(k) { try { localStorage.removeItem(k); } catch {} },
};

const state = {
  token: storage.get("rate_token"),
  me: null,              // UserResponse of the logged-in user
  genres: [],            // full catalog, loaded once
  users: new Map(),      // id -> username cache (posts only carry author_id)
};

// ------------------------------------------------------------------ helpers

const $app = document.getElementById("app");

function esc(s) {
  return String(s ?? "").replace(/[&<>"']/g, (c) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  }[c]));
}

function fmtDate(iso) {
  const d = new Date(iso);
  const diff = (Date.now() - d) / 1000;
  if (diff < 60) return "just now";
  if (diff < 3600) return `${Math.floor(diff / 60)} min ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)} h ago`;
  if (diff < 86400 * 7) return `${Math.floor(diff / 86400)} d ago`;
  return d.toLocaleDateString("en-US", { day: "numeric", month: "short", year: "numeric" });
}

function excerpt(text, n = 180) {
  return text.length > n ? text.slice(0, n).trimEnd() + "…" : text;
}

function toast(msg, bad = false) {
  const t = document.getElementById("toast");
  t.textContent = msg;
  t.className = "toast" + (bad ? " bad" : "");
  t.hidden = false;
  clearTimeout(toast._t);
  toast._t = setTimeout(() => (t.hidden = true), 3200);
}

const ICON = {
  heart: '<svg class="icon" viewBox="0 0 24 24"><path d="M20.8 4.6a5.5 5.5 0 0 0-7.8 0L12 5.7l-1-1.1a5.5 5.5 0 0 0-7.8 7.8l1 1.1L12 21l7.8-7.5 1-1.1a5.5 5.5 0 0 0 0-7.8z"/></svg>',
  comment: '<svg class="icon" viewBox="0 0 24 24"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>',
};

function avatarColor(name) {
  const colors = ["#ff5c7a", "#ffb35c", "#7c6cff", "#2fc5a0", "#5cb8ff", "#e27cff"];
  let h = 0;
  for (const c of name) h = (h * 31 + c.charCodeAt(0)) >>> 0;
  return colors[h % colors.length];
}

// ------------------------------------------------------------------ API

class ApiError extends Error {
  constructor(status, message) { super(message); this.status = status; }
}

function errorText(data) {
  if (!data || !data.detail) return null;
  if (typeof data.detail === "string") return data.detail;
  if (Array.isArray(data.detail)) {
    return data.detail.map((e) => `${(e.loc || []).slice(1).join(".")}: ${e.msg}`).join(" · ");
  }
  return JSON.stringify(data.detail);
}

async function api(path, { method = "GET", body, form, auth = true } = {}) {
  const send = async (withToken) => {
    const headers = {};
    let payload;
    if (withToken && state.token) headers.Authorization = "Bearer " + state.token;
    if (form) {
      payload = new URLSearchParams(form);
    } else if (body !== undefined) {
      payload = JSON.stringify(body);
      headers["Content-Type"] = "application/json";
    }
    try {
      return await fetch(API + path, { method, headers, body: payload });
    } catch {
      throw new ApiError(0, `Cannot reach the API at ${API}. Is it running (make run)?`);
    }
  };

  let res = await send(auth);

  // Expired token (they last 15 minutes): log out and, for reads, retry
  // anonymously so public pages keep working.
  if (res.status === 401 && auth && state.token) {
    logout(true);
    toast("Your session has expired. Please log in again.", true);
    if (method === "GET") res = await send(false);
  }

  if (res.status === 204) return null;
  const data = await res.json().catch(() => null);
  if (!res.ok) {
    if (res.status === 401) throw new ApiError(401, "You need to log in.");
    throw new ApiError(res.status, errorText(data) || `Error ${res.status}`);
  }
  return data;
}

async function loadUsers(ids) {
  const missing = [...new Set(ids)].filter((id) => !state.users.has(id));
  await Promise.all(missing.map(async (id) => {
    try {
      const u = await api(`/users/${id}`, { auth: false });
      state.users.set(id, u.username);
    } catch {
      state.users.set(id, `user ${id}`);
    }
  }));
}
const uname = (id) => state.users.get(id) || `user ${id}`;

async function loadGenres() {
  if (!state.genres.length) state.genres = await api("/genres/", { auth: false });
  return state.genres;
}

// There is no GET /posts/{id}/comments yet, so we read all comments once
// and group them by post.
async function commentsByPost() {
  const all = await api("/comment/", { auth: false });
  const map = new Map();
  for (const c of all) {
    if (!map.has(c.post_id)) map.set(c.post_id, []);
    map.get(c.post_id).push(c);
  }
  return map;
}

// ------------------------------------------------------------------ session

async function loadMe() {
  if (!state.token) { state.me = null; return; }
  try {
    state.me = await api("/users/me");
    state.users.set(state.me.id, state.me.username);
  } catch {
    state.me = null;
  }
}

function logout(silent = false) {
  state.token = null;
  state.me = null;
  storage.del("rate_token");
  renderNav();
  if (!silent) { toast("Logged out"); location.hash = "#/"; }
}

function renderNav() {
  const nav = document.getElementById("nav");
  const route = location.hash || "#/";
  const link = (href, label, cls = "") =>
    `<a href="${href}" class="${cls} ${route === href || (href !== "#/" && route.startsWith(href)) ? "active" : ""}">${label}</a>`;

  nav.innerHTML = state.me
    ? link("#/", "Home") + link("#/new", "New post") +
      link("#/me", "@" + esc(state.me.username), "me") +
      `<button class="linkish" id="logout">Log out</button>`
    : link("#/", "Home") + link("#/login", "Log in");

  document.getElementById("logout")?.addEventListener("click", () => logout());
}

// ------------------------------------------------------------------ pieces

function likeButton(p) {
  return `<button class="like ${p.liked_by_me ? "on" : ""}" data-like="${p.id}" title="Like">
    ${ICON.heart}<span>${p.like_count}</span></button>`;
}

function postCard(p, comments) {
  const n = comments.get(p.id)?.length || 0;
  return `
  <article class="card">
    <div class="card-top">
      <span class="badge ${p.post_type}">${p.post_type === "album" ? "Album" : "Song"}</span>
      <span class="muted">${fmtDate(p.created_at)}</span>
    </div>
    <h3><a href="#/post/${p.id}">${esc(p.title)}</a></h3>
    <p class="excerpt">${esc(excerpt(p.content))}</p>
    <div class="chips">${p.genres.map((g) => `<span class="chip">${esc(g.name)}</span>`).join("")}</div>
    <div class="card-foot">
      <a class="author" href="#/user/${p.author_id}">@${esc(uname(p.author_id))}</a>
      <span class="spacer"></span>
      <a class="meta" href="#/post/${p.id}">${ICON.comment}${n}</a>
      ${likeButton(p)}
    </div>
  </article>`;
}

function empty(html) { return `<div class="empty">${html}</div>`; }

// One click handler for every like button on the page.
document.addEventListener("click", async (e) => {
  const btn = e.target.closest("[data-like]");
  if (!btn) return;
  if (!state.token) { toast("Log in to like posts"); location.hash = "#/login"; return; }
  const id = btn.dataset.like;
  const on = btn.classList.contains("on");
  btn.disabled = true;
  try {
    const r = await api(`/posts/${id}/like`, { method: on ? "DELETE" : "POST" });
    btn.classList.toggle("on", r.liked_by_me);
    btn.querySelector("span").textContent = r.like_count;
  } catch (err) {
    toast(err.message, true);
  } finally {
    btn.disabled = false;
  }
});

// ------------------------------------------------------------------ views

const FEEDS = [
  { key: "latest", label: "Latest", desc: "The newest posts from the community." },
  { key: "popular", label: "Popular", desc: "The most liked posts this week." },
  { key: "recommended", label: "For you", auth: true, desc: "Posts from your favourite genres." },
  { key: "discover", label: "Discover", auth: true, desc: "Genres you don't follow yet." },
];

async function viewFeed(key, alive) {
  const feed = FEEDS.find((f) => f.key === key) || FEEDS[0];
  $app.innerHTML = `
    <section class="hero">
      <h1>${state.me ? `Hi, ${esc(state.me.username)}` : "Discover music through people"}</h1>
      <p>${feed.desc}</p>
    </section>
    <nav class="tabs">
      ${FEEDS.map((f) => `<a href="#/feed/${f.key}" class="${f.key === feed.key ? "active" : ""}">${f.label}${f.auth && !state.me ? '<span class="lock">· login</span>' : ""}</a>`).join("")}
    </nav>
    <div id="list" class="cards"><div class="loading">Loading…</div></div>
    <div class="more"><button id="more" class="btn ghost" hidden>Load more</button></div>`;

  const list = document.getElementById("list");
  const more = document.getElementById("more");

  if (feed.auth && !state.me) {
    list.innerHTML = empty(`This feed is based on your genres. <a href="#/login">Log in</a> to see it.`);
    return;
  }

  const LIMIT = 10;
  let offset = 0;
  const comments = await commentsByPost();

  async function loadPage() {
    more.disabled = true;
    const posts = await api(`/home/${feed.key}?limit=${LIMIT}&offset=${offset}`);
    await loadUsers(posts.map((p) => p.author_id));
    if (!alive()) return;
    if (offset === 0) list.innerHTML = "";
    list.insertAdjacentHTML("beforeend", posts.map((p) => postCard(p, comments)).join(""));
    offset += posts.length;
    more.hidden = posts.length < LIMIT;
    more.disabled = false;
    if (offset === 0) {
      list.innerHTML = feed.key === "recommended"
        ? empty(`Nothing for you yet. <a href="#/me">Pick your genres</a>.`)
        : empty(`No posts yet. Have you run <code>make seed</code>?`);
    }
  }

  more.addEventListener("click", () => loadPage().catch((e) => toast(e.message, true)));
  await loadPage();
}

async function viewPost(id, alive) {
  $app.innerHTML = `<div class="loading">Loading…</div>`;
  const [post, comments] = await Promise.all([api(`/posts/${id}`), commentsByPost()]);
  const list = (comments.get(post.id) || []).sort((a, b) => new Date(a.created_at) - new Date(b.created_at));
  await loadUsers([post.author_id, ...list.map((c) => c.author_id)]);
  if (!alive()) return;

  const mine = state.me && state.me.id === post.author_id;

  $app.innerHTML = `
    <a class="back" href="javascript:history.back()">← Back</a>
    <article class="panel">
      <div class="card-top">
        <span class="badge ${post.post_type}">${post.post_type === "album" ? "Album" : "Song"}</span>
        <span class="muted">${fmtDate(post.created_at)}</span>
      </div>
      <h1>${esc(post.title)}</h1>
      <p class="muted">by <a class="author" href="#/user/${post.author_id}">@${esc(uname(post.author_id))}</a></p>
      <div class="chips">${post.genres.map((g) => `<span class="chip">${esc(g.name)}</span>`).join("")}</div>
      <div class="post-body">${esc(post.content)}</div>
      <div class="card-foot">
        ${likeButton(post)}
        <span class="spacer"></span>
        ${mine ? `<a class="btn ghost small" href="#/edit/${post.id}">Edit</a>
                  <button class="btn danger small" id="del">Delete</button>` : ""}
      </div>
    </article>

    <section class="section">
      <h2>Comments (${list.length})</h2>
      <div class="panel">
        ${list.length ? list.map((c) => `
          <div class="comment">
            <div class="comment-head"><a href="#/user/${c.author_id}">@${esc(uname(c.author_id))}</a> · ${fmtDate(c.created_at)}</div>
            <div>${esc(c.content)}</div>
          </div>`).join("") : `<p class="muted">No comments yet.</p>`}
        ${state.me ? `
          <form class="comment-form" id="cform">
            <textarea name="content" placeholder="What do you think?" required></textarea>
            <div class="form-actions"><button class="btn">Comment</button></div>
          </form>` : `<p class="hint"><a href="#/login">Log in</a> to comment.</p>`}
      </div>
    </section>`;

  document.getElementById("cform")?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const content = e.target.content.value.trim();
    if (!content) return;
    try {
      await api(`/comment/post/${post.id}`, { method: "POST", body: { content } });
      toast("Comment posted");
      render();
    } catch (err) { toast(err.message, true); }
  });

  document.getElementById("del")?.addEventListener("click", async () => {
    if (!confirm("Delete this post and its comments?")) return;
    try {
      await api(`/posts/${post.id}`, { method: "DELETE" });
      toast("Post deleted");
      location.hash = "#/me";
    } catch (err) { toast(err.message, true); }
  });
}

function genrePicker(name, selected) {
  return `<div class="genre-picker">${state.genres.map((g) => `
    <input type="checkbox" id="${name}-${g.id}" name="${name}" value="${g.id}" ${selected.has(g.id) ? "checked" : ""}>
    <label for="${name}-${g.id}">${esc(g.name)}</label>`).join("")}</div>`;
}

const checkedIds = (form, name) =>
  [...form.querySelectorAll(`input[name=${name}]:checked`)].map((i) => Number(i.value));

async function viewEditor(id, alive) {
  if (!state.me) { location.hash = "#/login"; return; }
  $app.innerHTML = `<div class="loading">Loading…</div>`;
  await loadGenres();
  const post = id ? await api(`/posts/${id}`) : null;
  if (!alive()) return;

  const type = post?.post_type || "album";
  $app.innerHTML = `
    <section class="hero"><h1>${post ? "Edit post" : "New post"}</h1>
      <p>Share an album or a song that stuck with you.</p></section>
    <form class="panel" id="pform">
      <label>Type</label>
      <div class="type-picker genre-picker">
        <input type="radio" id="t-album" name="post_type" value="album" ${type === "album" ? "checked" : ""}><label for="t-album">Album</label>
        <input type="radio" id="t-song" name="post_type" value="song" ${type === "song" ? "checked" : ""}><label for="t-song">Song</label>
      </div>
      <label for="title">Title</label>
      <input type="text" id="title" name="title" required value="${esc(post?.title)}" placeholder="Artist — Title">
      <label for="content">What do you think?</label>
      <textarea id="content" name="content" required>${esc(post?.content)}</textarea>
      <label>Genres</label>
      ${genrePicker("g", new Set(post?.genres.map((g) => g.id) || []))}
      <div class="error" id="err"></div>
      <div class="form-actions">
        <button class="btn">${post ? "Save" : "Publish"}</button>
        <a class="linkish" href="${post ? `#/post/${post.id}` : "#/"}">Cancel</a>
      </div>
    </form>`;

  document.getElementById("pform").addEventListener("submit", async (e) => {
    e.preventDefault();
    const f = e.target;
    const body = {
      title: f.title.value.trim(),
      content: f.content.value.trim(),
      post_type: f.post_type.value,
      genre_ids: checkedIds(f, "g"),
    };
    try {
      const saved = await api(post ? `/posts/${post.id}` : "/posts/", { method: post ? "PATCH" : "POST", body });
      toast(post ? "Changes saved" : "Post published");
      location.hash = `#/post/${saved.id}`;
    } catch (err) {
      document.getElementById("err").textContent = err.message;
    }
  });
}

async function viewLogin(mode) {
  const signup = mode === "signup";
  $app.innerHTML = `
    <form class="panel narrow" id="auth">
      <h1>${signup ? "Sign up" : "Log in"}</h1>
      <p class="hint">${signup ? "" : "With the sample data: <code>john0</code> / <code>password123</code>"}</p>
      <label for="username">Username</label>
      <input type="text" id="username" name="username" required autocomplete="username">
      ${signup ? `<label for="email">Email</label><input type="email" id="email" name="email" required>` : ""}
      <label for="password">Password</label>
      <input type="password" id="password" name="password" required autocomplete="${signup ? "new-password" : "current-password"}">
      <div class="error" id="err"></div>
      <div class="form-actions">
        <button class="btn">${signup ? "Sign up" : "Log in"}</button>
        <a class="linkish" href="${signup ? "#/login" : "#/signup"}">${signup ? "I already have an account" : "Create an account"}</a>
      </div>
    </form>`;

  document.getElementById("auth").addEventListener("submit", async (e) => {
    e.preventDefault();
    const f = e.target;
    const username = f.username.value.trim();
    const password = f.password.value;
    try {
      if (signup) {
        await api("/users/signup", { method: "POST", auth: false, body: { username, email: f.email.value.trim(), password } });
      }
      const { access_token } = await api("/users/login", { method: "POST", auth: false, form: { username, password } });
      state.token = access_token;
      storage.set("rate_token", access_token);
      await loadMe();
      toast(signup ? "Account created. Pick your genres." : `Hi, ${state.me.username}`);
      location.hash = signup ? "#/me" : "#/";
    } catch (err) {
      document.getElementById("err").textContent = err.message;
    }
  });
}

function profileHead(user, extra = "") {
  return `<div class="profile-head">
    <div class="avatar" style="background:${avatarColor(user.username)}">${esc(user.username[0].toUpperCase())}</div>
    <div><h1>@${esc(user.username)}</h1>${extra}</div></div>`;
}

async function viewMe(alive) {
  if (!state.me) { location.hash = "#/login"; return; }
  $app.innerHTML = `<div class="loading">Loading…</div>`;
  const [, myGenres, myPosts, myComments, comments] = await Promise.all([
    loadGenres(), api("/users/me/genres"), api("/posts/me"), api("/comment/me"), commentsByPost(),
  ]);
  if (!alive()) return;
  myPosts.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));

  $app.innerHTML = `
    ${profileHead(state.me, `<p class="muted" style="margin:4px 0 0">${esc(state.me.email)}</p>`)}

    <section class="section">
      <h2>Your genres</h2>
      <form class="panel" id="gform">
        <p class="hint" style="margin-top:0">They decide what you see in “For you” and “Discover”.</p>
        ${genrePicker("mg", new Set(myGenres.map((g) => g.id)))}
        <div class="form-actions"><button class="btn small">Save genres</button></div>
      </form>
    </section>

    <section class="section">
      <h2>Your posts (${myPosts.length})</h2>
      <div class="cards">${myPosts.length ? myPosts.map((p) => postCard(p, comments)).join("") : empty(`You haven't posted yet. <a href="#/new">Write your first one</a>.`)}</div>
    </section>

    <section class="section">
      <h2>Your comments (${myComments.length})</h2>
      <div class="panel">${myComments.length ? myComments.map((c) => `
        <div class="comment">
          <div class="comment-head"><a href="#/post/${c.post_id}">on post #${c.post_id}</a> · ${fmtDate(c.created_at)}</div>
          <div>${esc(c.content)}</div>
        </div>`).join("") : `<p class="muted">You haven't commented yet.</p>`}</div>
    </section>`;

  document.getElementById("gform").addEventListener("submit", async (e) => {
    e.preventDefault();
    try {
      await api("/users/me/genres", { method: "PUT", body: { genre_ids: checkedIds(e.target, "mg") } });
      toast("Genres saved");
    } catch (err) { toast(err.message, true); }
  });
}

async function viewUser(id, alive) {
  if (state.me && String(state.me.id) === String(id)) { location.hash = "#/me"; return; }
  $app.innerHTML = `<div class="loading">Loading…</div>`;
  // There is no "posts by user" endpoint yet: filter the full list.
  const [user, posts, comments] = await Promise.all([
    api(`/users/${id}`, { auth: false }), api("/posts/"), commentsByPost(),
  ]);
  if (!alive()) return;
  state.users.set(user.id, user.username);
  const theirs = posts.filter((p) => p.author_id === user.id);
  const theirComments = [...comments.values()].flat().filter((c) => c.author_id === user.id).length;

  $app.innerHTML = `
    ${profileHead(user, `<p class="muted" style="margin:4px 0 0">${theirs.length} posts · ${theirComments} comments</p>`)}
    <section class="section">
      <h2>Posts</h2>
      <div class="cards">${theirs.length ? theirs.map((p) => postCard(p, comments)).join("") : empty("This user hasn't posted anything yet.")}</div>
    </section>`;
}

// ------------------------------------------------------------------ router

let renderSeq = 0;

async function render() {
  const seq = ++renderSeq;
  const alive = () => seq === renderSeq; // false once the user navigated away
  const parts = (location.hash.replace(/^#\/?/, "") || "").split("/");
  renderNav();
  window.scrollTo(0, 0);

  try {
    switch (parts[0]) {
      case "":
      case "feed": await viewFeed(parts[1] || "latest", alive); break;
      case "post": await viewPost(parts[1], alive); break;
      case "new": await viewEditor(null, alive); break;
      case "edit": await viewEditor(parts[1], alive); break;
      case "login": await viewLogin("login"); break;
      case "signup": await viewLogin("signup"); break;
      case "me": await viewMe(alive); break;
      case "user": await viewUser(parts[1], alive); break;
      default: $app.innerHTML = empty(`Page not found. <a href="#/">Go home</a>`);
    }
  } catch (err) {
    if (alive()) $app.innerHTML = empty(esc(err.message));
  }
}

window.addEventListener("hashchange", render);

(async () => {
  document.getElementById("api-url").textContent = API;
  // Opened by double-clicking index.html: the browser sends "Origin: null"
  // and the API's CORS rejects every call. It has to be served over http.
  if (location.protocol === "file:") {
    $app.innerHTML = empty(`You opened the file directly, so the browser blocks the API calls (CORS, “Origin null”).<br><br>
      Start it with <code>make front</code> and open <a href="http://localhost:8080">http://localhost:8080</a>.`);
    return;
  }
  await loadMe();
  render();
})();
