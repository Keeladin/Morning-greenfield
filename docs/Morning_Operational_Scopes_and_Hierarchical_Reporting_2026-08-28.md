# Morning — Operational Scopes & Hierarchical Reporting Direction

**Date:** 28 August 2026  
**Status:** Accepted product/architecture direction  
**Purpose:** Define how Morning expands beyond the current TMM-shaped prototype without becoming a generic, shapeless platform.

---

# 1. Decision

Morning 1.0 should be designed and validated against **three operational scopes**:

1. **TMM** — asset-centric engineering operations
2. **Construction** — project/work-package-centric engineering operations
3. **Mining** — production/process-centric operations

These three scopes are deliberately sufficient for the current design phase.

Morning should **not** attempt to model every possible department, support function or enterprise workflow now. The goal is to prove that one coherent operational-reporting core can serve three genuinely different kinds of work without hard-coding TMM assumptions into the product.

The current TMM implementation remains valuable as the first working operational profile, but **TMM is not Morning's product identity**.

---

# 2. Product Definition

Morning should be understood as an **operational reporting layer for an organisational hierarchy**.

It should help each reporting unit answer:

```text
What is our current status?
What was planned?
What actually happened?
Where did we deviate?
What is constraining us?
What matters from a safety perspective?
What requires attention next?
```

Morning then rolls the relevant information upward through the organisation so that each management level receives an increasingly compressed but still traceable view of the operation.

A concise statement is:

> **Morning captures operational truth at the level where work happens and progressively converts it into management information as it moves up the organisational hierarchy.**

---

# 3. The Three v1 Validation Scopes

The three scopes represent different operating models and therefore provide a useful test of whether the architecture is genuinely reusable.

## 3.1 TMM — asset-centric

TMM revolves primarily around machines and the engineering work required to keep them safe, compliant and available.

Typical concerns include:

```text
Fleet
Machine status
Breakdowns
Planned maintenance
Statutory maintenance
Availability
Utilization
Spares
Repeat failures
Artisan loading
Return to service
```

Example operational item:

```text
STC14
Tyre replacement
Machine unavailable
Awaiting tyre
Status: 🟠
```

## 3.2 Construction — project/work-package-centric

Construction revolves around installations, jobs, areas, work packages and commissioning rather than a fleet of machines.

Typical concerns include:

```text
Projects / jobs
Work fronts
Installation packages
Planned vs actual progress
Materials
Dependencies
Constraints
Quality / inspection
Testing
Commissioning
Handover
Contractors
```

Example operational item:

```text
17L Pump Station
Cable installation
70% complete
Awaiting transformer
Status: 🟠
```

## 3.3 Mining — production/process-centric

Mining revolves around production areas, sequential activities, targets, dependencies and constraints.

Typical concerns include:

```text
Work areas
Drilling
Charging
Blasting
Re-entry
Loading
Support
Services
Planned vs actual tonnes / metres / rounds
Production constraints
Ventilation / access / infrastructure conditions
Safety conditions
Recovery priorities
```

Example operational picture:

```text
NORTH PRODUCTION — MORNING

Overall status: 🟠

42L North
Drilling .............. 🟢 Complete
Charging .............. 🟢 Complete
Blasting .............. 🟢 Complete
Re-entry .............. 🟠 45 min delay
Loading ............... 🟢 In progress
Support ............... 🟢 On plan
Services .............. 🟠 Vent extension outstanding

Plan vs Actual
Planned tonnes ........ 4 200
Actual tonnes ......... 3 850
Achievement ........... 91.7%

Constraints
• Ventilation extension delaying 42L West
• One loading unit unavailable

Safety
• No significant incidents
• 1 stop-and-fix raised

Priority today
• Restore ventilation at 42L West
• Recover loading shortfall
```

This is the level of information Morning should optimise for: operationally meaningful, concise and actionable.

---

# 4. Common Reporting Grammar

The domain-specific workspaces may look very different, but their upward-facing reporting should follow a common grammar:

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

This is not intended to force every screen into the same layout. It defines the common meaning Morning should be able to derive from each operational scope.

Examples:

