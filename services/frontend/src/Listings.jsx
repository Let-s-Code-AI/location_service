import { useEffect, useState } from 'react'
import { listListings } from './api.js'
import { Field, Icon } from './ui.jsx'

const EMPTY_FILTERS = { q: '', price_min: '', price_max: '', rooms_min: '' }
const DEBOUNCE_MS = 300

const cell = (v) => (v == null || v === '' ? <span className="empty">—</span> : v)
const formatPrice = (v) => (v == null ? null : `${Number(v).toLocaleString('pl-PL')} zł`)
const formatArea = (v) => (v == null ? null : `${Number(v).toLocaleString('pl-PL')} m²`)

export default function Listings({ actions }) {
  const [filters, setFilters] = useState(EMPTY_FILTERS)
  const [rows, setRows] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  // Wyszukiwanie po stronie serwera z debounce: jedno żądanie na serię naciśnięć klawiszy.
  // Flaga `cancelled` odrzuca odpowiedzi, które przyszły po zmianie filtrów.
  useEffect(() => {
    let cancelled = false
    const timer = setTimeout(async () => {
      try {
        const data = await listListings({ ...filters, q: filters.q.trim() })
        if (!cancelled) {
          setRows(data)
          setError(null)
        }
      } catch (e) {
        if (!cancelled) setError(`Nie udało się pobrać ogłoszeń: ${e.message}`)
      } finally {
        if (!cancelled) setLoading(false)
      }
    }, DEBOUNCE_MS)
    return () => {
      cancelled = true
      clearTimeout(timer)
    }
  }, [filters])

  const setFilter = (name) => (e) => setFilters((f) => ({ ...f, [name]: e.target.value }))
  const hasFilters = Object.values(filters).some((v) => v !== '')

  return (
    <div className="container">
      <header className="page-header">
        <div>
          <div className="eyebrow">Oferty</div>
          <h1>Ogłoszenia</h1>
          <p className="subtitle">Wyszukuj mieszkania po lokalizacji, cenie i liczbie pokoi.</p>
        </div>
        {actions}
      </header>

      {error && (
        <div className="alert" role="alert">
          {error}
        </div>
      )}

      <section className="card spaced">
        <div className="card-head">
          <h2 className="card-title">Wyszukiwarka</h2>
        </div>
        <div className="card-body">
          <form role="search" onSubmit={(e) => e.preventDefault()}>
            <div className="form-grid">
              <Field
                id="listing-q"
                label="Szukaj ogłoszeń"
                icon="search"
                type="search"
                placeholder="Miasto, dzielnica, ulica…"
                maxLength={100}
                value={filters.q}
                onChange={setFilter('q')}
              />
              <Field
                id="price-min"
                label="Cena od"
                type="number"
                inputMode="numeric"
                min={0}
                placeholder="zł"
                value={filters.price_min}
                onChange={setFilter('price_min')}
              />
              <Field
                id="price-max"
                label="Cena do"
                type="number"
                inputMode="numeric"
                min={0}
                placeholder="zł"
                value={filters.price_max}
                onChange={setFilter('price_max')}
              />
              <Field
                id="rooms-min"
                label="Pokoje od"
                type="number"
                inputMode="numeric"
                min={1}
                placeholder="np. 2"
                value={filters.rooms_min}
                onChange={setFilter('rooms_min')}
              />
              <button
                type="button"
                className="btn btn-ghost"
                onClick={() => setFilters(EMPTY_FILTERS)}
                disabled={!hasFilters}
              >
                Wyczyść filtry
              </button>
            </div>
          </form>
        </div>
      </section>

      <section className="card">
        <div className="card-head tight">
          <h2 className="card-title">Wyniki</h2>
        </div>

        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th className="no-sort">ID</th>
                <th className="no-sort">Miasto</th>
                <th className="no-sort">Ulica</th>
                <th className="no-sort">Pokoje</th>
                <th className="no-sort">Metraż</th>
                <th className="no-sort">Cena</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={6} className="loading-cell">Ładowanie…</td>
                </tr>
              ) : rows.length === 0 ? (
                <tr>
                  <td colSpan={6}>
                    <div className="empty-state">
                      <Icon name="search" size={40} strokeWidth={1.5} />
                      <strong>{hasFilters ? 'Brak wyników' : 'Brak ogłoszeń'}</strong>
                      {hasFilters ? 'Spróbuj innej frazy lub poszerz filtry.' : 'W bazie nie ma jeszcze ogłoszeń.'}
                    </div>
                  </td>
                </tr>
              ) : (
                rows.map((r) => (
                  <tr key={r.listing_id}>
                    <td>
                      <span className="id-badge">#{r.listing_id}</span>
                    </td>
                    <td>
                      {r.location.city || <span className="empty">Bez nazwy</span>}
                      {r.location.city_district && <span className="sub">{r.location.city_district}</span>}
                    </td>
                    <td>{cell(r.location.street)}</td>
                    <td>{cell(r.rooms)}</td>
                    <td>{cell(formatArea(r.area))}</td>
                    <td>{cell(formatPrice(r.price_total_zl))}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        <div className="table-foot">
          <span>Znaleziono {rows.length}</span>
        </div>
      </section>
    </div>
  )
}
