import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import FilterBar from '../components/FilterBar'
import ProductCard from '../components/ProductCard'
import ProductDrawer from '../components/ProductDrawer'
import ProfileCard from '../components/ProfileCard'
import SearchBar from '../components/SearchBar'
import Wordmark from '../components/Wordmark'
import { api } from '../lib/api'
import { filledMeasurements, hasMeasurements, toApiProfile } from '../lib/profile'
import { go } from '../lib/route'
import { CM_PER_IN, feetInches, round1 } from '../lib/units'

const PAGE = 24

function useDebounced(value, ms) {
  const [v, setV] = useState(value)
  useEffect(() => {
    const t = setTimeout(() => setV(value), ms)
    return () => clearTimeout(t)
  }, [value, ms])
  return v
}

// "40″ chest, 32″ waist, 5′10″": the shopper's own numbers, as the page's headline.
function bodyLine(profile) {
  const m = filledMeasurements(profile)
  const inch = profile.unit === 'in'
  const len = (v) => (inch ? `${v}″` : `${v} cm`)
  const parts = []
  if (m.chest) parts.push(`${len(m.chest)} ${profile.gender === 'women' ? 'bust' : 'chest'}`)
  if (m.waist) parts.push(`${len(m.waist)} waist`)
  if (m.hips) parts.push(`${len(m.hips)} hips`)
  if (m.height) parts.push(inch ? feetInches(m.height) : `${m.height} cm tall`)
  return parts.join(', ')
}

function MeasureSheet({ profile, onChange, onClose }) {
  const closeRef = useRef(null)
  useEffect(() => {
    closeRef.current?.focus()
    const onKey = (e) => e.key === 'Escape' && onClose()
    document.addEventListener('keydown', onKey)
    const prev = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    return () => {
      document.removeEventListener('keydown', onKey)
      document.body.style.overflow = prev
    }
  }, [onClose])
  return (
    <div className="fixed inset-0 z-40 flex justify-end" role="dialog" aria-modal="true" aria-label="Your measurements">
      <button type="button" aria-label="Close" tabIndex={-1} onClick={onClose} className="absolute inset-0 bg-ink/40" />
      <div className="drawer-in relative flex h-full w-full max-w-[26rem] flex-col overflow-y-auto bg-paper">
        <div className="flex items-center justify-between px-5 pt-4">
          <p className="font-bold">Results update as you type.</p>
          <button ref={closeRef} type="button" onClick={onClose} className="rounded-full bg-ink px-4 py-1.5 text-sm font-semibold text-sheet">
            Done
          </button>
        </div>
        <div className="p-4">
          <ProfileCard profile={profile} onChange={onChange} alwaysOpen />
        </div>
      </div>
    </div>
  )
}

