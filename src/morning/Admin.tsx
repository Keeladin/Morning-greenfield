import { useEffect, useState, type FormEvent } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { morningApi } from './api'
import type { Machine, Person } from './types'

type Crew = { id: string; name: string; created_at?: string }
type Account = {
  principal_id: string; username: string; display_name: string | null; role: string | null
  created_at: string; approved_at: string | null; person_id: string | null; person_name: string | null
  crew_id: string | null; crew_name: string | null
}
type ShiftPolicy = { timezone: string; day_shift_start: string; night_shift_start: string; updated_at?: string }
type DailyReport = { reporting_date: string; status: 'waiting' | 'complete'; expected_inputs: { key: string; label: string; present: boolean }[]; detailed_text: string; compact_text: string }
type Section = 'machines' | 'personnel' | 'crews' | 'supervisors' | 'shift-policy' | 'daily-report'

export function Admin() {
  const [section, setSection] = useState<Section>('machines')
  const tabs: { id: Section; label: string }[] = [
    { id: 'machines', label: 'Machines' }, { id: 'personnel', label: 'Personnel' },
    { id: 'crews', label: 'Crews' }, { id: 'supervisors', label: 'Supervisors' },
    { id: 'shift-policy', label: 'Shift policy' }, { id: 'daily-report', label: 'Daily report' },
  ]
  return <div className="morning-admin">
    <div className="morning-admin-head"><div><h2>Morning administration</h2><p className="meta">Morning-owned configuration and reporting.</p></div></div>
    <div className="morning-admin-nav" role="tablist">{tabs.map((tab) => <button key={tab.id} type="button" className={section === tab.id ? 'active' : ''} onClick={() => setSection(tab.id)}>{tab.label}</button>)}</div>
    {section === 'machines' ? <Machines /> : null}
    {section === 'personnel' ? <Personnel /> : null}
    {section === 'crews' ? <Crews /> : null}
    {section === 'supervisors' ? <Supervisors /> : null}
    {section === 'shift-policy' ? <ShiftPolicyPanel /> : null}
    {section === 'daily-report' ? <DailyReportPanel /> : null}
  </div>
}

function Machines() {
  const qc = useQueryClient(); const query = useQuery({ queryKey:['admin-machines'], queryFn:() => morningApi<{machines:Machine[]}>('/api/morning/admin/machines') })
  const [machineId,setMachineId] = useState(''); const [machineType,setMachineType] = useState(''); const [section,setSection] = useState('')
  const invalidate = () => void qc.invalidateQueries({ queryKey:['admin-machines'] })
  const create = useMutation({ mutationFn:() => morningApi('/api/morning/admin/machines',{method:'POST',body:JSON.stringify({machine_id:machineId,machine_type:machineType||null,section:section||null})}), onSuccess:() => { setMachineId(''); setMachineType(''); setSection(''); invalidate() } })
  const active = useMutation({ mutationFn:({id,value}:{id:string;value:boolean}) => morningApi(`/api/morning/admin/machines/${id}/${value?'activate':'deactivate'}`,{method:'POST',body:'{}'}), onSuccess:invalidate })
  const scope = useMutation({ mutationFn:({id,value}:{id:string;value:boolean}) => morningApi(`/api/morning/admin/machines/${id}/control-room-scope`,{method:'POST',body:JSON.stringify({in_scope:value})}), onSuccess:invalidate })
  return <div className="morning-admin-stack"><section className="morning-admin-card"><h3>Add machine</h3><form className="morning-add-form" onSubmit={(e:FormEvent) => {e.preventDefault();if(machineId.trim())create.mutate()}}><input placeholder="Machine ID" value={machineId} onChange={(e)=>setMachineId(e.target.value)} required/><input placeholder="Machine type" value={machineType} onChange={(e)=>setMachineType(e.target.value)}/><input placeholder="Section" value={section} onChange={(e)=>setSection(e.target.value)}/><button className="primary" disabled={create.isPending}>Add machine</button></form></section><section className="morning-admin-card"><h3>Machines</h3>{query.isLoading?<p className="empty">Loading…</p>:null}{query.data?.machines.map((m)=><div key={m.id} className="morning-entry-row"><div><strong>{m.machine_id}</strong><div className="meta">{[m.machine_type,m.section].filter(Boolean).join(' · ')||'No type / section'}</div><div className="meta">{m.active?'Active':'Inactive'} · {m.control_room_scope?'Control-room scope':'Not in control-room scope'}</div></div><div className="morning-entry-actions"><button type="button" onClick={()=>active.mutate({id:m.id,value:!m.active})}>{m.active?'Deactivate':'Activate'}</button><button type="button" onClick={()=>scope.mutate({id:m.id,value:!m.control_room_scope})}>{m.control_room_scope?'Remove scope':'Add scope'}</button></div></div>)}</section></div>
}

