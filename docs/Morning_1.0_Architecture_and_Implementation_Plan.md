# Morning 1.0 — Architectural Blueprint & Implementation Plan

**Date:** 27 August 2026  
**Status:** Greenfield reference architecture  
**Purpose:** Define what Morning would look like if designed today from first principles, while remaining usable as a target architecture for evolving the existing implementation rather than forcing a rewrite.

---

# 1. Executive Summary

Morning should be designed as a **standalone engineering operations platform**.

Its purpose is not merely to generate a morning report.

Its purpose is to:

```text
Capture engineering activity once
        ↓
Resolve operational context
        ↓
Generate reports automatically
        ↓
Distribute reports automatically
        ↓
Preserve structured operational history
        ↓
Derive utilization and reliability metrics
        ↓
Support engineering-management decisions
```

The central architectural principle is:

> **Operational activities are the canonical truth. Reports, utilization views, reliability metrics and dashboards are deterministic projections of that truth.**

Morning should initially be implemented as a **modular monolith** with a **CQRS-lite read/write separation**, a relational PostgreSQL database, background workers for asynchronous work, and deterministic KPI projections.

It should not begin as a microservice architecture.

It should not depend on Atlas for normal operation.

It should not use AI as the source of truth for calculations that can be derived deterministically.

---

# 2. Product North Star

A strong product statement is:

> **Morning captures engineering activity once, turns it into the reports people need today, distributes those reports automatically, and preserves the structured operational history needed tomorrow.**

Expanded with the analytical direction:

> **Capture once → Resolve context → Report automatically → Distribute automatically → Build operational history → Understand the operation.**

For the normal supervisor:

> **Capture the shift once. Morning does the rest.**

---

# 3. Product Boundaries

Morning owns the application plane.

```text
APPLICATION PLANE — Morning
- users
- roles
- sites
- departments
- crews
- shifts
- machines
- people
- operational activities
- breakdowns
- maintenance activities
- standing reasons
- spares/orders
- reporting
- historical reports
- utilization
- reliability
- KPI analytics
- scheduling
- distribution
- audit
```

Atlas may later provide infrastructure administration, but Morning must remain independent.

```text
CONTROL PLANE — Atlas
- service health
- backup
- restore
- deployment
- migration control
- database inspection
- host maintenance
```

Required independence:

```text
Morning offline  → Atlas still works
Atlas offline    → Morning still works
```

---

# 4. Architectural Style

The recommended initial architecture is:

# **Modular Monolith + CQRS-lite + Deterministic Projections**

Conceptually:

```text
                         Morning PWA
                              │
                         Morning API
                              │
             ┌────────────────┴────────────────┐
             │       Modular Monolith          │
             │                                 │
             │ Organisation                    │
             │ Identity / Access               │
             │ Operations                      │
             │ Equipment                       │
             │ People                          │
             │ Rules                           │
             │ Reporting                       │
             │ Utilization                     │
             │ Reliability                     │
             │ Distribution                    │
             │ Audit                           │
             └────────────────┬────────────────┘
                              │
                         PostgreSQL
                              │
             ┌────────────────┴────────────────┐
             │                                 │
       Canonical operational             Read projections
             truth                            / views
```

Alongside the API:

```text
Morning Worker
Morning Scheduler
```

These remain part of one coherent application/repository.

---

# 5. Why a Modular Monolith

Morning is likely to become a serious application, but that does not mean it should start with microservices.

A modular monolith provides:

- one deployment unit,
- one primary database,
- transactional consistency,
- simple local development,
- easy refactoring,
- clear module boundaries,
- lower operational overhead,
- fewer distributed-system failure modes.

Suggested backend modules:

```text
morning/
├─ organisation/
├─ identity/
├─ operations/
├─ equipment/
├─ people/
├─ rules/
├─ reporting/
├─ utilization/
├─ reliability/
├─ distribution/
├─ audit/
└─ shared/
```

Each module should have clear ownership of its data and application logic.

Network boundaries should not be introduced until a module has a real independent scaling or operational requirement.

---

# 6. CQRS-lite

CQRS should be used as a design principle, not as an enterprise framework.

The core separation is:

```text
COMMAND SIDE
"What should change?"

QUERY SIDE
"What should I see?"
```

Example commands:

