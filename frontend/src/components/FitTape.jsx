import { CM_PER_IN, formatCm, formatRange } from '../lib/units'
import { TONE_HEX, statusTone } from '../lib/look'

const W = 320

// A strip of measuring tape: the size's range is the shaded band, the ink pin is your body.
export default function FitTape({ dimension, label, bodyCm, rangeCm, status, note, unit = 'cm', compact = false, estimated = false }) {
  const f = unit === 'in' ? 1 / CM_PER_IN : 1
  const lo = rangeCm[0] * f
  const hi = rangeCm[1] * f
  const body = bodyCm * f

  const pad = unit === 'in' ? 2 : 5
  const minSpan = unit === 'in' ? 10 : 24
  let start = Math.min(lo, body) - pad
  let end = Math.max(hi, body) + pad
  if (end - start < minSpan) {
    const grow = (minSpan - (end - start)) / 2
    start -= grow
    end += grow
  }
  const span = end - start
  const minor = unit === 'in' ? (span > 24 ? 1 : 0.5) : span > 60 ? 2 : 1
  const major = unit === 'in' ? (span > 24 ? 2 : 1) : 5
  const every = unit === 'in' ? (span > 24 ? 4 : 2) : 10
  start = Math.floor(start / minor) * minor
  end = Math.ceil(end / minor) * minor

  const H = compact ? 30 : 40
  const tapeTop = compact ? 4 : 6
  const tapeH = compact ? 22 : 28
  const x = (v) => ((v - start) / (end - start)) * W
  const tone = statusTone(status)
  const color = TONE_HEX[tone]

  const ticks = []
  for (let v = start; v <= end + 1e-9; v = Math.round((v + minor) * 100) / 100) {
    const isMajor = Math.abs(v / major - Math.round(v / major)) < 1e-6
    const isLabel = Math.abs(v / every - Math.round(v / every)) < 1e-6
    ticks.push({ v, isMajor, isLabel })
  }

  const you = formatCm(bodyCm, unit, dimension) + (estimated ? ' (est.)' : '')
  const range = formatRange(rangeCm, unit, dimension)
  const described = `${label}: you are ${you}; this size is cut for ${range}. ${note || ''}`

  return (
    <figure className="m-0">
      <figcaption className={`mb-1 flex items-baseline justify-between gap-3 ${compact ? 'text-xs' : 'text-sm'}`}>
        <span className="font-semibold">{label}</span>
        <span className="text-ink-soft">
          you {you}, size {range}
        </span>
      </figcaption>
      <svg viewBox={`0 0 ${W} ${H}`} className="block h-auto w-full" role="img" aria-label={described}>
        <rect x="0.5" y={tapeTop} width={W - 1} height={tapeH} rx="2" fill="var(--color-tape)" stroke="var(--color-tape-deep)" />
        {/* the size's range */}
        <rect
          x={x(lo)}
          y={tapeTop}
          width={Math.max(2, x(hi) - x(lo))}
          height={tapeH}
          fill={color}
          fillOpacity="0.3"
        />
        <line x1={x(lo)} x2={x(lo)} y1={tapeTop} y2={tapeTop + tapeH} stroke={color} strokeWidth="2.5" />
        <line x1={x(hi)} x2={x(hi)} y1={tapeTop} y2={tapeTop + tapeH} stroke={color} strokeWidth="2.5" />
        {ticks.map(({ v, isMajor, isLabel }) => (
          <g key={v}>
            <line
              x1={x(v)}
              x2={x(v)}
              y1={tapeTop}
              y2={tapeTop + (isMajor ? tapeH * 0.42 : tapeH * 0.22)}
              stroke="var(--color-ink)"
              strokeOpacity={isMajor ? 0.85 : 0.5}
              strokeWidth={isMajor ? 1.1 : 0.8}
            />
            {isLabel && !compact && x(v) > 8 && x(v) < W - 8 && (
              <text x={x(v)} y={tapeTop + tapeH - 4} textAnchor="middle" fontSize="8.5" fill="var(--color-ink)" fillOpacity="0.8">
                {Math.round(v)}
              </text>
            )}
          </g>
        ))}
        {/* you */}
        <line x1={x(body)} x2={x(body)} y1={1} y2={tapeTop + tapeH + 1} stroke="var(--color-ink)" strokeWidth="2.5" />
        <path d={`M ${x(body) - 5} ${H - 0.5} L ${x(body) + 5} ${H - 0.5} L ${x(body)} ${tapeTop + tapeH - 3} Z`} fill="var(--color-ink)" />
      </svg>
      {!compact && note && <p className="mt-1 text-sm" style={{ color }}>{note}</p>}
    </figure>
  )
}