function Personnel() {
  const qc=useQueryClient(); const people=useQuery({queryKey:['admin-persons'],queryFn:()=>morningApi<{persons:Person[]}>('/api/morning/admin/persons')}); const crews=useQuery({queryKey:['admin-crews'],queryFn:()=>morningApi<{crews:Crew[]}>('/api/morning/admin/crews')})
  const [name,setName]=useState(''); const [role,setRole]=useState(''); const [crewId,setCrewId]=useState('')
  const invalidate=()=>void qc.invalidateQueries({queryKey:['admin-persons']})
  const create=useMutation({mutationFn:()=>morningApi('/api/morning/admin/persons',{method:'POST',body:JSON.stringify({name,role:role||null,crew_id:crewId||null})}),onSuccess:()=>{setName('');setRole('');setCrewId('');invalidate()}})
  const assign=useMutation({mutationFn:({id,crew}:{id:string;crew:string})=>morningApi(`/api/morning/admin/persons/${id}`,{method:'PATCH',body:JSON.stringify({crew_id:crew||null})}),onSuccess:invalidate})
  const active=useMutation({mutationFn:({id,value}:{id:string;value:boolean})=>morningApi(`/api/morning/admin/persons/${id}/${value?'activate':'deactivate'}`,{method:'POST',body:'{}'}),onSuccess:invalidate})
  return <div className="morning-admin-stack"><section className="morning-admin-card"><h3>Add person</h3><form className="morning-add-form" onSubmit={(e:FormEvent)=>{e.preventDefault();if(name.trim())create.mutate()}}><input placeholder="Full name" value={name} onChange={(e)=>setName(e.target.value)} required/><input placeholder="Role / trade" value={role} onChange={(e)=>setRole(e.target.value)}/><select value={crewId} onChange={(e)=>setCrewId(e.target.value)}><option value="">No crew</option>{crews.data?.crews.map((c)=><option key={c.id} value={c.id}>{c.name}</option>)}</select><button className="primary">Add person</button></form></section><section className="morning-admin-card"><h3>Personnel</h3>{people.data?.persons.map((p)=><div key={p.id} className="morning-entry-row"><div><strong>{p.name}</strong><div className="meta">{p.role||'No role set'} · {p.active?'Active':'Inactive'}</div></div><div className="morning-entry-actions"><select value={p.crew_id||''} onChange={(e)=>assign.mutate({id:p.id,crew:e.target.value})}>{<option value="">No crew</option>}{crews.data?.crews.map((c)=><option key={c.id} value={c.id}>{c.name}</option>)}</select><button type="button" onClick={()=>active.mutate({id:p.id,value:!p.active})}>{p.active?'Deactivate':'Activate'}</button></div></div>)}</section></div>
}

function Crews() {
  const qc=useQueryClient(); const query=useQuery({queryKey:['admin-crews'],queryFn:()=>morningApi<{crews:Crew[]}>('/api/morning/admin/crews')}); const [name,setName]=useState('')
  const create=useMutation({mutationFn:()=>morningApi('/api/morning/admin/crews',{method:'POST',body:JSON.stringify({name})}),onSuccess:()=>{setName('');void qc.invalidateQueries({queryKey:['admin-crews']})}})
  return <div className="morning-admin-stack"><section className="morning-admin-card"><h3>Add crew</h3><form className="morning-add-form" onSubmit={(e:FormEvent)=>{e.preventDefault();if(name.trim())create.mutate()}}><input placeholder="Crew name" value={name} onChange={(e)=>setName(e.target.value)} required/><button className="primary">Add crew</button></form></section><section className="morning-admin-card"><h3>Crews</h3>{query.data?.crews.map((c)=><div key={c.id} className="morning-entry-row"><strong>{c.name}</strong></div>)}</section></div>
}

