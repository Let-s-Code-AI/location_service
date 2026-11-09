import {
  EMPTY_FILTERS,
  isEmptyFilters,
  pluralOffers,
  toQuery,
  validateFilters,
} from './listingFilters.js'

const filters = (patch) => ({ ...EMPTY_FILTERS, ...patch })

describe('toQuery', () => {
  test('pomija puste pola', () => {
    expect(toQuery(EMPTY_FILTERS)).toBe('')
    expect(toQuery(filters({ price_total_min: '100', city: '  ' }))).toBe('price_total_min=100')
  })

  test('powtarza parametr rooms i przycina tekst', () => {
    const query = new URLSearchParams(
      toQuery(filters({ rooms: [2, 3], city: ' Kraków ' }), { skip: 0, limit: 50 }),
    )
    expect(query.getAll('rooms')).toEqual(['2', '3'])
    expect(query.get('city')).toBe('Kraków')
    expect(query.get('skip')).toBe('0')
    expect(query.get('limit')).toBe('50')
  })

  test('przekazuje frazę q', () => {
    expect(toQuery(filters({ q: ' Mokotów ' }))).toBe(`q=${encodeURIComponent('Mokotów')}`)
  })
})

describe('validateFilters', () => {
  test('poprawne i puste filtry nie mają błędów', () => {
    expect(validateFilters(EMPTY_FILTERS)).toEqual({})
    expect(validateFilters(filters({ area_min: '30', area_max: '30' }))).toEqual({})
  })

  test('min większe niż max', () => {
    expect(validateFilters(filters({ price_sqm_min: '20000', price_sqm_max: '10000' }))).toEqual({
      price_sqm_max: 'Maksimum nie może być mniejsze niż minimum',
    })
  })

  test('wartość ujemna i nieliczbowa', () => {
    expect(validateFilters(filters({ price_total_min: '-1', area_max: 'abc' }))).toEqual({
      price_total_min: 'Wartość nie może być ujemna',
      area_max: 'Podaj liczbę',
    })
  })
})

test('isEmptyFilters', () => {
  expect(isEmptyFilters(EMPTY_FILTERS)).toBe(true)
  expect(isEmptyFilters(filters({ rooms: [1] }))).toBe(false)
  expect(isEmptyFilters(filters({ city: 'Kraków' }))).toBe(false)
  expect(isEmptyFilters(filters({ city: '   ' }))).toBe(true)
})

test.each([
  [0, '0 ofert'],
  [1, '1 oferta'],
  [2, '2 oferty'],
  [5, '5 ofert'],
  [12, '12 ofert'],
  [22, '22 oferty'],
  [112, '112 ofert'],
])('pluralOffers(%i) = %s', (n, expected) => {
  expect(pluralOffers(n)).toBe(expected)
})