```text
StartShift
RecordOperationalActivity
RecordBreakdown
UpdateActivity
AssignParticipant
CloseActivity
SubmitShiftReport
Publish24HourReport
CorrectOperationalRecord
CreateAssignmentRule
EnableDistributionRule
```

Example queries:

```text
GetCurrentShift
GetShiftHistory
Get24HourReports
GetMachineHistory
GetMachineUtilization
GetPersonnelUtilization
GetFleetAvailability
GetDowntimePareto
GetBadActors
GetMTBF
GetMTTR
GetLostOpportunityHours
```

The write model should be optimized for accurate operational capture.

The read model should be optimized for reporting and analysis.

---

# 7. Canonical Operational Truth

The most important domain object is not the report.

It is the **Operational Activity**.

Conceptually:

```text
OperationalActivity
- activity_id
- site_id
- department_id
- shift_id
- machine_id (optional depending on activity)
- activity_type
- start_time
- end_time
- status
- standing_reason
- failure_category
- planned / unplanned
- description
- created_by
- created_at
- corrected_at
```

Related structures:

```text
ActivityParticipant
- activity_id
- person_id
- participation_role
- start_time
- end_time

ActivitySpareRequirement
- activity_id
- spare_id / free-text fallback
- order_reference
- status
- delay_start
- delay_end
```

The exact schema may evolve, but the key principle remains:

> **Morning stores what happened, not merely how somebody described it in a report.**

---

# 8. Activity Types

An initial controlled activity taxonomy might include:

```text
Breakdown
Planned maintenance
Inspection
Statutory maintenance
Operational delay
Infrastructure delay
Waiting for spares
Waiting for artisan
Scheduled standing
Workshop repair
Machine recovery
Testing / commissioning
Other
```

The taxonomy should be configurable where appropriate, but critical invariants should remain controlled by the application.

---

# 9. Standing and Downtime Classification

Standing must not automatically mean engineering downtime.

Morning should explicitly distinguish:

```text
Engineering loss
Operational loss
Infrastructure loss
Supply-chain loss
Planned maintenance
Scheduled standing
Other
```

A standing reason should therefore have properties such as:

```text
StandingReason
- reason_id
- name
- owner_category
- counts_as_engineering_downtime
- counts_as_available
- counts_as_utilized
- active
```

This allows metrics to remain deterministic.

---

# 10. Equipment Domain

Core entity:

```text
Machine
- machine_id
- department_id
- code
- description
- machine_type
- active
- commissioning_date
- decommissioning_date
```

Optional future entities:

```text
MachineType
MachineGroup
MachineCriticality
Component
FailureMode
```

Machine identity must not depend on display name alone.

Historical records should reference immutable machine IDs.

---

# 11. People Domain

Core entity:

```text
Person
- person_id
- department_id
- employee_number
- display_name
- trade_id
- role_type
- active
```

Possible role types:

```text
Supervisor
Artisan
Engineering Assistant
Foreman
Planner
Other
```

A person's current role may change.

Historical activity participation must preserve the role/context that applied at the time.

---

# 12. Participation Model

People should be modeled as participants, not free-text names.

Example:

```text
OperationalActivity
       │
       ├─ ActivityParticipant
       │     person_id = Johan
       │     role = lead_artisan
       │
       └─ ActivityParticipant
             person_id = Sipho
             role = assistant
```

This enables deterministic derivation of:

- individual utilization,
- assistant utilization,
- trade loading,
- crew loading,
- activity participation,
- manpower distribution.

---

# 13. Organisation Model

Suggested hierarchy:

```text
Platform
 └─ Site
     └─ Department
         ├─ Users
         ├─ People
         ├─ Crews
         ├─ Machines
         ├─ Rules
         └─ Reports
```

Suggested entities:

```text
Site
Department
Crew
Trade
User
Role
UserDepartmentMembership
```

Morning should support multi-department use without making the first deployment unnecessarily complex.

---

# 14. Authentication and Roles

Authentication should be Morning-owned.

Suggested roles:

```text
Platform Admin
Site Admin
Department Admin / Foreman
Supervisor
Operational User
Read-only Viewer
```

Authorization should be explicit and role-based.

Examples:

```text
Supervisor
- create shift
- capture activities
- submit shift
- view own department

Department Admin
- configure machines
- configure people
- manage rules
- view analytics
- publish reports

Platform Admin
- manage sites
- manage departments
- platform configuration
```

