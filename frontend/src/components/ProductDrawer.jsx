import { useEffect, useRef, useState } from 'react'
import FitTape from './FitTape'
import { ProductImage, SizeTag } from './ProductCard'
import { api } from '../lib/api'
import { CHART_SOURCE, TONE_CLASSES, TONE_HEX, VERDICT, colorHex, formatPrice } from '../lib/look'
import { DIMENSIONS } from '../lib/profile'
import { formatRange } from '../lib/units'

function SizeRows({ sizes, selected, onSelect, best }) {
  return (
    <ul className="divide-y divide-ink/10 rounded-md border border-ink/15" aria-label="Every size">
      {sizes.map((row) => {
        const v = VERDICT[row.verdict] || VERDICT.needs_measurements
        const isSel = row.size === selected
        return (
          <li key={row.size}>
            <button
              type="button"
              onClick={() => onSelect(row.size)}
              aria-pressed={isSel}
              className={`grid w-full grid-cols-[4.5rem_1fr_auto] items-center gap-3 px-3 py-2 text-left ${
                isSel ? 'bg-tape/35' : 'hover:bg-paper/60'
              }`}
            >
              <span className="font-condensed text-xl leading-none font-bold">{row.size}</span>
              <span className="flex items-center gap-2">
                {row.score !== null ? (
                  <>
                    <span className="h-1.5 flex-1 overflow-hidden rounded-full bg-paper">
                      <span
                        className="block h-full rounded-full"
                        style={{ width: `${row.score}%`, background: TONE_HEX[v.tone] }}
                      />
                    </span>
                    <span className="w-6 text-right text-sm">{row.score}</span>
                  </>
                ) : (
                  <span className="text-sm text-ink-faint">Not checked</span>
                )}
              </span>
              <span className="text-right text-xs text-ink-soft">
                {!row.in_stock ? 'Sold out' : row.size === best ? 'Your size' : ''}
              </span>
            </button>
          </li>
        )
      })}
    </ul>
  )
}

