import { useEffect, useState } from 'react'
import {
  AUTH_EXPIRED_EVENT,
  clearToken,
  createLocation,
  deleteLocation,
  getToken,
  listLocations,
} from './api.js'
import Login from './Login.jsx'

const EMPTY_FORM = { city: '', locality: '', city_district: '', street: '' }

export default function App() {
  const [authed, setAuthed] = useState(() => Boolean(getToken()))

  useEffect(() => {
    const onExpired = () => setAuthed(false)
    window.addEventListener(AUTH_EXPIRED_EVENT, onExpired)
    return () => window.removeEventListener(AUTH_EXPIRED_EVENT, onExpired)
  }, [])

  if (!authed) {
    return <Login onLoggedIn={() => setAuthed(true)} />
  }

  function handleLogout() {
    clearToken()
    setAuthed(false)
  }

  return <Locations onLogout={handleLogout} />
}

function Locations({ onLogout }) {
  const [locations, setLocations] = useState([])
  const [form, setForm] = useState(EMPTY_FORM)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  async function load() {
    try {
      setLocations(await listLocations())
      setError(null)
    } catch (e) {
      setError(`Nie udało się pobrać lokalizacji: ${e.message}`)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [])

  async function handleSubmit(e) {
    e.preventDefault()
    // Send only non-empty fields; the rest stay null in the DB.
    const data = Object.fromEntries(
      Object.entries(form)
        .map(([k, v]) => [k, v.trim()])
        .filter(([, v]) => v !== ''),
    )
    try {
      await createLocation(data)
      setForm(EMPTY_FORM)
      await load()
    } catch (e) {
      setError(`Nie udało się dodać lokalizacji: ${e.message}`)
    }
  }

  async function handleDelete(id) {
    try {
      await deleteLocation(id)
      await load()
    } catch (e) {
      setError(`Nie udało się usunąć lokalizacji: ${e.message}`)
    }
  }

  const field = (name, label) => (
    <label>
      {label}
      <input
        value={form[name]}
        onChange={(e) => setForm({ ...form, [name]: e.target.value })}
      />
    </label>
  )

  return (
    <main>
      <header>
        <h1>Lokalizacje</h1>
        <button type="button" onClick={onLogout}>Wyloguj</button>
      </header>

      {error && <p className="error">{error}</p>}

      <form onSubmit={handleSubmit}>
        {field('city', 'Miasto')}
        {field('locality', 'Miejscowość')}
        {field('city_district', 'Dzielnica')}
        {field('street', 'Ulica')}
        <button type="submit">Dodaj</button>
      </form>

      {loading ? (
        <p>Ładowanie…</p>
      ) : locations.length === 0 ? (
        <p>Brak lokalizacji.</p>
      ) : (
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Miasto</th>
              <th>Dzielnica</th>
              <th>Ulica</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {locations.map((l) => (
              <tr key={l.location_id}>
                <td>{l.location_id}</td>
                <td>{l.city ?? l.locality ?? '—'}</td>
                <td>{l.city_district ?? '—'}</td>
                <td>{l.street ?? '—'}</td>
                <td>
                  <button onClick={() => handleDelete(l.location_id)}>Usuń</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </main>
  )
}
