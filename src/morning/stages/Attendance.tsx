import { morningApi } from '../api'
import type { Person, ShiftReport } from '../types'

export function AttendanceStage({ report, people, onUpdated, onNext }: { report: ShiftReport; people: Person[]; onUpdated: (report: ShiftReport) => void; onNext: () => void }) {
  const presentIds = new Set(report.attendance.filter((e) => e.present).map((e) => e.person_id))
  const recordedIds = new Set(report.attendance.map((e) => e.person_id))
  const setStatus = async (personId: string, present: boolean) => {
    const entries = people.filter((p) => p.id === personId || recordedIds.has(p.id)).map((p) => ({ person_id: p.id, present: p.id === personId ? present : presentIds.has(p.id) }))
    onUpdated(await morningApi<ShiftReport>(`/api/morning/reports/${report.id}/attendance`, { method: 'POST', body: JSON.stringify({ entries }) }))
  }
  return <div className="morning-stage">
    {!people.length ? <p className="empty">No personnel rostered for this shift yet.</p> : null}
    <div className="morning-attendance-list">{people.map((person) => <div key={person.id} className="morning-attendance-row"><div className="morning-attendance-name"><strong>{person.name}</strong>{person.role ? <span className="meta">{person.role}</span> : null}</div><div className="morning-attendance-actions"><button type="button" className={recordedIds.has(person.id) && presentIds.has(person.id) ? 'morning-present active' : 'morning-present'} onClick={() => void setStatus(person.id, true)}>Present</button><button type="button" className={recordedIds.has(person.id) && !presentIds.has(person.id) ? 'morning-absent active' : 'morning-absent'} onClick={() => void setStatus(person.id, false)}>Absent</button></div></div>)}</div>
    <div className="morning-stage-nav"><button type="button" className="primary" onClick={onNext}>Next: Safety</button></div>
  </div>
}
