import { useEffect, useMemo, useRef, useState } from 'react'
import Wordmark from '../components/Wordmark'
import { SAMPLES, convertProfile } from '../lib/profile'
import { go } from '../lib/route'
import { CM_PER_IN, round1 } from '../lib/units'

// Sensible body ranges, in inches; anything outside is probably a typo.
const RANGE_IN = { height: [48, 90], chest: [24, 80], waist: [20, 75], hips: [24, 80] }

const MEASURE_HELP = {
  height: 'Stand against a wall without shoes.',
  chest: 'Around the fullest part, under your arms. Keep the tape level and snug, not tight.',
  waist: 'Where your trousers usually sit. Breathe out normally before you read it.',
  hips: 'Around the fullest part of your seat, feet together.',
}

const FITS = [
  { value: 'snug', label: 'Snug', text: 'Close to the body.' },
  { value: 'regular', label: 'Regular', text: 'Room to move, nothing baggy.' },
  { value: 'relaxed', label: 'Relaxed', text: 'Loose and easy.' },
]

const BUDGETS = [
  { value: '', label: 'Any budget' },
  { value: '1000', label: 'Up to ₹1,000' },
  { value: '2000', label: 'Up to ₹2,000' },
  { value: '3000', label: 'Up to ₹3,000' },
  { value: '5000', label: 'Up to ₹5,000' },
]

function Choice({ selected, onClick, children, sub }) {
  return (
    <button
      type="button"
      aria-pressed={selected}
      onClick={onClick}
      className={`rounded-2xl border-2 px-5 py-4 text-left transition-colors ${
        selected ? 'border-cobalt bg-cobalt text-sheet' : 'border-ink/20 bg-sheet hover:border-ink'
      }`}
    >
      <span className="block text-lg font-bold">{children}</span>
      {sub && <span className={`mt-0.5 block text-sm ${selected ? 'text-sheet/85' : 'text-ink-soft'}`}>{sub}</span>}
    </button>
  )
}

function Chip({ selected, onClick, children }) {
  return (
    <button
      type="button"
      aria-pressed={selected}
      onClick={onClick}
      className={`rounded-full border-2 px-4 py-2 font-semibold transition-colors ${
        selected ? 'border-ink bg-ink text-sheet' : 'border-ink/20 bg-sheet hover:border-ink'
      }`}
    >
      {children}
    </button>
  )
}

// The progress bar is a measuring tape that fills in saffron as the shopper goes.
function Tape({ step, total }) {
  const ticks = total * 4
  return (
    <div className="relative h-3 w-full overflow-hidden rounded-sm border border-ink/30 bg-sheet" aria-hidden="true">
      <div className="absolute inset-y-0 left-0 bg-tape transition-[width] duration-300" style={{ width: `${((step + 1) / total) * 100}%` }} />
      <svg className="absolute inset-0 h-full w-full" preserveAspectRatio="none" viewBox={`0 0 ${ticks} 10`}>
        {Array.from({ length: ticks - 1 }, (_, i) => (
          <line key={i} x1={i + 1} x2={i + 1} y1="0" y2={(i + 1) % 4 === 0 ? 6 : 3} stroke="var(--color-ink)" strokeWidth="0.06" />
        ))}
      </svg>
    </div>
  )
}

