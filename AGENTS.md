# AGENTS.md — User Profile Management System

These instructions apply to the entire repository and should guide GitHub Copilot and other coding agents.

## 1. Project Goal and Scope

Build a secure, administrator-only website to create and search user profiles.

**Current phase: local development only.** Do not set up hosting, production infrastructure, deployment pipelines, domains, or cloud services unless the user explicitly requests them.

### Required functionality

- Admin login and logout.
- Authenticated access to the profile management application and protected backend endpoints.
- Create a profile with:
  - First name
  - Last name
  - Date of birth
  - Email address
  - Country
  - City
- All profile fields are mandatory.
- Validate email format in the frontend and backend.
- Country choices are limited to `US` and `IN`.
- The city dropdown dynamically shows exactly three approved cities for the selected country.
- Changing the country clears the current city selection.
- The backend independently validates each country-city combination.
- Save profiles in MySQL.
- Show saved profiles in a table/grid.
- Search by first name or last name.
- Implement server-side pagination and return total record information.
- **Profile email addresses must be unique, case-insensitively.**
- Show field-level validation and useful loading, empty, success, and error states.
- Add appropriate audit logging and security tests.

### Initial city configuration

Use this proposed initial configuration until the client confirms otherwise:

- US: New York, Los Angeles, Chicago
- IN: Mumbai, Delhi, Ahmedabad

Keep this configuration easy to update. Do not scatter country/city rules across UI components and backend handlers.

### Email uniqueness rules

