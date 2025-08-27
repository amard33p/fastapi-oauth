# FastAPI + React OAuth (fastapi-users)

This project demonstrates a minimal, end-to-end OAuth login with Google using FastAPI on the backend and a React + Vite SPA on the frontend. It builds on top of fastapi-users and shows how to wire a redirect-based OAuth flow to an SPA while using a JWT bearer token in the client.

The goal of this README is to be explicit enough that another LLM (or developer) can recreate the project and wiring by following the descriptions below.


## Project Structure

```
fastapi-oauth/
├─ backend/
│  ├─ app/
│  │  ├─ app.py            # FastAPI app, routers, CORS, demo protected route
│  │  ├─ users.py          # fastapi-users setup + OAuth redirect transport
│  │  ├─ db.py             # SQLAlchemy models + async engine/session helpers
│  │  ├─ schemas.py        # fastapi-users schemas used by routers
│  │  └─ __init__.py
│  ├─ main.py              # Uvicorn entrypoint for backend
│  └─ requirements.txt
│
├─ frontend/
│  ├─ src/
│  │  ├─ api.js            # API URL + fetch helper (adds Authorization header)
│  │  ├─ token.js          # Local storage helpers for token
│  │  ├─ Auth.jsx          # Small widget that shows login/logout or user email
│  │  ├─ App.jsx           # Router + RequireAuth wrapper
│  │  └─ pages/
│  │     ├─ Login.jsx          # “Login with Google” entrypoint
│  │     ├─ OAuthCallback.jsx  # Handles redirect and stores token
│  │     └─ Home.jsx           # Example protected page calling the API
│  ├─ index.html
│  ├─ package.json
│  └─ README.md (frontend-only doc)
│
└─ .gitignore
```

- The SQLite DB is created at `backend/app/test.db`.
- The backend serves JSON APIs only; the SPA is served separately by Vite in development.


## Backend: Key Files and Concepts

- `backend/app/users.py`
  - Configures fastapi-users with a `JWTStrategy` and a standard bearer `AuthenticationBackend`.
  - Defines `RedirectBearerTransport`, a subclass of `BearerTransport` overriding `get_login_response` to return `302` and redirect back to the SPA: `FRONTEND_URL/oauth-callback?access_token=<token>`.
  - Creates `oauth_redirect_auth_backend` using this transport.
  - Exposes `google_oauth_client` using `httpx-oauth` and env vars.
  - Exposes `fastapi_users` instance and `current_active_user` dependency.

- `backend/app/app.py`
  - Creates the FastAPI app and enables CORS for `http://localhost:5173`.
  - Mounts fastapi-users routers:
    - JWT login router under `/auth/jwt` (not used by the Google flow, but available).
    - Register, reset password, verify routers under `/auth`.
    - Users router under `/users`.
    - Google OAuth router under `/auth/google`, using `oauth_redirect_auth_backend` so the callback redirects to the SPA.
  - Defines `/authenticated-route` as an example protected endpoint using `current_active_user`.

- `backend/app/db.py`
  - Defines `User` and `OAuthAccount` SQLAlchemy models compatible with fastapi-users.
  - Uses a local SQLite DB at `backend/app/test.db` via `sqlite+aiosqlite`.


## Backend: Endpoints You Need

- OAuth (mounted at `/auth/google`):
  - `GET /auth/google/authorize?redirect_url=<SPA URL>` → returns `{ "authorization_url": "…" }`. You redirect the browser to this URL.
  - `GET /auth/google/callback?code=…&state=…` → fastapi-users exchanges the code; our custom transport responds with `302` to `FRONTEND_URL/oauth-callback?access_token=<token>`.

- Users:
  - `GET /users/me` → returns the current user, requires `Authorization: Bearer <token>`.

- Demo protected route:
  - `GET /authenticated-route` → returns a greeting, requires `Authorization: Bearer <token>`.

- JWT (optional, not used by the OAuth button):
  - `POST /auth/jwt/login` → password login if you later add credentials-based auth.
  - `POST /auth/jwt/logout`

Notes:
- CORS is configured to allow `http://localhost:5173`.
- `FRONTEND_URL` controls where the backend redirects after OAuth success.


## Frontend: Wiring and Responsibilities

- `src/api.js`
  - Exports `API_URL` from `import.meta.env.VITE_API_URL` (default `http://localhost:8000`).
  - Exports `apiFetch(path, options)` that adds `Authorization: Bearer <token>` if present and `credentials: 'include'`.

- `src/token.js`
  - Manages the token in `localStorage` under the key `app_jwt`.

- `src/Auth.jsx`
  - On mount, calls `getUser()` (which calls `GET /users/me`) to show `Welcome, <email>!` or "Login with Google".