Avoid “admin means everything everywhere” where possible.

---

# 15. Shift Model

Suggested core:

```text
Shift
- shift_id
- department_id
- shift_date
- shift_type
- supervisor_id
- crew_id
- start_time
- end_time
- status
```

Potential statuses:

```text
draft
active
submitted
closed
corrected
```

The shift should represent the operational context for captured activities.

---

# 16. Assignment Rules

Dynamic staffing logic should be rule-driven.

Example:

```text
IF department = TMM
AND shift = Day
THEN include Crew C
```

A rule should be stored as controlled configuration, not executable code.

Suggested rule structure:

```text
AssignmentRule
- rule_id
- department_id
- name
- condition_type
- condition_value
- action_type
- action_value
- priority
- enabled
```

At runtime:

```text
Shift created
     ↓
Assignment rules evaluated
     ↓
Resolved participants / context
     ↓
Result snapshotted into shift
```

Historical outcomes should survive later rule changes.

---

# 17. Historical Integrity

Morning needs two different historical behaviours.

## Operational records

Operational records should be auditable and correctable.

Corrections should record:

```text
who changed it
when
what changed
why
previous value where consequential
```

## Published reports

Published reports should be immutable snapshots.

Once a 24-hour report is published:

```text
PublishedReport
      ↓
frozen historical truth
```

Later configuration changes must not rewrite old reports.

---

# 18. Audit Model

Consequential changes should generate audit records.

Suggested audit fields:

```text
AuditRecord
- audit_id
- actor_user_id
- action
- entity_type
- entity_id
- timestamp
- before_json
- after_json
- reason
```

Not every keystroke needs auditing.

Focus on:

- submitted shifts,
- corrections,
- published reports,
- role changes,
- machine configuration,
- rule changes,
- distribution changes.

---

# 19. Reporting Architecture

Reporting should be treated as a product module.

Concept:

```text
Operational data
      ↓
Report Definition
      ↓
Report Generator
      ↓
Report Snapshot
      ↓
Artifact
      ↓
Distribution
```

Initial report types:

```text
Department Meeting Report
24-Hour Engineering Report
```

---

# 20. 24-Hour Reports

The user-facing tab:

```text
[ 24-Hour Reports ]
```

should list historical report periods.

Example:

```text
27 Aug 2026   05:00–05:00
26 Aug 2026   05:00–05:00
25 Aug 2026   05:00–05:00
```

Opening a report should provide:

```text
[ View Report ] [ Download PDF ]
```

Suggested report entities:

```text
ReportDefinition
ReportRun
ReportSnapshot
ReportArtifact
```

---

# 21. Report Snapshot Model

Suggested:

```text
ReportSnapshot
- report_snapshot_id
- report_type
- department_id
- period_start
- period_end
- generated_at
- published_at
- source_revision
- snapshot_json
- status
```

A report artifact:

```text
ReportArtifact
- artifact_id
- report_snapshot_id
- format
- storage_path
- checksum
- created_at
```

The first format should likely be PDF.

---

# 22. Distribution

Scheduled report delivery belongs inside Morning.

Suggested entities:

```text
DistributionRule
- report_type
- department_id
- days
- time
- timezone
- recipients
- enabled
```

Delivery history:

```text
DeliveryAttempt
- report_snapshot_id
- recipient
- attempted_at
- status
- provider_message_id
- error
- retry_count
```

Distribution should be idempotent.

Morning should prevent accidental duplicate scheduled sends.

---

# 23. Worker and Scheduler

The web API should not perform long-running work inline.

Background worker responsibilities:

```text
Generate scheduled reports
Render PDFs
Send email
Retry failed delivery
Refresh analytical projections
Run expensive recalculation
Perform batch correction rebuilds
```

Scheduler responsibilities:

```text
Determine which report is due
Create idempotent scheduled job
Queue worker task
```

---

# 24. Utilization Architecture

User-facing tab:

```text
[ Utilization ]
```

Initial split:

```text
Utilization
├─ Machines
└─ Personnel
```

Utilization is derived from structured operational history.

It should not require a separate utilization-capture process.

---

# 25. Machine Utilization

Example read model:

