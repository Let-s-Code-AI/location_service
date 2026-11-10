// Panel filtrów ofert (komponent prezentacyjny): stan, walidację i pobieranie danych trzyma rodzic.
import Autocomplete from './Autocomplete.jsx'
import { RANGES, isEmptyFilters, pluralOffers } from './listingFilters.js'

const ROOM_OPTIONS = [1, 2, 3, 4, 5]

const ENDS = [
  { end: 'min', placeholder: 'od' },
  { end: 'max', placeholder: 'do' },
]

// fetchSuggestions(field, q, city) ma sygnaturę suggestListingValues z api.js.
export default function ListingFilters({
  filters,
  errors = {},
  total,
  loading = false,
  onChange,
  onReset,
  fetchSuggestions,
}) {
  function toggleRoom(room) {
    const rooms = filters.rooms.includes(room)
      ? filters.rooms.filter((r) => r !== room)
      : [...filters.rooms, room].sort((a, b) => a - b)
    onChange({ rooms })
  }

  return (
    <section className="card spaced">
      <div className="card-head">
        <h2 className="card-title">Filtry</h2>
        <div className="filters-summary">
          <span className="filters-count" aria-live="polite">
            {loading ? 'Szukam ofert…' : total != null && <>Wyniki: <strong>{pluralOffers(total)}</strong></>}
          </span>
          <button
            type="button"
            className="btn btn-ghost"
            onClick={onReset}
            disabled={isEmptyFilters(filters)}
          >
            Wyczyść filtry
          </button>
        </div>
      </div>
      <div className="card-body filters-grid">
        <div className="filter-group filter-search">
          <label htmlFor="filter-q">Szukaj ofert</label>
          <div className="input-wrap">
            <input
              id="filter-q"
              type="search"
              className="no-icon"
              placeholder="miasto, dzielnica lub ulica"
              maxLength={100}
              value={filters.q}
              onChange={(event) => onChange({ q: event.target.value })}
            />
          </div>
        </div>
        {RANGES.map(({ key, label }) => (
          <fieldset key={key} className="filter-group">
            <legend>{label}</legend>
            <div className="range-inputs">
              {ENDS.map(({ end, placeholder }) => {
                const field = `${key}_${end}`
                return (
                  <div key={end} className="input-wrap">
                    <input
                      type="number"
                      min="0"
                      inputMode="decimal"
                      aria-label={`${label} ${placeholder}`}
                      aria-invalid={Boolean(errors[field])}
                      aria-describedby={errors[field] ? `${field}-error` : undefined}
                      className={errors[field] ? 'no-icon invalid' : 'no-icon'}
                      placeholder={placeholder}
                      value={filters[field]}
                      onChange={(event) => onChange({ [field]: event.target.value })}
                    />
                  </div>
                )
              })}
            </div>
            {ENDS.map(({ end }) => {
              const field = `${key}_${end}`
              return (
                errors[field] && (
                  <div key={end} id={`${field}-error`} className="hint">
                    {errors[field]}
                  </div>
                )
              )
            })}
          </fieldset>
        ))}

        <fieldset className="filter-group">
          <legend>Pokoje</legend>
          <div className="room-chips">
            {ROOM_OPTIONS.map((room) => (
              <label key={room} className="room-chip">
                <input
                  type="checkbox"
                  checked={filters.rooms.includes(room)}
                  onChange={() => toggleRoom(room)}
                />
                <span>{room}</span>
              </label>
            ))}
          </div>
        </fieldset>

        <Autocomplete
          id="filter-city"
          label="Miasto"
          icon="city"
          placeholder="np. Kraków"
          value={filters.city}
          onChange={(city) => onChange({ city })}
          fetchSuggestions={(q) => fetchSuggestions('city', q)}
        />
        <Autocomplete
          id="filter-district"
          label="Dzielnica"
          icon="district"
          placeholder="np. Podgórze"
          value={filters.city_district}
          onChange={(city_district) => onChange({ city_district })}
          fetchSuggestions={(q) => fetchSuggestions('city_district', q, filters.city.trim() || undefined)}
        />
      </div>
    </section>
  )
}
