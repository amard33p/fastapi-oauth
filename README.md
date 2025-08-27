# FastAPI + React OAuth (fastapi-users)

This project demonstrates a minimal, end-to-end OAuth login with Google using FastAPI on the backend and a React + Vite SPA on the frontend. It builds on top of fastapi-users and shows how to wire a redirect-based OAuth flow to an SPA using secure HttpOnly cookies (no tokens in URLs or localStorage).

The goal of this README is to be explicit enough that another LLM (or developer) can recreate the project and wiring by following the descriptions below.


## Project Structure

```
fastapi-oauth/
├─ backend/
│  ├─ app/
│  │  ├─ app.py            # FastAPI app, routers, CORS, demo protected route
│  │  ├─ users.py          # fastapi-users setup + cookie auth + OAuth cookie transport
│  │  ├─ db.py             # SQLAlchemy models + async engine/session helpers
│  │  ├─ schemas.py        # fastapi-users schemas used by routers
│  │  └─ __init__.py
│  ├─ main.py              # Uvicorn entrypoint for backend
│  └─ requirements.txt
│
├─ frontend/
│  ├─ src/
│  │  ├─ api.js            # API URL + fetch helper (credentials: 'include'; no Authorization header)
│  │  ├─ Auth.jsx          # Small widget that shows login/logout or user email
│  │  ├─ App.jsx           # Router + RequireAuth wrapper
│  │  └─ pages/
│  │     ├─ Login.jsx          # “Login with Google” entrypoint
│  │     ├─ OAuthCallback.jsx  # Handles redirect and verifies session via cookie
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
  - Configures fastapi-users with a `JWTStrategy` and both bearer and cookie auth backends.
  - Implements `OAuthCookieTransport` (subclass of `CookieTransport`) to set an HttpOnly cookie and then redirect the browser to the SPA after OAuth success.
  - Provides `cookie_auth_backend` and `cookie_oauth_auth_backend` used by the app.
  - Exposes `google_oauth_client` (from `httpx-oauth`), the `fastapi_users` instance, and `current_active_user` dependency.

- `backend/app/app.py`
  - Creates the FastAPI app and enables CORS for `http://localhost:5173`.
  - Mounts fastapi-users routers:
    - JWT login router under `/auth/jwt` (optional, not used in this cookie flow).
    - Cookie login/logout router under `/auth/cookie`.
    - Register, reset password, verify routers under `/auth`.
    - Users router under `/users`.
    - Google OAuth router under `/auth/google`, using `cookie_oauth_auth_backend` so the callback sets the cookie and redirects to the SPA.
  - Defines `/authenticated-route` as an example protected endpoint using `current_active_user`.

- `backend/app/db.py`
  - Defines `User` and `OAuthAccount` SQLAlchemy models compatible with fastapi-users.
  - Uses a local SQLite DB at `backend/app/test.db` via `sqlite+aiosqlite`.


## Backend: Endpoints You Need

- OAuth (mounted at `/auth/google`):
  - `GET /auth/google/authorize?redirect_url=<SPA URL>` → returns `{ "authorization_url": "…" }`. The SPA redirects the browser to this URL.
  - `GET /auth/google/callback?code=…&state=…` → backend exchanges the code with Google; `OAuthCookieTransport` sets an HttpOnly cookie and responds with `302` to `FRONTEND_URL/oauth-callback`.

- Users:
  - `GET /users/me` → returns the current user. Authenticated via the session cookie (no Authorization header).

- Demo protected route:
  - `GET /authenticated-route` → returns a greeting. Authenticated via the session cookie.

- JWT (optional, not used by the OAuth button):
  - `POST /auth/jwt/login` and `POST /auth/jwt/logout` are available if you later add credentials-based auth.

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

Backend:
- `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` (required) — from Google Cloud Console.
  - Authorized redirect URI: `http://localhost:8000/auth/google/callback`
  - Authorized JavaScript origin: `http://localhost:5173`
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
pip install -r backend/requirements.txt
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

- “Landing on backend JSON page at `/auth/google/callback`” → ensure the OAuth router uses the redirect-aware backend (we use `oauth_redirect_auth_backend` in `app.py`).
- SPA doesn’t see the user → ensure `Authorization` header is set in `api.js` and token exists in `localStorage`.
- 401 on protected routes → token missing or expired; re-login.


## References

- fastapi-users: https://github.com/fastapi-users/fastapi-users
- httpx-oauth: https://github.com/terrycain/httpx-oauth
- React Router: https://reactrouter.com/
