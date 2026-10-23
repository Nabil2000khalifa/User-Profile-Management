# ADR-001: Modular Monolith

- **Status**: proposed
- **Date**: 2026-10-23
- **Deciders**: Project maintainers

## Context

The project is a local administrator-only profile-management application with
one React client, one Python backend, and MySQL. The current repository has no
application implementation. The design must keep security-sensitive rules in
one backend while remaining straightforward to test and evolve.

The local machine currently has MySQL Server 8.0.46, while the project
requirement is MySQL 8.4 LTS. This decision does not authorize a database
upgrade and does not claim compatibility testing.

## Decision

Use a modular monolith: React communicates with versioned FastAPI endpoints,
and only FastAPI accesses MySQL. Organize backend code by API, services,
schemas, models, database/configuration, and migrations.

## Options considered

1. **Modular monolith** - Keeps deployment and local development simple while
   preserving boundaries for validation, authorization, and data access.
2. **Microservices** - Rejected as unnecessary operational complexity for the
   current scope and local-only phase.
3. **Do nothing** - Rejected because unstructured placement would scatter
   security and business rules.

## Consequences

- Positive: one deployable application, clear trust boundary, simple local
  testing, and a path to later extraction if justified.
- Negative / trade-offs: the backend remains one process and requires discipline
  to preserve module boundaries.
- What becomes harder later: independently scaling or deploying subsystems.

## Revisit when

Reconsider if independently scaling a subsystem, separate team ownership, or a
validated operational requirement makes a modular monolith insufficient.

## Unresolved decisions

- The supported local MySQL version must be confirmed before migrations.
- The dependency bootstrap and lockfile toolchain must be selected and run.
- Session storage and CSRF details require a security design before auth work.
