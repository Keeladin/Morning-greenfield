# Morning — Extraction Contract

**Date:** 28 August 2026  
**Status:** Authoritative implementation contract  
**Product name:** Morning

## 1. Purpose

This document fixes the implementation boundary for moving the proven Morning workflow into an independently deployable production product.

It exists to prevent the project from drifting back into speculative redesign, accidental Atlas coupling, or repeated rediscovery of workflow decisions that already exist in the working implementation.

Where older planning material conflicts with this document, this contract governs the standalone Morning implementation.

## 2. Product identity

The product is named **Morning**.

Development labels are not product names and must not appear in user-facing branding or be allowed to become accidental product identity.

Morning is a standalone operational reporting product for shift-based engineering and mining operations.

## 3. Extraction, not clean-room redesign

The current Morning implementation inside `Keeladin/atlas-agent` is the functional reference implementation.

The standalone product should preserve proven behaviour, workflow, terminology, validation and useful implementation logic while removing Atlas-specific runtime ownership.

The goal is not to recreate Morning from first principles. The goal is to make the Morning that already exists independently deployable and then extend it where the data model genuinely needs strengthening.

## 4. Green launch — no legacy data migration

Morning will launch with a fresh production database.

Existing SQLite data does **not** need to be migrated into the standalone product.

The current implementation is a behavioural and implementation reference, not a historical database that must be preserved.

At cutover, Morning will be configured afresh with the required:

- users;
- roles;
- crews;
- personnel;
- machines;
- shift policy;
- operational configuration.

Production operational history begins at cutover.

> **Migrate the product, not the data.**

This decision removes the requirement to build legacy-row reconciliation, timestamp conversion for historical records, ID preservation or a SQLite-to-PostgreSQL data importer.

## 5. Established supervisor workflow

The production supervisor workflow is already defined:

```text
Start report
    ↓
Attendance
    ↓
Safety
    ↓
Machine activity
    ↓
Other activities
    ↓
Review
    ↓
Submit
```

This staged workflow is the reference behaviour for the first standalone release.

It must not be replaced by an alternative capture paradigm unless operational use provides a concrete reason to do so.

## 6. Existing behaviour to preserve

The extraction should preserve the current Morning semantics for:

- configurable shift policy and timezone;
- day/night shift resolution;
- cross-midnight shift identity;
- deliberate report creation rather than auto-creation on page load;
- supervisor-to-person-to-crew resolution;
- crew identity frozen onto a report when the report starts;
- draft lifecycle;
- abandoned drafts remaining historical but excluded from submitted truth;
- attendance capture;
- Stop & Fix capture and rectification state;
- red/green card records;
- machine work intervals;
- other activities;
- submitted reports becoming immutable through the normal edit path;
- WhatsApp-ready deterministic rendering;
- day + night daily aggregation;
- distinct preservation of supervisor and control-room evidence;
- incomplete/complete expected-input status;
- rendered reports being projections rather than a second source of truth.

## 7. Production architecture

Morning 1.0 should be implemented as a **modular monolith**.

The first production shape is:

```text
Browser / PWA
      ↓
Morning application + API
      ↓
Morning domain/runtime modules
      ↓
PostgreSQL
```

A worker or scheduler may be added only when a real asynchronous workload requires it.

Do not introduce microservices, event sourcing, a generic workflow engine or distributed architecture without a concrete production benefit.

## 8. Persistence

Production persistence is PostgreSQL from day one.

Schema evolution is managed through Alembic migrations.

The existing `MorningStore` behaviour and tests are the reference for the persistence contract, but the standalone product does not need to reproduce SQLite-specific implementation details.

The production schema should include proper relational constraints from the outset, including appropriate:

- primary keys;
- foreign keys;
- uniqueness constraints;
- indexes;
- PostgreSQL boolean types;
- `timestamptz` for real instants.

Because the database launches fresh, no compatibility layer for historical SQLite rows is required.

## 9. Morning-owned identity and authorization

Morning owns its own users, principals, credentials, sessions, roles and authorization.

The current Atlas `IdentityStore` dependency in `MorningAccounts` must be replaced by a Morning-owned identity model.

Existing Morning account semantics should be preserved where useful:

- username/password authentication;
- account approval before supervisor access;
- account-to-person linking;
- supervisor identity used on reports;
- separate session and CSRF protection.

At minimum, standalone authorization must distinguish:

- **admin** — manages configuration, accounts and management/reporting surfaces;
- **supervisor** — captures and submits operational shift reports.

The current Atlas owner-session gate on Morning admin routes must become Morning-owned admin authorization.

## 10. Atlas relationship

Morning must be independently deployable, operable, upgradeable and recoverable without Atlas.

Morning must not:

- import Atlas runtime libraries;
- use an Atlas database as its production store;
- require Atlas authentication;
- require Atlas endpoints;
- require Atlas Work/capability machinery to perform normal Morning functions.

The existing `atlas_core/integrations/morning.py` and `atlas_core/integrations/morning_report.py` are external adapter layers and do not belong inside standalone Morning.

Atlas may later integrate with Morning through a neutral interface such as an API or MCP boundary.

The dependency direction is:

```text
Atlas → Morning
```

not:

