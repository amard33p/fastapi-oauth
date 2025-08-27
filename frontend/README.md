# FastAPI + Google OAuth POC (React/Vite)

This SPA demonstrates logging in with Google via your FastAPI Users backend and attaching the returned JWT to subsequent API requests.

## Prereqs
- Backend running at http://localhost:8000 (see `main.py`).
- Google OAuth Client configured with Authorized redirect URIs including:
  - http://localhost:8000/auth/google/callback (required)
  - Optionally: http://localhost:5173/oauth-callback (only needed if your backend redirects to frontend after callback)
- Environment vars for backend: `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`.

## Frontend setup
```bash
# From repository root
cd frontend
npm install
npm run dev
```
Open http://localhost:5173/login

## Flow
1. Click "Login with Google".
2. App calls `GET /auth/google/authorize?redirect_url=http://localhost:5173/oauth-callback` to get the provider URL and redirects the browser there.
3. After Google login, one of two things happens depending on your fastapi-users version:
   - Backend responds with JSON at `/auth/google/callback` and then redirects to `/oauth-callback` with `access_token` in query (handled automatically).
   - Or Google redirects back to `/oauth-callback?code=...&state=...` (frontend then calls `/auth/google/callback?code=...&state=...` to exchange code for token).
4. The token is stored in `localStorage` and all API calls use `Authorization: Bearer <token>` via `apiFetch`.

## Config
Create `.env` in `frontend/` if the API URL differs:
```
VITE_API_URL=http://localhost:8000
```

## Test
- Visit Home and click "Call /authenticated-route" to verify the token.