- Normalize email addresses consistently before validation and persistence (at minimum trim surrounding whitespace and lowercase the address according to the project's documented policy).
- Enforce uniqueness at the database level with a MySQL unique constraint/index on the normalized email value.
- Do not rely on a pre-insert lookup alone; concurrent requests can race.
- Handle unique-constraint violations and return HTTP `409 Conflict` with a safe, field-specific message.
- The frontend should display duplicate-email errors beside the email field.
- Profile email uniqueness is separate from admin login email uniqueness. Do not impose cross-table uniqueness unless explicitly requested.

## 2. Approved Technology Stack

Keep this stack unless the user approves a change.

### Frontend

- React
- TypeScript
- Vite
- Tailwind CSS
- React Hook Form
- Zod
- TanStack Table for table and pagination UI

### Backend

- Python
- FastAPI
- Pydantic
- SQLAlchemy 2.x
- Alembic
- Argon2id for admin password hashing

### Database

- MySQL 8.4 LTS
- Foreign keys, unique constraints, transactions, and indexes where justified

### Quality and testing

- Pytest for backend tests
- Vitest and React Testing Library for frontend tests
- Playwright for end-to-end tests when practical
- Ruff and a suitable TypeScript/ESLint configuration

Before adding or upgrading dependencies, verify their current official documentation, compatibility, maintenance status, and exact APIs. Do not invent package names or APIs.

## 3. Architecture

Use a **modular monolith** with clear boundaries. Do not introduce microservices, Kubernetes, Redis, background workers, or other infrastructure unless an approved requirement justifies them.

Target responsibilities:

- `frontend/`: pages, components, client-side validation, API client, and UI state.
- `backend/app/api/`: HTTP routes, request/response boundaries, and dependency wiring.
- `backend/app/schemas/`: Pydantic request and response schemas.
- `backend/app/services/`: business rules and use cases.
- `backend/app/repositories/`: database queries where a repository abstraction adds value.
- `backend/app/models/`: SQLAlchemy models.
- `backend/app/db/`: database engine, session lifecycle, and database configuration.
- `backend/app/core/`: settings, authentication, security utilities, and common exceptions.
- `backend/migrations/`: Alembic migrations.
- `backend/tests/` and frontend test directories: automated tests.
- `docs/`: architecture, API contracts, security choices, and decisions.

Keep route handlers thin. Put business logic in services rather than React components, route handlers, or ORM model definitions. Avoid unnecessary abstractions and duplicated logic.

**All database access must go through the backend.** Never connect to MySQL from browser code.

## 4. Initial Data Model

Start with these conceptual tables, refining types and constraints during design:

### `admins`

- `id` primary key
- normalized unique login email
- password hash
- active/disabled status
- created, updated, and last-login timestamps as appropriate

### `user_profiles`

- `id` primary key
- first name
- last name
- date of birth (`DATE`, not a timestamp)
- normalized email with unique constraint
- country code (`US` or `IN`)
- city
- `created_by` foreign key to `admins`
- created and updated timestamps

### `audit_logs`

- `id` primary key
- nullable or required admin reference according to event type
- action
- entity type and entity ID
- timestamp
- request/correlation ID
- minimal safe metadata

Database rules:

- All schema changes must be represented by Alembic migrations.
- Do not rely on manual database changes as the only record of a schema change.
- Do not make any profile field unique other than email without an explicit requirement.
- Use foreign keys and transactions where appropriate.
- Add indexes based on real search and sorting patterns.
- Validate dates and reject dates of birth in the future.
- Avoid exposing internal DB errors, stack traces, or sensitive columns in API responses.
- Do not put passwords, session IDs/tokens, encryption keys, or unnecessary personal information into audit logs.

## 5. API Conventions

Use versioned REST endpoints under `/api/v1`.

Expected endpoints:

- `POST /api/v1/auth/login`
- `POST /api/v1/auth/logout`
- `GET /api/v1/auth/me`
- `GET /api/v1/locations/countries`
- `GET /api/v1/locations/cities?country=IN`
- `POST /api/v1/profiles`
- `GET /api/v1/profiles?q=...&page=1&page_size=20`
- `GET /api/v1/profiles/{id}`

For profile search/listing:

- Search first name OR last name using parameterized queries/SQLAlchemy expressions.
- Use deterministic ordering.
- Default page size: 20; maximum page size: 100 unless an approved requirement changes this.
- Return a documented response containing `items`, `page`, `page_size`, `total`, and `total_pages`.
- Filter and paginate in the backend/database; never retrieve all records simply to paginate in the browser.
- Use suitable HTTP statuses:
  - `401` for unauthenticated requests
  - `403` for authenticated users without permission
  - `409` for duplicate normalized profile email
  - `422` or another consistently documented `4xx` status for invalid input
- Return safe, consistent error schemas and do not leak internal exception details.

## 6. Authentication and Security

Security decisions must be implemented and tested on the backend. Frontend route guards improve navigation but are not authorization controls.

- Use Argon2id for admin password hashes. Never store plaintext or reversibly encrypted passwords.
- Prefer server-managed sessions with cryptographically random, opaque session IDs in `HttpOnly` cookies.
- Use `Secure` cookies over HTTPS and appropriate `SameSite` settings. Keep local-development settings explicitly documented without weakening production-safe defaults.
- Implement logout, session expiry, session rotation after login, login throttling/rate limiting, and authorization checks on every protected endpoint.
- If using cookie authentication, implement and test CSRF defenses for state-changing requests.
- Configure CORS only for the required local frontend origin. Do not use wildcard origins with credentialed requests.
- Keep secrets in environment variables or ignored local environment files. Commit only a safe `.env.example`.
- Do not use the MySQL root account from the application; use a least-privilege application user.
- Validate inputs with Pydantic and business rules, even if the frontend also validates with Zod.
- Return safe error messages and do not expose tracebacks to users.
- Use vetted cryptographic libraries. Never create custom cryptographic algorithms or confuse password hashing with encryption.
- Treat personal-data encryption as a separate requirement from password hashing. Before implementing field-level encryption, document which fields must be encrypted and how that affects search and uniqueness. If required, use authenticated encryption such as AES-GCM through a vetted library and store/manage keys separately from the database.
- Audit security-relevant actions such as login success/failure and profile creation. Restrict log access and keep logged data minimal.
- Do not claim the application is secure just because tests or scanners pass.

## 7. Frontend Validation and Accessibility

- Use semantic HTML, associated labels, keyboard navigation, visible focus, and accessible validation messaging.
- Show validation errors near their respective fields.
- Keep client-side validation aligned with the API contract, but treat the backend as authoritative.
- Reset the city selection when country changes.
- Disable or otherwise guard against repeated form submission while saving.
- Map a `409` duplicate-email response to the email field.
- Preserve entered values after safe, recoverable request failures.
- Handle loading, empty results, network errors, API validation errors, and success states.
- Keep components focused and typed. Avoid `any` unless it is justified and tightly scoped.
- Never put secrets or authoritative access-control rules in frontend code.

## 8. Mandatory Engineering Skills Repository

The user maintains this skills repository:

https://github.com/Nabil2000khalifa/engineering-skills

For this project, `engineering-skills/` is a separate local Git checkout and is
ignored by the application repository. It must be available locally when its
guidance or scripts are needed. Contributors who do not have the checkout
should clone it separately from the URL above; do not copy or vendor it into
this repository.

Apply its guidance for **every coding task**, not just when asked. Read relevant skill files rather than merely mentioning them.

Required skills:

- `skills/engineering-standards/SKILL.md` — required workflow for each coding task.
- `skills/architecture-first/SKILL.md` — non-trivial design or feature work.
- `skills/secure-by-default/SKILL.md` and its security checklist — auth, validation, database access, cryptography, secrets, API boundaries.
- `skills/fresh-knowledge/SKILL.md` — packages, frameworks, APIs, versions, or potentially changed technical guidance.
- `skills/readable-code/SKILL.md` — naming, readability, complexity, and simplification.
- `skills/upgradable-code/SKILL.md` — dependency seams, tests, and reversible changes.

If the skills repository is checked out locally, inspect and use its scripts as applicable:

```bash
python skills/fresh-knowledge/scripts/check_deps.py .
python skills/secure-by-default/scripts/scan_secrets.py .
python skills/readable-code/scripts/complexity_check.py .
```

If the skills repository is not present locally, read its public skill files through available GitHub/docs access. Do not claim to have run its scripts unless they were actually executed. These scanners are heuristics, not replacements for tests, code review, dependency audits, or static analysis.

Do not copy the skills repository into this project unless the user explicitly asks for vendoring it.

## 9. Required Workflow for Non-Trivial Tasks

1. **Understand:** inspect relevant files, existing conventions, dependencies, tests, and Git status before editing.
2. **Refresh knowledge:** verify current official documentation/changelogs for relevant package versions and APIs. If verification is unavailable, state the limitation instead of guessing.
3. **Design first:** state the goal, affected files/modules, boundaries, data flow, failure cases, and tests before coding. For meaningful design decisions, add an ADR under `docs/adr/` using the template from the architecture skill when appropriate.
4. **Implement narrowly:** make the smallest cohesive change. Avoid unrelated rewrites and do not mix refactoring with feature work unless needed.
5. **Secure by default:** validate input, verify authorization, avoid secrets, use vetted dependencies and cryptography, and consider failure and abuse cases.
6. **Test:** add/update tests for success paths, edge cases, and expected failures. Run relevant tests, linting, type checking, and available scanners.
7. **Review:** inspect the diff for unrelated changes, dead code, logging leaks, unused dependencies, migration issues, and missing tests.
8. **Report honestly:** summarize changes and exact checks run, including failures and unverified areas. Never say a test passed or code works unless the relevant check was actually run.

## 10. Working With GitHub Copilot

- Work on one bounded task at a time. Do not generate the whole application in one prompt.
- Define acceptance criteria and test cases before implementing a feature.
- Keep changes small and reviewable.
- Explain non-obvious security or data-model decisions in code or documentation.
- Review generated diffs and run tests before accepting generated code.
- Never include real client personal data, passwords, API keys, database credentials, or other secrets in prompts.
- If a requested task conflicts with this architecture or the acceptance criteria, explain the conflict before making a major change.
- Prefer maintainable, straightforward code over clever abstractions or unnecessary dependencies.

## 11. Out of Scope Unless Explicitly Requested

- Deployment, hosting, cloud infrastructure, production setup, or deployment CI/CD.
- Microservices, Kubernetes, Redis, background workers, and other unneeded infrastructure.
- Public user registration.
- Profile editing, deletion, CSV export, password reset, or additional roles unless separately approved.
- Countries or cities beyond the specified list.
- Business rules not confirmed by the user/client.

## 12. Completion Checklist

Before declaring a task complete, verify the applicable items:

- [ ] Acceptance criteria are met.
- [ ] Relevant tests cover successful and failing cases.
- [ ] Server-side validation and authorization are enforced.
- [ ] Duplicate profile emails are rejected case-insensitively at the database level.
- [ ] Database migrations and constraints are correct.
- [ ] No secrets or unnecessary sensitive data were introduced into source code or logs.
- [ ] Relevant lint, type, test, and scanner commands were actually run.
- [ ] Changes are focused, readable, and maintainable.
- [ ] Documentation and API contracts match the implementation.
- [ ] The final report accurately describes what was verified and what remains unverified.
