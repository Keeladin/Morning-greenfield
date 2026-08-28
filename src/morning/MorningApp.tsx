import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useEffect, useState } from 'react'
import { Admin } from './Admin'
import { morningApi, setMorningCsrfToken } from './api'
import { ControlRoomAdmin } from './ControlRoomAdmin'
import { InstallPrompt } from './InstallPrompt'
import { Login } from './Login'
import type { MorningSession } from './types'
import { Workflow } from './Workflow'
import './tokens.css'
import './morning.css'

const queryClient = new QueryClient({ defaultOptions:{ queries:{ retry:1, refetchOnWindowFocus:false } } })
function MorningInner() {
  const [ready,setReady] = useState(false); const [session,setSession] = useState<MorningSession>({authenticated:false})
  useEffect(() => { void morningApi<MorningSession>('/api/morning/auth/session').then((result) => { setSession(result); if (result.csrf_token) setMorningCsrfToken(result.csrf_token) }).catch(() => setSession({authenticated:false})).finally(() => setReady(true)) }, [])
  const onAuthed = (result: MorningSession) => { setSession(result); if (result.csrf_token) setMorningCsrfToken(result.csrf_token) }
  const signOut = async () => { try { await morningApi('/api/morning/auth/logout',{method:'POST',body:'{}'}) } finally { setMorningCsrfToken(null); queryClient.clear(); setSession({authenticated:false}) } }
  const authenticatedSurface = session.principal?.role === 'admin'
    ? <><Admin /><ControlRoomAdmin /></>
    : session.principal ? <Workflow principal={session.principal} /> : null
  return <div className="morning-shell"><header className="morning-topbar"><div className="morning-brand">Morning</div>{session.authenticated && session.principal ? <div className="morning-topbar-actions"><span className="morning-supervisor-name">{session.principal.display_name} · {session.principal.role}</span><button type="button" className="ghost" onClick={() => void signOut()}>Sign out</button></div> : null}</header><InstallPrompt /><main className={session.principal?.role === 'admin' ? 'morning-main morning-main-admin' : 'morning-main'}>{!ready ? <p className="morning-loading">Loading…</p> : session.authenticated ? authenticatedSurface : <Login onAuthed={onAuthed} />}</main></div>
}
export default function MorningApp() { return <QueryClientProvider client={queryClient}><MorningInner /></QueryClientProvider> }