```text
MachineUtilizationView
- machine_id
- period_start
- period_end
- scheduled_hours
- available_hours
- running_hours
- breakdown_hours
- planned_maintenance_hours
- operational_delay_hours
- infrastructure_delay_hours
- spares_delay_hours
```

Potential derived calculations:

```text
Availability = available_hours / scheduled_hours
Utilization  = running_hours / available_hours
```

Definitions must be explicit and versioned if business interpretation changes.

---

# 26. Personnel Utilization

Example read model:

```text
PersonUtilizationView
- person_id
- period_start
- period_end
- on_shift_hours
- assigned_hours
- blocked_hours
- available_unallocated_hours
- training_hours
- meeting_hours
- leave_hours
```

Personnel utilization must remain a resource-planning view.

It must not become a simplistic employee-performance score.

---

# 27. Personnel Utilization Categories

Suggested categories:

```text
Productively assigned
Blocked
Available / unallocated
Training
Meeting
Leave
Not on shift
Other
```

Blocked time should retain cause.

Examples:

```text
Waiting for spares
Waiting for access
Waiting for machine
Waiting for instruction
Infrastructure unavailable
```

---

# 28. KPI Architecture

Morning should use a hierarchical KPI model.

```text
Fundamental KPI
      ↓
Category
      ↓
Subcategory
      ↓
Machine / person / trade
      ↓
Operational activity
```

Every major KPI should be explainable down to source evidence.

---

# 29. Fundamental KPI Set

A strong initial top-level set:

```text
Fleet Availability
Fleet Utilization
Engineering Downtime
Lost Opportunity Hours
Repeat Failures
MTTR
Personnel Utilization
Reactive Workload
```

Possible dashboard:

```text
Row 1
Availability | Utilization | Engineering Downtime | Lost Opportunity

Row 2
Repeat Failures | MTTR | Bad Actors | Personnel Utilization

Below
Downtime Pareto
Fleet trend
Top recurring faults
Trade loading
```

---

# 30. KPI Drill-Down

Example:

```text
Fleet Availability
      ↓
Engineering loss
      ↓
Hydraulics
      ↓
STC14
      ↓
27 Aug 01:20–02:45
      ↓
Breakdown record
```

The system should support:

> “How did Morning calculate this number?”

without requiring a spreadsheet reconstruction.

---

# 31. Reliability Metrics

Initial derived reliability metrics:

```text
MTBF
MTTR
Breakdown frequency
Repeat failure count
Repeat repair rate
First-time-fix rate
Downtime Pareto
Bad actor ranking
Availability trend
Failure-category trend
```

---

# 32. MTBF

Conceptually:

```text
Operating hours / failure count
```

Morning should define exactly which failures qualify.

The formula is simple.

The definition is the important part.

---

# 33. MTTR

Conceptually:

```text
Repair hours / completed repairs
```

The system should distinguish:

```text
Response delay
Troubleshooting
Waiting for spares
Repair
Testing
```

when the data supports it.

---

# 34. Repeat Failure Detection

Repeat failures should be deterministic.

Potential windows:

```text
24 hours
48 hours
72 hours
7 days
```

Example:

```text
STC14
Hydraulic hose
7 events
14.2 h downtime
3 repeated within 72 h
```

---

# 35. Downtime Pareto

Projection example:

```text
Hydraulic failures      31%
Electrical              18%
Waiting for spares      15%
Tyres                     9%
No operator               8%
Infrastructure            7%
Other                    12%
```

Each slice should drill into source activities.

---

# 36. Bad Actor Machines

A bad-actor view might combine:

```text
Total lost hours
Breakdown frequency
Repeat failures
MTBF deterioration
MTTR
Availability trend
Criticality
```

The score must remain explainable.

Avoid opaque “AI health scores.”

---

# 37. Lost Opportunity Hours

Potential definition:

```text
Potential productive machine hours
-
productive machine hours
=
Lost opportunity hours
```

Breakdown:

```text
Engineering
Operations
Supply chain
Infrastructure
Planned maintenance
Other
```

This is likely to become one of Morning's strongest management metrics.

---

# 38. Planned vs Reactive Work

Projection:

```text
Planned hours
Reactive hours
Inspection hours
Statutory hours
Other hours
```

Useful trend:

```text
Reactive workload %
```

This can show whether the department is moving toward controlled maintenance.

---

# 39. Trade Loading

Morning should derive workload by trade:

```text
Diesel mechanics
Auto electricians
Boilermakers
Electricians
Engineering assistants
```

Metrics:

```text
assigned %
blocked %
unallocated %
work carried forward
```

This supports manpower planning.

---

# 40. Spares Intelligence

From activity-linked spares data Morning can eventually derive:

```text
Most frequently required parts
Parts causing longest downtime
Machines consuming most spares
Repeat orders
Spares-related lost hours
```

This can support engineering, Stores and procurement.

---

# 41. Read Projections

The system should avoid recalculating every KPI from raw history on every request.

Suggested projection tables:

```text
machine_daily_metrics
person_daily_metrics
trade_daily_metrics
department_daily_metrics
failure_daily_metrics
downtime_daily_metrics
report_summary_metrics
```

These can be recomputed deterministically from canonical operational data.

---

# 42. Projection Strategy

Initial approach:

```text
Operational change
      ↓
mark affected projection period dirty
      ↓
worker recalculates
      ↓
replace deterministic projection
```

For example:

```text
STC14 activity corrected on 27 Aug
      ↓
rebuild STC14 daily metrics for 27 Aug
      ↓
rebuild affected department rollup
```

This is simpler than full event streaming.

---

# 43. Correction Handling

Corrections to operational history should trigger recalculation of affected projections.

If a correction changes a previously published report, Morning should **not** silently rewrite the published report.

Instead:

```text
Operational history corrected
Published report remains immutable
```

A future feature may support explicit report revision/supersession.

---

# 44. API Shape

Possible command endpoints:

```text
POST   /shifts
POST   /activities
PATCH  /activities/{id}
POST   /activities/{id}/participants
POST   /shifts/{id}/submit
POST   /reports/24-hour/generate
POST   /reports/{id}/publish
POST   /rules
```

Possible query endpoints:

```text
GET /shifts/current
GET /reports/24-hour
GET /reports/24-hour/{id}
GET /machines/{id}/history
GET /machines/{id}/utilization
GET /people/{id}/utilization
GET /kpis/availability
GET /kpis/downtime
GET /kpis/reliability
GET /kpis/personnel
```

Exact API design should be refined during implementation.

---

# 45. Frontend Architecture

Morning should remain a PWA-friendly web application.

Suggested major surfaces:

```text
Landing / Start Shift
Shift Capture
24-Hour Reports
Utilization
Dashboard
Admin
```

The frontend should not duplicate business logic.

Calculations and authorization belong on the backend.

---

# 46. Dashboard UX

Avoid one giant page containing every KPI.

Use three levels.

## Level 1 — Management Overview

```text
Availability
Utilization
Engineering downtime
Lost opportunity
Repeat failures
MTTR
Personnel utilization
Reactive workload
```

## Level 2 — Analysis

Examples:

```text
Availability by machine
Downtime by cause
Downtime by shift
Bad actors
Fleet trend
```

## Level 3 — Evidence

```text
machine
date/time
activity
people
classification
spares
description
```

---

# 47. Database Choice

The standalone Morning architecture should use:

# **PostgreSQL**

Reasons:

```text
concurrent users
transactional integrity
constraints
indexes
analytical SQL
materialized views if needed
JSON where useful
background-worker concurrency
backup tooling
migration tooling
long-term durability
```

SQLite remains appropriate for prototypes and small local components, but Morning's standalone direction benefits from PostgreSQL.

---

# 48. Database Migration Strategy

Morning should treat production data as durable.

Never rely on:

```text
schema changed
→ delete database
```

Use explicit versioned migrations.

Each migration should:

```text
have a unique version
run transactionally where possible
be tested
support upgrade from the previous supported version
validate result
```

Production startup should refuse unknown/future schema versions.

---

# 49. Backup and Restore

Morning should have tested backup/restore procedures.

Minimum:

```text
scheduled PostgreSQL backup
report-artifact backup
configuration backup
restore verification
retention policy
```

Backups are not complete until restore has been tested.

---

# 50. Artifact Storage

Generated PDFs and future file artifacts should be stored separately from database rows.

Possible first implementation:

```text
local persistent filesystem
```

with DB metadata pointing to the artifact.

Future:

```text
S3-compatible object storage
```

if deployment needs it.

---

# 51. Security

Minimum security architecture:

```text
TLS
secure sessions
CSRF protection
role-based authorization
department scoping
audit trail
safe password/auth provider
rate limits for login
server-side authorization
strict input validation
```

A user must never be able to obtain another department's data merely by changing an ID in a URL.

---

# 52. Multi-Tenancy / Department Isolation

Initial logical tenancy:

```text
Site
  ↓
Department
```

Every operational record should belong to a department.

Queries should be scoped through authenticated membership.

Avoid relying solely on frontend filtering.

---

# 53. Observability

Morning should expose operational telemetry.

Suggested:

```text
application health
database health
worker health
scheduler health
queue depth
failed report jobs
failed deliveries
projection lag
request error rate
```

Logs should be structured.

---

# 54. Testing Strategy

Testing should be layered.

## Unit tests

```text
domain rules
calculations
classification
authorization
report logic
projection logic
```

## Integration tests

```text
database constraints
migrations
repository behaviour
worker jobs
PDF generation
email delivery adapters
```

## API tests

```text
authentication
authorization
validation
command endpoints
query endpoints
```

## End-to-end tests

```text
start shift
capture breakdown
submit shift
generate report
view report
derive utilization
```

---

# 55. KPI Golden Tests

Critical KPI calculations should have fixture-based golden tests.

Example fixture:

```text
machine scheduled: 24 h
breakdown: 4 h
operational delay: 2 h
running: 18 h
```

Expected:

```text
availability = defined expected value
utilization = defined expected value
engineering downtime = 4 h
operational loss = 2 h
```

This protects KPI meaning from accidental drift.

---

# 56. Report Golden Tests

Historical report outputs should be tested against stable fixtures.

Test:

```text
same canonical inputs
→ same report snapshot
```

Rendering changes may alter PDF appearance, but underlying report content should remain deterministic.

---

# 57. Performance Strategy

Do not prematurely optimize.

Initial performance tools:

```text
proper indexes
daily projection tables
pagination
date-range filtering
background recalculation
cached report artifacts
```

Only introduce more complex infrastructure when measurement shows a need.

---

# 58. No AI in Core Truth

AI may later assist with:

```text
natural-language search
trend explanation
summaries
correlation suggestions
draft management commentary
```

But AI should not be the authority for:

```text
availability
utilization
MTBF
MTTR
downtime
repeat-failure classification
historical report identity
authorization
```

Where the result can be calculated deterministically, calculate it.

---

# 59. Explainability Requirement

Every fundamental KPI should be traceable.

Example:

```text
Fleet Availability = 82.4%
       ↓
Engineering loss = 11.2%
       ↓
Hydraulics = 5.7%
       ↓
STC14 = 3.1%
       ↓
Breakdown activity #8472
       ↓
01:20–02:45
```

This should be treated as an architectural invariant.

---

# 60. Implementation Philosophy

Do not build every future feature at once.

The implementation should proceed by **vertical slices**.

Each phase should deliver a real user outcome and leave the system in a coherent state.

Avoid:

```text
build all database tables
then all APIs
then all UI
then discover model is wrong
```

Prefer:

```text
domain
→ persistence
→ API
→ UI
→ tests
→ user outcome
```

---

# 61. Implementation Phase 0 — Architecture & Domain Contract

## Goal

Freeze the core language and domain boundaries before major coding.

## Deliverables

```text
Architecture document
Domain glossary
Entity relationship model
KPI definitions
Standing/downtime taxonomy
Report-period definition
Historical-correction policy
Role model
```

## Acceptance gate

The team can answer consistently:

```text
What is a shift?
What is an activity?
What is downtime?
What is availability?
What is utilization?
What becomes immutable?
What can be corrected?
```

No major implementation should proceed until these are clear.

---

# 62. Phase 1 — Platform Foundation

## Goal

Create the standalone Morning application skeleton.

## Scope

```text
repository
backend
frontend
PostgreSQL
migrations
authentication
user/session model
basic roles
site/department model
CI
test harness
```

## Acceptance

A user can:

```text
sign in
access an authorized department
be denied unauthorized departments
```

---

# 63. Phase 2 — Organisation, People & Equipment

## Goal

Establish master data required for operational capture.

## Scope

```text
Sites
Departments
Users
People
Trades
Crews
Machines
Machine types
active/inactive state
```

## Acceptance

Department admin can configure the operational entities needed for a shift.

