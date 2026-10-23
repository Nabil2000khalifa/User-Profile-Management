# Frontend

This directory contains the React, TypeScript, Vite, and Tailwind CSS frontend.

Planned boundaries:

- `src/api/` for typed backend API calls
- `src/components/` for reusable accessible UI
- `src/features/` for auth, locations, and profile-management features
- `src/lib/` for small framework-neutral utilities
- `src/schemas/` for frontend boundary validation
- `tests/` for Vitest and React Testing Library tests

The frontend will communicate with FastAPI only. It will not connect directly
to MySQL.

## Local setup

Use Node.js 22 or newer. From this directory:

```powershell
npm install
npm run dev
```

The Vite development server defaults to `http://localhost:5173`. The frontend
uses `http://localhost:8000` as its local backend default. Set
`VITE_API_BASE_URL` in a local `.env` file when using another API origin, for
example:

```text
VITE_API_BASE_URL=http://localhost:8000
```

Run the checks with:

```powershell
npm run test
npm run typecheck
npm run lint
npm run build
```

The frontend uses the backend's HttpOnly session cookie. It does not store
session or CSRF tokens in local storage; state-changing requests read the
CSRF cookie and send it in `X-CSRF-Token`.