| Reporting concept | TMM | Construction | Mining |
|---|---|---|---|
| Responsibility | Fleet | Installations / work packages | Production areas |
| Plan | Services, maintenance, availability target | Planned work / milestones | Drill, blast, load, support, tonnes/metres |
| Actual | Machines available, work completed | Progress achieved | Actual production / completed activities |
| Deviation | Breakdown, overdue work | Delay, missed milestone | Production or sequence deviation |
| Constraint | Spares, labour, access | Materials, dependency, access | Ventilation, equipment, access, re-entry |
| Safety | Defects, actions, compliance | Worksite hazards, controls | Ground, support, ventilation, blasting conditions |
| Priority | Restore equipment | Complete / unblock work | Recover production / remove constraint |

The objective is **shared operational meaning, not identical domain screens**.

---

# 5. Organisational Hierarchy

Morning should not assume a flat `Site → Department` structure.

The core organisational concept should be an **Organisational Unit** that may contain child units and report to a parent unit.

Conceptually:

```text
OrganisationalUnit
- unit_id
- site_id
- parent_unit_id (nullable)
- unit_type
- name
- active
```

Possible unit types may include:

```text
site
department
section
team
project
other
```

The unit type is descriptive. The parent/child relationship defines the reporting hierarchy.

Example:

```text
SITE MANAGER
│
├── Engineering
│   ├── TMM
│   ├── Construction
│   └── Engineering Section 3
│
├── Mining
│   ├── North Production
│   ├── South Production
│   └── Development
│
├── Safety
└── Other site functions
```

The hierarchy may continue below a section when operationally useful:

```text
Engineering
└── TMM
    ├── Dayshift
    ├── Shift Team A
    └── Shift Team B
```

Morning should not impose a fixed number of levels.

---

# 6. Reporting Units: Producers and Aggregators

A reporting unit may behave primarily as an **operational producer**, an **aggregation/management unit**, or both.

## Operational producer

A TMM section, construction team or mining production section captures detailed work at the level where it happens.

Examples:

```text
Machine breakdown
Installation progress
Blast completed
Support outstanding
Ventilation constraint
```

## Aggregation / management unit

A higher-level engineering or mining manager may not capture every underlying activity directly.

Instead, that unit receives structured contributions from its children, adds its own context where required, and produces a higher-level report.

Example:

```text
ENGINEERING — MORNING

Overall status: 🟠

TMM ................. 🟠
Construction ........ 🟢
Engineering #3 ...... 🟠

Critical issues
• TMM — production machine unavailable
• Engineering #3 — pump installation delayed

Safety
• 2 new actions
• 0 significant incidents

Today's priorities
• Restore constrained TMM capacity
• Recover delayed installation
```

That Engineering report can in turn become an input to the Site-level report.

---

# 7. Hierarchical Roll-up

Morning should support a reporting chain such as:

```text
Shift / Team
      ↓
Section
      ↓
Department
      ↓
Site
```

At each level:

1. child units contribute structured operational information;
2. the parent applies defined roll-up rules;
3. locally owned information may be added;
4. a report/dashboard is produced for that level;
5. the result becomes an input to the next level.

This should not become copy-and-paste reporting.

The system should reuse the same underlying information and progressively change its level of abstraction.

---

# 8. Progressive Compression and Drill-down

Detail should **compress as it moves upward**, while remaining traceable downward.

Example:

```text
SHIFT
STC14 tyre damaged; replacement requested

        ↓

TMM
1 critical production machine unavailable

        ↓

ENGINEERING
TMM capacity constrained — production risk

        ↓

SITE
Engineering 🟠 — potential production impact
```

A higher-level user should not need to read every machine or activity record to understand the operation.

However, Morning should preserve a drill-down chain:

```text
Site status
  ↓
Engineering
  ↓
TMM
  ↓
STC14
  ↓
Tyre replacement activity
  ↓
Source shift record / evidence
```

This extends the existing principle that KPIs and reports should be explainable back to source evidence.

---

# 9. KPI Roll-up Rules

KPIs must not be aggregated by a single generic rule.

Each KPI definition should specify how, or whether, it rolls upward.

Examples:

```text
Attendance
aggregation = weighted_average
weight = planned_headcount

Safety incidents
aggregation = sum

Outstanding actions
aggregation = sum

Overall unit status
aggregation = defined severity / exception rule

Critical issues
aggregation = filtered collection

Machine availability
scope = TMM-specific
roll_up = only when meaningful at parent level
```

A simple average of child percentages is often mathematically wrong.

Example:

```text
TMM:          90% attendance across 100 people
Construction: 100% attendance across 10 people
```

The parent result should be based on underlying counts, not `(90 + 100) / 2`.

Morning should therefore preserve the numerator/denominator or equivalent evidence required for deterministic aggregation.

Some KPIs should deliberately **not** roll upward.

