# FastAPI + React OAuth (fastapi-users)

This project demonstrates a minimal, end-to-end OAuth login with Google using FastAPI on the backend and a React + Vite SPA on the frontend. It builds on top of fastapi-users and shows how to wire a redirect-based OAuth flow to an SPA using secure HttpOnly cookies (no tokens in URLs or localStorage).

## Project Structure

```
├── backend
│   ├── app
│   │   ├── auth                             # fastapi-users auth setup
│   │   │   ├── auth_backend.py              # Cookie-based auth backend wiring
│   │   │   ├── auth_transport.py            # OAuthCookieTransport (cookie name, flags)
│   │   │   ├── oauth_client.py              # Google OAuth client
│   │   │   ├── token_strategy.py            # DB-backed token strategy provider
│   │   │   ├── user_manager.py              # fastapi-users UserManager
│   │   │   └── user_setup.py                # fastapi_users instance and deps
│   │   ├── config.py                        # Pydantic Settings; loads env from backend/demo.env
│   │   ├── crud_user.py                     # get_or_create_user, issue_access_token helpers
│   │   ├── db.py                            # SQLAlchemy models + engine/session + create_db_and_tables()
│   │   ├── main.py                          # FastAPI app, CORS, includes routers
│   │   ├── routes                           # API routers
│   │   │   ├── auth.py                      # /auth cookie login + Google OAuth routers
│   │   │   ├── main.py                      # Aggregates routers; defines /authenticated-route
│   │   │   └── users.py                     # /users routes (get current user, etc.)
│   │   ├── schemas.py                       # Pydantic user schemas (read/create/update)
│   │   └── test.db                          # Local SQLite DB (auto-created for dev/tests)
│   ├── demo.env                             # Backend env file consumed by app/config.py
│   ├── main.py                              # Uvicorn entrypoint (imports app from app/main.py)
│   ├── pyproject.toml                       # Backend deps + dev-deps (pytest, ruff)
│   ├── tests                                # Test suite
│   │   ├── conftest.py                      # async_session, client, auth_client, convenience clients
│   │   ├── repositories
│   │   │   └── test_user_repository.py      # Repository/CRUD tests
│   │   └── routes
│   │       └── test_authenticated_route.py  # Route tests for /authenticated-route
│   └── uv.lock                              # uv lockfile
├── frontend
│   ├── biome.json                           # Frontend linter config
│   ├── index.html                           # Vite HTML entrypoint
│   ├── openapi-ts.config.ts                 # OpenAPI TS generator config
│   ├── openapi.json                         # Exported backend OpenAPI spec
│   ├── package-lock.json                    # NPM lockfile
│   ├── package.json                         # Frontend manifest & scripts
│   ├── README.md                            # Frontend instructions
│   ├── src
│   │   ├── App.jsx                          # Routes + simple route guard
│   │   ├── Auth.jsx                         # Minimal demo auth widget
│   │   ├── client                           # Generated OpenAPI SDK
│   │   │   ├── core                         # Generator internals
│   │   │   ├── index.ts                     # SDK bootstrap/config
│   │   │   ├── sdk.gen.ts                   # Generated service methods
│   │   │   └── types.gen.ts                 # Generated types
│   │   ├── main.jsx                         # React bootstrap
│   │   └── pages
│   │       ├── Home.jsx                     # Protected home, calls /authenticated-route
│   │       ├── Login.jsx                    # Login page (starts OAuth)
│   │       └── OAuthCallback.jsx            # Verifies session after backend redirect
│   └── vite.config.js                       # Vite + dev server config
├── generate_client.sh                       # Script to (re)generate frontend SDK
```


## Backend

- OAuth (mounted at `/auth/google`):
  - `GET /auth/google/authorize` → returns `{ "authorization_url": "…" }`. The SPA redirects the browser to this URL.
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


## Frontend

- `src/client/`
  - Generated SDK via `@hey-api/openapi-ts`. Use services like `AuthService`, `UsersService`, `DefaultService`.
  - In `src/main.jsx`, configure `OpenAPI.BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'` and `OpenAPI.WITH_CREDENTIALS = true` so axios sends cookies.

- `src/Auth.jsx`
  - On mount, calls `UsersService.currentUserUsersMeGet()` to show `Welcome, <email>!` or "Login with Google".

- `src/pages/Login.jsx`
  - Checks session by calling `UsersService.currentUserUsersMeGet()`. If logged in, prompts to go Home; else shows a “Login with Google” button.

- `src/pages/OAuthCallback.jsx`
  - After redirect from backend, verifies the session by calling `UsersService.currentUserUsersMeGet()` and navigates to `/`.

- `src/App.jsx`
  - Defines routes: `/login`, `/oauth-callback`, and `/`.
  - Wraps `/` in `RequireAuth`, which calls `UsersService.currentUserUsersMeGet()` to check for a valid session and redirects to `/login` if unauthenticated.

- Login and logout
  - Start login by calling `AuthService.oauthGoogleCookieOauthAuthorizeAuthGoogleAuthorizeGet()` and redirect to `authorization_url`.
  - Logout by calling `AuthService.cookieOauthLogoutAuthCookieLogoutPost()` and then navigate to `/login`.


## User Journey and Network Calls

1. User visits the SPA at `http://localhost:5173/login`.
2. User clicks “Login with Google”. Frontend executes:
   - `GET {API_URL}/auth/google/authorize` → `{ authorization_url }`.
   - Browser navigates to `authorization_url` (Google).
3. User completes Google authentication. Google redirects to backend:
   - `GET {API_URL}/auth/google/callback?code=…&state=…`.
4. Backend exchanges the code with Google, sets an HttpOnly cookie session, then returns:
   - `302 Location: {FRONTEND_URL}/oauth-callback`.
5. Frontend `OAuthCallback.jsx` verifies the session by calling `UsersService.currentUserUsersMeGet()` and navigates to `/`.
6. The home page (`/`) is protected by `RequireAuth` which calls `UsersService.currentUserUsersMeGet()` to ensure the session is valid.
7. `Auth` calls `UsersService.currentUserUsersMeGet()` to display the user’s email.
8. The “Call /authenticated-route” button uses `DefaultService.authenticatedRouteAuthenticatedRouteGet()` and displays the response.
9. Logout calls `AuthService.cookieOauthLogoutAuthCookieLogoutPost()` and returns the user to `/login`.


## Environment Variables and Configuration

Google Cloud Console:
- Authorized JavaScript origins: `http://localhost:5173`
- Authorized redirect URIs: `http://localhost:8000/auth/google/callback`

Backend:
- `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` (required) — from Google Cloud Console.
- `FRONTEND_URL` (optional, default `http://localhost:5173`) — where to redirect after OAuth success.
- `SECURE_COOKIES` (optional, default `false`) — set to `true` in production to enable the Secure flag on cookies.

Frontend:
- `VITE_API_URL` (optional, default `http://localhost:8000`) — the backend base URL used to configure the generated SDK in `src/main.jsx`.

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
- SPA doesn’t see the user → ensure the SDK is configured with `OpenAPI.WITH_CREDENTIALS = true` in `src/main.jsx` and your cookie domain/SameSite are set correctly for your environment.
- 401 on protected routes → session cookie missing or expired; re-login.


## References

- fastapi-users: https://github.com/fastapi-users/fastapi-users
- https://github.com/PeterTakahashi/service-base-auth-fastapi/
