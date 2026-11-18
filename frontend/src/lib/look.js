// Display helpers: prices, colours, verdicts.

const inr = new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 })
export const formatPrice = (n, currency = 'INR') =>
  currency === 'INR' ? inr.format(n) : new Intl.NumberFormat('en-IN', { style: 'currency', currency }).format(n)

const COLOR_HEX = {
  black: '#24252B', white: '#F8F8F4', navy: '#26335E', olive: '#6E6C3B', sage: '#9DB08B', rust: '#B4572C',
  maroon: '#6E2230', beige: '#D9C8A7', grey: '#9A9EA7', gray: '#9A9EA7', charcoal: '#47494F',
  'sky blue': '#93C5E6', 'light blue': '#A8C6E3', blue: '#3E68B0', mustard: '#D3A23C', yellow: '#E4C24C',
  teal: '#2F7D78', indigo: '#3A3F8C', pink: '#E7A4B6', lavender: '#B8A7D8', purple: '#6E4C99',
  brown: '#6D4B34', cream: '#EFE5CE', 'off white': '#F1ECE0', khaki: '#B8A679', red: '#B5332F',
  orange: '#D8782C', green: '#4E7C4A',
}

export function colorHex(name) {
  if (!name) return '#C9CCD6'
  const key = name.toLowerCase()
  if (COLOR_HEX[key]) return COLOR_HEX[key]
  const hit = Object.keys(COLOR_HEX).find((k) => key.includes(k))
  return hit ? COLOR_HEX[hit] : '#C9CCD6'
}

export const VERDICT = {
  true_fit: { label: 'True Fit', tone: 'fit' },
  good: { label: 'Good fit', tone: 'fit' },
  compromise: { label: 'Fits with a compromise', tone: 'ok' },
  no_fit: { label: "Won't fit", tone: 'no' },
  needs_measurements: { label: 'Add measurements', tone: 'none' },
}

export const TONE_CLASSES = {
  fit: 'text-fit bg-fit-bg',
  ok: 'text-ok bg-ok-bg',
  no: 'text-no bg-no-bg',
  none: 'text-ink-soft bg-paper',
}

export const TONE_HEX = { fit: '#1F7A4D', ok: '#A85F0F', no: '#B0392B', none: '#7C8199' }

export function statusTone(status) {
  if (status === 'good') return 'fit'
  if (status?.startsWith('too_')) return 'no'
  return 'ok'
}

export const CHART_SOURCE = {
  product: "Size chart from this product's page.",
  brand: "Size chart from the brand.",
  standard: 'No size chart was published, so this is matched against a standard chart. Treat it as a rough guide.',
}
