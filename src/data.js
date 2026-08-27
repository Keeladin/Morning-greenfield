export const navigation = [
  { id: 'overview', label: 'Overview', icon: 'grid' },
  { id: 'shift', label: 'Shift Capture', icon: 'clipboard' },
  { id: 'reports', label: '24-Hour Reports', icon: 'report' },
  { id: 'utilization', label: 'Utilization', icon: 'gauge' },
  { id: 'reliability', label: 'Reliability', icon: 'pulse' },
]

export const machines = [
  { id: 'STC14', type: 'Utility Vehicle', area: 'South', availability: 71.8, utilization: 88.2, lost: 42.4, failures: 13, repeat: 4, mttr: 2.6, trend: [90, 87, 83, 78, 74, 72] },
  { id: 'RLH3', type: 'Reef Loader', area: 'North Production', availability: 79.4, utilization: 91.1, lost: 31.1, failures: 8, repeat: 3, mttr: 2.1, trend: [88, 86, 84, 82, 80, 79] },
  { id: 'STV6', type: 'Service Vehicle', area: 'North Development', availability: 88.1, utilization: 73.2, lost: 19.2, failures: 11, repeat: 2, mttr: 1.1, trend: [91, 91, 90, 89, 88, 88] },
  { id: 'RLH1', type: 'Reef Loader', area: 'South', availability: 84.9, utilization: 86.4, lost: 24.7, failures: 6, repeat: 1, mttr: 2.8, trend: [82, 84, 85, 86, 85, 85] },
  { id: 'L91', type: 'LDV', area: 'North Production', availability: 94.3, utilization: 62.8, lost: 8.6, failures: 4, repeat: 0, mttr: 0.9, trend: [92, 93, 95, 94, 95, 94] },
]

export const people = [
  { id: 'johan', name: 'Johan M.', role: 'Diesel Mechanic', trade: 'Diesel Mechanics', assigned: 78, blocked: 11, unallocated: 6, other: 5, hours: 172, trend: [74, 79, 82, 77, 80, 78] },
  { id: 'sipho', name: 'Sipho N.', role: 'Engineering Assistant', trade: 'Engineering Assistants', assigned: 71, blocked: 14, unallocated: 10, other: 5, hours: 168, trend: [68, 72, 75, 70, 73, 71] },
  { id: 'thabo', name: 'Thabo K.', role: 'Engineering Assistant', trade: 'Engineering Assistants', assigned: 67, blocked: 9, unallocated: 18, other: 6, hours: 160, trend: [65, 64, 69, 71, 68, 67] },
  { id: 'pieter', name: 'Pieter V.', role: 'Auto Electrician', trade: 'Auto Electricians', assigned: 89, blocked: 6, unallocated: 2, other: 3, hours: 176, trend: [82, 86, 87, 91, 90, 89] },
  { id: 'musa', name: 'Musa D.', role: 'Boilermaker', trade: 'Boilermakers', assigned: 59, blocked: 8, unallocated: 27, other: 6, hours: 154, trend: [61, 58, 56, 60, 62, 59] },
]

export const activityLog = [
  { id: 'A-1042', date: '27 Aug', start: '01:20', end: '02:45', machine: 'STC14', category: 'Breakdown', owner: 'Engineering', detail: 'Hydraulic hose failure — hose replaced and system tested.', people: ['Johan M.', 'Sipho N.'], delay: '25 min waiting for spares', failure: 'Hydraulics', status: 'Returned to service' },
  { id: 'A-1041', date: '27 Aug', start: '00:10', end: '01:05', machine: 'RLH3', category: 'Breakdown', owner: 'Engineering', detail: 'Steering response intermittent. Electrical connector cleaned and secured.', people: ['Pieter V.'], delay: 'None', failure: 'Electrical', status: 'Returned to service' },
  { id: 'A-1039', date: '26 Aug', start: '21:30', end: '23:10', machine: 'STV6', category: 'Operational delay', owner: 'Operations', detail: 'Machine available; no operator allocated during production changeover.', people: [], delay: '1 h 40 min', failure: 'No operator', status: 'Available' },
  { id: 'A-1037', date: '26 Aug', start: '18:00', end: '20:20', machine: 'RLH1', category: 'Planned maintenance', owner: 'Planned', detail: 'Weekly inspection, alternator belt tension and hose condition checks.', people: ['Johan M.', 'Thabo K.'], delay: 'None', failure: 'Planned maintenance', status: 'Returned to service' },
  { id: 'A-1035', date: '26 Aug', start: '13:10', end: '15:00', machine: 'STC14', category: 'Waiting for spares', owner: 'Supply Chain', detail: 'Turbo replacement held pending stores issue. Work resumed when part arrived.', people: ['Johan M.', 'Sipho N.'], delay: '1 h 50 min', failure: 'Engine', status: 'Work resumed' },
  { id: 'A-1032', date: '26 Aug', start: '09:40', end: '10:30', machine: 'L91', category: 'Breakdown', owner: 'Engineering', detail: 'Reverse light circuit repaired and battery terminals cleaned.', people: ['Pieter V.'], delay: 'None', failure: 'Electrical', status: 'Returned to service' },
  { id: 'A-1029', date: '25 Aug', start: '04:20', end: '05:40', machine: 'STC14', category: 'Breakdown', owner: 'Engineering', detail: 'Hydraulic hose at articulation replaced. Same circuit as prior event flagged for reliability review.', people: ['Johan M.', 'Sipho N.'], delay: 'None', failure: 'Hydraulics', status: 'Returned to service' },
]