---

# 64. Phase 3 — Structured Shift Capture

## Goal

Replace “report as prose” with structured operational capture while keeping the workflow fast.

## Scope

```text
Start shift
Shift context
OperationalActivity
Breakdown
Maintenance
Standing reason
Activity participants
Orders/spares
Submit shift
```

## Acceptance

A supervisor can capture a full real-world shift without needing an external spreadsheet.

---

# 65. Phase 4 — Assignment Rules

## Goal

Resolve operational context automatically.

## Scope

```text
controlled assignment rules
Crew C day-shift rule
rule priority
enable/disable
resolved snapshot
conflict validation
```

## Acceptance

A day shift automatically resolves Crew C correctly without changing historical assignments when rules later change.

---

# 66. Phase 5 — 24-Hour Reports

## Goal

Create the first major report product.

## Scope

```text
24-hour period definition
report generator
historical report list
report snapshot
view report
PDF artifact
download
```

## Acceptance

User can open:

```text
24-Hour Reports
```

select any prior published period, view it and download the frozen PDF.

---

# 67. Phase 6 — Distribution Engine

## Goal

Automatically deliver report products.

## Scope

```text
scheduler
worker
distribution rules
email provider
delivery history
retry
idempotency
manual send
test send
```

## Acceptance

Configured reports are generated and sent exactly once for a scheduled period, with delivery evidence.

---

# 68. Phase 7 — Machine Operational History

## Goal

Make accumulated shift capture useful beyond reporting.

## Scope

```text
machine timeline
activity history
breakdown history
standing history
date filters
failure categories
```

## Acceptance

A user can open a machine and see what happened to it over time.

---

# 69. Phase 8 — Machine Utilization

## Goal

Derive machine usage from operational history.

## Scope

```text
scheduled hours
running hours
available hours
standing hours
loss ownership
daily projection
period rollups
drill-down
```

## Acceptance

A machine's utilization view is fully traceable to source activities.

---

# 70. Phase 9 — Personnel Utilization

## Goal

Derive resource loading from existing activity participation.

## Scope

```text
assigned time
blocked time
unallocated time
training/meeting
artisan views
assistant views
trade views
person drill-down
```

## Acceptance

Morning can show how a person or trade was utilized without requiring separate timesheet entry.

---

# 71. Phase 10 — Fundamental KPI Dashboard

## Goal

Create the management overview.

## Initial KPIs

```text
Fleet Availability
Fleet Utilization
Engineering Downtime
Lost Opportunity Hours
Repeat Failures
MTTR
Personnel Utilization
Reactive Workload
```

## Acceptance

Every KPI drills down to categories and source operational records.

---

# 72. Phase 11 — Reliability Analytics

## Goal

Turn operational history into maintenance insight.

## Scope

```text
MTBF
MTTR
repeat failure detection
first-time-fix rate
downtime Pareto
bad actors
fleet trend
failure trend
```

## Acceptance

Reliability metrics are deterministic, tested and explainable.

---

# 73. Phase 12 — Spares & Delay Intelligence

## Goal

Expose supply-chain contribution to downtime.

## Scope

```text
spares delay
frequent parts
lost hours by part
repeat orders
machine spares consumption
```

## Acceptance

Management can identify where unavailable spares materially affect fleet performance.

---

# 74. Phase 13 — Admin & Multi-Department Maturity

## Goal

Scale Morning beyond one department without compromising usability.

## Scope

```text
site administration
department administration
role delegation
cross-department reporting
templates
configuration inheritance
```

## Acceptance

Multiple departments can operate independently within one Morning deployment.

---

# 75. Phase 14 — Production Hardening

## Goal

Prepare Morning for serious operational dependency.

## Scope

```text
backup
restore testing
migration discipline
observability
security review
load testing
disaster recovery
artifact retention
audit review
```

## Acceptance

Morning can be upgraded, restored and operated without treating production data as disposable.

---

# 76. Existing Morning Migration Strategy

This greenfield design should be a **reference architecture**, not an automatic rewrite mandate.

Existing code should be inspected and classified:

```text
KEEP
ADAPT
REPLACE
ADD
REMOVE
```

Suggested categories:

## Keep

```text
proven domain logic
useful validation
report-generation logic
working UI flows
tests
useful persistence abstractions
```

## Adapt

