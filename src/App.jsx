import { useMemo, useState } from 'react'
import {
  navigation,
  machines,
  people,
  activityLog,
  reportHistory,
  dashboardKpis,
  downtimePareto,
  lossOwnership,
  tradeLoading,
  failureFamilies,
  currentShiftSeed,
} from './data.js'

function Icon({ name, size = 18 }) {
  const common = { width: size, height: size, viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', strokeWidth: 1.8, strokeLinecap: 'round', strokeLinejoin: 'round', 'aria-hidden': true }
  const paths = {
    grid: <><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/></>,
    clipboard: <><rect x="5" y="4" width="14" height="17" rx="2"/><path d="M9 4.5V3h6v1.5M8 9h8M8 13h8M8 17h5"/></>,
    report: <><path d="M6 3h9l3 3v15H6z"/><path d="M14 3v4h4M9 11h6M9 15h6M9 19h4"/></>,
    gauge: <><path d="M4.2 18a9 9 0 1 1 15.6 0"/><path d="M12 13l4-4"/><path d="M8 18h8"/></>,
    pulse: <><path d="M3 12h4l2-5 4 10 2-5h6"/></>,
    chevron: <path d="M9 18l6-6-6-6"/>,
    arrow: <path d="M5 12h14M14 7l5 5-5 5"/>,
    clock: <><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></>,
    machine: <><path d="M4 17h16M6 17v-5h12v5M8 12V8h8v4M9 8V5h6v3"/><circle cx="8" cy="19" r="1"/><circle cx="16" cy="19" r="1"/></>,
    person: <><circle cx="12" cy="8" r="3"/><path d="M5 20c.8-4.2 3.2-6 7-6s6.2 1.8 7 6"/></>,
    download: <><path d="M12 3v12M8 11l4 4 4-4"/><path d="M5 20h14"/></>,
    close: <><path d="M6 6l12 12M18 6L6 18"/></>,
    plus: <><path d="M12 5v14M5 12h14"/></>,
    check: <path d="M5 12l4 4L19 6"/>,
    filter: <path d="M4 5h16l-6 7v6l-4 2v-8z"/>,
    menu: <><path d="M4 7h16M4 12h16M4 17h16"/></>,
    search: <><circle cx="11" cy="11" r="6"/><path d="M16 16l4 4"/></>,
    spark: <><path d="M4 17l4-5 4 2 4-7 4 3"/></>,
    alert: <><path d="M12 3l10 18H2z"/><path d="M12 9v5M12 17h.01"/></>,
  }
  return <svg {...common}>{paths[name] || paths.grid}</svg>
}

function Sparkline({ values, tone = 'gold' }) {
  const max = Math.max(...values)
  const min = Math.min(...values)
  const span = max - min || 1
  const pts = values.map((v, i) => `${(i / (values.length - 1)) * 100},${34 - ((v - min) / span) * 28}`).join(' ')
  return (
    <svg className={`sparkline ${tone}`} viewBox="0 0 100 38" preserveAspectRatio="none" aria-hidden="true">
      <polyline points={pts} fill="none" vectorEffect="non-scaling-stroke" />
    </svg>
  )
}

function ProgressBar({ value, secondary = 0, tertiary = 0, label }) {
  return (
    <div className="progress-wrap" aria-label={label}>
      <div className="progress-track">
        <span className="progress-primary" style={{ width: `${Math.min(value, 100)}%` }} />
        {secondary > 0 && <span className="progress-secondary" style={{ width: `${Math.min(secondary, 100 - value)}%`, left: `${value}%` }} />}
        {tertiary > 0 && <span className="progress-tertiary" style={{ width: `${Math.min(tertiary, 100 - value - secondary)}%`, left: `${value + secondary}%` }} />}
      </div>
    </div>
  )
}

function PageHeader({ eyebrow, title, subtitle, actions }) {
  return (
    <div className="page-header">
      <div>
        {eyebrow && <div className="eyebrow">{eyebrow}</div>}
        <h1>{title}</h1>
        {subtitle && <p>{subtitle}</p>}
      </div>
      {actions && <div className="page-actions">{actions}</div>}
    </div>
  )
}

function KpiCard({ kpi, onClick }) {
  return (
    <button className={`kpi-card accent-${kpi.accent}`} onClick={onClick}>
      <div className="kpi-topline">
        <span>{kpi.label}</span>
        <Icon name="chevron" size={16} />
      </div>
      <div className="kpi-value">{kpi.value}</div>
      <div className="kpi-footer">
        <span className={`delta ${kpi.deltaTone}`}>{kpi.delta}</span>
        <span>{kpi.hint}</span>
      </div>
    </button>
  )
}

function Overview({ onOpenKpi, onNavigate }) {
  return (
    <section>
      <PageHeader
        eyebrow="TMM Engineering · 27 August 2026"
        title="Good evening"
        subtitle="A live prototype view of the operation — from headline KPIs down to the evidence behind them."
        actions={<button className="button primary" onClick={() => onNavigate('shift')}><Icon name="plus" size={16}/> Capture activity</button>}
      />

      <div className="status-strip">
        <div><span className="status-dot live"/><strong>Night shift active</strong><span>Lyle · Crew A</span></div>
        <div><Icon name="clock" size={16}/><strong>24-hour period</strong><span>06:00 → 05:59</span></div>
        <div><span className="status-dot warn"/><strong>2 exceptions</strong><span>need review before publish</span></div>
      </div>

      <div className="section-title-row">
        <div><span className="eyebrow">Fundamental KPIs</span><h2>Operating picture</h2></div>
        <span className="section-note">Rolling 30 days · click any KPI to drill down</span>
      </div>
      <div className="kpi-grid">
        {dashboardKpis.map(kpi => <KpiCard key={kpi.id} kpi={kpi} onClick={() => onOpenKpi(kpi.id)} />)}
      </div>

      <div className="dashboard-grid two-one">
        <article className="panel">
          <div className="panel-head">
            <div><span className="eyebrow">Loss analysis</span><h3>Downtime Pareto</h3></div>
            <button className="text-button" onClick={() => onOpenKpi('engineering')}>Explore <Icon name="arrow" size={14}/></button>
          </div>
          <div className="pareto-list">
            {downtimePareto.slice(0, 6).map((row, index) => (
              <div className="pareto-row" key={row.label}>
                <span className="rank">{String(index + 1).padStart(2, '0')}</span>
                <div className="pareto-name"><strong>{row.label}</strong><small>{row.owner}</small></div>
                <div className="bar-cell"><div className="bar-bg"><span style={{ width: `${row.value}%` }}/></div></div>
                <span className="metric-cell">{row.hours.toFixed(1)} h</span>
                <span className="percent-cell">{row.value}%</span>
              </div>
            ))}
          </div>
        </article>

        <article className="panel bad-actors">
          <div className="panel-head"><div><span className="eyebrow">Attention</span><h3>Bad actors</h3></div></div>
          {machines.slice(0, 3).map((m, i) => (
            <button className="actor-row" key={m.id} onClick={() => onNavigate('utilization', { type: 'machine', id: m.id })}>
              <span className={`actor-rank rank-${i + 1}`}>{i + 1}</span>
              <span className="actor-copy"><strong>{m.id}</strong><small>{m.failures} failures · {m.lost} h lost</small></span>
              <span className="actor-availability">{m.availability}%</span>
            </button>
          ))}
          <div className="panel-callout"><Icon name="alert" size={17}/><span>STC14 hydraulic circuit has repeated 3 times in 72 hours.</span></div>
        </article>
      </div>

      <div className="dashboard-grid equal">
        <article className="panel">
          <div className="panel-head"><div><span className="eyebrow">Fleet trend</span><h3>Availability by machine</h3></div></div>
          <div className="machine-trend-list">
            {machines.map(m => (
              <button className="machine-trend" key={m.id} onClick={() => onNavigate('utilization', { type: 'machine', id: m.id })}>
                <div><strong>{m.id}</strong><small>{m.type}</small></div>
                <Sparkline values={m.trend} tone={m.availability < 80 ? 'red' : 'gold'} />
                <span className={m.availability < 80 ? 'bad-number' : ''}>{m.availability}%</span>
              </button>
            ))}
          </div>
        </article>

        <article className="panel">
          <div className="panel-head"><div><span className="eyebrow">Resource loading</span><h3>Trade utilization</h3></div><button className="text-button" onClick={() => onNavigate('utilization', { type: 'person' })}>People <Icon name="arrow" size={14}/></button></div>
          <div className="trade-list">
            {tradeLoading.map(t => (
              <div className="trade-row" key={t.trade}>
                <div className="trade-label"><strong>{t.trade}</strong><span>{t.assigned}% assigned</span></div>
                <ProgressBar value={t.assigned} secondary={t.blocked} tertiary={t.free} label={`${t.trade} utilization`} />
                <div className="trade-legend"><span><i className="legend assigned"/>Assigned {t.assigned}%</span><span><i className="legend blocked"/>Blocked {t.blocked}%</span><span><i className="legend free"/>Available {t.free}%</span></div>
              </div>
            ))}
          </div>
        </article>
      </div>
    </section>
  )
}

function ShiftCapture() {
  const [started, setStarted] = useState(false)
  const [shiftKind, setShiftKind] = useState(currentShiftSeed.suggestion)
  const [entries, setEntries] = useState(activityLog.slice(0, 3))
  const [showForm, setShowForm] = useState(false)
  const [submitted, setSubmitted] = useState(false)

  const addDemoEntry = () => {
    const next = {
      id: `A-${1050 + entries.length}`,
      date: '27 Aug', start: '22:40', end: '23:25', machine: 'RLH1',
      category: 'Breakdown', owner: 'Engineering', failure: 'Engine',
      detail: 'Low boost pressure investigated. Hose clamp replaced and machine tested.',
      people: ['Johan M.', 'Thabo K.'], delay: 'None', status: 'Returned to service',
    }
    setEntries(prev => [next, ...prev])
    setShowForm(false)
  }

  if (!started) {
    return (
      <section>
        <PageHeader eyebrow="Shift capture" title="Start shift report" subtitle="Morning suggests the shift from the clock. The supervisor confirms it before anything is created." />
        <div className="start-layout">
          <article className="start-card">
            <div className="start-brand-mark"><span>M</span></div>
            <h2>Ready for the next shift</h2>
            <p>Capture the work once. Morning will turn the same operational record into handover, reporting, history and utilization.</p>
            <dl className="start-facts">
              <div><dt>Reporting date</dt><dd>{currentShiftSeed.date}</dd></div>
              <div><dt>Shift</dt><dd><div className="segmented compact"><button className={shiftKind === 'Day' ? 'active' : ''} onClick={() => setShiftKind('Day')}>Day</button><button className={shiftKind === 'Night' ? 'active' : ''} onClick={() => setShiftKind('Night')}>Night</button></div></dd></div>
              <div><dt>Crew</dt><dd>{currentShiftSeed.crew}</dd></div>
              <div><dt>Supervisor</dt><dd>{currentShiftSeed.supervisor}</dd></div>
              <div><dt>Department</dt><dd>{currentShiftSeed.department}</dd></div>
            </dl>
            <button className="button primary wide" onClick={() => setStarted(true)}>Start {shiftKind.toLowerCase()} report <Icon name="arrow" size={16}/></button>
          </article>
          <aside className="principle-card">
            <span className="eyebrow">Prototype principle</span>
            <blockquote>“Capture once. Never make the user re-enter information Morning already knows.”</blockquote>
            <div className="flow-mini"><span>Shift capture</span><i/><span>24-hour report</span><i/><span>Utilization</span><i/><span>KPIs</span></div>
          </aside>
        </div>
      </section>
    )
  }

  return (
    <section>
      <PageHeader
        eyebrow={`${currentShiftSeed.department} · ${shiftKind} shift`}
        title={submitted ? 'Shift submitted' : 'Shift report in progress'}
        subtitle={submitted ? 'This prototype freezes the submitted shift as a historical record.' : `${currentShiftSeed.supervisor} · ${currentShiftSeed.crew} · 27 August 2026`}
        actions={!submitted && <button className="button primary" onClick={() => setShowForm(true)}><Icon name="plus" size={16}/> Add activity</button>}
      />
      {submitted ? (
        <div className="success-state"><div className="success-icon"><Icon name="check" size={28}/></div><h2>Shift captured once.</h2><p>The same {entries.length} structured activities are now available to the 24-hour report, machine history, personnel utilization and KPI projections.</p><button className="button secondary" onClick={() => { setSubmitted(false); setStarted(false) }}>Start another prototype shift</button></div>
      ) : (
        <>
          <div className="shift-summary-row">
            <div><span>Activities</span><strong>{entries.length}</strong></div>
            <div><span>Engineering</span><strong>{entries.filter(e => e.owner === 'Engineering').length}</strong></div>
            <div><span>Non-engineering</span><strong>{entries.filter(e => e.owner !== 'Engineering').length}</strong></div>
            <div><span>Exceptions</span><strong className="warn-text">2</strong></div>
          </div>
          <article className="panel activity-panel">
            <div className="panel-head"><div><span className="eyebrow">Operational record</span><h3>Activities captured this shift</h3></div><button className="text-button"><Icon name="filter" size={14}/> Filter</button></div>
            <div className="activity-table">
              {entries.map(e => <ActivityRow key={e.id} activity={e} />)}
            </div>
          </article>
          <div className="submit-bar"><div><strong>Ready when you are.</strong><span>Submitting freezes the shift context; corrections remain auditable.</span></div><button className="button primary" onClick={() => setSubmitted(true)}>Submit shift report <Icon name="check" size={16}/></button></div>
        </>
      )}
      {showForm && <ActivityModal onClose={() => setShowForm(false)} onSave={addDemoEntry} />}
    </section>
  )
}

function ActivityModal({ onClose, onSave }) {
  return (
    <div className="modal-backdrop" onMouseDown={e => e.target === e.currentTarget && onClose()}>
      <div className="modal activity-modal">
        <div className="modal-head"><div><span className="eyebrow">New operational activity</span><h2>Capture what happened</h2></div><button className="icon-button" onClick={onClose}><Icon name="close"/></button></div>
        <div className="form-grid">
          <label><span>Machine</span><select defaultValue="RLH1"><option>RLH1</option><option>STC14</option><option>RLH3</option><option>STV6</option><option>L91</option></select></label>
          <label><span>Activity type</span><select defaultValue="Breakdown"><option>Breakdown</option><option>Planned maintenance</option><option>Inspection</option><option>Operational delay</option><option>Waiting for spares</option></select></label>
          <label><span>Start</span><input type="time" defaultValue="22:40" /></label>
          <label><span>End</span><input type="time" defaultValue="23:25" /></label>
          <label><span>Loss owner</span><select defaultValue="Engineering"><option>Engineering</option><option>Operations</option><option>Supply Chain</option><option>Infrastructure</option><option>Planned</option></select></label>
          <label><span>Failure category</span><select defaultValue="Engine"><option>Hydraulics</option><option>Electrical</option><option>Engine</option><option>Tyres</option><option>Other</option></select></label>
          <label className="span-two"><span>People involved</span><input defaultValue="Johan M., Thabo K." /></label>
          <label className="span-two"><span>What happened</span><textarea rows="4" defaultValue="Low boost pressure investigated. Hose clamp replaced and machine tested." /></label>
          <label><span>Last reported state</span><select defaultValue="Returned to service"><option>Returned to service</option><option>Work ongoing</option><option>Awaiting spares</option><option>Not tested</option></select></label>
          <label><span>Delay / blocker</span><input defaultValue="None" /></label>
        </div>
        <div className="modal-footer"><button className="button secondary" onClick={onClose}>Cancel</button><button className="button primary" onClick={onSave}>Save activity <Icon name="check" size={16}/></button></div>
      </div>
    </div>
  )
}

function ActivityRow({ activity, compact = false }) {
  return (
    <div className={`activity-row ${compact ? 'compact-row' : ''}`}>
      <div className="activity-time"><strong>{activity.start}</strong><span>{activity.end}</span></div>
      <div className="activity-machine"><strong>{activity.machine}</strong><span>{activity.category}</span></div>
      <div className="activity-main"><strong>{activity.detail}</strong><div className="activity-tags"><span>{activity.failure}</span><span className={`owner owner-${activity.owner.toLowerCase().replaceAll(' ', '-')}`}>{activity.owner}</span>{activity.people.length > 0 && <span>{activity.people.join(' + ')}</span>}</div></div>
      <div className="activity-state"><span>{activity.status}</span><small>{activity.delay}</small></div>
    </div>
  )
}

function Reports() {
  const [selected, setSelected] = useState(null)
  return (
    <section>
      <PageHeader eyebrow="Published history" title="24-Hour Reports" subtitle="Each published report is a frozen historical snapshot of the full engineering period." actions={<button className="button secondary"><Icon name="search" size={16}/> Search reports</button>} />
      <div className="report-list panel">
        <div className="report-list-head"><span>Reporting period</span><span>Availability</span><span>Downtime</span><span>Activities</span><span>Status</span><span/></div>
        {reportHistory.map(r => (
          <button className="report-row" key={r.id} onClick={() => setSelected(r)}>
            <span className="report-date"><strong>{r.date}</strong><small>{r.period}</small></span>
            <strong>{r.availability}</strong><span>{r.downtime}</span><span>{r.activities}</span>
            <span className="status-pill published"><i/>Published</span><Icon name="chevron" size={16}/>
          </button>
        ))}
      </div>
      {selected && <ReportViewer report={selected} onClose={() => setSelected(null)} />}
    </section>
  )
}

function ReportViewer({ report, onClose }) {
  const download = () => {
    const text = `Morning — 24-Hour Engineering Report\n${report.period}\n\nFleet availability: ${report.availability}\nEngineering downtime: ${report.downtime}\nActivities: ${report.activities}\n\nPrototype artifact — PDF rendering is a production implementation concern.`
    const blob = new Blob([text], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url; a.download = `Morning-${report.id}.txt`; a.click(); URL.revokeObjectURL(url)
  }
  return (
    <div className="modal-backdrop report-backdrop">
      <div className="report-viewer">
        <header className="report-toolbar"><div><span className="eyebrow">Frozen snapshot</span><strong>{report.date}</strong></div><div><button className="button secondary" onClick={download}><Icon name="download" size={16}/> Download prototype</button><button className="icon-button" onClick={onClose}><Icon name="close"/></button></div></header>
        <div className="paper-wrap">
          <article className="report-paper">
            <div className="paper-brand"><div className="paper-mark">M</div><div><strong>MORNING</strong><span>Engineering Operations</span></div><div className="paper-meta"><span>24-HOUR REPORT</span><strong>{report.date}</strong></div></div>
            <div className="paper-title"><span>TMM ENGINEERING</span><h1>24-Hour Engineering Report</h1><p>{report.period}</p></div>
            <div className="paper-kpis"><div><span>Fleet availability</span><strong>{report.availability}</strong></div><div><span>Engineering downtime</span><strong>{report.downtime}</strong></div><div><span>Activities captured</span><strong>{report.activities}</strong></div><div><span>Exceptions</span><strong>{report.exceptions}</strong></div></div>
            <section className="paper-section"><h2>Management Summary</h2><p>Fleet availability remains below the 30-day baseline, driven primarily by STC14 and RLH3. Hydraulic failures remain the largest engineering loss category. Two exceptions require follow-up: repeat hydraulic failures on STC14 and outstanding spares delay attribution.</p></section>
            <section className="paper-section"><h2>Machine Activity</h2>{activityLog.slice(0, 5).map(a => <div className="paper-activity" key={a.id}><strong>{a.machine}</strong><span>{a.start}–{a.end}</span><p>{a.detail}</p><em>{a.status}</em></div>)}</section>
            <section className="paper-section"><h2>Loss Ownership</h2><div className="paper-loss-grid">{lossOwnership.slice(0, 5).map(l => <div key={l.label}><span>{l.label}</span><strong>{l.hours} h</strong></div>)}</div></section>
            <footer className="paper-footer"><span>Published {report.date} at {report.generated}</span><span>Historical snapshot · source records preserved</span></footer>
          </article>
        </div>
      </div>
    </div>
  )
}

function Utilization({ initialSelection }) {
  const [kind, setKind] = useState(initialSelection?.type === 'person' ? 'person' : 'machine')
  const [machineId, setMachineId] = useState(initialSelection?.id || machines[0].id)
  const [personId, setPersonId] = useState(people[0].id)
  const machine = machines.find(m => m.id === machineId) || machines[0]
  const person = people.find(p => p.id === personId) || people[0]
  const relevant = activityLog.filter(a => a.machine === machine.id)

  return (
    <section>
      <PageHeader eyebrow="Operational history" title="Utilization" subtitle="See how equipment and people were actually used — and why productive time was lost." actions={<div className="period-picker">01–31 Aug 2026 <Icon name="chevron" size={14}/></div>} />
      <div className="segmented utilization-switch"><button className={kind === 'machine' ? 'active' : ''} onClick={() => setKind('machine')}><Icon name="machine" size={16}/> Machines</button><button className={kind === 'person' ? 'active' : ''} onClick={() => setKind('person')}><Icon name="person" size={16}/> Personnel</button></div>
      {kind === 'machine' ? (
        <div className="util-layout">
          <aside className="entity-list panel"><div className="entity-list-head"><span>Fleet</span><small>{machines.length} machines</small></div>{machines.map(m => <button key={m.id} className={m.id === machine.id ? 'active' : ''} onClick={() => setMachineId(m.id)}><div><strong>{m.id}</strong><span>{m.type}</span></div><b className={m.availability < 80 ? 'bad-number' : ''}>{m.availability}%</b></button>)}</aside>
          <div className="util-content"><MachineDetail machine={machine} activities={relevant} /></div>
        </div>
      ) : (
        <div className="util-layout">
          <aside className="entity-list panel"><div className="entity-list-head"><span>Personnel</span><small>{people.length} people</small></div>{people.map(p => <button key={p.id} className={p.id === person.id ? 'active' : ''} onClick={() => setPersonId(p.id)}><div><strong>{p.name}</strong><span>{p.role}</span></div><b>{p.assigned}%</b></button>)}</aside>
          <div className="util-content"><PersonDetail person={person} /></div>
        </div>
      )}
    </section>
  )
}

function MachineDetail({ machine, activities }) {
  return (
    <>
      <article className="entity-hero panel"><div><span className="eyebrow">{machine.area}</span><h2>{machine.id}</h2><p>{machine.type}</p></div><div className="hero-spark"><Sparkline values={machine.trend} tone={machine.availability < 80 ? 'red' : 'gold'}/><span>6-month availability trend</span></div></article>
      <div className="mini-kpi-grid"><div><span>Availability</span><strong>{machine.availability}%</strong><small>scheduled time</small></div><div><span>Utilization</span><strong>{machine.utilization}%</strong><small>when available</small></div><div><span>Lost hours</span><strong>{machine.lost} h</strong><small>rolling 30 days</small></div><div><span>MTTR</span><strong>{machine.mttr} h</strong><small>{machine.failures} failures</small></div></div>
      <article className="panel utilization-breakdown"><div className="panel-head"><div><span className="eyebrow">Time allocation</span><h3>How {machine.id} was utilized</h3></div></div><div className="stacked-time"><span className="running" style={{width:'61%'}}/><span className="breakdown" style={{width:'16%'}}/><span className="planned" style={{width:'9%'}}/><span className="ops" style={{width:'8%'}}/><span className="supply" style={{width:'6%'}}/></div><div className="stack-legend"><span><i className="running"/>Running 61%</span><span><i className="breakdown"/>Breakdown 16%</span><span><i className="planned"/>Planned 9%</span><span><i className="ops"/>Operational 8%</span><span><i className="supply"/>Spares 6%</span></div></article>
      <article className="panel"><div className="panel-head"><div><span className="eyebrow">Evidence</span><h3>Operational history</h3></div><span className="section-note">Every metric can drill back to these records</span></div><div className="activity-table">{(activities.length ? activities : activityLog.slice(0,2)).map(a => <ActivityRow key={a.id} activity={a} compact />)}</div></article>
    </>
  )
}

function PersonDetail({ person }) {
  const personActivities = activityLog.filter(a => a.people.includes(person.name))
  return (
    <>
      <article className="entity-hero panel person-hero"><div className="person-avatar">{person.name.split(' ').map(x => x[0]).join('').slice(0,2)}</div><div><span className="eyebrow">{person.trade}</span><h2>{person.name}</h2><p>{person.role}</p></div><div className="hero-spark"><Sparkline values={person.trend}/><span>6-month assigned-time trend</span></div></article>
      <div className="mini-kpi-grid"><div><span>Assigned</span><strong>{person.assigned}%</strong><small>productive activity</small></div><div><span>Blocked</span><strong>{person.blocked}%</strong><small>cause retained</small></div><div><span>Available</span><strong>{person.unallocated}%</strong><small>unallocated</small></div><div><span>Recorded</span><strong>{person.hours} h</strong><small>on-shift hours</small></div></div>
      <article className="panel utilization-breakdown"><div className="panel-head"><div><span className="eyebrow">Resource view</span><h3>How time was utilized</h3></div><span className="context-note">Not a performance score</span></div><ProgressBar value={person.assigned} secondary={person.blocked} tertiary={person.unallocated} label="Personnel utilization"/><div className="people-breakdown"><div><strong>{person.assigned}%</strong><span>Productively assigned</span></div><div><strong>{person.blocked}%</strong><span>Blocked</span></div><div><strong>{person.unallocated}%</strong><span>Available / unallocated</span></div><div><strong>{person.other}%</strong><span>Training / meeting / other</span></div></div></article>
      <article className="panel"><div className="panel-head"><div><span className="eyebrow">Evidence</span><h3>Activity participation</h3></div></div><div className="activity-table">{(personActivities.length ? personActivities : activityLog.slice(0,2)).map(a => <ActivityRow key={a.id} activity={a} compact />)}</div></article>
    </>
  )
}

function Reliability() {
  return (
    <section>
      <PageHeader eyebrow="Maintenance intelligence" title="Reliability" subtitle="Turn accumulated operational history into repeat-failure, bad-actor and repair-quality insight." />
      <div className="reliability-hero-grid">
        <article className="panel reliability-callout"><span className="eyebrow">Priority insight</span><h2>STC14 hydraulic failures are recurring.</h2><p>Three events on the same hydraulic circuit were captured inside the 72-hour repeat window. Together they account for 8.4 hours of downtime.</p><button className="button secondary">Open evidence <Icon name="arrow" size={15}/></button></article>
        <article className="panel health-score"><span className="eyebrow">Fleet reliability</span><div className="score-ring"><div><strong>76</strong><span>/100</span></div></div><p>Deterministic composite preview — not an AI health score.</p></article>
      </div>
      <div className="dashboard-grid equal">
        <article className="panel"><div className="panel-head"><div><span className="eyebrow">Failure families</span><h3>Recurring causes</h3></div></div><div className="failure-table">{failureFamilies.map(f => <div key={f.name}><div><strong>{f.name}</strong><span>{f.events} events</span></div><strong>{f.downtime} h</strong><span>{f.repeats} repeats</span><span className={`trend-${f.trend}`}>{f.trend === 'up' ? '↑ worsening' : f.trend === 'down' ? '↓ improving' : '→ stable'}</span></div>)}</div></article>
        <article className="panel"><div className="panel-head"><div><span className="eyebrow">Repair effectiveness</span><h3>Quality indicators</h3></div></div><div className="quality-grid"><div><span>First-time resolution</span><strong>91%</strong><small>all completed repairs</small></div><div><span>Repeat within 24h</span><strong>4%</strong><small>watch threshold 5%</small></div><div><span>Repeat within 72h</span><strong>7%</strong><small>9 events</small></div><div><span>Median repair time</span><strong>1.6 h</strong><small>vs MTTR 2.14 h</small></div></div></article>
      </div>
      <article className="panel"><div className="panel-head"><div><span className="eyebrow">Bad-actor ranking</span><h3>Machines requiring attention</h3></div><span className="section-note">Explainable inputs: lost hours · failures · repeats · trend</span></div><div className="bad-actor-table">{machines.map((m,i) => <div key={m.id}><span className="actor-rank">{i+1}</span><div><strong>{m.id}</strong><span>{m.type}</span></div><div><span>Lost</span><strong>{m.lost} h</strong></div><div><span>Failures</span><strong>{m.failures}</strong></div><div><span>Repeats</span><strong>{m.repeat}</strong></div><div><span>Availability</span><strong>{m.availability}%</strong></div></div>)}</div></article>
    </section>
  )
}

function KpiDrawer({ id, onClose }) {
  const kpi = dashboardKpis.find(k => k.id === id) || dashboardKpis[0]
  const titles = {
    availability: ['Fleet Availability', 'Why availability is 82.4%'],
    utilization: ['Fleet Utilization', 'Where available machine hours went'],
    engineering: ['Engineering Downtime', 'What created 121 engineering lost hours'],
    opportunity: ['Lost Opportunity', 'Where 318 potential productive hours went'],
    repeat: ['Repeat Failures', 'Which faults returned inside 72 hours'],
    mttr: ['MTTR', 'What is driving repair duration'],
    people: ['Personnel Utilization', 'Assigned, blocked and available time'],
    reactive: ['Reactive Workload', 'How engineering hours are being consumed'],
  }
  return (
    <div className="drawer-backdrop" onMouseDown={e => e.target === e.currentTarget && onClose()}>
      <aside className="drawer">
        <div className="drawer-head"><div><span className="eyebrow">KPI drill-down</span><h2>{titles[id]?.[0] || kpi.label}</h2><p>{titles[id]?.[1]}</p></div><button className="icon-button" onClick={onClose}><Icon name="close"/></button></div>
        <div className="drawer-kpi"><strong>{kpi.value}</strong><span className={`delta ${kpi.deltaTone}`}>{kpi.delta} · {kpi.hint}</span></div>
        {(id === 'opportunity' || id === 'engineering' || id === 'availability') ? (
          <><h3 className="drawer-section-title">Loss ownership</h3><div className="drawer-bars">{lossOwnership.map(l => <div key={l.label}><div><span>{l.label}</span><strong>{l.hours} h</strong></div><div className="bar-bg"><span style={{width:`${l.percent}%`}}/></div></div>)}</div><h3 className="drawer-section-title">Source evidence</h3><div className="drawer-activities">{activityLog.slice(0,4).map(a => <ActivityRow key={a.id} activity={a} compact />)}</div></>
        ) : id === 'people' ? (
          <><h3 className="drawer-section-title">Trade loading</h3><div className="drawer-bars">{tradeLoading.map(t => <div key={t.trade}><div><span>{t.trade}</span><strong>{t.assigned}%</strong></div><ProgressBar value={t.assigned} secondary={t.blocked} tertiary={t.free}/></div>)}</div></>
        ) : (
          <><h3 className="drawer-section-title">Top contributors</h3><div className="drawer-bars">{machines.slice(0,4).map(m => <div key={m.id}><div><span>{m.id}</span><strong>{id === 'repeat' ? `${m.repeat} repeats` : id === 'mttr' ? `${m.mttr} h` : `${m.utilization}%`}</strong></div><div className="bar-bg"><span style={{width:`${Math.max(10, id === 'repeat' ? m.repeat*20 : id === 'mttr' ? m.mttr*25 : m.utilization)}%`}}/></div></div>)}</div></>
        )}
        <div className="drawer-principle"><Icon name="spark" size={18}/><p><strong>Explainable by construction.</strong> Production Morning should let every fundamental KPI drill all the way back to the structured activity records that produced it.</p></div>
      </aside>
    </div>
  )
}

export default function App() {
  const [page, setPage] = useState('overview')
  const [mobileOpen, setMobileOpen] = useState(false)
  const [kpiDrawer, setKpiDrawer] = useState(null)
  const [navContext, setNavContext] = useState(null)

  const navigate = (next, context = null) => {
    setPage(next); setNavContext(context); setMobileOpen(false); window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  const title = useMemo(() => navigation.find(n => n.id === page)?.label || 'Morning', [page])

  return (
    <div className="app-shell">
      <aside className={`sidebar ${mobileOpen ? 'mobile-open' : ''}`}>
        <div className="brand"><div className="brand-mark">M</div><div><strong>Morning</strong><span>Engineering Operations</span></div></div>
        <nav>{navigation.map(n => <button key={n.id} className={page === n.id ? 'active' : ''} onClick={() => navigate(n.id)}><Icon name={n.icon}/><span>{n.label}</span></button>)}</nav>
        <div className="sidebar-foot"><div className="prototype-badge"><span className="status-dot live"/>Interactive prototype</div><p>Prototype build · assumptions remain provisional.</p></div>
      </aside>
      {mobileOpen && <button className="mobile-scrim" onClick={() => setMobileOpen(false)} aria-label="Close menu"/>}
      <div className="app-main">
        <header className="topbar"><button className="mobile-menu" onClick={() => setMobileOpen(true)} aria-label="Open menu"><Icon name="menu"/></button><div className="mobile-title">{title}</div><div className="topbar-context"><span className="status-dot live"/><span>TMM Engineering</span><b>•</b><span>Night shift</span></div><div className="user-pill"><div>JF</div><span><strong>Engineering Lead</strong><small>Cullinan · TMM</small></span></div></header>
        <main className="content">
          {page === 'overview' && <Overview onOpenKpi={setKpiDrawer} onNavigate={navigate} />}
          {page === 'shift' && <ShiftCapture />}
          {page === 'reports' && <Reports />}
          {page === 'utilization' && <Utilization initialSelection={navContext} />}
          {page === 'reliability' && <Reliability />}
        </main>
        <footer className="app-footer"><span>Morning · interactive learning prototype</span><span>Seed data only — assumptions are intentionally easy to change.</span></footer>
      </div>
      <nav className="mobile-bottom-nav">{navigation.slice(0,4).map(n => <button key={n.id} className={page === n.id ? 'active' : ''} onClick={() => navigate(n.id)}><Icon name={n.icon} size={19}/><span>{n.label === '24-Hour Reports' ? 'Reports' : n.label.replace(' Capture','')}</span></button>)}</nav>
      {kpiDrawer && <KpiDrawer id={kpiDrawer} onClose={() => setKpiDrawer(null)} />}
    </div>
  )
}