function ChartTable({ sizes, unit }) {
  const dims = DIMENSIONS.filter((d) => sizes.some((s) => s.measurements[d.key]))
  return (
    <div className="overflow-x-auto rounded-md border border-ink/15">
      <table className="w-full text-sm">
        <caption className="sr-only">Size chart</caption>
        <thead className="bg-paper/60 text-left">
          <tr>
            <th scope="col" className="px-3 py-2 font-semibold">Size</th>
            {dims.map((d) => (
              <th key={d.key} scope="col" className="px-3 py-2 font-semibold whitespace-nowrap">{d.label}</th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-ink/10">
          {sizes.map((s) => (
            <tr key={s.size}>
              <th scope="row" className="px-3 py-1.5 font-condensed text-base font-bold">{s.size}</th>
              {dims.map((d) => (
                <td key={d.key} className="px-3 py-1.5 whitespace-nowrap">
                  {s.measurements[d.key] ? formatRange(s.measurements[d.key], unit, d.key) : '–'}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export default function ProductDrawer({ productId, profile, unit, onClose }) {
  const [detail, setDetail] = useState(null)
  const [error, setError] = useState(null)
  const [selected, setSelected] = useState(null)
  const closeRef = useRef(null)
  const profileKey = JSON.stringify(profile)

  useEffect(() => {
    const ctrl = new AbortController()
    api
      .product(productId, profile, ctrl.signal)
      .then((d) => {
        setDetail(d)
        setError(null)
        setSelected(d.fit?.best_size || null)
      })
      .catch((e) => e.name !== 'AbortError' && setError(e.message))
    return () => ctrl.abort()
    // profileKey stands in for profile so edits refetch but re-renders don't
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [productId, profileKey])

  useEffect(() => {
    const opener = document.activeElement
    closeRef.current?.focus()
    const onKey = (e) => e.key === 'Escape' && onClose()
    document.addEventListener('keydown', onKey)
    const prev = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    return () => {
      document.removeEventListener('keydown', onKey)
      document.body.style.overflow = prev
      if (opener instanceof HTMLElement) opener.focus()
    }
  }, [onClose])

  const p = detail?.product
  const fit = detail?.fit
  const row = detail?.sizes.find((s) => s.size === selected)
  const verdict = fit ? VERDICT[fit.verdict] || VERDICT.needs_measurements : null

  return (
    <div className="fixed inset-0 z-40 flex justify-end" role="dialog" aria-modal="true" aria-labelledby="drawer-title">
      <button type="button" aria-label="Close" tabIndex={-1} onClick={onClose} className="absolute inset-0 bg-ink/40" />
      <div className="drawer-in relative flex h-full w-full max-w-[36rem] flex-col overflow-y-auto bg-sheet shadow-2xl">
        <div className="sticky top-0 z-10 flex items-center justify-between border-b border-ink/10 bg-sheet px-5 py-3">
          <p className="text-sm text-ink-soft">{p ? p.brand : 'Loading'}</p>
          <button ref={closeRef} type="button" onClick={onClose} className="rounded-[4px] border border-ink/25 px-3 py-1 text-sm hover:border-ink">
            Close
          </button>
        </div>

        {error && <p className="m-5 rounded-md bg-no-bg p-3 text-no">{error}</p>}

        {p && (
          <div className="space-y-6 px-5 pt-4 pb-10">
            <div className="grid grid-cols-[8rem_1fr] gap-4 sm:grid-cols-[11rem_1fr]">
              <div className="aspect-square overflow-hidden rounded-md bg-paper/70">
                <ProductImage product={p} />
              </div>
              <div className="min-w-0">
                <h2 id="drawer-title" className="text-xl leading-tight font-semibold">{p.title}</h2>
                <p className="mt-1 text-lg">{formatPrice(p.price, p.currency)}</p>
                {p.colors.length > 0 && (
                  <p className="mt-2 flex flex-wrap items-center gap-1.5 text-sm text-ink-soft">
                    {p.colors.map((c) => (
                      <span key={c} className="inline-flex items-center gap-1">
                        <span className="h-3 w-3 rounded-full border border-ink/30" style={{ background: colorHex(c) }} />
                        {c}
                      </span>
                    ))}
                  </p>
                )}
                {p.materials.length > 0 && <p className="mt-1 text-sm text-ink-soft">{p.materials.join(', ')}</p>}
                {p.product_url ? (
                  <a
                    href={p.product_url}
                    target="_blank"
                    rel="noreferrer"
                    className="mt-3 inline-block rounded-[4px] border-2 border-ink bg-tape px-3 py-1.5 text-sm font-semibold hover:bg-tape-deep"
                  >
                    View at {p.store}
                  </a>
                ) : (
                  <p className="mt-3 text-xs text-ink-faint">Demo catalog item, not for sale.</p>
                )}
              </div>
            </div>

            {p.description && <p className="max-w-prose text-sm text-ink-soft">{p.description}</p>}

            {fit && fit.score !== null ? (
              <section aria-labelledby="fit-title" className="space-y-4">
                <div className="flex items-center gap-4">
                  <SizeTag size={fit.best_size} large />
                  <div>
                    <h3 id="fit-title" className="text-sm text-ink-soft">Your size</h3>
                    <p className={`mt-0.5 inline-block rounded-sm px-1.5 font-semibold ${TONE_CLASSES[verdict.tone]}`}>
                      {verdict.label}, {fit.score}/100
                    </p>
                  </div>
                </div>

                {row && (
                  <div className="space-y-6 rounded-md border border-ink/15 p-4">
                    <p className="text-sm font-semibold">
                      {row.size === fit.best_size ? `How ${row.size} fits you` : `How ${row.size} would fit you`}
                    </p>
                    {row.dimensions.map((d) => (
                      <FitTape
                        key={d.dimension}
                        dimension={d.dimension}
                        label={d.label}
                        bodyCm={d.body_cm}
                        rangeCm={d.range_cm}
                        status={d.status}
                        note={d.note}
                        estimated={d.estimated}
                        unit={unit}
                      />
                    ))}
                  </div>
                )}

                {fit.missing.length > 0 && (
                  <p className="text-sm text-ink-soft">
                    Add your {fit.missing.map((m) => DIMENSIONS.find((d) => d.key === m)?.label.toLowerCase()).join(' and ')} for a
                    sharper match.
                  </p>
                )}

                <div>
                  <h3 className="mb-2 text-sm font-semibold">Every size, checked against you</h3>
                  <SizeRows sizes={detail.sizes} selected={selected} onSelect={setSelected} best={fit.best_size} />
                </div>
              </section>
            ) : (
              <section className="space-y-3">
                <p className="rounded-md bg-paper/70 p-3 text-sm">
                  {fit
                    ? fit.summary
                    : 'Add your measurements to see which size fits you and where it would be tight or loose.'}
                </p>
                <h3 className="text-sm font-semibold">Size chart</h3>
                <ChartTable sizes={detail.sizes} unit={unit} />
              </section>
            )}

            <p className="text-xs text-ink-faint">{CHART_SOURCE[detail.size_chart_source]}</p>
          </div>
        )}
      </div>
    </div>
  )
}
