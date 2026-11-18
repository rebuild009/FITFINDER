import { CM_PER_IN, round1 } from './units'

const KEY = 'fitfinder.profile.v1'

export const DIMENSIONS = [
  { key: 'chest', label: 'Chest / bust', hint: 'Around the fullest part, under the arms' },
  { key: 'waist', label: 'Waist', hint: 'Where your trousers usually sit' },
  { key: 'hips', label: 'Hips', hint: 'Around the fullest part of your seat' },
  { key: 'shoulder', label: 'Shoulder width', hint: 'Across your back, shoulder point to shoulder point' },
  { key: 'inseam', label: 'Inseam', hint: 'Inside of the leg, crotch to ankle' },
  { key: 'height', label: 'Height', hint: 'Without shoes' },
]

const EMPTY_MEASUREMENTS = Object.fromEntries(DIMENSIONS.map((d) => [d.key, '']))

export const emptyProfile = () => ({
  unit: 'in',
  gender: null,
  fit_preference: 'regular',
  measurements: { ...EMPTY_MEASUREMENTS },
})

// Sample bodies for trying the app. Values in inches.
export const SAMPLES = [
  {
    key: 'big-tall',
    label: 'Big and tall',
    detail: '52″ chest, 6′2″',
    profile: { unit: 'in', gender: 'men', fit_preference: 'regular', measurements: { chest: 52, waist: 46, hips: 49, shoulder: 20.5, inseam: 32, height: 74 } },
  },
  {
    key: 'very-tall',
    label: 'Very tall',
    detail: '6′6″, slim',
    profile: { unit: 'in', gender: 'men', fit_preference: 'regular', measurements: { chest: 39.5, waist: 33, hips: 39, shoulder: 18.5, inseam: '', height: 78 } },
  },
  {
    key: 'petite',
    label: 'Petite',
    detail: '4′11″',
    profile: { unit: 'in', gender: 'women', fit_preference: 'regular', measurements: { chest: 32.5, waist: 26, hips: 35.5, shoulder: '', inseam: 27, height: 59 } },
  },
  {
    key: 'plus',
    label: 'Plus size',
    detail: '50″ bust',
    profile: { unit: 'in', gender: 'women', fit_preference: 'relaxed', measurements: { chest: 50, waist: 44, hips: 53.5, shoulder: '', inseam: 29, height: 64 } },
  },
]

export function loadProfile() {
  try {
    const raw = localStorage.getItem(KEY)
    if (!raw) return emptyProfile()
    const saved = JSON.parse(raw)
    return { ...emptyProfile(), ...saved, measurements: { ...EMPTY_MEASUREMENTS, ...saved.measurements } }
  } catch {
    return emptyProfile()
  }
}

export function saveProfile(profile) {
  try {
    localStorage.setItem(KEY, JSON.stringify(profile))
  } catch {
    /* storage unavailable: the profile still works for this visit */
  }
}

function num(v) {
  const n = typeof v === 'number' ? v : parseFloat(String(v).replace(',', '.'))
  return Number.isFinite(n) && n > 0 ? n : null
}

export function filledMeasurements(profile) {
  return Object.fromEntries(
    Object.entries(profile.measurements)
      .map(([k, v]) => [k, num(v)])
      .filter(([, v]) => v !== null),
  )
}

export function hasMeasurements(profile) {
  return Object.keys(filledMeasurements(profile)).length > 0
}

// Shape the API expects. Sent even when empty so fit notes come back in the shopper's unit.
export function toApiProfile(profile) {
  const measurements = filledMeasurements(profile)
  return { unit: profile.unit, gender: profile.gender, fit_preference: profile.fit_preference, measurements }
}

export function convertProfile(profile, unit) {
  if (profile.unit === unit) return profile
  const factor = unit === 'cm' ? CM_PER_IN : 1 / CM_PER_IN
  const measurements = Object.fromEntries(
    Object.entries(profile.measurements).map(([k, v]) => {
      const n = num(v)
      return [k, n === null ? '' : round1(n * factor)]
    }),
  )
  return { ...profile, unit, measurements }
}
