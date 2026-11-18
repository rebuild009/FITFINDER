import { useCallback, useEffect, useMemo, useState } from 'react'
import FilterBar from './components/FilterBar'
import ProductCard from './components/ProductCard'
import ProductDrawer from './components/ProductDrawer'
import ProfileCard from './components/ProfileCard'
import SearchBar from './components/SearchBar'
import { api } from './lib/api'
import { hasMeasurements, loadProfile, saveProfile, toApiProfile } from './lib/profile'
import { CM_PER_IN, round1 } from './lib/units'

const PAGE = 24
const DEFAULT_FILTERS = { category: '', max_price: '', sort: 'fit' }

function useDebounced(value, ms) {
  const [v, setV] = useState(value)
  useEffect(() => {
    const t = setTimeout(() => setV(value), ms)
    return () => clearTimeout(t)
  }, [value, ms])
  return v
}

function Wordmark() {
  return (
    <a href="/" className="flex items-center gap-2.5" aria-label="FitFinder home">
      <svg viewBox="0 0 32 32" className="h-7 w-7" aria-hidden="true">
        <rect x="2" y="9" width="28" height="14" rx="2" fill="var(--color-tape)" stroke="var(--color-ink)" strokeWidth="2" />
        <path d="M7 9v6M11 9v4M15 9v6M19 9v4M23 9v6" stroke="var(--color-ink)" strokeWidth="2" />
      </svg>
      <span className="font-expanded text-xl font-extrabold tracking-tight">FitFinder</span>
    </a>
  )
}

