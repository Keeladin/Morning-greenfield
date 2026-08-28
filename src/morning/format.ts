export function hhmm(iso: string): string {
  return iso.slice(11, 16)
}

const MONTHS = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
export function formatShiftDate(shiftDate: string): string {
  const [year, month, day] = shiftDate.split('-').map(Number)
  if (!year || !month || !day) return shiftDate
  return `${day} ${MONTHS[month - 1]} ${year}`
}

export function stateLabel(state: string): string {
  return state.split('_').map((part) => part.charAt(0).toUpperCase() + part.slice(1)).join(' ')
}
