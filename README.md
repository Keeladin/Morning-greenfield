# Morning

Interactive learning prototype for the standalone Morning operational reporting product.

This prototype exists to make the product concrete enough to interact with, criticize and change before the production architecture and domain contract are frozen.

## Current prototype

The current implementation is intentionally seeded with **TMM-style engineering data** and therefore remains strongly asset/fleet shaped.

It currently includes:

- Management overview with fundamental engineering KPIs
- KPI drill-downs to contributing categories and source activities
- Structured shift-capture prototype
- 24-hour historical report list and frozen-report viewer
- Machine utilization and operational history
- Personnel utilization with assigned, blocked and unallocated time
- Reliability views for repeat failures, repair effectiveness and bad actors
- Responsive desktop/mobile experience

The current TMM shape is a **prototype boundary, not the intended product boundary**.

## Morning 1.0 validation scopes

Morning 1.0 should be designed and tested against three genuinely different operational scopes:

1. **TMM** — asset-centric engineering operations
2. **Construction** — project/work-package-centric engineering operations
3. **Mining** — production/process-centric operations

The product should support domain-specific workspaces over a shared operational-reporting foundation.

A useful common reporting grammar is:

```text
STATUS
↓
PLAN
↓
ACTUAL
↓
DEVIATIONS
↓
CONSTRAINTS
↓
SAFETY
↓
PRIORITIES
```

Morning should also support a recursive organisational reporting hierarchy so that operational units contribute upward into their parent unit's report/dashboard, eventually producing an appropriate site-level management view.

Information should become more compressed as it moves upward while remaining traceable back to the source activity/evidence.

## Product principles represented

- Capture once; use many times.
- Reports and KPIs are views of the same structured operational truth.
- Morning core models operational reporting rather than assuming every scope revolves around machines.
- Domain-specific presentation is desirable; duplicating the reporting engine per domain is not.
- Standing is not automatically engineering downtime.
- Personnel utilization is a resource-planning measure, not a performance score.
- Fundamental KPIs must be explainable down to source evidence.
- KPI roll-ups must use explicit aggregation rules rather than naive averaging.
- Deterministic calculations remain authoritative where the truth can be calculated.
- Published 24-hour reports are treated as frozen historical snapshots.
- Do not generalise beyond TMM, Construction and Mining until the model earns it.

## Prototype boundary

This is intentionally a frontend learning implementation. It does not claim to be the production backend, database, authentication model, PDF engine or final KPI contract.

Assumptions are deliberately easy to change as the product model matures.

## Run locally

```bash
npm install
npm run dev
```

Production-style build check:

```bash
npm run build
```

## Design references

See `docs/` for the current product direction and greenfield architecture/implementation plan.

The 28 August 2026 decision on multi-scope compatibility and hierarchical reporting is captured in:

- `docs/Morning_Operational_Scopes_and_Hierarchical_Reporting_2026-08-28.md`
