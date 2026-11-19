const PRICES = [
  { value: '', label: 'Any price' },
  { value: '1000', label: 'Up to ₹1,000' },
  { value: '2000', label: 'Up to ₹2,000' },
  { value: '3000', label: 'Up to ₹3,000' },
  { value: '5000', label: 'Up to ₹5,000' },
]

const SORTS = [
  { value: 'fit', label: 'Best fit first' },
  { value: 'price_asc', label: 'Price, low to high' },
  { value: 'price_desc', label: 'Price, high to low' },
]

function Select({ label, value, onChange, children }) {
  return (
    <label className="flex flex-col text-sm">
      <span className="sr-only">{label}</span>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="rounded-full border-2 border-ink/20 bg-sheet py-1.5 pr-8 pl-3.5 font-semibold hover:border-ink"
      >
        {children}
      </select>
    </label>
  )
}

export default function FilterBar({ filters, onChange, categories, onlyFitting, onOnlyFitting, canFit, hideCategory = false }) {
  const set = (patch) => onChange({ ...filters, ...patch })
  return (
    <div className="flex flex-wrap items-center gap-2">
      {!hideCategory && (
      <Select label="Category" value={filters.category} onChange={(category) => set({ category })}>
        <option value="">All clothing</option>
        {categories
          .filter((c) => c.count > 0)
          .map((c) => (
            <option key={c.key} value={c.key}>
              {c.label}
            </option>
          ))}
      </Select>
      )}
      <Select label="Price" value={filters.max_price} onChange={(max_price) => set({ max_price })}>
        {PRICES.map((p) => (
          <option key={p.value} value={p.value}>
            {p.label}
          </option>
        ))}
      </Select>
      <Select label="Sort" value={filters.sort} onChange={(sort) => set({ sort })}>
        {SORTS.map((s) => (
          <option key={s.value} value={s.value}>
            {s.label}
          </option>
        ))}
      </Select>
      <label
        className={`ml-auto flex cursor-pointer items-center gap-2 text-sm select-none ${canFit ? '' : 'cursor-not-allowed opacity-50'}`}
        title={canFit ? undefined : 'Add your measurements first'}
      >
        <input
          type="checkbox"
          className="peer sr-only"
          checked={onlyFitting && canFit}
          disabled={!canFit}
          onChange={(e) => onOnlyFitting(e.target.checked)}
        />
        <span
          aria-hidden="true"
          className="relative h-5 w-9 rounded-full border border-ink/40 bg-paper transition-colors peer-checked:border-fit peer-checked:bg-fit peer-focus-visible:outline-2 peer-focus-visible:outline-chalk after:absolute after:top-0.5 after:left-0.5 after:h-3.5 after:w-3.5 after:rounded-full after:bg-sheet after:shadow-sm after:transition-transform peer-checked:after:translate-x-4"
        />
        Only what fits me
      </label>
    </div>
  )
}
