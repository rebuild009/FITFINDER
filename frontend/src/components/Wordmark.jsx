import { go } from '../lib/route'

// The name, with a short tape-measure mark. `light` is for use on the cobalt block.
export default function Wordmark({ light = false }) {
  return (
    <a
      href="#"
      onClick={(e) => {
        e.preventDefault()
        go('home')
      }}
      className={`inline-flex items-center gap-2 ${light ? 'text-sheet' : 'text-ink'}`}
      aria-label="FitFinder home"
    >
      <svg viewBox="0 0 34 14" className="h-3.5 w-8.5" aria-hidden="true">
        <rect x="1" y="1" width="32" height="12" rx="1.5" fill="var(--color-tape)" stroke="currentColor" strokeWidth="1.6" />
        <path d="M6 1v5M10.5 1v3M15 1v5M19.5 1v3M24 1v5M28.5 1v3" stroke="currentColor" strokeWidth="1.6" />
      </svg>
      <span className="font-expanded text-lg font-black tracking-tight">FitFinder</span>
    </a>
  )
}
