// Wspólne elementy UI (ikony i pole formularza) w stylu z lokalizacje.html.

export const ICONS = {
  pin: [
    'M12 21s-7-6.2-7-11.5A7 7 0 0 1 19 9.5C19 14.8 12 21 12 21z',
    'M12 9.5m-2.5 0a2.5 2.5 0 1 0 5 0a2.5 2.5 0 1 0-5 0',
  ],
  check: ['M20 6 9 17l-5-5'],
  warn: [
    'M12 9v4M12 17h.01',
    'M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z',
  ],
  city: ['M3 21h18M5 21V7l7-4 7 4v14M9 9h1M9 13h1M14 9h1M14 13h1'],
  locality: ['M3 10.5 12 3l9 7.5V21H3z', 'M9 21v-6h6v6'],
  district: ['M9 3 3 6v15l6-3 6 3 6-3V3l-6 3-6-3z', 'M9 3v15M15 6v15'],
  street: ['M4 19 8 5M20 19 16 5M12 6v2M12 11v2M12 16v2'],
  search: ['M11 4a7 7 0 1 0 0 14 7 7 0 1 0 0-14z', 'm20 20-3.5-3.5'],
  plus: ['M12 5v14M5 12h14'],
  trash: ['M3 6h18M8 6V4h8v2M19 6l-1 14H6L5 6M10 11v6M14 11v6'],
  mail: ['M3 5h18v14H3z', 'm3 7 9 6 9-6'],
  lock: ['M5 11h14v10H5z', 'M8 11V7a4 4 0 0 1 8 0v4'],
}

export function Icon({ name, size = 16, strokeWidth = 2 }) {
  return (
    <svg
      width={size}
      height={size}
      fill="none"
      stroke="currentColor"
      strokeWidth={strokeWidth}
      viewBox="0 0 24 24"
      aria-hidden="true"
    >
      {ICONS[name].map((d) => (
        <path key={d} d={d} />
      ))}
    </svg>
  )
}

export function Field({ id, label, required = false, icon, invalid = false, ...inputProps }) {
  return (
    <div className="field">
      <label htmlFor={id}>
        {label}
        {required && <span className="req"> *</span>}
      </label>
      <div className="input-wrap">
        {icon && <Icon name={icon} />}
        <input
          id={id}
          type="text"
          autoComplete="off"
          required={required}
          className={invalid ? 'invalid' : undefined}
          {...inputProps}
        />
      </div>
    </div>
  )
}
