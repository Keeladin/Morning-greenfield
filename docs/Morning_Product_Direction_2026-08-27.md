# Morning — Product Direction, Reporting, Utilization & KPI Architecture

**Date:** 27 August 2026  
**Status:** Product/design discussion capture  
**Purpose:** Preserve the current direction for Morning before implementation work resumes.

---

# 1. Current Product Direction

Morning is evolving beyond being a morning-report generator.

The original value proposition was primarily:

```text
Capture shift information
        ↓
Generate the morning report
```

That remains useful, but the broader product direction is now:

```text
Capture operations once
        ↓
Resolve operational context
        ↓
Generate reports automatically
        ↓
Distribute reports automatically
        ↓
Build structured operational history
        ↓
Derive utilization, reliability and engineering KPIs
        ↓
Support better engineering decisions
```

The important shift is that Morning should become an **engineering operations record that happens to generate reports**, rather than merely a report generator.

The system should gain more value from information users are already capturing, without significantly increasing their administrative burden.

A core principle therefore becomes:

> **Capture once. Never make the user re-enter information Morning already knows.**

And:

> **Do not ask for extra data unless it creates clear operational value. Prefer structuring information users already capture.**

---

# 2. Morning as a Standalone Product

Morning should continue moving toward being a standalone application rather than a hard-coded Atlas feature.

The current embedded Morning implementation can be treated as a prototype/reference implementation and evolved into its own system.

Long-term separation:

```text
APPLICATION PLANE — Morning
- users
- departments
- machines
- shifts
- reports
- attendance
- safety
- utilization
- operational history
- normal CRUD

CONTROL PLANE — Atlas
- health
- backup
- restore
- migration
- database inspection
- service status
- deployment
- maintenance
```

Morning should be able to operate if Atlas is offline.

Atlas should be able to operate if Morning is unavailable.

Possible future domains:

```text
morning.atlas-agentic.co.za
morningadmin.atlas-agentic.co.za
atlas.atlas-agentic.co.za
```

---

# 3. Main User Experience

The normal supervisor/user should still feel like:

> “I am just doing my normal shift report.”

Morning should quietly transform that same structured capture into multiple outputs:

```text
One shift entry
      ↓
Shift handover
24-hour report
Machine utilization
Personnel utilization
Downtime history
Repeat-failure history
Standing reasons
Reliability data
Future analytics
```

The user should not have to enter separate “analytics data.”

The analytics should emerge from the operational record.

---

# 4. Main Navigation Change

The earlier concept of:

```text
[ Report History ] [ Operational History ]
```

should evolve into:

```text
[ 24-Hour Reports ] [ Utilization ]
```

These two areas serve different purposes:

- **24-Hour Reports** = historical compiled report products.
- **Utilization** = analytical views derived from operational history.

---

# 5. 24-Hour Reports

The first tab should be called:

# **24-Hour Reports**

This area should show the complete compiled engineering report for each previous 24-hour period.

Example:

```text
24-Hour Reports

27 Aug 2026   05:00–05:00   Complete
26 Aug 2026   05:00–05:00   Complete
25 Aug 2026   05:00–05:00   Complete
24 Aug 2026   05:00–05:00   Complete
...
```

Opening a historical report should offer:

```text
24-Hour Engineering Report
26 Aug 05:00 → 27 Aug 05:00

[ View Report ]   [ Download ]
```

The first download format should likely be PDF.

Excel can be considered later if there is a real operational need.

## Historical integrity

A completed 24-hour report should be treated as a **frozen historical snapshot**.

If later changes are made to:

- machine names,
- crew rules,
- assignments,
- user details,
- configuration,
- classifications,

historical reports should not silently rewrite themselves.

Historical reporting should preserve what was resolved and submitted at that time.

---

# 6. Utilization

The second tab should be called:

# **Utilization**

This is a stronger concept than “Operational History.”

Operational history is what Morning stores.

Utilization is one of the useful things Morning derives from that history.

The first structure should be:

```text
Utilization
├─ Machines
└─ Personnel
```

---

# 7. Machine Utilization

For each machine, Morning should be able to show how the machine was used over a selected period.

Example:

```text
STC14

Selected period: 01–31 August

Available / Running        176 h
Breakdown                    31 h
Planned maintenance          18 h
Waiting for spares           11 h
No operator                   6 h
Operational standing         22 h
Other                         4 h
```

Below the summary, Morning should show the history that produced the result:

```text
27 Aug  01:20–02:45   Breakdown       Hydraulic hose
26 Aug  13:10–15:00   Waiting spares  Turbo
25 Aug  08:00–09:30   Maintenance     Weekly inspection
...
```

The important distinction is:

> **Standing does not automatically mean engineering downtime.**

Morning should therefore classify standing reasons.

Possible categories:

```text
Running
Planned maintenance
Breakdown
Waiting for spares
Waiting for artisan
No operator
Operational delay
Infrastructure / area unavailable
Scheduled standing
Other
```

These categories can evolve over time, but they should be structured rather than inferred from prose wherever possible.

---

# 8. Machine Availability vs Utilization

Morning should distinguish **availability** from **utilization**.

Example conceptual model:

```text
Scheduled time
      ↓
Available time
      ↓
Running / utilized time
```

Potential calculations:

```text
Availability = Available time / Scheduled time
Utilization  = Running time / Available time
```

This distinction matters.

A machine may have:

```text
Availability = 95%
Utilization  = 60%
```

Meaning engineering availability is good, but the machine is not being used.

Another machine may show:

```text
Availability = 70%
Utilization when available = 95%
```

Meaning reliability is likely the constraint.

Morning should therefore make it possible to distinguish engineering losses from operational or planning losses.

---

# 9. Personnel Utilization

The utilization area should also support:

# **Personnel Utilization**

This includes both:

- artisans,
- engineering assistants,
- and potentially other operational personnel later.

Example:

```text
Johan — Diesel Mechanic
August 2026

Breakdown response        42%
Planned maintenance       29%
Inspection / compliance   11%
Waiting / delay            8%
Other productive work      7%
Unallocated                 3%
```

Drill-down:

```text
27 Aug
01:20–02:45  STC14   Breakdown      Hose replacement
03:15–04:10  RLH3    Breakdown      Steering fault
05:30–07:00  Workshop Planned work  Service
...
```

A work activity may contain:

```text
Lead artisan: Johan

Assistants:
- Thabo
- Sipho
```

Morning should understand that all participants were consumed by that work.

---

# 10. Personnel Utilization Must Not Become a Performance Score

Personnel utilization should be designed as an **engineering resource-planning measure**, not a simplistic employee-performance score.

For example:

```text
Person blocked for 2 hours because spares were unavailable
```

must not become:

```text
Person was only 75% utilized
→ poor performance
```

Instead, the reason should remain visible.

A better model is:

```text
Productively assigned
Available / unallocated
Blocked
Leave / training / meeting
Not on shift
```

Morning should allow management to understand whether underutilization is caused by:

- lack of available work,
- spares shortages,
- poor planning,
- access delays,
- infrastructure delays,
- trade imbalance,
- staffing imbalance,
- training/meeting obligations,
- or other causes.

---

# 11. Structured Operational Capture

The dashboard and utilization system depend on a strong event/activity model.

Where information matters analytically, Morning should store it structurally.

Potential core fields:

```text
machine
person / people
activity type
start time
end time
status
standing reason
failure category
planned / unplanned
parts delay
shift
crew
supervisor
orders / spares
description
```

The prose report should increasingly become an **output of structured operational data**, rather than being the primary data itself.

The user should still be able to capture information quickly.

The aim is not to turn the shift report into a giant form.

The aim is to structure information that is already naturally being reported.

---

# 12. Morning's Three Product Layers

The product can now be understood in three clear layers:

```text
1. CAPTURE
   What happened during the shift?

2. REPORT
   What do people need to know today?

3. UNDERSTAND
   What does the accumulated history tell us?
```

The third layer is what moves Morning beyond being a reporting convenience.

It turns accumulated shift data into operational knowledge.

---

# 13. KPI Dashboard

Morning should have a serious engineering-management dashboard.

The dashboard should **not** try to put every KPI on one page.

Instead, it should use a hierarchy:

```text
Fundamental KPI
      ↓
Category breakdown
      ↓
Subcategory
      ↓
Machine / person / event
      ↓
Raw operational record
```

The dashboard should answer both:

> **What is happening?**

and:

> **Why is it happening?**

---

# 14. Fundamental KPI Dashboard

The top level should probably contain only a small number of high-value indicators.

Possible first set:

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

A possible dashboard layout:

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

The exact visual design can evolve later.

---

# 15. KPI Drill-Down Model

Each fundamental KPI should open into deeper analysis.

Example:

