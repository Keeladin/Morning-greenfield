import { useState } from 'react'
import { morningApi } from '../api'
import { OTHER_ACTIVITY_CATEGORIES } from '../types'
import type { ShiftReport } from '../types'

export function OtherActivitiesStage({ report, onUpdated, onNext, onBack }: { report: ShiftReport; onUpdated: (report: ShiftReport) => void; onNext: () => void; onBack: () => void }) {
  const [category, setCategory] = useState(''); const [description, setDescription] = useState('')
  const add = async () => { if (!description.trim()) return; onUpdated(await morningApi<ShiftReport>(`/api/morning/reports/${report.id}/other-activities`, { method: 'POST', body: JSON.stringify({ category: category || null, description: description.trim() }) })); setDescription('') }
  const remove = async (id: string) => onUpdated(await morningApi<ShiftReport>(`/api/morning/reports/${report.id}/other-activities/${id}`, { method: 'DELETE' }))
  return <div className="morning-stage"><div className="morning-events-list">{report.other_activities.map((activity) => <div key={activity.id} className="morning-entry-row"><div>{activity.category ? <strong>{activity.category}: </strong> : null}<span>{activity.description}</span></div><button type="button" className="danger" onClick={() => void remove(activity.id)}>Remove</button></div>)}{!report.other_activities.length ? <p className="empty">Nothing entered yet.</p> : null}</div><div className="morning-add-form"><label>Category (optional)<select value={category} onChange={(e) => setCategory(e.target.value)}><option value="">None</option>{OTHER_ACTIVITY_CATEGORIES.map((item) => <option key={item} value={item}>{item}</option>)}</select></label><textarea placeholder="What happened" value={description} onChange={(e) => setDescription(e.target.value)} /><button type="button" onClick={() => void add()}>Add</button></div><div className="morning-stage-nav"><button type="button" onClick={onBack}>Back</button><button type="button" className="primary" onClick={onNext}>Next: Review</button></div></div>
}
