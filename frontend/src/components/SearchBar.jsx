import { formatCm } from '../lib/units'
import { formatPrice } from '../lib/look'

const EXAMPLES = [
  'shirt for a 52 inch chest under 3000',
  "jeans for a 6'5 guy, 34 waist",
  'plus size maxi dress, bust 50',
  'petite kurta for 4.11 ft',
]

const DIM_NAMES = { chest: 'chest', waist: 'waist', hips: 'hips', shoulder: 'shoulder', inseam: 'inseam', height: 'height' }

// What the search understood, as plain-language pieces.
function readings(parsed, applied, categories, unit) {
  if (!parsed) return []
  const out = []
  const cat = categories.find((c) => c.key === parsed.category)
  if (cat) out.push(cat.label)
  if (parsed.gender) out.push({ men: 'Men', women: 'Women', unisex: 'Unisex' }[parsed.gender])
  parsed.colors.forEach((c) => out.push(c))
  parsed.materials.forEach((m) => out.push(m))
  if (parsed.min_price && parsed.max_price) out.push(`${formatPrice(parsed.min_price)} to ${formatPrice(parsed.max_price)}`)
  else if (parsed.max_price) out.push(`Up to ${formatPrice(parsed.max_price)}`)
  else if (parsed.min_price) out.push(`From ${formatPrice(parsed.min_price)}`)
  Object.entries(parsed.measurements).forEach(([k, v]) => out.push(`${DIM_NAMES[k] || k} ${formatCm(v, unit, k)}`))
  if (parsed.size_label) out.push(`Size ${parsed.size_label}`)
  if (parsed.fit_preference) out.push(`${parsed.fit_preference} fit`)
  parsed.tags.forEach((t) => out.push(t.replace(/-/g, ' ')))
  ;(applied?.keywords || []).forEach((k) => out.push(`“${k}”`))
  return out
}

export default function SearchBar({ value, onChange, onSubmit, parsed, applied, parser, categories, unit, busy }) {
  const pieces = readings(parsed, applied, categories, unit)
  return (
    <div>
      <form
        role="search"
        onSubmit={(e) => {
          e.preventDefault()
          onSubmit(value)
        }}
        className="flex items-stretch gap-2"
      >
        <label htmlFor="q" className="sr-only">
          Describe what you're looking for
        </label>
        <input
          id="q"
          type="search"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder="Search, e.g. linen shirt"
          className="min-w-0 flex-1 rounded-full border-2 border-ink bg-sheet px-5 py-3 text-base outline-none placeholder:text-ink-faint focus-visible:outline-3 focus-visible:outline-offset-2 focus-visible:outline-chalk sm:text-lg"
        />
        <button
          type="submit"
          disabled={busy}
          className="rounded-full bg-cobalt px-6 font-bold text-sheet hover:bg-cobalt-deep disabled:opacity-60"
        >
          Search
        </button>
      </form>

      {pieces.length > 0 ? (
        <div className="mt-3 flex flex-wrap items-center gap-1.5 text-sm" aria-live="polite">
          <span className="mr-1 text-ink-soft">Reading this as</span>
          {pieces.map((p) => (
            <span key={p} className="rounded-[3px] border border-ink/20 bg-sheet px-2 py-0.5 first-letter:uppercase">
              {p}
            </span>
          ))}
          <span className="ml-1 text-xs text-ink-faint">
            {parser === 'rules' ? 'built-in parser' : parser ? `read by ${parser}` : ''}
          </span>
        </div>
      ) : (
        <div className="mt-3 flex flex-wrap items-center gap-x-3 gap-y-1 text-sm">
          <span className="text-ink-soft">Try</span>
          {EXAMPLES.map((ex) => (
            <button
              key={ex}
              type="button"
              onClick={() => {
                onChange(ex)
                onSubmit(ex)
              }}
              className="text-chalk underline decoration-chalk/40 underline-offset-2 hover:decoration-chalk"
            >
              {ex}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