```text
Fleet Availability
      ↓
Engineering loss
Operational loss
Infrastructure loss
Planned maintenance
      ↓
Engineering loss
      ↓
Hydraulics
Electrical
Tyres
Engine
Brakes
      ↓
Hydraulics
      ↓
STC14
RLH3
STC9
      ↓
STC14
      ↓
Individual breakdown events
```

The same pattern works for people:

```text
Personnel Utilization
      ↓
Artisans
Assistants
      ↓
Diesel mechanics
Auto electricians
Boilermakers
      ↓
Individual person
      ↓
Assigned work
Blocked time
Waiting
Training
Unallocated
      ↓
Actual shift activities
```

A KPI should always be traceable back to evidence.

Example:

```text
Engineering downtime = 14 h
      ↓
click
      ↓
six contributing events
      ↓
timestamps
      ↓
machines
      ↓
classification
      ↓
original operational record
```

This avoids “mystery numbers.”

---

# 16. Reliability Metrics

Once the data foundation is available, Morning can derive useful reliability metrics.

## MTBF — Mean Time Between Failures

Conceptually:

```text
Operating hours / Number of failures
```

Example:

```text
STC14 — August

Breakdowns:           11
Operating hours:     183 h
Breakdown downtime:   27 h

MTBF:                 16.6 h
```

## MTTR — Mean Time To Repair

Conceptually:

```text
Total repair time / Number of repairs
```

Example:

```text
MTTR: 2.45 h
```

---

# 17. Repeat-Failure Detection

Morning should identify recurring failures.

Example:

```text
STC14 — recurring issues

Hydraulic hoses       7 events   14.2 h downtime
Starting system       4 events    6.8 h
Tyres                 3 events    5.1 h
```

This allows management to recognize chronic problems instead of seeing each repair as an isolated event.

Morning should eventually support configurable windows such as:

```text
Repeat within 24 hours
Repeat within 48 hours
Repeat within 72 hours
```

Possible metric:

```text
First-time resolution       91%
Repeat within 24 h           4%
Repeat within 72 h           7%
```

This is more meaningful than simply counting completed jobs.

---

# 18. Downtime Pareto

Morning should automatically derive a downtime Pareto.

Example:

```text
August downtime

Hydraulic failures      31%
Electrical              18%
Waiting for spares      15%
Tyres                     9%
No operator               8%
Infrastructure            7%
Other                    12%
```

Each category should drill down further.

Example:

```text
Waiting for spares
      ↓
STC14 turbo       8.5 h
RLH3 hose         5.0 h
STV6 lights       2.1 h
...
```

This enables management to identify the relatively small number of causes responsible for most lost hours.

---

# 19. Engineering vs Non-Engineering Losses

Morning should explicitly distinguish loss ownership.

Possible categories:

```text
Engineering loss
Operational loss
Infrastructure loss
Supply-chain loss
Planned standing
```

Example:

```text
Fleet lost hours — August

Engineering              142 h
Operations                87 h
Spares / supply chain     61 h
Infrastructure            38 h
Planned maintenance       54 h
```

This prevents all machine standing time from being incorrectly attributed to engineering.

---

# 20. Lost Opportunity Hours

A particularly useful management metric is:

# **Lost Opportunity Hours**

Conceptually:

```text
Potential machine hours
-
Productive machine hours
=
Lost opportunity hours
```

Morning should then explain those losses:

```text
Lost opportunity: 318 h

Engineering              121 h
Operations                74 h
Supply chain              53 h
Infrastructure            36 h
Planned maintenance       22 h
Other                     12 h
```

This turns downtime into an actionable management view.

---

# 21. Response Time vs Repair Time

If capture can naturally support it, Morning should eventually distinguish:

```text
Breakdown reported
      ↓
Artisan assigned / arrived
      ↓
Repair started
      ↓
Machine returned
```

This allows total downtime to be decomposed into:

```text
Response delay
+
Troubleshooting
+
Waiting for parts
+
Actual repair
+
Testing / return to service
=
Total downtime
```

Example:

```text
4-hour breakdown

45 min waiting for artisan
1 h 20 min troubleshooting
40 min waiting for part
1 h 15 min repair/test
```

These losses require different management actions.

This should only be added if the timestamps can be captured without creating unnecessary reporting burden.

---

# 22. Planned vs Reactive Work

Morning should measure maintenance workload composition.

Example:

```text
Planned work       63%
Reactive work      37%
```

Trend example:

```text
Reactive workload

May       48%
June      42%
July      35%
August    27%
```

This may become a meaningful indicator of whether maintenance is moving from breakdown response toward controlled planning.

---

# 23. Bad-Actor Machines

