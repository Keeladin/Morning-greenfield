import { useState, type FormEvent } from 'react'
import { MorningApiError, morningApi } from './api'
import type { MorningSession } from './types'

export function Login({ onAuthed }: { onAuthed: (session: MorningSession) => void }) {
  const [mode, setMode] = useState<'login' | 'register'>('login')
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [displayName, setDisplayName] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [notice, setNotice] = useState<string | null>(null)
  const [pending, setPending] = useState(false)

  const submit = async (event: FormEvent) => {
    event.preventDefault(); setError(null); setNotice(null); setPending(true)
    try {
      if (mode === 'register') {
        await morningApi('/api/morning/auth/register', { method: 'POST', body: JSON.stringify({ username, password, display_name: displayName }) })
        setMode('login'); setPassword('')
        setNotice('Registration submitted. A Morning administrator must approve your account before you can log in.')
      } else {
        const result = await morningApi<{ principal: MorningSession['principal']; csrf_token: string }>('/api/morning/auth/login', { method: 'POST', body: JSON.stringify({ username, password }) })
        onAuthed({ authenticated: true, principal: result.principal, csrf_token: result.csrf_token })
      }
    } catch (err) {
      setError(err instanceof MorningApiError ? err.message : 'Something went wrong. Try again.')
    } finally { setPending(false) }
  }

  return <div className="morning-auth-card">
    <h1>Morning</h1><p className="meta">Structured shift reporting.</p>
    <div className="morning-auth-toggle" role="tablist"><button type="button" role="tab" aria-selected={mode === 'login'} className={mode === 'login' ? 'active' : ''} onClick={() => setMode('login')}>Log in</button><button type="button" role="tab" aria-selected={mode === 'register'} className={mode === 'register' ? 'active' : ''} onClick={() => setMode('register')}>Register</button></div>
    <form onSubmit={submit} className="morning-auth-form">
      {mode === 'register' ? <label>Full name<input value={displayName} onChange={(e) => setDisplayName(e.target.value)} required autoComplete="name" /></label> : null}
      <label>Username<input value={username} onChange={(e) => setUsername(e.target.value)} required autoComplete="username" autoCapitalize="none" /></label>
      <label>Password<input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required minLength={8} autoComplete={mode === 'login' ? 'current-password' : 'new-password'} /></label>
      {notice ? <p className="meta">{notice}</p> : null}{error ? <p className="error-text">{error}</p> : null}
      <button type="submit" className="primary" disabled={pending}>{pending ? 'Please wait…' : mode === 'login' ? 'Log in' : 'Register'}</button>
    </form>
  </div>
}
