// Stan filtrów ofert: wartości pól trzymamy jako stringi (prosto z <input>), pokoje jako tablicę liczb.

export const RANGES = [
  { key: 'price_total', label: 'Cena (zł)' },
  { key: 'price_sqm', label: 'Cena za m² (zł)' },
  { key: 'area', label: 'Metraż (m²)' },
]

export const EMPTY_FILTERS = Object.freeze({
  price_total_min: '',
  price_total_max: '',
  price_sqm_min: '',
  price_sqm_max: '',
  area_min: '',
  area_max: '',
  rooms: [],
  city: '',
  city_district: '',
})

const isBlank = (value) => String(value ?? '').trim() === ''

export function isEmptyFilters(filters) {
  return Object.entries(filters).every(([key, value]) =>
    key === 'rooms' ? value.length === 0 : isBlank(value),
  )
}

// Zwraca mapę { pole: komunikat }; pusta mapa = filtry poprawne.
export function validateFilters(filters) {
  const errors = {}
  for (const { key } of RANGES) {
    const values = {}
    for (const end of ['min', 'max']) {
      const field = `${key}_${end}`
      if (isBlank(filters[field])) continue
      const number = Number(filters[field])
      if (!Number.isFinite(number)) errors[field] = 'Podaj liczbę'
      else if (number < 0) errors[field] = 'Wartość nie może być ujemna'
      else values[end] = number
    }
    if (values.min !== undefined && values.max !== undefined && values.min > values.max) {
      errors[`${key}_max`] = 'Maksimum nie może być mniejsze niż minimum'
    }
  }
  return errors
}

export function toQuery(filters, { skip, limit } = {}) {
  const params = new URLSearchParams()
  for (const [key, value] of Object.entries(filters)) {
    if (key === 'rooms') value.forEach((room) => params.append('rooms', String(room)))
    else if (!isBlank(value)) params.append(key, String(value).trim())
  }
  if (skip !== undefined) params.append('skip', String(skip))
  if (limit !== undefined) params.append('limit', String(limit))
  return params.toString()
}

// 1 oferta, 2–4 oferty, 5+ ofert (12–14 to zawsze "ofert").
export function pluralOffers(n) {
  if (n === 1) return '1 oferta'
  const lastDigit = n % 10
  const lastTwo = n % 100
  if (lastDigit >= 2 && lastDigit <= 4 && (lastTwo < 12 || lastTwo > 14)) return `${n} oferty`
  return `${n} ofert`
}
