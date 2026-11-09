import { fireEvent, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import ListingFilters from './ListingFilters.jsx'
import { EMPTY_FILTERS } from './listingFilters.js'

function setup(props = {}) {
  const handlers = { onChange: vi.fn(), onReset: vi.fn(), fetchSuggestions: vi.fn().mockResolvedValue([]) }
  render(<ListingFilters filters={EMPTY_FILTERS} total={0} {...handlers} {...props} />)
  return { user: userEvent.setup(), ...handlers }
}

test('zmiana ceny minimalnej woła onChange z łatką pola', () => {
  const { onChange } = setup()

  fireEvent.change(screen.getByLabelText('Cena (zł) od'), { target: { value: '300000' } })

  expect(onChange).toHaveBeenCalledWith({ price_total_min: '300000' })
})

test('zaznaczenie i odznaczenie pokoju', async () => {
  const { user, onChange } = setup({ filters: { ...EMPTY_FILTERS, rooms: [3] } })

  await user.click(screen.getByRole('checkbox', { name: '2' }))
  expect(onChange).toHaveBeenLastCalledWith({ rooms: [2, 3] })

  await user.click(screen.getByRole('checkbox', { name: '3' }))
  expect(onChange).toHaveBeenLastCalledWith({ rooms: [] })
})

test('błąd z errors jest widoczny przy polu', () => {
  setup({ errors: { area_max: 'Maksimum nie może być mniejsze niż minimum' } })

  const input = screen.getByLabelText('Metraż (m²) do')
  expect(input.getAttribute('aria-invalid')).toBe('true')
  expect(input.className).toContain('invalid')
  const message = document.getElementById(input.getAttribute('aria-describedby'))
  expect(message.textContent).toBe('Maksimum nie może być mniejsze niż minimum')
})

test.each([
  [1, '1 oferta'],
  [3, '3 oferty'],
  [12, '12 ofert'],
])('licznik dla total=%i pokazuje „%s”', (total, text) => {
  setup({ total })

  expect(screen.getByText(text)).toBeTruthy()
})

test('licznik pokazuje stan ładowania', () => {
  setup({ total: 5, loading: true })

  expect(screen.getByText('Szukam ofert…')).toBeTruthy()
  expect(screen.queryByText('5 ofert')).toBeNull()
})

test('reset jest wyłączony przy pustych filtrach', () => {
  setup()

  expect(screen.getByRole('button', { name: 'Wyczyść filtry' }).disabled).toBe(true)
})

test('reset woła onReset przy ustawionych filtrach', async () => {
  const { user, onReset } = setup({ filters: { ...EMPTY_FILTERS, city: 'Kraków' } })

  await user.click(screen.getByRole('button', { name: 'Wyczyść filtry' }))

  expect(onReset).toHaveBeenCalledTimes(1)
})

test('podpowiedzi dzielnic są zawężane do wybranego miasta', async () => {
  vi.useFakeTimers({ shouldAdvanceTime: true })
  try {
    const { fetchSuggestions } = setup({ filters: { ...EMPTY_FILTERS, city: 'Kraków' } })
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime })

    await user.type(screen.getByRole('combobox', { name: 'Dzielnica' }), 'P')
    await vi.advanceTimersByTimeAsync(250)

    expect(fetchSuggestions).toHaveBeenCalledWith('city_district', 'P', 'Kraków')
  } finally {
    vi.useRealTimers()
  }
})
