# ADR-000 — Morning extraction classification

**Status:** Accepted  
**Date:** 28 August 2026  
**Decision owner:** Morning

## Context

Morning already has a working functional reference inside `Keeladin/atlas-agent`. The standalone product must extract proven behaviour without carrying Atlas runtime ownership or treating the design-reference frontend currently in this repository as the production implementation.

This ADR turns the extraction contract into a file-level implementation rule so the project does not repeatedly re-litigate what should be preserved, adapted, replaced, or removed.

## Classification

| Reference area | Classification | Standalone treatment |
| --- | --- | --- |
| `atlas_core/morning/models.py` | KEEP / ADAPT | Preserve domain behaviour and dataclass contracts. Remove Atlas wording and extend only where the standalone domain requires it. |
| `atlas_core/morning/shift.py` | KEEP | Port behaviour and tests unchanged. |
| `atlas_core/morning/intervals.py` | KEEP / ADAPT | Preserve deterministic interval arithmetic. Correct downtime terminology before reporting it as a management metric. |
| `atlas_core/morning/runtime.py` | KEEP / ADAPT | Preserve the established supervisor workflow and business rules; inject standalone store/accounts. |
| `atlas_core/morning/aggregate.py` | KEEP / ADAPT | Preserve traceability and deterministic projection behaviour; separate work-duration semantics from true machine-state downtime. |
| `atlas_core/morning/renderers.py` | KEEP | Preserve deterministic report rendering. |
| `atlas_core/morning/controlroom.py` | KEEP | Preserve distinct control-room evidence and deterministic extraction. |
| `atlas_core/morning/pdf_text.py` | KEEP | Port as Morning-owned utility. |
| `atlas_core/morning/teams_workbook.py` | KEEP | Preserve existing deterministic projection/export behaviour. |
| `atlas_core/morning/store.py` | REPLACE IMPLEMENTATION | Keep the public behavioural contract, replace SQLite persistence with PostgreSQL + Alembic. No legacy data migration. |
| `atlas_core/morning/accounts.py` | ADAPT | Preserve credential/approval behaviour, replace `atlas_core.identity` with Morning-owned identity and roles. |
| `atlas_api/morning_auth.py` | ADAPT | Preserve Morning session + CSRF semantics; remove shared Atlas cookie policy/config fallbacks. |
| Supervisor section of `atlas_api/routes/morning.py` | KEEP / ADAPT | Preserve endpoint behaviour and ownership checks inside standalone routes. |
| Admin section of `atlas_api/routes/morning.py` | ADAPT | Replace Atlas owner-session gate with Morning-owned admin authorization. |
| `companion/src/morning/` | KEEP / ADAPT | This is the production frontend reference. Port the staged workflow, fix known timestamp issue, then extend machine-state capture. |
| `companion/src/screens/MorningAdmin.tsx` | KEEP / ADAPT | Port the existing admin configuration UI and point it at Morning-owned admin auth/routes. |
| `atlas_core/integrations/morning_report.py` | REMOVE | Atlas Work wrapper only; domain/report logic remains inside Morning. |
| `atlas_core/integrations/morning.py` | REMOVE / OPTIONAL IMPORT | Do not carry Atlas capability machinery into Morning. Any useful legacy import can later become a Morning-owned import adapter. |
| `atlas_morning/` | OPTIONAL IMPORT REFERENCE | Not the standalone runtime. Reuse only proven import/parsing behaviour if a concrete import path is required. |
| `atlas_mobile/` | SELECTIVE REFERENCE | Do not replace the staged workflow. Reuse only machine-state vocabulary or offline patterns that earn their place. |
| Current repository `src/` fake-data prototype | REPLACE | Design-reference only. Remove when the real frontend is ported. |

## Non-negotiable boundaries

1. Morning launches with a fresh database. Migrate the product, not the data.
2. Morning has no runtime or database dependency on Atlas.
3. The staged supervisor workflow remains the first-release functional reference.
4. Work intervals are not automatically downtime.
5. Machine state is explicit truth and is modelled separately from engineering work intervals.
6. Reports and KPIs are projections of authoritative typed source records.
7. TMM is the first production scope. Construction and Mining validate seams without blocking rollout.

## Consequences

The extraction is primarily a persistence/auth ownership change plus targeted domain extension, not a clean-room product rewrite. Existing tests from the reference repository should move with the behaviour they protect wherever practical.