export default function App() {
  const [profile, setProfile] = useState(loadProfile)
  const [meta, setMeta] = useState(null)
  const [query, setQuery] = useState('')
  const [submitted, setSubmitted] = useState('')
  const [filters, setFilters] = useState(DEFAULT_FILTERS)
  const [onlyFitting, setOnlyFitting] = useState(true)
  const [limit, setLimit] = useState(PAGE)
  const [result, setResult] = useState({ data: null, error: null, key: null })
  const [openId, setOpenId] = useState(null)

  useEffect(() => saveProfile(profile), [profile])
  useEffect(() => {
    api.meta().then(setMeta).catch(() => {})
  }, [])

  const apiProfile = useMemo(() => toApiProfile(profile), [profile])
  const profileKey = useDebounced(JSON.stringify(apiProfile), 450)
  const canFit = hasMeasurements(profile)

  const requestKey = JSON.stringify([submitted, profileKey, filters, onlyFitting, limit])
  const loading = result.key !== requestKey

  useEffect(() => {
    const ctrl = new AbortController()
    const p = JSON.parse(profileKey)
    const hasBody = !!p && Object.keys(p.measurements || {}).length > 0
    const body = {
      profile: p,
      filters: {
        category: filters.category || null,
        max_price: filters.max_price ? Number(filters.max_price) : null,
      },
      only_fitting: onlyFitting && hasBody,
      sort: filters.sort,
      limit,
      offset: 0,
    }
    const q = submitted.trim()
    const req = q ? api.search({ ...body, query: q }, ctrl.signal) : api.match(body, ctrl.signal)
    req
      .then((data) => setResult({ data, error: null, key: requestKey }))
      .catch((e) => {
        if (e.name !== 'AbortError') setResult((r) => ({ ...r, error: e.message, key: requestKey }))
      })
    return () => ctrl.abort()
  }, [requestKey, submitted, profileKey, filters, onlyFitting, limit])

  const submit = (q) => {
    setSubmitted(q)
    // a new query decides category and price itself
    setFilters((f) => ({ ...DEFAULT_FILTERS, sort: f.sort }))
    setLimit(PAGE)
  }
  const updateProfile = (next) => {
    setProfile(next)
    setLimit(PAGE)
  }
  const closeDrawer = useCallback(() => setOpenId(null), [])

  const { data, error } = result
  const categories = meta?.categories || []

  // The drawer checks fit with what the search actually used: saved measurements plus any typed into the query.
  const effectiveProfile = useMemo(() => {
    const cm = data?.applied?.measurements_cm
    if (!cm) return apiProfile
    const f = apiProfile.unit === 'in' ? 1 / CM_PER_IN : 1
    const measurements = Object.fromEntries(Object.entries(cm).map(([k, v]) => [k, round1(v * f)]))
    return { ...apiProfile, fit_preference: data.applied.fit_preference || apiProfile.fit_preference, measurements }
  }, [data, apiProfile])
  const fittingNow = data?.fitting !== null && data?.fitting !== undefined

  return (
    <div className="mx-auto max-w-[88rem] px-4 pb-16 sm:px-6">
      <header className="flex flex-wrap items-center justify-between gap-3 py-5">
        <Wordmark />
        {meta && (
          <p className="text-sm text-ink-soft">
            {meta.total} products from {meta.brands.length} brands
          </p>
        )}
      </header>

      <section className="pt-4 pb-8 sm:pt-8 sm:pb-10">
        <h1 className="max-w-4xl font-expanded text-[1.8rem] leading-[1.12] font-bold tracking-tight sm:text-[2.6rem]">
          Clothes matched to your measurements, not to a size label.
        </h1>
        <p className="mt-4 max-w-[62ch] text-lg text-ink-soft">
          FitFinder checks every size of every product against your body, then tells you which size fits and where it would
          be tight or loose. Built for the people standard sizes skip: very tall, petite, plus-size, big and tall.
        </p>
      </section>

      <div className="grid gap-6 lg:grid-cols-[22rem_minmax(0,1fr)] lg:items-start">
        <aside className="lg:sticky lg:top-4 lg:max-h-[calc(100svh-2rem)] lg:overflow-y-auto">
          <ProfileCard profile={profile} onChange={updateProfile} />
        </aside>

        <main className="min-w-0 space-y-4">
          <SearchBar
            value={query}
            onChange={setQuery}
            onSubmit={submit}
            parsed={submitted ? data?.parsed : null}
            applied={data?.applied}
            parser={data?.parser}
            categories={categories}
            unit={profile.unit}
            busy={loading}
          />
          <FilterBar
            filters={filters}
            onChange={(f) => {
              setFilters(f)
              setLimit(PAGE)
            }}
            categories={categories}
            onlyFitting={onlyFitting}
            onOnlyFitting={setOnlyFitting}
            canFit={canFit}
          />

          <div className="flex flex-wrap items-baseline justify-between gap-2 border-b border-ink/15 pb-2" aria-live="polite">
            <p className="font-semibold">
              {data &&
                (data.checked === 0
                  ? 'No matching products'
                  : fittingNow
                    ? `${data.fitting} of ${data.checked} ${data.checked === 1 ? 'product fits' : 'products fit'} you`
                    : `${data.total} ${data.total === 1 ? 'product' : 'products'}`)}
            </p>
            <p className="text-sm text-ink-faint">{loading ? 'Checking sizes…' : ''}</p>
          </div>

          {data?.notes?.length > 0 && (
            <ul className="space-y-1 text-sm text-ink-soft">
              {data.notes.map((n) => (
                <li key={n}>{n}</li>
              ))}
            </ul>
          )}

          {error && (
            <div role="alert" className="rounded-md border border-no/30 bg-no-bg p-4 text-no">
              <p className="font-semibold">{error}</p>
              <p className="mt-1 text-sm">
                Start it with <code>uvicorn app.main:app --reload</code> in the backend folder, then search again.
              </p>
            </div>
          )}

          {data && data.items.length === 0 && !error && (
            <div className="rounded-md border border-dashed border-ink/30 bg-sheet/70 p-6">
              <p className="font-semibold">Nothing matches all of that.</p>
              <p className="mt-1 text-sm text-ink-soft">
                {onlyFitting && canFit && data.checked > 0
                  ? `${data.checked} products match your search, but none come in a size that fits you.`
                  : 'Try fewer words, or remove the price limit.'}
              </p>
              <div className="mt-3 flex flex-wrap gap-2">
                {onlyFitting && canFit && data.checked > 0 && (
                  <button type="button" onClick={() => setOnlyFitting(false)} className="rounded-[4px] border border-ink/30 px-3 py-1.5 text-sm hover:border-ink">
                    Show them anyway
                  </button>
                )}
                {(submitted || filters.category || filters.max_price) && (
                  <button
                    type="button"
                    onClick={() => {
                      setQuery('')
                      submit('')
                    }}
                    className="rounded-[4px] border border-ink/30 px-3 py-1.5 text-sm hover:border-ink"
                  >
                    Clear search
                  </button>
                )}
              </div>
            </div>
          )}

          {data && data.items.length > 0 && (
            <div className={`grid gap-4 sm:grid-cols-2 xl:grid-cols-3 ${loading ? 'opacity-60' : ''}`}>
              {data.items.map((item) => (
                <ProductCard key={item.product.id} item={item} unit={profile.unit} onOpen={setOpenId} />
              ))}
            </div>
          )}

          {data && data.total > data.items.length && (
            <div className="pt-2 text-center">
              <button
                type="button"
                onClick={() => setLimit((l) => l + PAGE)}
                className="rounded-[4px] border-2 border-ink bg-sheet px-5 py-2 font-semibold hover:bg-tape"
              >
                Show more ({data.total - data.items.length} left)
              </button>
            </div>
          )}
        </main>
      </div>

      <footer className="mt-16 border-t border-ink/15 pt-4 text-sm text-ink-faint">
        FitFinder. Products and size charts come from real Indian stores (bigbanana, Janasya, Angrakhaa); prices and stock may have changed since they were collected.
      </footer>

      {openId !== null && (
        <ProductDrawer productId={openId} profile={effectiveProfile} unit={profile.unit} onClose={closeDrawer} />
      )}
    </div>
  )
}
