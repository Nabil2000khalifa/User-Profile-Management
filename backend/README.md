# Backend

This directory will contain the FastAPI modular-monolith backend.

Planned boundaries:

- `app/api/` for HTTP routes and dependency wiring
- `app/core/` for settings, authentication, and security utilities
- `app/db/` for SQLAlchemy engine and session lifecycle
- `app/models/` for SQLAlchemy models
- `app/repositories/` for database queries where an abstraction is justified
- `app/schemas/` for Pydantic request and response schemas
- `app/services/` for business rules and use cases
- `migrations/` for Alembic migrations
- `tests/` for backend tests

## Database foundation

The backend loads local settings from `backend/.env`. Copy
`backend/.env.example` to `backend/.env` and replace only the local placeholder
values. The real `.env` file is ignored by Git and must never be committed.

The expected local database is `user_profile_management`, accessed through the
least-privilege application account `profile_app`. This foundation does not
create users, grant permissions, change server configuration, or alter existing
databases.

Run migrations from this directory after configuring a local MySQL 8.4
environment:

```powershell
python -m alembic upgrade head
```

The connectivity endpoint is:

```text
GET /api/v1/health/database
```

It returns only `{"status":"ok"}` or a `503` response with
`{"status":"unavailable"}`. It never returns connection details.

The migration targets MySQL 8.4 and has been applied to the local MySQL Server
8.4.13 database `user_profile_management` using the existing `profile_app`
account. No users, permissions, server configuration, or unrelated data were
changed.

## Authentication and profiles

Run the one-time first-admin provisioning command locally after applying
migrations. It prompts for the password and refuses to add an admin if any
admin already exists:

```powershell
python -m app.cli.provision_admin admin@example.com
```

To change an existing administrator's email, run this command and confirm the
change explicitly when prompted:

```powershell
python -m app.cli.change_admin_email
```

The command normalizes and validates both email addresses, preserves the
administrator ID, password hash, and other fields, rejects an email already
used by another administrator, and records an audit event without storing
either email address or other sensitive data in the event metadata.

To change an existing administrator's password, run:

```powershell
python -m app.cli.change_admin_password
```

The command prompts for the administrator email, current password, new
password, and new-password confirmation. It verifies the current Argon2id
password hash, updates only the existing password hash, and records a safe
audit event without storing passwords or password-derived values.

The authentication API is:

- `POST /api/v1/auth/login`
- `POST /api/v1/auth/logout`
- `GET /api/v1/auth/me`

Successful login rotates all existing sessions for that admin and sets an
opaque, `HttpOnly` session cookie plus a separate CSRF cookie. State-changing
authenticated requests must send the CSRF value in `X-CSRF-Token`. Local
development cookies are not marked `Secure`; non-local environments are.
Sessions expire after `SESSION_TTL_HOURS` and are stored as token hashes in
MySQL.

Login throttling is process-local and configured by
`LOGIN_MAX_ATTEMPTS`/`LOGIN_WINDOW_SECONDS`. This is sufficient for the current
single-process local phase; distributed deployments would require a shared
rate-limit store.

Profile endpoints:

- `POST /api/v1/profiles`
- `GET /api/v1/profiles?q=...&page=1&page_size=20`
- `GET /api/v1/profiles/{id}`
- `GET /api/v1/locations/countries`
- `GET /api/v1/locations/cities?country=US`

All profile and location endpoints require an authenticated admin. Profile
creation validates dates, country-city combinations, and returns a field-level
`409 Conflict` error for duplicate normalized email addresses.
Dates of birth must be on or after `1900-01-01` and cannot be in the future.

## Profile email canonicalization

Profile emails retain the submitted trimmed display address in `email` and use
`canonical_email` for uniqueness. All addresses are lowercased. For consumer
`gmail.com` and `googlemail.com` addresses, dots in the local part are removed,
the `+tag` suffix is ignored, and `googlemail.com` is canonicalized to
`gmail.com`. These Gmail rules are not applied to other providers. For example,
`jane.doe+team@gmail.com` conflicts with `janedoe@gmail.com`, while
`khalifanabil@gmail.com` and `nabilkhalifa@gmail.com` remain different.

Before applying the canonical-email migration to an existing database, run:

```powershell
python -m app.cli.check_profile_email_collisions
python -m alembic upgrade head
```

The diagnostic reports profile IDs requiring manual review and never merges,
deletes, or rewrites records. The migration refuses to create the canonical
unique index when collisions exist. Administrator login email semantics remain
unchanged.