```text
Morning → Atlas
```

## 11. Canonical truth and projections

Morning follows the principle:

> **Capture once; derive everything else.**

Canonical truth is the set of authoritative typed operational source records plus their shift/submission/audit semantics.

Reports, summaries, machine history, reliability calculations and KPIs are projections over those records.

Do not create a second competing source of operational truth for reporting.

A unified operational timeline may be provided as a query/view over typed records; it does not require a single polymorphic god table.

## 12. Machine work interval versus machine state

These are separate domain concepts and must remain separate.

### Work interval

A `MachineEvent` records when engineering activity occurred and what work was performed.

Its interval must not automatically be interpreted as machine downtime.

### Machine state

Morning must add an explicit, controlled declaration of how the machine was left / what its operational state was at handover or activity completion.

Machine-state truth is the basis for later continuity, downtime, availability and reliability calculations.

A state carried across a shift boundary must remain distinguishable from a state explicitly declared or confirmed during the new shift.

Do not fabricate confidence when a machine has not been tested or its state is unknown.

## 13. Aggregation terminology correction

The existing interval merge algorithm is useful and should be preserved.

However, current aggregation code names supervisor `MachineEvent` duration as `total_downtime_seconds` even though the event interval represents engineering work time.

Until true state-based downtime exists, this value must be renamed/reframed so Morning does not publish engineering work duration as machine downtime.

The same deterministic interval-merging machinery may later be reused for genuine downtime intervals derived from explicit machine-state history.

## 14. Safety corrections before rollout

The extracted frontend must fix two known issues before controlled rollout:

1. The red/green card add flow exists in model/runtime/API but is not currently reachable through the Safety UI.
2. Stop & Fix client timestamps currently use `toISOString()` and therefore produce UTC rather than the configured local operational time.

The standalone implementation should store real instants consistently and render them in the configured operational timezone.

## 15. Submission, corrections and audit

Normal submission remains an immutable transition: a submitted shift report is no longer edited through the draft mutation path.

A controlled correction/amendment mechanism with audit history is required for production maturity, but it does not block the first controlled rollout.

The later correction path must record consequential changes with actor, time, reason and before/after evidence where appropriate.

Published management reports should remain reproducible/frozen historical snapshots once publication semantics are introduced.

## 16. Operational scopes

TMM is the first production implementation scope.

Construction and Mining are validation scopes, not first-rollout blockers.

They are used to test that Morning's core model is not accidentally hard-coded to a fleet workshop domain.

Morning should preserve clean seams for broader operational scope and organisational hierarchy, but must not build a generic cross-domain configuration or KPI-rollup engine before real second-scope requirements prove the abstraction.

## 17. Hierarchy

Morning should support a simple recursive organisational relationship so operational units can belong to parent units.

The hierarchy seam may be established early because it is cheap and foundational.

Complex cross-domain aggregation rules are deferred until real operational scopes establish how each metric should roll upward.

## 18. Initial extraction classification

### Extract / preserve

- domain models and semantics;
- `MorningRuntime` behaviour;
- shift logic;
- roster/crew semantics;
- safety behaviour;
- machine work-event behaviour;
- daily aggregation structure;
- renderers;
- supervisor API shapes where useful;
- staged supervisor frontend;
- admin CRUD behaviour;
- tests that encode Morning invariants.

### Port with modification

- persistence: SQLite implementation → PostgreSQL + Alembic;
- accounts: Atlas identity → Morning identity;
- admin authorization: Atlas owner gate → Morning admin role;
- machine activity: add explicit machine-state declaration;
- aggregation terminology: work/event duration must not be called downtime;
- frontend safety defects and local-time handling.

### Drop from standalone runtime

- Atlas Work/capability wrappers;
- Atlas-specific identity dependency;
- Atlas owner auth dependency;
- Atlas-specific host/error wording.

## 19. Controlled rollout target

The controlled rollout critical path is:

```text
Production schema
      ↓
Morning identity + roles
      ↓
Extract runtime/API
      ↓
Extract supervisor/admin UI
      ↓
Machine-state capture
      ↓
End-to-end production verification
      ↓
Deploy
```

The first rollout does not require:

- legacy database migration;
- generic multi-scope configuration;
- recursive KPI roll-up engine;
- full reliability dashboard;
- availability/utilization headline metrics;
- MTBF;
- offline-first redesign;
- Atlas integration.

Those can follow once the independent production foundation is operating reliably.

## 20. Definition of standalone completion

Morning is considered successfully extracted when:

1. it starts and operates without Atlas;
2. it owns its PostgreSQL schema and migrations;
3. it owns authentication and authorization;
4. admins can configure machines, people, crews, supervisors and shift policy;
5. supervisors can complete the established staged workflow and submit a shift;
6. submitted records survive restart and remain historical truth;
7. deterministic shift and 24-hour reporting works from Morning-owned data;
8. machine work intervals are not misreported as downtime;
9. explicit machine-state capture exists for future continuity/reliability derivation;
10. backup and restore of the Morning database can be demonstrated;
11. no normal Morning operation requires an Atlas runtime or database.

At that point, further reporting, reliability, KPI, hierarchy and scope work is normal product evolution rather than extraction work.