function Supervisors() {
  const qc=useQueryClient(); const accounts=useQuery({queryKey:['admin-accounts'],queryFn:()=>morningApi<{accounts:Account[]}>('/api/morning/admin/accounts')}); const people=useQuery({queryKey:['admin-persons'],queryFn:()=>morningApi<{persons:Person[]}>('/api/morning/admin/persons')}); const invalidate=()=>void qc.invalidateQueries({queryKey:['admin-accounts']})
  const approve=useMutation({mutationFn:(id:string)=>morningApi(`/api/morning/admin/accounts/${id}/approve`,{method:'POST',body:'{}'}),onSuccess:invalidate})
  const link=useMutation({mutationFn:({id,personId}:{id:string;personId:string})=>morningApi(`/api/morning/admin/accounts/${id}/link`,{method:'POST',body:JSON.stringify({person_id:personId||null})}),onSuccess:invalidate})
  return <section className="morning-admin-card"><h3>Supervisor accounts</h3><p className="meta">New registrations remain blocked until approved here.</p>{accounts.data?.accounts.map((a)=><div key={a.principal_id} className="morning-entry-row"><div><strong>{a.display_name||a.username}</strong><div className="meta">@{a.username} · {a.role||'unknown role'} · {a.approved_at?'Approved':'Pending approval'}</div><div className="meta">{a.person_name?`${a.person_name}${a.crew_name?` · ${a.crew_name}`:''}`:'Not linked to personnel'}</div></div><div className="morning-entry-actions">{!a.approved_at?<button type="button" className="primary" onClick={()=>approve.mutate(a.principal_id)}>Approve</button>:null}<select value={a.person_id||''} onChange={(e)=>link.mutate({id:a.principal_id,personId:e.target.value})}><option value="">No personnel link</option>{people.data?.persons.map((p)=><option key={p.id} value={p.id}>{p.name}</option>)}</select></div></div>)}</section>
}

function ShiftPolicyPanel() {
  const qc=useQueryClient(); const query=useQuery({queryKey:['admin-shift-policy'],queryFn:()=>morningApi<ShiftPolicy>('/api/morning/admin/shift-policy')}); const [timezone,setTimezone]=useState('Africa/Johannesburg'); const [day,setDay]=useState('06:00'); const [night,setNight]=useState('18:00')
  useEffect(()=>{if(query.data){setTimezone(query.data.timezone);setDay(query.data.day_shift_start);setNight(query.data.night_shift_start)}},[query.data])
  const save=useMutation({mutationFn:()=>morningApi('/api/morning/admin/shift-policy',{method:'PUT',body:JSON.stringify({timezone,day_shift_start:day,night_shift_start:night})}),onSuccess:()=>void qc.invalidateQueries({queryKey:['admin-shift-policy']})})
  return <section className="morning-admin-card"><h3>Shift policy</h3><form className="morning-add-form" onSubmit={(e:FormEvent)=>{e.preventDefault();save.mutate()}}><label>Timezone<input value={timezone} onChange={(e)=>setTimezone(e.target.value)}/></label><div className="morning-time-row"><label>Day shift start<input type="time" value={day} onChange={(e)=>setDay(e.target.value)}/></label><label>Night shift start<input type="time" value={night} onChange={(e)=>setNight(e.target.value)}/></label></div><button className="primary" disabled={save.isPending}>{save.isPending?'Saving…':'Save shift policy'}</button></form></section>
}

function DailyReportPanel() {
  const [date,setDate]=useState(()=>new Date().toISOString().slice(0,10)); const [requireControlRoom,setRequireControlRoom]=useState(true); const [report,setReport]=useState<DailyReport|null>(null); const [error,setError]=useState<string|null>(null); const [loading,setLoading]=useState(false)
  const load=async()=>{setLoading(true);setError(null);try{setReport(await morningApi<DailyReport>(`/api/morning/admin/reports/${date}?require_control_room=${requireControlRoom?'true':'false'}`))}catch(err){setError(err instanceof Error?err.message:'Could not load report')}finally{setLoading(false)}}
  return <section className="morning-admin-card"><h3>24-hour report</h3><div className="morning-add-form"><label>Reporting date<input type="date" value={date} onChange={(e)=>setDate(e.target.value)}/></label><label className="morning-checkbox"><input type="checkbox" checked={requireControlRoom} onChange={(e)=>setRequireControlRoom(e.target.checked)}/>Require control-room input for completeness</label><button type="button" className="primary" onClick={()=>void load()} disabled={loading}>{loading?'Loading…':'Generate report'}</button></div>{error?<p className="error-text">{error}</p>:null}{report?<div className="morning-report-preview"><p className={report.status==='complete'?'morning-status-ok':'morning-status-warn'}>{report.status==='complete'?'Complete':'Waiting for inputs'}</p><div className="meta">{report.expected_inputs.map((i)=>`${i.present?'✓':'○'} ${i.label}`).join(' · ')}</div><h4>Department summary</h4><pre>{report.compact_text}</pre><details><summary>Detailed report</summary><pre>{report.detailed_text}</pre></details></div>:null}</section>
}
