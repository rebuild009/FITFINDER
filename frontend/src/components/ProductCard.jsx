import { useState } from 'react'
import FitTape from './FitTape'
import GarmentArt from './GarmentArt'
import { TONE_CLASSES, VERDICT, formatPrice } from '../lib/look'
import { DIMENSIONS } from '../lib/profile'

// Show the dimension that decides the fit: the worst one if anything is off, else the main one.
function decisive(dimensions) {
  if (!dimensions?.length) return null
  const worst = dimensions.reduce((a, b) => (b.score < a.score ? b : a))
  return worst.status === 'good' ? dimensions[0] : worst
}

export function ProductImage({ product, className = '' }) {
  const [broken, setBroken] = useState(false)
  if (product.image_url && !broken) {
    return (
      <img
        src={product.image_url}
        alt=""
        loading="lazy"
        onError={() => setBroken(true)}
        className={`h-full w-full object-cover ${className}`}
      />
    )
  }
  return <GarmentArt category={product.category} color={product.colors[0]} className={`h-full w-full p-6 ${className}`} />
}

export function SizeTag({ size, large = false }) {
  return (
    <span
      className={`inline-flex items-center justify-center rounded-[3px] border-2 border-ink bg-sheet font-condensed font-bold leading-none ${
        large ? 'min-w-16 px-3 py-2 text-3xl' : 'min-w-11 px-2 py-1.5 text-xl'
      }`}
    >
      {size}
    </span>
  )
}

export default function ProductCard({ item, unit, onOpen }) {
  const { product, fit } = item
  const verdict = fit ? VERDICT[fit.verdict] || VERDICT.needs_measurements : null
  const dim = fit ? decisive(fit.dimensions) : null
  const missingLabel = fit?.missing?.length
    ? DIMENSIONS.find((d) => d.key === fit.missing[0])?.label.toLowerCase()
    : null

  return (
    <article className="relative flex flex-col overflow-hidden rounded-md border border-ink/15 bg-sheet transition-colors hover:border-ink/45 has-[button:focus-visible]:ring-2 has-[button:focus-visible]:ring-chalk">
      <div className="aspect-[4/3] bg-paper/60">
        <ProductImage product={product} />
      </div>
      <div className="flex flex-1 flex-col gap-3 p-4">
        <div>
          <p className="text-sm text-ink-soft">{product.brand}</p>
          <h3 className="text-base leading-snug font-semibold">
            <button
              type="button"
              onClick={() => onOpen(product.id)}
              className="text-left after:absolute after:inset-0 after:content-[''] focus-visible:outline-none"
            >
              {product.title}
            </button>
          </h3>
          <p className="mt-1">{formatPrice(product.price, product.currency)}</p>
        </div>

        {fit && fit.score !== null && (
          <div className="mt-auto flex flex-col gap-2 border-t border-ink/10 pt-3">
            <div className="flex items-center gap-3">
              <SizeTag size={fit.best_size} />
              <div className="min-w-0">
                <p className={`inline-block rounded-sm px-1.5 text-sm font-semibold ${TONE_CLASSES[verdict.tone]}`}>
                  {verdict.label}
                </p>
                <p className="text-xs text-ink-faint">Fit score {fit.score}/100</p>
              </div>
            </div>
            {dim && (
              <FitTape
                compact
                dimension={dim.dimension}
                label={dim.label}
                bodyCm={dim.body_cm}
                rangeCm={dim.range_cm}
                status={dim.status}
                note={dim.note}
                unit={unit}
              />
            )}
            <p className="text-sm text-ink-soft">{fit.summary}</p>
          </div>
        )}
        {fit && fit.score === null && (
          <p className="mt-auto border-t border-ink/10 pt-3 text-sm text-ink-soft">
            {missingLabel ? `Add your ${missingLabel} to check the fit.` : 'No size chart to check against.'}
          </p>
        )}
      </div>
    </article>
  )
}
