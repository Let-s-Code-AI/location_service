import { useState } from 'react'
import { login, register } from './api.js'
import { Field, Icon } from './ui.jsx'

// Formularz logowania; przełącza się w tryb rejestracji.
export default function Login({ onLoggedIn }) {
  const [mode, setMode] = useState('login')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState(null)
  const [busy, setBusy] = useState(false)

  const isRegister = mode === 'register'

  async function handleSubmit(e) {
    e.preventDefault()
    setError(null)
    setBusy(true)
    try {
      if (isRegister) {
        await register(email.trim(), password)
      }
      await login(email.trim(), password)
      onLoggedIn()
    } catch (err) {
      setError(
        isRegister
          ? `Nie udało się zarejestrować: ${err.message}`
          : `Nie udało się zalogować: ${err.message}`,
      )
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="container narrow">
      <header className="page-header">
        <div>
          <div className="eyebrow">Konto</div>
          <h1>{isRegister ? 'Rejestracja' : 'Logowanie'}</h1>
          <p className="subtitle">
            {isRegister ? 'Załóż konto, aby zarządzać lokalizacjami.' : 'Zaloguj się, aby zarządzać lokalizacjami.'}
          </p>
        </div>
      </header>

      {error && (
        <div className="alert" role="alert">
          {error}
        </div>
      )}

      <section className="card auth-card">
        <div className="card-body">
          <form onSubmit={handleSubmit} className="stack">
            <Field
              id="email"
              label="Email"
              type="email"
              icon="mail"
              autoComplete="username"
              required
              placeholder="np. jan@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
            <Field
              id="password"
              label="Hasło"
              type="password"
              icon="lock"
              autoComplete={isRegister ? 'new-password' : 'current-password'}
              required
              minLength={isRegister ? 8 : undefined}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
            <button type="submit" className="btn btn-primary btn-block" disabled={busy}>
              {isRegister ? 'Zarejestruj się' : 'Zaloguj'}
            </button>
          </form>
        </div>
      </section>

      <p className="switch">
        <button
          type="button"
          className="btn btn-ghost"
          onClick={() => {
            setError(null)
            setMode(isRegister ? 'login' : 'register')
          }}
        >
          {isRegister ? 'Mam już konto' : 'Nie mam konta'}
        </button>
      </p>
    </div>
  )
}