```text
database ownership
authentication
routing
configuration
scheduling
identity assumptions
```

## Leave in Atlas

```text
Atlas capability bindings
Atlas runtime coupling
Atlas identity coupling
Atlas-specific Work integration
```

---

# 77. Migration Approach

Recommended:

```text
1. Define target architecture
2. Inspect current Morning
3. Map existing code to target modules
4. Preserve useful logic
5. Extract reusable domain code
6. Establish standalone persistence
7. Run parity tests
8. Compare report outputs
9. Operate standalone
10. Add thin Atlas connector if useful
11. Remove embedded implementation only after parity
```

Avoid a flag-day rewrite.

---

# 78. Decision Records

Major architecture decisions should be preserved as ADRs.

Examples:

```text
ADR-001 Modular monolith
ADR-002 PostgreSQL
ADR-003 CQRS-lite
ADR-004 OperationalActivity as canonical truth
ADR-005 Published reports immutable
ADR-006 Deterministic KPI projections
ADR-007 No AI as KPI authority
ADR-008 Morning independent of Atlas
```

This helps prevent architecture drift later.

---

# 79. Core Invariants

Suggested initial invariants:

```text
Every operational activity belongs to one department.

Every published report belongs to one fixed period.

Published report snapshots are immutable.

Every KPI is derived from canonical operational records.

Every fundamental KPI can drill down to source evidence.

A historical rule change never rewrites an already-resolved shift.

A machine display-name change does not change historical machine identity.

Standing is not automatically engineering downtime.

Personnel utilization is not an employee-performance score.

No user can access another department without explicit authorization.
```

---

# 80. Non-Goals for Morning 1.0

Do not initially build:

```text
microservices
Kafka
full event sourcing
generic workflow engines
AI-generated truth
complex plugin marketplaces
custom report scripting language
arbitrary user-written formulas
real-time streaming architecture
```

These can be considered later only if real requirements justify them.

---

# 81. Suggested Technology Shape

One reasonable implementation stack:

```text
Frontend
- TypeScript
- React / PWA

Backend
- Python
- FastAPI

Database
- PostgreSQL

Migrations
- Alembic or equivalent

Worker
- Python worker process

Scheduler
- application-owned deterministic scheduler

Artifact generation
- HTML → PDF or dedicated PDF renderer

Email
- provider abstraction

Deployment
- Docker
- reverse proxy
- TLS
```

The exact libraries can change without altering the architecture.

---

# 82. Suggested Deployment Topology

Initial production topology:

```text
                    Internet / VPN
                         │
                    Reverse Proxy
                         │
                 ┌───────┴────────┐
                 │                │
             Morning API      Morning PWA
                 │
        ┌────────┴────────┐
        │                 │
 Morning Worker     Morning Scheduler
        │                 │
        └────────┬────────┘
                 │
             PostgreSQL
                 │
        Report Artifact Store
```

This can all run on one server initially while remaining logically separated.

---

# 83. Future Atlas Integration

Atlas should integrate through narrow interfaces.

Possible future capabilities:

```text
Morning health
Morning backup status
Morning migration status
Morning report status
Morning service restart
Morning database inspection
```

Atlas should not become the runtime dependency for Morning's normal user workflows.

---

# 84. Product Maturity Model

Morning can be seen as progressing through:

```text
Stage 1 — Capture
Stage 2 — Report
Stage 3 — History
Stage 4 — Utilization
Stage 5 — Reliability
Stage 6 — Decision support
```

The architecture should support all six without forcing all six to be built immediately.

---

# 85. Final Architectural Statement

Morning should be:

> **A modular, event-centred engineering operations platform where structured shift activities form the canonical operational record, and reports, utilization, reliability metrics and dashboards are deterministic, auditable projections of that same record.**

The system should optimize for:

```text
easy capture
structured truth
historical integrity
explainable KPIs
low administrative burden
strong reporting
deterministic analytics
gradual product growth
```

---

# 86. Final Implementation Principle

When deciding whether to add a field, feature or metric, ask:

```text
Does the user already know this?
Can Morning derive it?
Does it materially improve operational understanding?
Will it create more admin than value?
```

The ideal Morning experience remains:

> **The supervisor does approximately the same reporting work as today, but the organization gets dramatically more value from the information already being captured.**

That should remain the product's defining advantage.
