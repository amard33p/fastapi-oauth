# FastAPI + React OAuth (fastapi-users)

This project demonstrates a minimal, end-to-end OAuth login with Google using FastAPI on the backend and a React + Vite SPA on the frontend. It builds on top of fastapi-users and shows how to wire a redirect-based OAuth flow to an SPA using secure HttpOnly cookies (no tokens in URLs or localStorage).

The goal of this README is to be explicit enough that another LLM (or developer) can recreate the project and wiring by following the descriptions below.


## Project Structure

```
fastapi-oauth/
.
├── backend/                          # Backend FastAPI project
│   ├── app/                          # Application code
│   │   ├── app.py                    # FastAPI app setup: CORS, routers, OAuth routes
│   │   ├── crud_user.py              # CRUD utilities for users via SQLAlchemy/UserManager
│   │   ├── db.py                     # SQLAlchemy models, engine/session, create_db_and_tables()
│   │   ├── schemas.py                # Pydantic user schemas (UserRead, UserCreate, UserUpdate)
│   │   ├── test.db                   # Local SQLite DB (auto-created)
│   │   └── users.py                  # fastapi-users config: OAuth backend, current_active_user
│   ├── main.py                       # Uvicorn entrypoint to run the API locally
│   ├── pyproject.toml                # Backend dependencies & metadata
│   ├── tests/                        # Test suite
│   │   ├── conftest.py               # Pytest fixtures: db session & authenticated TestClient
│   │   ├── e2e/                      # End-to-end tests (e.g., authenticated route)
│   │   └── repositories/             # Repository/CRUD tests (e.g., user update)
├── frontend/                         # Frontend React/Vite project
│   ├── index.html                    # Vite HTML entrypoint
│   ├── package-lock.json             # NPM lockfile
│   ├── package.json                  # Frontend manifest & scripts
│   ├── README.md                     # Frontend-specific instructions
│   ├── src/                          # Source code
│   │   ├── api.js                    # Fetch helper with credentials: 'include'
│   │   ├── App.jsx                   # Routes + simple route guard
│   │   ├── Auth.jsx                  # Minimal demo auth component
│   │   ├── authClient.js             # Cookie-session auth helpers (login/logout/getUser)
│   │   ├── main.jsx                  # App bootstrap with React Router
│   │   └── pages/                    # Route components
│   │       ├── Home.jsx              # Protected home, calls /authenticated-route
│   │       ├── Login.jsx             # Login page with Google sign-in
│   │       └── OAuthCallback.jsx     # Verifies session after backend redirect
│   └── vite.config.js                # Vite + dev server config

```


## Backend: Key Files and Concepts

- `backend/app/users.py`
  - Implements a cookie-only OAuth backend: `cookie_oauth_auth_backend` using `OAuthCookieTransport` to set an HttpOnly cookie and redirect to the SPA after OAuth success.
  - Uses a database-backed auth strategy (`DatabaseStrategy`) so tokens are persisted and deleted on logout.
  - Exposes `google_oauth_client` (from `httpx-oauth`), the `fastapi_users` instance, and `current_active_user` dependency.

- `backend/app/app.py`
  - Creates the FastAPI app and enables CORS for `http://localhost:5173`.
  - Mounts fastapi-users routers:
    - Cookie login/logout router under `/auth/cookie` using `cookie_oauth_auth_backend`.
    - Register, reset password, verify routers under `/auth`.
    - Users router under `/users`.
    - Google OAuth router under `/auth/google`, using `cookie_oauth_auth_backend` so the callback sets the cookie and redirects to the SPA.
  - Defines `/authenticated-route` as an example protected endpoint using `current_active_user`.

- `backend/app/db.py`
  - Defines `User` and `OAuthAccount` SQLAlchemy models compatible with fastapi-users.
  - Defines an `AccessToken` model and adapter for storing access tokens when using the database auth strategy.
  - Uses a local SQLite DB at `backend/app/test.db` via `sqlite+aiosqlite`.


## Backend: Endpoints You Need

- OAuth (mounted at `/auth/google`):
  - `GET /auth/google/authorize?redirect_url=<SPA URL>` → returns `{ "authorization_url": "…" }`. The SPA redirects the browser to this URL.
  - `GET /auth/google/callback?code=…&state=…` → backend exchanges the code with Google; `OAuthCookieTransport` sets an HttpOnly cookie and responds with `302` to `FRONTEND_URL/oauth-callback`.

- Users:
  - `GET /users/me` → returns the current user. Authenticated via the session cookie (no Authorization header).

- Demo protected route:
  - `GET /authenticated-route` → returns a greeting. Authenticated via the session cookie.

- Cookie:
  - `POST /auth/cookie/logout` → invalidates the session by deleting the corresponding token in the database.

Notes:
- CORS is configured to allow `http://localhost:5173`.
- `FRONTEND_URL` controls where the backend redirects after OAuth success.


## Frontend: Wiring and Responsibilities

- `src/api.js`
  - Exports `API_URL` from `import.meta.env.VITE_API_URL` (default `http://localhost:8000`).
  - Exports `apiFetch(path, options)` that uses `credentials: 'include'` so the browser sends the HttpOnly cookie automatically. No Authorization header.

