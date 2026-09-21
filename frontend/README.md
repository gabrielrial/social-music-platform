# Rate — demo frontend

A small web client for the Rate API, written in plain HTML, CSS and JavaScript.
There is no build step and there are no dependencies: the browser loads the files as they are.

It exists to **show the API working**. It is not a production frontend.

---

## Files

```
frontend/
├── index.html   # Page shell: top bar, <main id="app">, footer
├── styles.css   # All the styles (dark theme, responsive down to phone width)
├── config.js    # Decides which API URL the page calls
└── app.js       # API client, hash router and every view
```

`app.js` is a single-page app with a hash router: each URL fragment renders one view into `<main id="app">`.

| Route            | View                                                        | Login |
|------------------|-------------------------------------------------------------|-------|
| `#/`             | Home, "Latest" feed                                         | No    |
| `#/feed/<name>`  | Home feed: `latest`, `popular`, `recommended`, `discover`   | `recommended` and `discover` only |
| `#/post/<id>`    | Post detail, likes and comments (edit/delete if it is yours) | To like or comment |
| `#/new`          | Create a post (type, title, text, genres)                   | Yes   |
| `#/edit/<id>`    | Edit one of your posts                                      | Yes   |
| `#/me`           | Your profile: favourite genres, your posts, your comments   | Yes   |
| `#/user/<id>`    | Someone else's profile and posts                            | No    |
| `#/login`, `#/signup` | Log in / create an account                             | No    |

The JWT from `POST /users/login` is kept in `localStorage` (`rate_token`) and sent as `Authorization: Bearer <token>`.
Tokens last 15 minutes: when the API answers 401, the page logs out, shows "Your session has expired" and retries public reads without the token.

---

## Running it

The API must be running first (`make run`), with sample data if you want something to see (`make seed`).
Sample login: `john0` / `password123`.

There are two ways to open the frontend:

| Option | Command | URL | How it calls the API |
|--------|---------|-----|----------------------|
| **Served by the API** (recommended) | nothing, `make run` is enough | http://localhost:8000/app | Same origin, no CORS involved |
| Separate static server | `make front` | http://localhost:8080 | Cross-origin to `localhost:8000`, allowed by `CORS_ORIGINS` |

The API serves this folder at `/app` with FastAPI's `StaticFiles` (see the end of `app/main.py`). If `frontend/` does not exist, the mount is skipped and the API works as before.

### How `config.js` picks the API URL

```js
window.RATE_API = location.port === "8080" ? "http://localhost:8000" : location.origin;
```

- Page on port 8080 (`make front`) → calls `http://localhost:8000`.
- Anything else (`localhost:8000/app`, an ngrok URL...) → calls the same origin the page came from.

This is what makes the same files work locally and through ngrok without editing anything.

---

## Workarounds for missing endpoints

The API does not have everything the UI needs yet, so the frontend fills the gaps on its side. This is fine with the sample data, but it downloads more than necessary as the data grows:

| The UI needs | Missing endpoint | What the frontend does instead |
|---|---|---|
| Comments of one post, comment counts on cards | `GET /posts/{id}/comments` | Downloads `GET /comment/` and groups it by `post_id` |
| Posts of another user | `GET /users/{id}/posts` | Downloads `GET /posts/` and filters by `author_id` |
| Author names on posts and comments | Author name in `PostResponse` / `CommentResponse` | Calls `GET /users/{id}` once per author and caches it |

When those endpoints exist, replace `commentsByPost()`, the filter in `viewUser()` and `loadUsers()` in `app.js`.

---

## Troubleshooting (CORS)

| Symptom in the browser console | Cause | Fix |
|---|---|---|
| `Origin null is not allowed by Access-Control-Allow-Origin` | `index.html` was opened by double-clicking it (`file://`), so the browser sends `Origin: null` | Open http://localhost:8000/app or use `make front`. The page now shows a warning when opened as a file |
| Same error, but with `http://127.0.0.1:8080` | `localhost` and `127.0.0.1` are different origins for CORS | Use `localhost`, or add the other origin to `CORS_ORIGINS` |
| "Save genres" fails with a CORS error | `PUT` was missing from `allow_methods` in `app/main.py` | Already fixed: `allow_methods` now includes `PUT` |
| `Cannot reach the API at ...` | The API is not running, or it runs on another port | `make run`, or adjust `config.js` |

Do not add `null` to `CORS_ORIGINS`: it would let any local HTML file call the API.

---

## Sharing it on the internet with ngrok

[ngrok](https://ngrok.com) opens a public HTTPS URL that forwards to a port on your machine.
Because the API serves the frontend on the same port, **one tunnel to port 8000 shares both** the web page and the API.

### 1. One-time setup

```bash
brew install ngrok                               # macOS
ngrok config add-authtoken <YOUR_AUTHTOKEN>      # token from the ngrok dashboard
```

The questions ngrok asks when you sign up (what you use it for, your role...) are only a survey: any answer works. The **Free** plan is enough.

### 2. Endpoint options in the dashboard

If the dashboard asks you to create an endpoint, choose:

| Question | Choose | Why |
|---|---|---|
| How will this endpoint be deployed? | **Agent Endpoint** | It is the one created by running `ngrok http` on your Mac. Cloud Endpoints are managed from the dashboard and are not needed here |
| Where do you want your endpoint to be available? | **Public** | So other people can open the link. *Internal* and *Kubernetes Operator* are not reachable from a browser |
| Choose your URL | Your free static domain (`something.ngrok-free.app`) | The URL stays the same every time you restart ngrok |
| Do you want to allow pooling? | **Don't allow pooling** | Pooling load-balances between several copies of the app; there is only one |
| Traffic policy | None, just **Continue** | Not needed for a demo |

The dashboard then suggests a command ending in `80`. Use port **8000** instead, which is where the API listens.

### 3. Start it

```bash
make run                                            # terminal 1: database + API on :8000
make share                                          # terminal 2: random URL
make share NGROK_URL=something.ngrok-free.app       # or: your fixed domain
```

`make share` runs `ngrok http 8000` (with `--url=...` when `NGROK_URL` is set). Then open:

- Frontend: `https://<your-url>/app`
- Swagger: `https://<your-url>/docs`

### 4. Good to know

- **Warning page.** On the free plan, the first visit shows an ngrok warning page. Click **Visit Site** once; after that the page and its API calls work normally.
- **It only works while your Mac is on**, with both `make run` and `make share` running.
- **The URL changes** on every restart unless you use your static domain.
- **It is public.** Anyone with the link can reach the whole API. Before sharing:
  - start the API with a real secret: `JWT_SECRET=<long-random-string> make run` (the default secret is public, in this repo);
  - remember that every sample user has the password `password123`.
