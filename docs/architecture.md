# Initial Architecture

## Decision

The application will be a local modular monolith. A React frontend will
communicate with a FastAPI backend over versioned HTTP APIs. FastAPI is the
only application layer that accesses MySQL.

The backend will use SQLAlchemy 2.x for database access and Alembic for all
schema changes. Route handlers will remain thin. Responsibilities will be
separated into API boundaries, services, schemas, models, repositories where
useful, database lifecycle code, and centralized configuration.

The frontend will own UI state, accessibility, and client-side validation
aligned with the API contract. The backend remains authoritative for
authorization, validation, country-city rules, persistence, and uniqueness.

## Explicit non-goals for the current phase

This project will not introduce microservices, deployment configuration, cloud
services, Redis, background workers, or production hosting. Authentication,
profile CRUD, and frontend screens are deferred to later phases.

## Database version status

The project requirement is MySQL 8.4 LTS. The local environment is running
MySQL Server 8.4.13. The initial Alembic migration was applied successfully to
the empty `user_profile_management` database using the existing
`profile_app` account. No MySQL users, permissions, server configuration, or
unrelated data were changed.

Phase 2 adds a MySQL-backed `admin_sessions` table. Session cookies contain
opaque random values; only SHA-256 token digests are persisted. Login rotates
existing sessions, state-changing requests require a double-submit CSRF token
bound to the persisted session, and the first administrator is provisioned
through a local interactive command rather than public registration or a
hardcoded credential.

Profile records retain the submitted email for display and store a separate
canonical uniqueness key. The key lowercases all addresses and applies dot,
plus-tag, and `googlemail.com` equivalence rules only to consumer Gmail
addresses. A MySQL unique index enforces the canonical key under concurrency.
Administrator login addresses intentionally retain their existing normalization
semantics.

## Dependency and lockfile status

Direct dependency versions in the initial manifests were checked against the
PyPI and npm registries on 2026-10-23. No packages were installed during Phase
0. The backend uses exact direct requirements in `pyproject.toml`, and the
frontend uses exact direct versions in `package.json`. Project lockfiles must be
generated and committed during the dependency-bootstrap task, after dependency
installation is approved; no lockfile has been fabricated in this phase.

The registry lookup verifies published versions, not full application
compatibility. Compatibility and security audits remain required before use.
