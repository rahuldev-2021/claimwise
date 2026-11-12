# Authentication (JWT + refresh cookie)

Local email/password sign-in with split tokens:

| Piece | Location | Notes |
|-------|----------|--------|
| Access JWT | Frontend memory (`authStore.ts`) | ~15 min, `Authorization: Bearer` |
| Refresh token | HttpOnly cookie `refresh_token`, path `/api/auth/refresh` | ~30 days, rotation + family revocation |

## Prerequisites

- MongoDB running (`MONGODB_URI`)
- `JWT_SECRET` set in `.env` (see `.env.example`)
- On startup, `seed_auth_data()` creates org + bootstrap admin if missing

## Endpoints

- `POST /api/auth/login`
- `POST /api/auth/refresh`
- `POST /api/auth/logout`
- `POST /api/auth/logout-all` (requires access token)
- `GET /api/auth/me`

## Bootstrap admin (change in production)

- Email: `AUTH_BOOTSTRAP_ADMIN_EMAIL` (default `adminuser2021@gmail.com`)
- Password: `AUTH_BOOTSTRAP_ADMIN_PASSWORD`

No OAuth/SSO or MFA in this release.