export default function Results({ profile, onProfile, intent, onIntent, meta }) {
  const [query, setQuery] = useState('')
  const [submitted, setSubmitted] = useState('')
  const [filters, setFilters] = useState({ category: intent.category, max_price: intent.max_price, sort: 'fit' })
  const [onlyFitting, setOnlyFitting] = useState(true)
  const [limit, setLimit] = useState(PAGE)
  const [result, setResult] = useState({ data: null, error: null, key: null })
  const [openId, setOpenId] = useState(null)
  const [editing, setEditing] = useState(false)

  const apiProfile = useMemo(() => toApiProfile(profile), [profile])
  const profileKey = useDebounced(JSON.stringify(apiProfile), 450)
  const canFit = hasMeasurements(profile)
  const categories = meta?.categories || []

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

  const setFilter = (f) => {
    setFilters(f)
    setLimit(PAGE)
    onIntent({ category: f.category, max_price: f.max_price })
  }
  const submit = (q) => {
    setSubmitted(q)
    // a new query decides category and price itself
    setFilters((f) => ({ category: '', max_price: '', sort: f.sort }))
    setLimit(PAGE)
  }
  const updateProfile = (next) => {
    onProfile(next)
    setLimit(PAGE)
  }
  const closeDrawer = useCallback(() => setOpenId(null), [])
  const closeSheet = useCallback(() => setEditing(false), [])

  const { data, error } = result
  // The drawer checks fit with what the search actually used: saved measurements plus any typed into the query.
  const effectiveProfile = useMemo(() => {
    const cm = data?.applied?.measurements_cm
    if (!cm) return apiProfile
    const f = apiProfile.unit === 'in' ? 1 / CM_PER_IN : 1
    const measurements = Object.fromEntries(Object.entries(cm).map(([k, v]) => [k, round1(v * f)]))
    return { ...apiProfile, fit_preference: data.applied.fit_preference || apiProfile.fit_preference, measurements }
  }, [data, apiProfile])
  const fittingNow = data?.fitting !== null && data?.fitting !== undefined
  const what = categories.find((c) => c.key === filters.category)?.label.toLowerCase() || 'pieces'
  const line = bodyLine(profile)

  return (
    <div>
      <section className="bg-blush">
        <div className="mx-auto max-w-[96rem] px-5 sm:px-8">
          <header className="flex items-center justify-between gap-4 py-5">
            <Wordmark />
            <div className="flex items-center gap-2">
              <button type="button" onClick={() => setEditing(true)} className="rounded-full bg-ink px-4 py-2 text-sm font-semibold text-sheet">
                Edit measurements
              </button>
              <button type="button" onClick={() => go('fit')} className="hidden px-2 text-sm font-semibold underline underline-offset-4 sm:block">
                Start over
              </button>
            </div>
          </header>
          <div className="pt-4 pb-10 sm:pt-8 sm:pb-14">
            {canFit ? (
              <>
                <p className="text-lg font-semibold text-ink-soft">Fitted to</p>
                <h1 className="mt-1 max-w-[24ch] font-expanded text-[clamp(2.1rem,5.4vw,4.6rem)] leading-[1.02] font-extrabold tracking-tight">
                  {line}
                </h1>
              </>
            ) : (
              <>
                <h1 className="max-w-[20ch] font-expanded text-[clamp(2.1rem,5.4vw,4.6rem)] leading-[1.02] font-extrabold tracking-tight">
                  Everything, in every size.
                </h1>
                <button type="button" onClick={() => go('fit')} className="mt-6 rounded-full bg-cobalt px-7 py-3 font-bold text-sheet hover:bg-cobalt-deep">
                  Add my measurements
                </button>
              </>
            )}
            <p className="mt-5 text-lg font-semibold" aria-live="polite">
              {data &&
                (data.checked === 0
                  ? 'Nothing matches yet.'
                  : fittingNow
                    ? `${data.fitting} of ${data.checked} ${what} come in a size that fits you.`
                    : `${data.total} ${what}.`)}
              <span className="ml-2 font-normal text-ink-soft">{loading ? 'Checking sizes…' : ''}</span>
            </p>
          </div>
        </div>
      </section>

      <div className="mx-auto max-w-[96rem] space-y-5 px-5 pt-8 pb-16 sm:px-8">
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

        <nav aria-label="Categories" className="-mx-5 overflow-x-auto px-5 sm:mx-0 sm:px-0">
          <div className="flex w-max gap-2 sm:w-auto sm:flex-wrap">
            {[{ key: '', label: 'Everything' }, ...categories.filter((c) => c.count > 0)].map((c) => (
              <button
                key={c.key}
                type="button"
                aria-pressed={filters.category === c.key}
                onClick={() => setFilter({ ...filters, category: c.key })}
                className={`rounded-full border-2 px-4 py-1.5 font-semibold whitespace-nowrap transition-colors ${
                  filters.category === c.key ? 'border-ink bg-ink text-sheet' : 'border-ink/20 bg-sheet hover:border-ink'
                }`}
              >
                {c.label}
              </button>
            ))}
          </div>
        </nav>

        <FilterBar
          filters={filters}
          onChange={setFilter}
          categories={categories}
          onlyFitting={onlyFitting}
          onOnlyFitting={setOnlyFitting}
          canFit={canFit}
          hideCategory
        />

        {data?.notes?.length > 0 && (
          <ul className="space-y-1 text-sm text-ink-soft">
            {data.notes.map((n) => (
              <li key={n}>{n}</li>
            ))}
          </ul>
        )}

        {error && (
          <div role="alert" className="rounded-2xl bg-no-bg p-5 text-no">
            <p className="font-semibold">{error}</p>
            <p className="mt-1 text-sm">Start the backend, then search again.</p>
          </div>
        )}

        {data && data.items.length === 0 && !error && (
          <div className="rounded-2xl border-2 border-dashed border-ink/25 p-6">
            <p className="text-lg font-bold">Nothing matches all of that.</p>
            <p className="mt-1 text-ink-soft">
              {onlyFitting && canFit && data.checked > 0
                ? `${data.checked} pieces match, but none come in a size that fits you.`
                : 'Try fewer words, another category, or a bigger budget.'}
            </p>
            <div className="mt-4 flex flex-wrap gap-2">
              {onlyFitting && canFit && data.checked > 0 && (
                <button type="button" onClick={() => setOnlyFitting(false)} className="rounded-full border-2 border-ink px-4 py-1.5 font-semibold">
                  Show them anyway
                </button>
              )}
              {(submitted || filters.category || filters.max_price) && (
                <button
                  type="button"
                  onClick={() => {
                    setQuery('')
                    submit('')
                    onIntent({ category: '', max_price: '' })
                  }}
                  className="rounded-full border-2 border-ink px-4 py-1.5 font-semibold"
                >
                  Clear search and filters
                </button>
              )}
            </div>
          </div>
        )}

        {data && data.items.length > 0 && (
          <div className={`grid gap-x-5 gap-y-8 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 ${loading ? 'opacity-60' : ''}`}>
            {data.items.map((item) => (
              <ProductCard key={item.product.id} item={item} unit={profile.unit} onOpen={setOpenId} />
            ))}
          </div>
        )}

        {data && data.total > data.items.length && (
          <div className="pt-4 text-center">
            <button type="button" onClick={() => setLimit((l) => l + PAGE)} className="rounded-full bg-ink px-7 py-3 font-bold text-sheet">
              Show more ({data.total - data.items.length} left)
            </button>
          </div>
        )}
      </div>

      <footer className="border-t border-ink/15">
        <p className="mx-auto max-w-[96rem] px-5 py-6 text-sm text-ink-faint sm:px-8">
          Products and size charts come from the brands’ own stores. Prices and stock may have changed since they were collected.
        </p>
      </footer>

      {openId !== null && <ProductDrawer productId={openId} profile={effectiveProfile} unit={profile.unit} onClose={closeDrawer} />}
      {editing && <MeasureSheet profile={profile} onChange={updateProfile} onClose={closeSheet} />}
    </div>
  )
}
