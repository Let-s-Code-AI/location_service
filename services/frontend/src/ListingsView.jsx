// Widok ofert: trzyma stan filtrów, waliduje je i pobiera pierwszą stronę wyników z licznikiem total.
import { useEffect, useRef, useState } from 'react'
import { listListings, suggestListingValues } from './api.js'
import ListingFilters from './ListingFilters.jsx'
import { EMPTY_FILTERS, isEmptyFilters, validateFilters } from './listingFilters.js'
import { Icon } from './ui.jsx'

export const DEBOUNCE_MS = 300
export const PAGE_SIZE = 50

const number = new Intl.NumberFormat('pl-PL', { maximumFractionDigits: 2 })
const dash = <span className="empty">—</span>
const fmt = (value, unit) => (value == null ? dash : `${number.format(value)} ${unit}`)

export default function ListingsView({ onLogout }) {
  const [filters, setFilters] = useState(EMPTY_FILTERS)
  const [page, setPage] = useState({ items: [], total: null })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  // Pierwsze pobranie i reset idą od razu, zwykła zmiana filtra po debounce.
  const immediate = useRef(true)
  // Numer ostatniego żądania: odpowiedź z innym numerem jest spóźniona i jest ignorowana.
  const requestId = useRef(0)

  const errors = validateFilters(filters)
  const valid = Object.keys(errors).length === 0

  useEffect(() => {
    const current = ++requestId.current
    if (!valid) {
      setLoading(false)
      return
    }
    setLoading(true)
    const timer = setTimeout(async () => {
      immediate.current = false
      try {
        // Każda zmiana filtrów zaczyna od pierwszej strony (skip=0).
        const result = await listListings(filters, { skip: 0, limit: PAGE_SIZE })
        if (current !== requestId.current) return
        setPage(result)
        setError(null)
      } catch (e) {
        if (current === requestId.current) setError(`Nie udało się pobrać ofert: ${e.message}`)
      } finally {
        if (current === requestId.current) setLoading(false)
      }
    }, immediate.current ? 0 : DEBOUNCE_MS)
    return () => clearTimeout(timer)
  }, [filters, valid])

  function handleReset() {
    immediate.current = true
    setFilters(EMPTY_FILTERS)
  }

  const { items, total } = page

  return (
    <div className="container">
      <header className="page-header">
        <div>
          <div className="eyebrow">Rynek</div>
          <h1>Oferty</h1>
          <p className="subtitle">Zawężaj oferty po cenie, metrażu, liczbie pokoi i lokalizacji.</p>
        </div>
        <button type="button" className="btn btn-ghost" onClick={onLogout}>
          Wyloguj
        </button>
      </header>

      {error && (
        <div className="alert" role="alert">
          {error}
        </div>
      )}

      <ListingFilters
        filters={filters}
        errors={errors}
        total={valid ? total : null}
        loading={loading}
        onChange={(patch) => setFilters((f) => ({ ...f, ...patch }))}
        onReset={handleReset}
        fetchSuggestions={suggestListingValues}
      />

      <section className="card">
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                {['Miasto', 'Dzielnica', 'Pokoje', 'Metraż', 'Cena', 'Cena/m²'].map((label) => (
                  <th key={label} className="no-sort">
                    {label}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {total === null ? (
                <tr>
                  <td colSpan={6} className="loading-cell">
                    {loading ? 'Ładowanie…' : '—'}
                  </td>
                </tr>
              ) : items.length === 0 ? (
                <tr>
                  <td colSpan={6}>
                    <div className="empty-state">
                      <Icon name="search" size={40} strokeWidth={1.5} />
                      <strong>Brak ofert</strong>
                      {isEmptyFilters(filters) ? 'W bazie nie ma jeszcze ofert.' : 'Zmień lub wyczyść filtry.'}
                    </div>
                  </td>
                </tr>
              ) : (
                items.map((l) => (
                  <tr key={l.listing_id}>
                    <td>{l.location.city || dash}</td>
                    <td>{l.location.city_district || dash}</td>
                    <td>{l.rooms ?? dash}</td>
                    <td>{fmt(l.area, 'm²')}</td>
                    <td>{fmt(l.price_total_zl, 'zł')}</td>
                    <td>{fmt(l.price_sqm_zl, 'zł')}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
        <div className="table-foot">
          <span>
            Wyświetlono {items.length} z {total ?? 0}
          </span>
        </div>
      </section>
    </div>
  )
}