Morning should automatically identify machines requiring attention.

Example:

```text
Machines requiring attention

1. STC14
   42 h lost
   13 breakdowns
   4 repeat failures
   deteriorating trend

2. RLH3
   31 h lost
   8 breakdowns
   hydraulic system dominant

3. STV6
   19 h lost
   11 small electrical failures
```

A “bad actor” score should be explainable, not opaque.

Inputs might eventually include:

- total lost hours,
- failure frequency,
- repeat-failure count,
- worsening availability trend,
- MTBF deterioration,
- repair duration,
- operational criticality.

---

# 24. Fleet Health Trends

Morning should compare performance over time.

Example:

```text
STC14

30-day availability

May       91%
June      87%
July      82%
August    74%
```

Trend detection should be deterministic wherever possible.

AI may later help explain trends, but the underlying calculations should remain auditable.

---

# 25. Crew and Shift Patterns

Because Morning knows:

- shift,
- crew,
- supervisor,
- machine,
- activity,
- fault category,

it can show patterns by shift or crew.

Example:

```text
Hydraulic failures

Day shift:    18 events
Night shift:  41 events
```

This should not become a simplistic leaderboard.

The purpose is to identify questions worth investigating, such as:

- workload,
- production intensity,
- machine mix,
- staffing,
- inspection practices,
- access,
- environmental conditions.

The data should support investigation, not accusation.

---

# 26. Personnel and Trade Loading

Morning should aggregate utilization by trade.

Example:

```text
Diesel mechanics
  82% assigned
  10% blocked
   8% available/unallocated

Auto electricians
  97% assigned
  18 h work carried forward

Boilermakers
  54% assigned
  32% available/unallocated
```

This can help answer:

> Do we actually need more people?

or:

> Are existing people losing productive time because of spares, access, planning or trade imbalance?

Morning should support both artisan and assistant utilization.

It should also allow analysis of artisan/assistant pairing and crew loading.

---

# 27. Spares Intelligence

Because breakdown records already contain orders/spares information, Morning can eventually derive:

```text
Most frequently required parts
Parts causing longest waits
Machines consuming most spares
Repeat orders for the same component
Downtime attributable to unavailable spares
```

Example:

```text
August spares-related downtime: 61 h

Turbochargers        21 h
Hydraulic hoses      14 h
Starter motors        9 h
Tyres                  8 h
Other                  9 h
```

This could eventually provide useful information to Stores and procurement without creating a separate data-capture process.

---

# 28. Fundamental KPI Families

The broader KPI system can be grouped into several families.

## Machine Performance

- Availability %
- Utilization %
- Running hours
- Standing hours
- Breakdown hours
- Planned vs unplanned downtime

## Reliability

- MTBF
- MTTR
- Breakdown frequency
- Repeat failures
- Failure Pareto
- Chronic / bad-actor machines

## Operational Losses

- Waiting for spares
- No operator
- Infrastructure delay
- Access delay
- Waiting for artisan
- Scheduled standing
- Lost opportunity hours

## Personnel / Resources

- Productively assigned time
- Blocked time
- Available / unallocated time
- Workload distribution
- Trade loading
- Artisan/assistant pairing

## Maintenance Effectiveness

- Planned vs reactive work
- Response time
- Repair duration
- First-time-fix rate
- Repeat repair rate
- Outstanding work

## Management / Trends

- Crew patterns
- Shift patterns
- Downtime by area
- Top loss reasons
- Reliability deterioration
- Recurring bottlenecks

---

# 29. Suggested Dashboard Hierarchy

Morning should have multiple dashboard depths rather than one overloaded page.

## Level 1 — Management Overview

Only major indicators:

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

## Level 2 — Analysis Pages

Example for Availability:

```text
Fleet trend
Downtime by cause
Downtime by machine
Downtime by shift
Top contributors
```

Example for Personnel Utilization:

```text
By trade
By crew
By person
Blocked vs unallocated
Work categories
```

## Level 3 — Evidence

Every metric should eventually drill down into operational records.

Example:

```text
STC14
27 Aug
01:20–02:45
Hydraulic hose failure
Johan + Sipho
Waiting for spares: 25 min
Repair: 1 h
Returned to service
```

This gives Morning an auditable “why” chain.

---

# 30. Morning's Emerging Operational Model

Morning is starting to develop a model of the engineering operation rather than merely a collection of screens.

Conceptually:

