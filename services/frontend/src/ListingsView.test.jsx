import { act, fireEvent, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { listListings } from './api.js'
import { EMPTY_FILTERS } from './listingFilters.js'
import ListingsView, { DEBOUNCE_MS, PAGE_SIZE } from './ListingsView.jsx'

vi.mock('./api.js', () => ({
  listListings: vi.fn(),
  suggestListingValues: vi.fn().mockResolvedValue([]),
}))

const listing = (id, city) => ({
  listing_id: id,
  rooms: 2,
  area: 48.5,
  price_total_zl: 650000,
  price_sqm_zl: 13402.06,
  location: { city, city_district: 'Podgórze' },
})

const PAGE = { items: [listing(1, 'Kraków'), listing(2, 'Kraków')], total: 2, skip: 0, limit: PAGE_SIZE }
const FIRST_PAGE = { skip: 0, limit: PAGE_SIZE }

// Pozwala opróżnić kolejkę mikrozadań, żeby rozwiązany mock zdążył ustawić stan.
const flush = (ms = 0) => act(() => vi.advanceTimersByTimeAsync(ms))

beforeEach(() => {
  vi.useFakeTimers({ shouldAdvanceTime: true })
  listListings.mockReset().mockResolvedValue(PAGE)
})
afterEach(() => vi.useRealTimers())

async function renderView() {
  render(<ListingsView actions={null} />)
  await flush()
}

test('pierwsze renderowanie pobiera oferty bez filtrów i pokazuje licznik', async () => {
  await renderView()

  expect(listListings).toHaveBeenCalledTimes(1)
  expect(listListings).toHaveBeenCalledWith(EMPTY_FILTERS, FIRST_PAGE)
  expect(screen.getByText('2 oferty')).toBeTruthy()
  expect(screen.getAllByText('Kraków')).toHaveLength(2)
  expect(screen.getAllByText('650 000 zł')).toHaveLength(2)
  expect(screen.getByText('Wyświetlono 2 z 2')).toBeTruthy()
})

test('zmiana filtra pobiera oferty po debounce i aktualizuje licznik', async () => {
  await renderView()
  listListings.mockResolvedValueOnce({ ...PAGE, items: [listing(3, 'Kraków')], total: 1 })

  fireEvent.change(screen.getByLabelText('Cena (zł) od'), { target: { value: '600000' } })
  await flush(DEBOUNCE_MS - 1)
  expect(listListings).toHaveBeenCalledTimes(1)
  await flush(1)

  expect(listListings).toHaveBeenCalledTimes(2)
  expect(listListings).toHaveBeenLastCalledWith({ ...EMPTY_FILTERS, price_total_min: '600000' }, FIRST_PAGE)
  expect(screen.getByText('1 oferta')).toBeTruthy()
})

test('min > max nie wysyła żądania i pokazuje komunikat', async () => {
  await renderView()

  fireEvent.change(screen.getByLabelText('Metraż (m²) od'), { target: { value: '80' } })
  fireEvent.change(screen.getByLabelText('Metraż (m²) do'), { target: { value: '40' } })
  await flush(DEBOUNCE_MS)

  expect(listListings).toHaveBeenCalledTimes(1)
  expect(screen.getByText('Maksimum nie może być mniejsze niż minimum')).toBeTruthy()
  expect(screen.queryByText('2 oferty')).toBeNull()
})

test('reset pobiera oferty z pustymi filtrami bez debounce', async () => {
  const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime })
  await renderView()
  fireEvent.change(screen.getByLabelText('Cena (zł) od'), { target: { value: '600000' } })
  await flush(DEBOUNCE_MS)

  await user.click(screen.getByRole('button', { name: 'Wyczyść filtry' }))
  await flush()

  expect(listListings).toHaveBeenCalledTimes(3)
  expect(listListings).toHaveBeenLastCalledWith(EMPTY_FILTERS, FIRST_PAGE)
  expect(screen.getByLabelText('Cena (zł) od').value).toBe('')
})

test('spóźniona odpowiedź nie nadpisuje nowszej', async () => {
  await renderView()
  let resolveSlow
  listListings
    .mockImplementationOnce(() => new Promise((resolve) => (resolveSlow = resolve)))
    .mockResolvedValueOnce({ ...PAGE, items: [], total: 0 })

  fireEvent.change(screen.getByLabelText('Cena (zł) od'), { target: { value: '1' } })
  await flush(DEBOUNCE_MS)
  fireEvent.change(screen.getByLabelText('Cena (zł) od'), { target: { value: '10' } })
  await flush(DEBOUNCE_MS)
  await act(async () => resolveSlow({ ...PAGE, total: 7 }))

  expect(screen.getByText('0 ofert')).toBeTruthy()
  expect(screen.queryByText('7 ofert')).toBeNull()
})

test('błąd API pokazuje alert', async () => {
  listListings.mockRejectedValue(new Error('HTTP 500'))
  await renderView()

  expect(screen.getByRole('alert').textContent).toBe('Nie udało się pobrać ofert: HTTP 500')
})
