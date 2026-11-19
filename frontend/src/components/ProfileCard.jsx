import { useId, useState } from 'react'
import { DIMENSIONS, SAMPLES, convertProfile, emptyProfile, filledMeasurements } from '../lib/profile'
import { feetInches } from '../lib/units'

function Segmented({ label, value, options, onChange }) {
  return (
    <fieldset className="min-w-0">
      <legend className="mb-1 text-sm text-ink-soft">{label}</legend>
      <div className="flex rounded-full border border-ink/20 bg-paper/50 p-0.5">
        {options.map((o) => (
          <label
            key={String(o.value)}
            className={`flex-1 cursor-pointer rounded-full px-2 py-1.5 text-center text-sm select-none has-[:focus-visible]:outline-2 has-[:focus-visible]:outline-chalk ${
              value === o.value ? 'bg-ink font-semibold text-sheet' : 'text-ink hover:bg-sheet'
            }`}
          >
            <input
              type="radio"
              className="sr-only"
              name={label}
              checked={value === o.value}
              onChange={() => onChange(o.value)}
            />
            {o.label}
          </label>
        ))}
      </div>
    </fieldset>
  )
}

function MeasurementField({ dim, value, unit, onChange }) {
  const id = useId()
  const [focused, setFocused] = useState(false)
  const n = parseFloat(value)
  const heightHelp = dim.key === 'height' && unit === 'in' && n > 36 ? feetInches(n) : null
  return (
    <div className="min-w-0">
      <label htmlFor={id} className="block text-sm font-medium">
        {dim.label}
      </label>
      <div className="mt-1 flex items-center rounded-xl border border-ink/20 bg-sheet focus-within:border-ink focus-within:outline-2 focus-within:outline-chalk">
        <input
          id={id}
          inputMode="decimal"
          autoComplete="off"
          value={value}
          placeholder="–"
          aria-describedby={`${id}-hint`}
          onFocus={() => setFocused(true)}
          onBlur={() => setFocused(false)}
          onChange={(e) => onChange(e.target.value.replace(/[^\d.,]/g, ''))}
          className="w-full min-w-0 bg-transparent px-2.5 py-1.5 text-lg font-semibold outline-none placeholder:text-ink-faint"
        />
        <span className="pr-2.5 text-sm text-ink-faint">{heightHelp || unit}</span>
      </div>
      <p id={`${id}-hint`} className={`mt-1 text-xs text-ink-soft ${focused ? '' : 'sr-only'}`}>
        {dim.hint}
        {dim.key === 'height' && unit === 'in' ? ' (in inches: 6 ft 2 in is 74)' : ''}
      </p>
    </div>
  )
}

export default function ProfileCard({ profile, onChange, alwaysOpen = false }) {
  const [open, setOpen] = useState(alwaysOpen)
  const filled = filledMeasurements(profile)
  const count = Object.keys(filled).length
  const setMeasurement = (key, v) => onChange({ ...profile, measurements: { ...profile.measurements, [key]: v } })

  return (
    <section aria-labelledby="profile-title" className="rounded-2xl border border-ink/15 bg-sheet">
      <header className="flex items-center justify-between gap-3 border-b border-ink/10 px-4 py-3">
        <div>
          <h2 id="profile-title" className="font-expanded text-lg font-bold">
            Your measurements
          </h2>
          <p className="text-sm text-ink-soft">
            {count ? `${count} of 6 added. Saved on this device.` : 'Add them once. Every result is checked against them.'}
          </p>
        </div>
        {!alwaysOpen && (
        <button
          type="button"
          onClick={() => setOpen((o) => !o)}
          aria-expanded={open}
          aria-controls="profile-body"
          className="shrink-0 rounded-full border border-ink/25 px-3 py-1 text-sm lg:hidden"
        >
          {open ? 'Hide' : count ? 'Edit' : 'Add'}
        </button>
        )}
      </header>

      <div id="profile-body" className={`${open ? 'block' : 'hidden'} space-y-4 px-4 py-4 lg:block`}>
        <div className="grid grid-cols-2 gap-3">
          <Segmented
            label="Units"
            value={profile.unit}
            options={[{ value: 'in', label: 'Inches' }, { value: 'cm', label: 'cm' }]}
            onChange={(unit) => onChange(convertProfile(profile, unit))}
          />
          <Segmented
            label="Shopping for"
            value={profile.gender}
            options={[{ value: 'men', label: 'Men' }, { value: 'women', label: 'Women' }, { value: null, label: 'All' }]}
            onChange={(gender) => onChange({ ...profile, gender })}
          />
        </div>

        <div className="grid grid-cols-2 gap-x-3 gap-y-3">
          {DIMENSIONS.map((dim) => (
            <MeasurementField
              key={dim.key}
              dim={dim}
              unit={profile.unit}
              value={profile.measurements[dim.key]}
              onChange={(v) => setMeasurement(dim.key, v)}
            />
          ))}
        </div>

        <Segmented
          label="How you like clothes to fit"
          value={profile.fit_preference}
          options={[
            { value: 'snug', label: 'Snug' },
            { value: 'regular', label: 'Regular' },
            { value: 'relaxed', label: 'Relaxed' },
          ]}
          onChange={(fit_preference) => onChange({ ...profile, fit_preference })}
        />

        <div className="border-t border-ink/10 pt-3">
          <p className="text-sm text-ink-soft">Or try a sample body</p>
          <div className="mt-2 grid grid-cols-2 gap-2">
            {SAMPLES.map((s) => (
              <button
                key={s.key}
                type="button"
                onClick={() => onChange(convertProfile({ ...emptyProfile(), ...s.profile }, profile.unit))}
                className="rounded-xl border border-ink/20 px-3 py-1.5 text-left hover:border-ink/60 hover:bg-paper/60"
              >
                <span className="block text-sm font-semibold">{s.label}</span>
                <span className="block text-xs text-ink-soft">{s.detail}</span>
              </button>
            ))}
          </div>
          {count > 0 && (
            <button
              type="button"
              onClick={() => onChange({ ...emptyProfile(), unit: profile.unit })}
              className="mt-3 text-sm text-chalk underline underline-offset-2"
            >
              Clear measurements
            </button>
          )}
        </div>
      </div>
    </section>
  )
}