- `src/Auth.jsx`
  - On mount, calls `getUser()` (which calls `GET /users/me`) to show `Welcome, <email>!` or "Login with Google".

- `src/pages/Login.jsx`
  - Checks session by calling `/users/me`. If logged in, prompts to go Home; else shows a “Login with Google” button.

- `src/pages/OAuthCallback.jsx`
  - After redirect from backend, simply verifies the session by calling `/users/me` and navigates to `/`.

- `src/App.jsx`
  - Defines routes: `/login`, `/oauth-callback`, and `/`.
  - Wraps `/` in `RequireAuth`, which calls `/users/me` to check for a valid session and redirects to `/login` if unauthenticated.

- `src/authClient.js`
  - `loginWithGoogle()` calls `GET ${API_URL}/auth/google/authorize?redirect_url=${window.location.origin}/oauth-callback`, expects `{ authorization_url }`, then redirects the browser to it.
  - `getUser()` calls `apiFetch('/users/me')`.
  - `logoutUser()` calls `POST /auth/cookie/logout` and navigates to `/login`.


## User Journey and Network Calls

1. User visits the SPA at `http://localhost:5173/login`.
2. User clicks “Login with Google”. Frontend executes:
   - `GET {API_URL}/auth/google/authorize?redirect_url=http://localhost:5173/oauth-callback` → `{ authorization_url }`.
   - Browser navigates to `authorization_url` (Google).
3. User completes Google authentication. Google redirects to backend:
   - `GET {API_URL}/auth/google/callback?code=…&state=…`.
4. Backend exchanges the code with Google, sets an HttpOnly cookie session, then returns:
   - `302 Location: {FRONTEND_URL}/oauth-callback`.
5. Frontend `OAuthCallback.jsx` verifies the session by calling `GET {API_URL}/users/me` and navigates to `/`.
6. The home page (`/`) is protected by `RequireAuth` which calls `/users/me` to ensure the session is valid.
7. `Auth` calls `GET {API_URL}/users/me` to display the user’s email.
8. The “Call /authenticated-route” button triggers `GET {API_URL}/authenticated-route` and displays the response.
9. Logout calls `POST {API_URL}/auth/cookie/logout` and returns the user to `/login`.


## Environment Variables and Configuration

Google Cloud Console:
- Authorized JavaScript origins: `http://localhost:5173`
- Authorized redirect URIs: `http://localhost:8000/auth/google/callback`

Backend:
- `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` (required) — from Google Cloud Console.
- `FRONTEND_URL` (optional, default `http://localhost:5173`) — where to redirect after OAuth success.
- `SECURE_COOKIES` (optional, default `false`) — set to `true` in production to enable the Secure flag on cookies.

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
pip install -e ./backend
export GOOGLE_CLIENT_ID=your_id
export GOOGLE_CLIENT_SECRET=your_secret
# optionally: export FRONTEND_URL=http://localhost:5173
# optionally (prod-like): export SECURE_COOKIES=true
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

- This implementation uses an HttpOnly cookie session for authentication. The SPA never handles tokens directly.
- Alternative: SPA PKCE flow (frontend receives code and exchanges with backend) — useful for pure SPA architectures or specific gateway patterns, but not necessary here.
- If you switch to a bearer-token SPA model, you’d re-introduce storing tokens and Authorization headers; that is less secure by default than HttpOnly cookies.

## Production notes

- Cookies
  - Set `SECURE_COOKIES=true` so cookies are only sent over HTTPS.
  - For cross-site setups (different frontend/backend domains), set cookie `SameSite=None` and ensure HTTPS; also set an appropriate cookie domain (e.g., `.example.com`) so the browser sends it to the API.
  - Consider CSRF protection for state-changing endpoints when using cookies.
- CORS
  - Ensure `allow_credentials=True` is set server-side and origins are restricted to your exact frontend origin(s).
- Google OAuth
  - Configure production Authorized redirect URI (e.g., `https://api.example.com/auth/google/callback`) and JavaScript origin (e.g., `https://app.example.com`).
  - Keep client secret server-side only.
- Proxies/Deployments
  - Run behind HTTPS. If behind a proxy (NGINX, Cloudflare), ensure forwarded headers are preserved so URLs are generated correctly.


## Extending This Template

- Add GitHub OAuth by mounting another `get_oauth_router` with a GitHub client.
- Add password-based auth by using the `/auth/jwt/login` endpoint in the UI.
- Replace SQLite with Postgres and introduce Alembic migrations.
- Harden CORS and configure domain-specific `FRONTEND_URL` for deployment.


## Troubleshooting

- “Landing on backend JSON page at `/auth/google/callback`” → ensure the OAuth router uses the cookie-based backend (we use `cookie_oauth_auth_backend` with `OAuthCookieTransport` in `app.py`).
- SPA doesn’t see the user → ensure requests use `credentials: 'include'` (see `src/api.js`) and your cookie domain/SameSite are set correctly for your environment.
- 401 on protected routes → session cookie missing or expired; re-login.


## References

- fastapi-users: https://github.com/fastapi-users/fastapi-users
- httpx-oauth: https://github.com/terrycain/httpx-oauth
- React Router: https://reactrouter.com/