export const reportHistory = [
  { id: 'R-0827', date: '27 Aug 2026', period: '26 Aug 06:00 → 27 Aug 05:59', status: 'Published', generated: '05:12', availability: '82.4%', downtime: '17.8 h', activities: 18, exceptions: 2 },
  { id: 'R-0826', date: '26 Aug 2026', period: '25 Aug 06:00 → 26 Aug 05:59', status: 'Published', generated: '05:09', availability: '84.1%', downtime: '15.2 h', activities: 16, exceptions: 1 },
  { id: 'R-0825', date: '25 Aug 2026', period: '24 Aug 06:00 → 25 Aug 05:59', status: 'Published', generated: '05:14', availability: '86.7%', downtime: '12.6 h', activities: 14, exceptions: 0 },
  { id: 'R-0824', date: '24 Aug 2026', period: '23 Aug 06:00 → 24 Aug 05:59', status: 'Published', generated: '05:11', availability: '85.5%', downtime: '13.9 h', activities: 17, exceptions: 3 },
  { id: 'R-0823', date: '23 Aug 2026', period: '22 Aug 06:00 → 23 Aug 05:59', status: 'Published', generated: '05:10', availability: '88.2%', downtime: '9.8 h', activities: 11, exceptions: 1 },
  { id: 'R-0822', date: '22 Aug 2026', period: '21 Aug 06:00 → 22 Aug 05:59', status: 'Published', generated: '05:08', availability: '89.4%', downtime: '8.9 h', activities: 13, exceptions: 0 },
]

export const dashboardKpis = [
  { id: 'availability', label: 'Fleet Availability', value: '82.4%', delta: '↓ 3.1%', deltaTone: 'bad', hint: 'vs previous 30 days', accent: 'gold' },
  { id: 'utilization', label: 'Fleet Utilization', value: '76.8%', delta: '↑ 1.8%', deltaTone: 'good', hint: 'when available', accent: 'blue' },
  { id: 'engineering', label: 'Engineering Downtime', value: '121 h', delta: '38%', deltaTone: 'neutral', hint: 'of lost opportunity', accent: 'orange' },
  { id: 'opportunity', label: 'Lost Opportunity', value: '318 h', delta: '↓ 24 h', deltaTone: 'good', hint: 'rolling 30 days', accent: 'red' },
  { id: 'repeat', label: 'Repeat Failures', value: '9', delta: '4 critical', deltaTone: 'bad', hint: 'within 72 hours', accent: 'purple' },
  { id: 'mttr', label: 'MTTR', value: '2.14 h', delta: '↓ 0.22 h', deltaTone: 'good', hint: 'rolling 30 days', accent: 'green' },
  { id: 'people', label: 'Personnel Utilization', value: '74.6%', delta: '11% blocked', deltaTone: 'neutral', hint: 'productive assignment', accent: 'cyan' },
  { id: 'reactive', label: 'Reactive Workload', value: '34%', delta: '↓ 6%', deltaTone: 'good', hint: 'of engineering hours', accent: 'lime' },
]

export const downtimePareto = [
  { label: 'Hydraulics', value: 31, hours: 39.4, owner: 'Engineering' },
  { label: 'Electrical', value: 18, hours: 22.9, owner: 'Engineering' },
  { label: 'Waiting for spares', value: 15, hours: 19.1, owner: 'Supply Chain' },
  { label: 'Tyres', value: 9, hours: 11.4, owner: 'Engineering' },
  { label: 'No operator', value: 8, hours: 10.2, owner: 'Operations' },
  { label: 'Infrastructure', value: 7, hours: 8.9, owner: 'Infrastructure' },
  { label: 'Other', value: 12, hours: 15.2, owner: 'Mixed' },
]

export const lossOwnership = [
  { label: 'Engineering', hours: 121, percent: 38 },
  { label: 'Operations', hours: 74, percent: 23 },
  { label: 'Supply chain', hours: 53, percent: 17 },
  { label: 'Infrastructure', hours: 36, percent: 11 },
  { label: 'Planned maintenance', hours: 22, percent: 7 },
  { label: 'Other', hours: 12, percent: 4 },
]

export const tradeLoading = [
  { trade: 'Diesel Mechanics', assigned: 82, blocked: 10, free: 8 },
  { trade: 'Auto Electricians', assigned: 91, blocked: 7, free: 2 },
  { trade: 'Boilermakers', assigned: 59, blocked: 8, free: 33 },
  { trade: 'Engineering Assistants', assigned: 70, blocked: 12, free: 18 },
]

export const failureFamilies = [
  { name: 'Hydraulics', events: 17, downtime: 39.4, repeats: 5, trend: 'up' },
  { name: 'Electrical', events: 14, downtime: 22.9, repeats: 2, trend: 'flat' },
  { name: 'Engine / turbo', events: 7, downtime: 18.6, repeats: 1, trend: 'down' },
  { name: 'Tyres', events: 9, downtime: 11.4, repeats: 1, trend: 'flat' },
]

export const currentShiftSeed = {
  date: '27 August 2026',
  kind: 'Night',
  supervisor: 'Lyle',
  crew: 'Crew A',
  department: 'TMM Engineering',
  suggestion: 'Night',
}
