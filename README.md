# Morning

Interactive learning prototype for the standalone Morning engineering operations product.

This prototype exists to make the product concrete enough to interact with, criticize and change before the production architecture and domain contract are frozen.

## What is included

- Management overview with fundamental engineering KPIs
- KPI drill-downs to contributing categories and source activities
- Structured shift-capture prototype
- 24-hour historical report list and frozen-report viewer
- Machine utilization and operational history
- Personnel utilization with assigned, blocked and unallocated time
- Reliability views for repeat failures, repair effectiveness and bad actors
- Responsive desktop/mobile experience
- Seeded TMM-style demo data only

## Product principles represented

- Capture once; use many times.
- Reports and KPIs are views of the same structured operational truth.
- Standing is not automatically engineering downtime.
- Personnel utilization is a resource-planning measure, not a performance score.
- Fundamental KPIs must be explainable down to source evidence.
- Deterministic calculations remain authoritative where the truth can be calculated.
- Published 24-hour reports are treated as frozen historical snapshots.

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