function MeasureInput({ dimKey, value, unit, onChange, onEnter }) {
  const ref = useRef(null)
  useEffect(() => ref.current?.focus(), [dimKey])
  const unitLabel = unit === 'in' ? 'inches' : 'cm'

  if (dimKey === 'height' && unit === 'in') {
    const total = parseFloat(value)
    const ft = Number.isFinite(total) ? Math.floor(total / 12) : ''
    const inch = Number.isFinite(total) ? round1(total - ft * 12) : ''
    const set = (f, i) => {
      const fv = parseFloat(f)
      const iv = parseFloat(i) || 0
      onChange(Number.isFinite(fv) ? String(round1(fv * 12 + iv)) : '')
    }
    return (
      <div className="flex items-end gap-4">
        {[
          ['feet', ft, (v) => set(v, inch), ref],
          ['inches', inch, (v) => set(ft, v), null],
        ].map(([label, v, on, r]) => (
          <label key={label} className="flex items-baseline gap-2">
            <input
              ref={r}
              type="number"
              inputMode="decimal"
              value={v}
              onChange={(e) => on(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && onEnter()}
              className="w-[2.2em] border-b-4 border-ink bg-transparent font-expanded text-[clamp(3.5rem,9vw,6rem)] leading-none font-black outline-none focus-visible:border-cobalt"
              aria-label={`Height, ${label}`}
            />
            <span className="text-xl font-semibold text-ink-soft">{label === 'feet' ? 'ft' : 'in'}</span>
          </label>
        ))}
      </div>
    )
  }

  return (
    <label className="flex items-baseline gap-3">
      <input
        ref={ref}
        type="number"
        inputMode="decimal"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onKeyDown={(e) => e.key === 'Enter' && onEnter()}
        className="w-[3.2em] border-b-4 border-ink bg-transparent font-expanded text-[clamp(3.5rem,9vw,6rem)] leading-none font-black outline-none focus-visible:border-cobalt"
        aria-label={`${dimKey} in ${unitLabel}`}
      />
      <span className="text-xl font-semibold text-ink-soft">{unitLabel}</span>
    </label>
  )
}

export default function Quiz({ profile, intent, categories, onDone }) {
  const [draft, setDraft] = useState(profile)
  const [want, setWant] = useState(intent)
  const [step, setStep] = useState(0)
  const [problem, setProblem] = useState(null)

  const chestWord = draft.gender === 'women' ? 'bust' : 'chest'
  const STEPS = useMemo(
    () => [
      { key: 'who', title: 'Who are you shopping for?' },
      { key: 'height', title: 'How tall are you?' },
      { key: 'chest', title: `What’s your ${chestWord}?` },
      { key: 'waist', title: 'And your waist?' },
      { key: 'hips', title: 'Your hips?', note: 'Matters most for trousers, jeans and dresses.' },
      { key: 'fit', title: 'How do you like clothes to fit?' },
      { key: 'want', title: 'What are you looking for?' },
    ],
    [chestWord],
  )
  const s = STEPS[step]
  const last = step === STEPS.length - 1
  const isMeasure = ['height', 'chest', 'waist', 'hips'].includes(s.key)
  const value = isMeasure ? draft.measurements[s.key] : null

  const setMeasure = (v) => {
    setProblem(null)
    setDraft((d) => ({ ...d, measurements: { ...d.measurements, [s.key]: v } }))
  }
  const finish = (p = draft, w = want) => onDone(p, w)

  const next = () => {
    if (isMeasure && value !== '' && value != null) {
      const n = parseFloat(value)
      const inches = draft.unit === 'cm' ? n / CM_PER_IN : n
      const [lo, hi] = RANGE_IN[s.key]
      if (!Number.isFinite(n) || inches < lo || inches > hi) {
        const show = (x) => (draft.unit === 'cm' ? `${Math.round(x * CM_PER_IN)}` : `${x}`)
        setProblem(`That looks off. Enter a number between ${show(lo)} and ${show(hi)} ${draft.unit === 'cm' ? 'cm' : 'inches'}, or skip this one.`)
        return
      }
    }
    if (last) finish()
    else setStep(step + 1)
  }
  const skip = () => {
    setProblem(null)
    if (isMeasure) setDraft((d) => ({ ...d, measurements: { ...d.measurements, [s.key]: '' } }))
    if (last) finish()
    else setStep(step + 1)
  }
  const back = () => {
    setProblem(null)
    if (step === 0) go('home')
    else setStep(step - 1)
  }

  return (
    <div className="flex min-h-svh flex-col">
      <header className="mx-auto flex w-full max-w-5xl items-center justify-between gap-4 px-5 pt-5 sm:px-8">
        <Wordmark />
        <div className="flex items-center gap-1 rounded-full border border-ink/25 bg-sheet p-0.5 text-sm" role="group" aria-label="Units">
          {[
            ['in', 'Inches'],
            ['cm', 'cm'],
          ].map(([u, label]) => (
            <button
              key={u}
              type="button"
              aria-pressed={draft.unit === u}
              onClick={() => setDraft((d) => convertProfile(d, u))}
              className={`rounded-full px-3 py-1 font-semibold ${draft.unit === u ? 'bg-ink text-sheet' : 'text-ink-soft hover:text-ink'}`}
            >
              {label}
            </button>
          ))}
        </div>
      </header>

      <div className="mx-auto w-full max-w-5xl px-5 pt-6 sm:px-8">
        <Tape step={step} total={STEPS.length} />
        <p className="mt-2 text-sm text-ink-faint">
          Question {step + 1} of {STEPS.length}
        </p>
      </div>

      <main key={s.key} className="step-in mx-auto flex w-full max-w-5xl flex-1 flex-col px-5 pt-10 pb-10 sm:px-8 sm:pt-16">
        <h1 className="max-w-[18ch] font-expanded text-[clamp(2.25rem,5.5vw,4.5rem)] leading-[1.02] font-extrabold tracking-tight">
          {s.title}
        </h1>
        {s.note && <p className="mt-3 text-lg text-ink-soft">{s.note}</p>}

        <div className="mt-10">
          {s.key === 'who' && (
            <>
              <div className="grid max-w-2xl gap-3 sm:grid-cols-3">
                {[
                  ['men', 'Men'],
                  ['women', 'Women'],
                  [null, 'Anyone'],
                ].map(([g, label]) => (
                  <Choice
                    key={label}
                    selected={draft.gender === g}
                    onClick={() => {
                      setDraft((d) => ({ ...d, gender: g }))
                      setStep(1)
                    }}
                  >
                    {label}
                  </Choice>
                ))}
              </div>
              <div className="mt-12 max-w-2xl">
                <p className="text-ink-soft">Just looking around? Start from a sample body instead.</p>
                <div className="mt-3 flex flex-wrap gap-2">
                  {SAMPLES.map((x) => (
                    <button
                      key={x.key}
                      type="button"
                      onClick={() => finish(convertProfile(x.profile, draft.unit), want)}
                      className="rounded-full border-2 border-ink/20 bg-sheet px-4 py-2 text-left hover:border-ink"
                    >
                      <span className="font-semibold">{x.label}</span>
                      <span className="ml-2 text-sm text-ink-soft">{x.detail}</span>
                    </button>
                  ))}
                </div>
              </div>
            </>
          )}

          {isMeasure && (
            <div className="max-w-2xl">
              <MeasureInput dimKey={s.key} value={value ?? ''} unit={draft.unit} onChange={setMeasure} onEnter={next} />
              <p className="mt-5 text-ink-soft">{MEASURE_HELP[s.key]}</p>
              {problem && (
                <p role="alert" className="mt-3 font-semibold text-no">
                  {problem}
                </p>
              )}
            </div>
          )}

          {s.key === 'fit' && (
            <div className="grid max-w-3xl gap-3 sm:grid-cols-3">
              {FITS.map((f) => (
                <Choice
                  key={f.value}
                  selected={draft.fit_preference === f.value}
                  sub={f.text}
                  onClick={() => {
                    setDraft((d) => ({ ...d, fit_preference: f.value }))
                    setStep(step + 1)
                  }}
                >
                  {f.label}
                </Choice>
              ))}
            </div>
          )}

          {s.key === 'want' && (
            <div className="max-w-3xl space-y-8">
              <div className="flex flex-wrap gap-2">
                <Chip selected={!want.category} onClick={() => setWant((w) => ({ ...w, category: '' }))}>
                  Anything
                </Chip>
                {categories
                  .filter((c) => c.count > 0)
                  .map((c) => (
                    <Chip key={c.key} selected={want.category === c.key} onClick={() => setWant((w) => ({ ...w, category: c.key }))}>
                      {c.label}
                    </Chip>
                  ))}
              </div>
              <div>
                <p className="mb-3 text-lg font-bold">Budget</p>
                <div className="flex flex-wrap gap-2">
                  {BUDGETS.map((b) => (
                    <Chip key={b.value} selected={want.max_price === b.value} onClick={() => setWant((w) => ({ ...w, max_price: b.value }))}>
                      {b.label}
                    </Chip>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>

        <div className="mt-auto flex flex-wrap items-center gap-x-6 gap-y-3 pt-14 sm:mt-16 sm:pt-0">
          {s.key !== 'who' && (
            <button
              type="button"
              onClick={next}
              className="rounded-full bg-cobalt px-8 py-3.5 text-lg font-bold text-sheet hover:bg-cobalt-deep"
            >
              {last ? 'Show my fits' : 'Next'}
            </button>
          )}
          {isMeasure && (
            <button type="button" onClick={skip} className="font-semibold text-ink-soft underline underline-offset-4 hover:text-ink">
              I don’t know, skip
            </button>
          )}
          <button type="button" onClick={back} className="font-semibold text-ink-soft hover:text-ink">
            {step === 0 ? 'Back to home' : 'Back'}
          </button>
        </div>
      </main>
    </div>
  )
}
