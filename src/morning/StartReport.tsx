import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { morningApi } from './api'
import { formatShiftDate } from './format'
import type { ShiftIdentity, ShiftKind, ShiftReport, SupervisorContext } from './types'

export function StartReport({ suggestion, supervisor, onStarted }: { suggestion?: ShiftIdentity; supervisor?: SupervisorContext; onStarted: (report: ShiftReport) => void }) {
  const [override, setOverride] = useState<ShiftKind | null>(null)
  const shiftKind = override ?? suggestion?.shift_kind ?? 'day'
  const start = useMutation({ mutationFn: () => morningApi<ShiftReport>('/api/morning/draft', { method: 'POST', body: JSON.stringify({ shift_date: suggestion?.shift_date, shift_kind: shiftKind }) }), onSuccess: onStarted })
  return <div className="morning-start-report">
    <h2 className="morning-stage-title">Start shift report</h2>
    <dl className="morning-start-report-facts">
      <div className="morning-start-report-fact"><dt>Reporting date</dt><dd>{suggestion ? formatShiftDate(suggestion.shift_date) : '…'}</dd></div>
      <div className="morning-start-report-fact"><dt>Shift</dt><dd><div className="morning-auth-toggle" role="radiogroup" aria-label="Shift"><button type="button" className={shiftKind === 'day' ? 'active' : ''} onClick={() => setOverride('day')}>Day</button><button type="button" className={shiftKind === 'night' ? 'active' : ''} onClick={() => setOverride('night')}>Night</button></div></dd></div>
      <div className="morning-start-report-fact"><dt>Crew</dt><dd>{supervisor?.crew_name || 'No crew linked — contact an administrator'}</dd></div>
      <div className="morning-start-report-fact"><dt>Supervisor</dt><dd>{supervisor?.display_name || '…'}</dd></div>
    </dl>
    {start.isError ? <p className="error-text">Could not start the report. Try again.</p> : null}
    <button type="button" className="primary" disabled={!suggestion || start.isPending} onClick={() => start.mutate()}>{start.isPending ? 'Starting…' : 'Start report'}</button>
  </div>
}
