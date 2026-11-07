import { useState } from 'react'
import { login, register } from './api.js'

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
    <main>
      <h1>{isRegister ? 'Rejestracja' : 'Logowanie'}</h1>

      {error && <p className="error">{error}</p>}

      <form onSubmit={handleSubmit}>
        <label>
          Email
          <input
            type="email"
            autoComplete="username"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
        </label>
        <label>
          Hasło
          <input
            type="password"
            autoComplete={isRegister ? 'new-password' : 'current-password'}
            required
            minLength={isRegister ? 8 : undefined}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </label>
        <button type="submit" disabled={busy}>
          {isRegister ? 'Zarejestruj się' : 'Zaloguj'}
        </button>
      </form>

      <p>
        <button
          type="button"
          onClick={() => {
            setError(null)
            setMode(isRegister ? 'login' : 'register')
          }}
        >
          {isRegister ? 'Mam już konto' : 'Nie mam konta'}
        </button>
      </p>
    </main>
  )
}