```text
SITE
 └─ DEPARTMENT
     ├─ PEOPLE
     │   ├─ crews
     │   ├─ trades
     │   └─ assignments
     │
     ├─ EQUIPMENT
     │   ├─ status
     │   ├─ utilization
     │   └─ failures
     │
     ├─ ACTIVITIES
     │   ├─ breakdown
     │   ├─ maintenance
     │   ├─ inspection
     │   └─ operational delay
     │
     └─ TIME
         ├─ shift
         ├─ 24-hour period
         ├─ week
         └─ month
```

Once those relationships are represented correctly:

> **Reports and KPIs become different views of the same operational truth.**

---

# 31. Data Quality Principle

The mathematics behind most of these KPIs is straightforward.

The difficult part is ensuring that the underlying operational record is correct.

Therefore:

> **Protect the data model before optimizing the dashboard.**

If the event/activity model is clean, most dashboards become relatively easy to calculate.

Morning should prefer deterministic calculations over AI-generated metrics.

AI may later help with:

- explaining trends,
- natural-language exploration,
- summarization,
- identifying interesting correlations,

but the underlying facts and calculations should remain auditable and reproducible.

---

# 32. Product Maturity

Morning is now moving through a significant product transition.

Earlier, it primarily had useful **features**.

It is now developing a coherent **model of engineering operations**.

That changes Morning from:

> “A nicer way to make the morning report”

into:

> **A structured engineering operations system that captures the shift once, generates the reports people need today, preserves operational history, and turns that history into utilization, reliability and management insight.**

This is the point where Morning moves from being a convenience or gimmick into something that can become a genuinely powerful engineering-management tool.

---

# 33. Product North Star

A strong current statement is:

> **Morning captures engineering activity once, turns it into the reports people need today, distributes those reports automatically, and preserves the structured operational history needed tomorrow.**

Expanded with the new analytics direction:

> **Capture once → Resolve operational context → Report automatically → Distribute automatically → Build operational history → Understand the operation.**

Or, in practical terms:

```text
A supervisor captures the shift once.

Morning turns that data into:
- shift handover,
- 24-hour engineering reports,
- machine history,
- machine utilization,
- personnel utilization,
- downtime analysis,
- reliability history,
- management KPIs,
- and future operational insight.
```

---

# 34. Immediate Future Direction

When Morning development resumes, the likely next conceptual work should include:

1. Inspect the existing embedded Morning implementation and preserve what is already useful.
2. Define the structured operational activity/event model needed for reporting and analytics.
3. Implement **24-Hour Reports** as frozen historical report products.
4. Implement **Utilization** with:
   - Machine Utilization
   - Personnel Utilization
5. Establish standing/downtime classifications.
6. Build the first fundamental KPI calculations.
7. Add hierarchical KPI drill-downs.
8. Expand reliability and loss analytics gradually.
9. Keep the capture workflow fast and familiar.
10. Avoid adding administrative work merely for the sake of analytics.

---

# 35. Design Principles to Preserve

The following principles should guide future Morning decisions:

> **Capture once. Use many times.**

> **Do not ask users to re-enter information Morning already knows.**

> **Do not add fields unless they create clear operational value.**

> **Structure what users already report before asking them to report more.**

> **Standing is not automatically engineering downtime.**

> **Personnel utilization is a resource-planning measure, not an employee-performance score.**

> **Preserve historical outcomes, not administrative clutter.**

> **Hard-code the invariants. Configure the circumstances.**

> **Reports and KPIs should be traceable to the operational records that produced them.**

> **Prefer deterministic calculations over AI interpretation where the truth can be calculated directly.**

> **Protect the data model; dashboards are downstream of it.**

---

# 36. Summary

Morning is maturing into a system with three fundamental responsibilities:

```text
CAPTURE
What happened?

REPORT
What does everyone need to know now?

UNDERSTAND
What does accumulated history tell us?
```

The two important new product areas are:

```text
[ 24-Hour Reports ] [ Utilization ]
```

From the same shift information Morning can eventually derive:

- frozen 24-hour engineering reports,
- machine availability,
- machine utilization,
- personnel utilization,
- engineering vs operational loss,
- MTBF,
- MTTR,
- repeat-failure rate,
- first-time-fix rate,
- downtime Pareto,
- bad-actor machines,
- fleet health trends,
- planned vs reactive workload,
- trade loading,
- spares-related loss,
- lost opportunity hours,
- and drill-down evidence for every major KPI.

The product should achieve this **without requiring supervisors to do substantially more than they already do today**.

That is the central opportunity:

> **Use the same operational information more efficiently, instead of demanding more administration.**