A site manager usually needs the operational consequence of a machine problem, not every machine-specific reliability metric.

---

# 10. Core Model vs Domain Profiles

Morning should avoid two opposite failures:

1. **Hard-coded TMM software** that cannot serve other scopes.
2. **Over-generic software** where everything becomes an `Entity`, `Metric` or configurable form and the domain meaning disappears.

The preferred model is:

```text
MORNING CORE
├── Organisation hierarchy
├── Identity / access
├── Shift / reporting periods
├── Operational activities
├── Status
├── Plan vs actual
├── Constraints / deviations
├── Safety
├── People / participation
├── Priorities / actions
├── Reporting
├── KPI definitions / projections
├── Hierarchical roll-up
├── Historical snapshots
└── Audit / evidence

DOMAIN PROFILE — TMM
├── Fleet
├── Machines
├── Breakdowns
├── Maintenance
├── Availability / utilization
└── Reliability

DOMAIN PROFILE — CONSTRUCTION
├── Projects / jobs
├── Work fronts
├── Installation packages
├── Progress
├── Materials / dependencies
├── QA / testing
└── Commissioning / handover

DOMAIN PROFILE — MINING
├── Production areas
├── Mining activities / sequence
├── Production targets
├── Tonnes / metres / rounds
├── Support
├── Services
├── Operational constraints
└── Production recovery
```

The UI may be strongly domain-specific while the underlying reporting model remains coherent.

> **Domain-specific presentation is desirable. Domain-specific duplication of the reporting engine is not.**

---

# 11. Operational Activity Remains Important, But Machines Are Optional Context

The existing architectural direction correctly identifies the **Operational Activity** as a central source of truth.

That principle should remain, but the activity model must not assume that every meaningful activity belongs to a machine.

Conceptually:

```text
OperationalActivity
- activity_id
- unit_id
- shift_id / reporting_period_id
- activity_type
- subject_type (optional)
- subject_id (optional)
- work_area_id (optional)
- start_time
- end_time
- status
- planned_or_unplanned
- description
- created_by
- created_at
- corrected_at
```

Domain profiles may attach additional structured context.

Examples:

```text
TMM activity
subject = machine: STC14
activity = tyre replacement

Construction activity
subject = work package: 17L Pump Station
activity = cable installation

Mining activity
subject = area: 42L North
activity = blasting
```

The precise schema should be resolved during the compatibility/refactor exercise. The key rule is that **machine identity must be optional domain context, not a universal Morning assumption**.

---

# 12. Mining and Construction Process Sequences

Morning should be able to represent operational sequences without turning itself into a workflow-engine product.

Examples:

## Mining

```text
Drill
  ↓
Charge
  ↓
Blast
  ↓
Re-entry
  ↓
Load
  ↓
Support
  ↓
Services
```

## Construction

```text
Excavate / prepare
  ↓
Fabricate
  ↓
Install
  ↓
Cable / connect
  ↓
Test
  ↓
Commission
  ↓
Handover
```

## TMM

```text
Diagnose
  ↓
Repair
  ↓
Test
  ↓
Return to service
```

An activity may carry common operational attributes such as:

```text
plan
actual
status
owner
location
start/end
constraint
safety condition
comment
```

Morning needs enough sequence awareness to explain progress and blockers. It does not need a general-purpose BPM/workflow engine in v1.

---

# 13. Reporting Contract Between Units

Each unit should be able to produce a normalized **Morning contribution** for its parent.

Conceptually:

```text
MorningContribution
- unit_id
- reporting_period
- overall_status
- plan_summary
- actual_summary
- deviations
- constraints
- safety_summary
- priorities
- kpi_observations
- critical_issues
- source_report_id
```

The exact persistence/API shape can evolve, but the semantic contract matters.

A parent unit should consume contributions without needing to understand every detail of the child domain.

For example, an Engineering parent can understand that TMM is constrained without understanding every failure mode on STC14.

---

# 14. External Systems Are Not a Current v1 Focus

Morning may later consume contributions from another system rather than requiring every department to work directly in Morning.

For example, a future HR, safety or specialist system could publish a normalized contribution into Morning.

That integration capability is useful, but **it is explicitly not the current design focus**.

The current priority is to prove compatibility across:

```text
TMM
Construction
Mining
```

Only after this internal operational model is sound should Morning spend significant design effort on cross-product contribution contracts.

---

# 15. What Morning Must Not Become

Morning should not become:

- a fleet-management system pretending to be universal;
- a construction project-management suite;
- a mining execution system;
- an HR system;
- an ERP;
- a configurable form builder;
- a generic workflow engine;
- a dashboard that stores numbers without source evidence;
- a collection of department-specific code paths with no shared model.

Morning's job is narrower and more valuable:

> **Capture and structure operational reporting, preserve operational history, calculate explainable management information, and roll the relevant truth through the organisational hierarchy.**

---

# 16. Design Test for Morning 1.0

A proposed Morning core abstraction should be considered credible only if it can represent all three validation scopes without awkward special cases.

For any important core concept, ask:

```text
How does this work for TMM?
How does this work for Construction?
How does this work for Mining?
```

If a concept only makes sense for TMM, it probably belongs in the TMM domain profile rather than Morning core.

If a concept becomes so generic that none of the three domains feels natural, the abstraction is probably too weak.

The target is **specific interfaces over a reusable operational-reporting foundation**.

---

# 17. Immediate Compatibility Exercise

Before large implementation changes, review the current Morning prototype and architecture using three classifications:

```text
CORE
Valid across TMM, Construction and Mining

TMM-SPECIFIC
Valid and useful, but belongs to the TMM profile

NEEDS GENERALISATION / MISSING
Currently assumes TMM or lacks concepts required by Construction/Mining
```

Review at least:

- organisation model;
- navigation;
- reporting periods and shift model;
- operational activity schema;
- machine references;
- status model;
- plan vs actual;
- constraints and deviations;
- safety capture;
- people / participation;
- KPI definitions;
- KPI roll-up rules;
- historical reports;
- dashboard views;
- drill-down / evidence chain.

The output of that exercise should determine the refactor size. Do not assume a rewrite is required.

---

# 18. Suggested First Validation Screens

To test the model rather than merely debate it, Morning should eventually be able to render one believable management screen for each scope from the same core reporting architecture.

## TMM

```text
Fleet status
Availability
Breakdowns
Planned/statutory work
Critical constraints
Safety
Today's return-to-service priorities
```

## Construction

```text
Active work fronts
Planned vs actual progress
Milestones
Blocked work
Materials / dependencies
Safety
Today's completion priorities
```

## Mining

```text
Area status
Drill / charge / blast / re-entry / load / support / services
Planned vs actual production
Constraints
Safety
Today's recovery priorities
```

The purpose is not visual polish first. The purpose is to prove that the **same core reporting concepts produce natural domain-specific operational views**.

---

# 19. Architectural Consequences

This decision changes several assumptions in the 27 August greenfield architecture.

The following should be treated as revised direction when implementation resumes:

1. `Site → Department` is not sufficient; Morning needs a recursive organisational-unit hierarchy.
2. `department_id` should progressively become `unit_id` where the relationship is truly organisational rather than specifically departmental.
3. `machine_id` must not be a universal attribute of operational activity.
4. Equipment/reliability remains an important **TMM domain**, not the definition of Morning core.
5. The top-level KPI dashboard cannot be globally fleet-centric.
6. KPI definitions need explicit scope and roll-up behaviour.
7. Parent dashboards are first-class reporting products, not merely broader filters over child records.
8. Reports should progressively compress detail upward while preserving drill-down evidence.
9. Construction and Mining are required architecture tests before broader departmental generalisation.

---

# 20. Updated Product North Star

The earlier statement remains useful for engineering activity, but the broader direction is now:

> **Morning captures operational activity once, turns it into the report each level of the organisation needs today, preserves the structured history needed tomorrow, and rolls explainable management information upward without losing the evidence beneath it.**

In practical terms:

```text
Capture where work happens
        ↓
Understand plan vs actual
        ↓
Explain deviations and constraints
        ↓
Surface safety and priorities
        ↓
Produce the unit report
        ↓
Roll the relevant truth upward
        ↓
Give management the whole operation at the right level of detail
```

---

# 21. Direction to Preserve

The following rules should guide the next Morning design decisions:

> **TMM, Construction and Mining are the v1 validation scopes.**

> **Morning core should model operational reporting, not machines.**

> **The UI may be domain-specific; the reporting engine should not be duplicated per domain.**

> **Every reporting unit may contribute upward and receive contributions from below.**

> **Information should compress as it rises and remain drillable to evidence.**

> **KPIs must declare their scope and aggregation semantics.**

> **Do not generalise beyond the three validation scopes until the model earns it.**

> **Morning should report operations, not merely display data.**