- `src/pages/Login.jsx`
  - If no token, shows a button calling `loginWithGoogle()`.

- `src/pages/OAuthCallback.jsx`
  - Parses `access_token` from the query string (when the backend redirects directly with a token) and stores it.
  - If no `access_token` but `code` and `state` are present, calls the backend callback to exchange and then stores the token from the response.
  - Navigates to `/` after storing the token.

- `src/App.jsx`
  - Defines routes: `/login`, `/oauth-callback`, and `/`.
  - Wraps `/` in `RequireAuth`, which redirects to `/login` when no token exists.

- `src/authClient.js`
  - `loginWithGoogle()` calls `GET ${API_URL}/auth/google/authorize?redirect_url=${window.location.origin}/oauth-callback`, expects `{ authorization_url }`, then `window.location.assign(authorization_url)`.
  - `getUser()` calls `apiFetch('/users/me')`.
  - `logoutUser()` clears the token and navigates to `/login`.


## User Journey and Network Calls

1. User visits the SPA at `http://localhost:5173/login`.
2. User clicks “Login with Google”. Frontend executes:
   - `GET {API_URL}/auth/google/authorize?redirect_url=http://localhost:5173/oauth-callback` → `{ authorization_url }`.
   - Browser navigates to `authorization_url` (Google).
3. User completes Google authentication. Google redirects to backend:
   - `GET {API_URL}/auth/google/callback?code=…&state=…`.
4. Backend (fastapi-users + `RedirectBearerTransport`) finishes the exchange and returns:
   - `302 Location: {FRONTEND_URL}/oauth-callback?access_token=<JWT>`.
5. Frontend `OAuthCallback.jsx` reads `access_token` from query, stores it in `localStorage`, and navigates to `/`.
   - Fallback: if token not present but `code`+`state` are, it calls `GET {API_URL}/auth/google/callback?...`, expects JSON with `access_token`, stores it, and navigates to `/`.
6. The home page (`/`) is protected by `RequireAuth`. With token stored, it renders `Home` and `Auth`.
7. `Auth` calls `GET {API_URL}/users/me` to display the user’s email.
8. The “Call /authenticated-route” button triggers `GET {API_URL}/authenticated-route` and displays the response.
9. Logout clears the token and sends the user back to `/login`.


## Environment Variables and Configuration

Backend:
- `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` (required) — from Google Cloud Console.
  - Authorized redirect URI: `http://localhost:8000/auth/google/callback`
  - Authorized JavaScript origin: `http://localhost:5173`
- `FRONTEND_URL` (optional, default `http://localhost:5173`) — where to redirect after OAuth success.

Frontend:
- `VITE_API_URL` (optional, default `http://localhost:8000`) — the backend base URL used by `api.js`.

Database:
- Local SQLite at `backend/app/test.db`. No migrations are included; tables are auto-created at startup.

CORS:
- Configured for `http://localhost:5173` in `backend/app/app.py`.


## Running Locally

Backend (terminal 1):
```
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
export GOOGLE_CLIENT_ID=your_id
export GOOGLE_CLIENT_SECRET=your_secret
# optionally: export FRONTEND_URL=http://localhost:5173
python3 backend/main.py
```

Frontend (terminal 2):
```
cd frontend
npm install
npm run dev
# open http://localhost:5173/login
```


## Security Notes and Alternatives

- This demo redirects with `?access_token=…` in the URL. For production, prefer one of these approaches:
  - Use an HttpOnly cookie transport (like the example repo’s `OAuthCookieTransport`) so the token is not accessible to JavaScript or present in URLs.
  - Use a short-lived one-time code in the redirect and exchange it in the SPA through a backend endpoint to obtain a token.
- If you switch to cookies, you will no longer store tokens in `localStorage`, and `api.js` won’t need to set the `Authorization` header.


## Extending This Template

- Add GitHub OAuth by mounting another `get_oauth_router` with a GitHub client.
- Add password-based auth by using the `/auth/jwt/login` endpoint in the UI.
- Replace SQLite with Postgres and introduce Alembic migrations.
- Harden CORS and configure domain-specific `FRONTEND_URL` for deployment.


## Troubleshooting

- “Landing on backend JSON page at `/auth/google/callback`” → ensure the OAuth router uses the redirect-aware backend (we use `oauth_redirect_auth_backend` in `app.py`).
- SPA doesn’t see the user → ensure `Authorization` header is set in `api.js` and token exists in `localStorage`.
- 401 on protected routes → token missing or expired; re-login.


## References

- fastapi-users: https://github.com/fastapi-users/fastapi-users
- httpx-oauth: https://github.com/terrycain/httpx-oauth
- React Router: https://reactrouter.com/
