export const CM_PER_IN = 2.54

export function fromCm(cm, unit) {
  return unit === 'in' ? cm / CM_PER_IN : cm
}

export function round1(n) {
  return Math.round(n * 10) / 10
}

export function feetInches(totalInches) {
  const ft = Math.floor(totalInches / 12)
  const inch = Math.round(totalInches - ft * 12)
  return inch === 12 ? `${ft + 1}′0″` : `${ft}′${inch}″`
}

// "132 cm" / "52 in"; height in inches is shown as feet and inches.
export function formatCm(cm, unit, dimension) {
  if (unit === 'in') {
    const inches = cm / CM_PER_IN
    if (dimension === 'height') return feetInches(inches)
    return `${round1(inches)} in`
  }
  return `${Math.round(cm)} cm`
}

export function formatRange([lo, hi], unit, dimension) {
  if (unit === 'in' && dimension === 'height') return `${feetInches(lo / CM_PER_IN)}–${feetInches(hi / CM_PER_IN)}`
  if (unit === 'in') return `${round1(lo / CM_PER_IN)}–${round1(hi / CM_PER_IN)} in`
  return `${Math.round(lo)}–${Math.round(hi)} cm`
}
