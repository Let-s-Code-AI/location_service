// Kontrolowane pole tekstowe z podpowiedziami (combobox ARIA). Źródło podpowiedzi jest wstrzykiwane
// przez fetchSuggestions(q), więc komponent nie zna API, a testy nie muszą mockować fetch.
import { useEffect, useRef, useState } from 'react'
import { Icon } from './ui.jsx'

export const DEBOUNCE_MS = 250

export default function Autocomplete({ id, label, value, onChange, fetchSuggestions, placeholder, icon }) {
  const [options, setOptions] = useState([])
  const [open, setOpen] = useState(false)
  const [active, setActive] = useState(-1)
  const timer = useRef(null)
  // Numer ostatniego żądania: odpowiedź z innym numerem jest spóźniona i jest ignorowana.
  const requestId = useRef(0)
  const listId = `${id}-listbox`

  useEffect(
    () => () => {
      clearTimeout(timer.current)
      requestId.current += 1
    },
    [],
  )

  function cancelPending() {
    clearTimeout(timer.current)
    requestId.current += 1
  }

  function close() {
    cancelPending()
    setOpen(false)
    setActive(-1)
  }

  function handleInput(event) {
    const q = event.target.value
    onChange(q)
    close()
    if (q.trim() === '') return
    const current = requestId.current
    timer.current = setTimeout(async () => {
      try {
        const result = await fetchSuggestions(q)
        if (current !== requestId.current) return
        setOptions(result)
        setOpen(result.length > 0)
      } catch {
        // Błąd podpowiedzi nie blokuje wpisywania: po prostu nie pokazujemy listy.
        if (current === requestId.current) setOptions([])
      }
    }, DEBOUNCE_MS)
  }

  function select(option) {
    onChange(option)
    close()
  }

  function handleKeyDown(event) {
    if (!open) return
    const last = options.length - 1
    if (event.key === 'ArrowDown') {
      event.preventDefault()
      setActive((i) => (i >= last ? 0 : i + 1))
    } else if (event.key === 'ArrowUp') {
      event.preventDefault()
      setActive((i) => (i <= 0 ? last : i - 1))
    } else if (event.key === 'Enter' && active >= 0) {
      event.preventDefault()
      select(options[active])
    } else if (event.key === 'Escape') {
      event.preventDefault()
      close()
    }
  }

  return (
    <div className="field">
      <label htmlFor={id}>{label}</label>
      <div className="input-wrap">
        {icon && <Icon name={icon} />}
        <input
          id={id}
          type="text"
          role="combobox"
          autoComplete="off"
          aria-autocomplete="list"
          aria-expanded={open}
          aria-controls={listId}
          aria-activedescendant={open && active >= 0 ? `${id}-option-${active}` : undefined}
          className={icon ? undefined : 'no-icon'}
          value={value}
          placeholder={placeholder}
          onChange={handleInput}
          onKeyDown={handleKeyDown}
          onBlur={close}
        />
        {open && (
          <ul id={listId} role="listbox" className="suggestions">
            {options.map((option, index) => (
              <li
                key={option}
                id={`${id}-option-${index}`}
                role="option"
                aria-selected={index === active}
                // mousedown zamiast click: inaczej blur pola zamknie listę przed wyborem.
                onMouseDown={(event) => {
                  event.preventDefault()
                  select(option)
                }}
              >
                {option}
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  )
}
