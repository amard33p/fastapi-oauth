# FastAPI + Google OAuth POC (React/Vite)

This SPA demonstrates logging in with Google via your FastAPI Users backend using a secure HttpOnly cookie session. No tokens are stored in localStorage and no Authorization header is used; requests send credentials via the browser automatically.

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
2. App calls `GET /auth/google/authorize` (via generated SDK) to get the provider URL and redirects the browser there.
3. After Google login, Google redirects to backend `/auth/google/callback?code=...&state=...`. The backend exchanges the code with Google, sets an HttpOnly cookie, then redirects the browser to `/oauth-callback`.
4. The SPA’s `/oauth-callback` page calls `GET /users/me` to verify the session, then navigates to `/`.
5. All subsequent API calls use `credentials: 'include'` so the cookie authenticates requests.

## Config
Create `.env` in `frontend/` if the API URL differs:
```
VITE_API_URL=http://localhost:8000
```

## Notes
- Generated SDK is in `src/client/`. `OpenAPI` is configured in `src/main.jsx` using `VITE_API_URL` and `WITH_CREDENTIALS=true` to send cookies.
- Logout triggers `POST /auth/cookie/logout` using `AuthService.cookieOauthLogoutAuthCookieLogoutPost()` and then redirects back to `/login`.
- Route protection calls `GET /users/me` via `UsersService.currentUserUsersMeGet()` (see `src/App.jsx`).

## Test
- Visit Home and click "Call /authenticated-route" to verify the token.
