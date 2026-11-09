import { act, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { useState } from 'react'
import Autocomplete, { DEBOUNCE_MS } from './Autocomplete.jsx'

function Harness({ fetchSuggestions, onChange = () => {} }) {
  const [value, setValue] = useState('')
  return (
    <Autocomplete
      id="city"
      label="Miasto"
      value={value}
      onChange={(next) => {
        setValue(next)
        onChange(next)
      }}
      fetchSuggestions={fetchSuggestions}
    />
  )
}

function setup(fetchSuggestions, onChange) {
  const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime })
  render(<Harness fetchSuggestions={fetchSuggestions} onChange={onChange} />)
  return { user, input: screen.getByRole('combobox', { name: 'Miasto' }) }
}

const flushDebounce = () => act(() => vi.advanceTimersByTimeAsync(DEBOUNCE_MS))

// shouldAdvanceTime: asyncWrapper Testing Library czeka na prawdziwy setTimeout, bez tego testy wiszą.
beforeEach(() => vi.useFakeTimers({ shouldAdvanceTime: true }))
afterEach(() => vi.useRealTimers())

test('woła fetchSuggestions raz po debounce z ostatnią wartością', async () => {
  const fetchSuggestions = vi.fn().mockResolvedValue(['Kraków'])
  const { user, input } = setup(fetchSuggestions)

  await user.type(input, 'Kra')
  expect(fetchSuggestions).not.toHaveBeenCalled()
  await flushDebounce()

  expect(fetchSuggestions).toHaveBeenCalledTimes(1)
  expect(fetchSuggestions).toHaveBeenCalledWith('Kra')
  expect(screen.getByRole('option', { name: 'Kraków' })).toBeTruthy()
})

test('kliknięcie podpowiedzi wybiera wartość i zamyka listę', async () => {
  const onChange = vi.fn()
  const { user, input } = setup(vi.fn().mockResolvedValue(['Kraków', 'Krosno']), onChange)

  await user.type(input, 'Kr')
  await flushDebounce()
  await user.click(screen.getByRole('option', { name: 'Krosno' }))

  expect(onChange).toHaveBeenLastCalledWith('Krosno')
  expect(input.value).toBe('Krosno')
  expect(screen.queryByRole('listbox')).toBeNull()
})

test('strzałki i Enter wybierają podpowiedź', async () => {
  const { user, input } = setup(vi.fn().mockResolvedValue(['Kraków', 'Krosno']))

  await user.type(input, 'Kr')
  await flushDebounce()
  await user.keyboard('{ArrowDown}{ArrowDown}')
  expect(screen.getByRole('option', { name: 'Krosno' }).getAttribute('aria-selected')).toBe('true')
  await user.keyboard('{ArrowDown}')
  expect(screen.getByRole('option', { name: 'Kraków' }).getAttribute('aria-selected')).toBe('true')
  await user.keyboard('{Enter}')

  expect(input.value).toBe('Kraków')
  expect(screen.queryByRole('listbox')).toBeNull()
})

test('Escape zamyka listę bez zmiany wartości', async () => {
  const { user, input } = setup(vi.fn().mockResolvedValue(['Kraków']))

  await user.type(input, 'Kr')
  await flushDebounce()
  await user.keyboard('{Escape}')

  expect(screen.queryByRole('listbox')).toBeNull()
  expect(input.value).toBe('Kr')
  expect(input.getAttribute('aria-expanded')).toBe('false')
})

test('spóźniona odpowiedź nie nadpisuje nowszej', async () => {
  let resolveSlow
  const fetchSuggestions = vi
    .fn()
    .mockImplementationOnce(() => new Promise((resolve) => (resolveSlow = resolve)))
    .mockResolvedValueOnce(['Kraków'])
  const { user, input } = setup(fetchSuggestions)

  await user.type(input, 'K')
  await flushDebounce()
  await user.type(input, 'ra')
  await flushDebounce()
  await act(async () => resolveSlow(['Katowice', 'Kielce']))

  expect(fetchSuggestions).toHaveBeenNthCalledWith(2, 'Kra')
  expect(screen.getAllByRole('option').map((o) => o.textContent)).toEqual(['Kraków'])
})

test('błąd pobierania nie pokazuje listy ani alertu', async () => {
  const { user, input } = setup(vi.fn().mockRejectedValue(new Error('HTTP 500')))

  await user.type(input, 'Kr')
  await flushDebounce()

  expect(screen.queryByRole('listbox')).toBeNull()
  expect(screen.queryByRole('alert')).toBeNull()
})
