import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { morningApi } from './api'
import { StartReport } from './StartReport'
import { AttendanceStage } from './stages/Attendance'
import { MachineActivityStage } from './stages/MachineActivity'
import { OtherActivitiesStage } from './stages/OtherActivities'
import { ReviewStage } from './stages/Review'
import { SafetyStage } from './stages/Safety'
import type { Machine, MachineStateDeclaration, MorningPrincipal, Person, ShiftIdentity, ShiftReport, SupervisorContext } from './types'

const STAGES = ['attendance','safety','machines','other','review'] as const
type Stage = (typeof STAGES)[number]
const STAGE_LABELS: Record<Stage,string> = { attendance:'Attendance', safety:'Safety', machines:'Machine activity', other:'Other activities', review:'Review & submit' }

export function Workflow({ principal }: { principal: MorningPrincipal }) {
  const [stage, setStage] = useState<Stage>('attendance'); const queryClient = useQueryClient()
  const shiftQuery = useQuery({ queryKey:['morning-shift'], queryFn:() => morningApi<ShiftIdentity>('/api/morning/shift') })
  const meQuery = useQuery({ queryKey:['morning-me'], queryFn:() => morningApi<SupervisorContext>('/api/morning/me') })
  const draftQuery = useQuery({ queryKey:['morning-draft'], queryFn:() => morningApi<{report: ShiftReport | null}>('/api/morning/draft') })
  const machinesQuery = useQuery({ queryKey:['morning-machines'], queryFn:() => morningApi<{machines: Machine[]}>('/api/morning/machines') })
  const report = draftQuery.data?.report ?? null
  const rosterQuery = useQuery({ queryKey:['morning-roster',report?.id], queryFn:() => morningApi<{people: Person[]}>(`/api/morning/roster?report_id=${report?.id}`), enabled:Boolean(report) && report?.status === 'draft' })
  const participantsQuery = useQuery({ queryKey:['morning-participants',report?.id], queryFn:() => morningApi<{people: Person[]}>(`/api/morning/reports/${report?.id}/participants`), enabled:Boolean(report) && report?.status === 'submitted' })
  const statesQuery = useQuery({ queryKey:['morning-machine-states',report?.id], queryFn:() => morningApi<{states: MachineStateDeclaration[]}>(`/api/morning/reports/${report?.id}/machine-states`), enabled:Boolean(report) })
  const machines = machinesQuery.data?.machines || []; const people = (report?.status === 'submitted' ? participantsQuery.data?.people : rosterQuery.data?.people) || []; const states = statesQuery.data?.states || []
  const refreshReport = (updated: ShiftReport) => queryClient.setQueryData(['morning-draft'], { report: updated })
  const refreshStates = () => void queryClient.invalidateQueries({ queryKey:['morning-machine-states',report?.id] })
  const abandon = useMutation({ mutationFn:() => morningApi<ShiftReport>(`/api/morning/reports/${report?.id}/abandon`, { method:'POST', body:'{}' }), onSuccess:() => queryClient.setQueryData(['morning-draft'], { report:null }) })
  const confirmAndAbandon = () => { if (report && window.confirm('Abandon this draft? You will not be able to resume it.')) abandon.mutate() }
  if (shiftQuery.isError || draftQuery.isError) return <div className="offline-banner">Could not reach Morning. Check your connection.</div>
  if (shiftQuery.isLoading || draftQuery.isLoading || meQuery.isLoading) return <p className="morning-loading">Loading your shift…</p>
  if (!report) return <div className="morning-workflow"><StartReport suggestion={shiftQuery.data} supervisor={meQuery.data} onStarted={(started) => queryClient.setQueryData(['morning-draft'], { report:started })} /></div>
  if (report.status === 'submitted') return <div className="morning-workflow"><ReviewStage report={report} machines={machines} people={people} states={states} principal={principal} submitted /></div>
  const stageIndex = STAGES.indexOf(stage)
  return <div className="morning-workflow"><div className="morning-shift-banner"><div className="morning-shift-banner-info"><strong>{report.shift_kind === 'day' ? 'Day Shift' : 'Night Shift'}</strong><span>{report.shift_date}</span></div><button type="button" className="ghost" onClick={confirmAndAbandon} disabled={abandon.isPending}>Abandon draft</button></div><div className="morning-stepper" aria-label="Progress">{STAGES.map((item,index) => <div key={item} className={['morning-step',index === stageIndex ? 'active':'',index < stageIndex ? 'done':''].filter(Boolean).join(' ')}>{index+1}</div>)}</div><h2 className="morning-stage-title">{STAGE_LABELS[stage]}</h2>
    {stage === 'attendance' ? <AttendanceStage report={report} people={people} onUpdated={refreshReport} onNext={() => setStage('safety')} /> : null}
    {stage === 'safety' ? <SafetyStage report={report} onUpdated={refreshReport} onNext={() => setStage('machines')} onBack={() => setStage('attendance')} /> : null}
    {stage === 'machines' ? <MachineActivityStage report={report} machines={machines} states={states} onUpdated={refreshReport} onStateAdded={refreshStates} onNext={() => setStage('other')} onBack={() => setStage('safety')} /> : null}
    {stage === 'other' ? <OtherActivitiesStage report={report} onUpdated={refreshReport} onNext={() => setStage('review')} onBack={() => setStage('machines')} /> : null}
    {stage === 'review' ? <ReviewStage report={report} machines={machines} people={people} states={states} principal={principal} onBack={() => setStage('other')} onSubmitted={refreshReport} /> : null}
  </div>
}
