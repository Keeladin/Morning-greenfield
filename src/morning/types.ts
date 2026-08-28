export type ShiftKind = 'day' | 'night'
export type PrincipalRole = 'admin' | 'supervisor'
export type MachineState = 'running' | 'not_tested' | 'under_repair' | 'awaiting_parts' | 'other'
export type MachineStateProvenance = 'declared' | 'carried'

export type MorningPrincipal = { principal_id: string; display_name: string; role: PrincipalRole }
export type MorningSession = { authenticated: boolean; principal?: MorningPrincipal; csrf_token?: string }
export type ShiftIdentity = { shift_date: string; shift_kind: ShiftKind; shift_id: string }
export type SupervisorContext = { principal_id: string; display_name: string; role: PrincipalRole; crew_id: string | null; crew_name: string | null }

export type Machine = {
  id: string; machine_id: string; machine_type: string | null; section: string | null
  active: boolean; created_at: string; retired_at: string | null; control_room_scope: boolean
}
export type Person = { id: string; name: string; employee_number: string | null; role: string | null; active: boolean; crew_id: string | null; created_at: string }
export type AttendanceEntry = { person_id: string; present: boolean }
export type StopFixRecord = {
  id: string; number: string; issued_at: string; area_of_concern: string; location: string
  reason: string; instruction: string; status: 'open' | 'rectified'; rectified_at: string | null
}
export type CardObservation = { id: string; card_type: 'red' | 'green'; reason: string }
export type MachineEvent = { id: string; machine_id: string; start_time: string; end_time: string; issue: string }
export type MachineStateDeclaration = {
  id: string; machine_id: string; report_id: string; declared_at: string; state: MachineState
  provenance: MachineStateProvenance; state_note: string | null; source_state_id: string | null
  follow_up: string | null; created_at: string | null
}
export type OtherActivity = { id: string; category: string | null; description: string }
export type ShiftReport = {
  id: string; shift_date: string; shift_kind: ShiftKind; shift_id: string; supervisor_principal_id: string
  crew_id: string | null; status: 'draft' | 'submitted' | 'abandoned'; attendance: AttendanceEntry[]
  stop_fix: StopFixRecord[]; cards: CardObservation[]; machine_events: MachineEvent[]
  other_activities: OtherActivity[]; created_at: string; updated_at: string; submitted_at: string | null
}

export const STOP_FIX_AREAS = ['Support','A Hazard','Working at height','Environmental/Ventilation','Transport and Tramming','De-energised/Lock out','Barring','Lifting','Guarding','Other'] as const
export const OTHER_ACTIVITY_CATEGORIES = ['Housekeeping','Inspections','Training','Workshop work','Recovery work','Assisting another team','Miscellaneous'] as const
export const MACHINE_STATES: { value: MachineState; label: string }[] = [
  { value: 'running', label: 'Running' },
  { value: 'not_tested', label: 'Not tested' },
  { value: 'under_repair', label: 'Under repair' },
  { value: 'awaiting_parts', label: 'Awaiting parts' },
  { value: 'other', label: 'Other' },
]
