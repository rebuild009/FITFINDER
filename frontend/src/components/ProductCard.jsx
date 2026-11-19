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
      className={`inline-flex items-center justify-center rounded-lg bg-ink font-condensed font-black leading-none text-sheet ${
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
    <article className="group relative flex flex-col has-[button:focus-visible]:outline-3 has-[button:focus-visible]:outline-offset-4 has-[button:focus-visible]:outline-chalk">
      <div className="relative aspect-[4/5] overflow-hidden rounded-2xl bg-sheet">
        <ProductImage product={product} className="transition-transform duration-300 group-hover:scale-[1.03]" />
        {fit && fit.score !== null && (
          <div className="absolute top-3 left-3 flex items-center gap-2">
            <SizeTag size={fit.best_size} />
            <span className={`rounded-full px-2.5 py-1 text-sm font-bold ${TONE_CLASSES[verdict.tone]}`}>{verdict.label}</span>
          </div>
        )}
      </div>
      <div className="flex flex-1 flex-col gap-2 pt-3">
        <div className="flex items-baseline justify-between gap-3">
          <p className="text-sm font-semibold text-ink-soft">{product.brand}</p>
          <p className="font-bold">{formatPrice(product.price, product.currency)}</p>
        </div>
        <h3 className="leading-snug font-semibold">
          <button
            type="button"
            onClick={() => onOpen(product.id)}
            className="text-left after:absolute after:inset-0 after:content-[''] focus-visible:outline-none"
          >
            {product.title}
          </button>
        </h3>

        {fit && fit.score !== null && dim && (
          <div className="mt-1">
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
            <p className="mt-1 text-sm text-ink-soft">{fit.summary}</p>
          </div>
        )}
        {fit && fit.score === null && (
          <p className="text-sm text-ink-soft">
            {missingLabel ? `Add your ${missingLabel} to check the fit.` : 'No size chart to check against.'}
          </p>
        )}
      </div>
    </article>
  )
}

