import Wordmark from '../components/Wordmark'
import { go } from '../lib/route'

// The catalog's real size range. Each label is set a little wider than the one before.
const LADDER = ['XXXS', 'XXS', 'XS', 'S', 'M', 'L', 'XL', '2XL', '3XL', '4XL', '5XL', '6XL', '7XL', '8XL', '9XL', '10XL']

function SizeLadder() {
  return (
    <p
      aria-label="Sizes from XXXS to 10XL"
      className="flex flex-wrap items-baseline gap-x-[0.28em] text-[clamp(3rem,10.5vw,9.5rem)] leading-[0.86] font-black tracking-[-0.01em]"
    >
      {LADDER.map((size, i) => (
        <span
          key={size}
          aria-hidden="true"
          className="rung"
          style={{ fontStretch: `${62 + (63 * i) / (LADDER.length - 1)}%`, animationDelay: `${i * 45}ms` }}
        >
          {size}
        </span>
      ))}
    </p>
  )
}

const STEPS = [
  {
    title: 'Answer a few questions',
    text: 'Height, chest, waist, hips and how you like clothes to fit. Skip anything you don’t know.',
  },
  {
    title: 'We read every size chart',
    text: 'Each brand grades its sizes its own way, so FitFinder checks every size of every piece against its own chart.',
  },
  {
    title: 'See the size that fits',
    text: 'For each piece: the size to buy, and whether it would be tight or loose anywhere.',
  },
]

export default function Home({ meta, hasProfile }) {
  const brands = meta?.brands || []
  const total = meta?.total
  return (
    <div>
      <section className="on-cobalt bg-cobalt text-sheet">
        <div className="mx-auto max-w-[96rem] px-5 sm:px-8">
          <header className="flex items-center justify-between py-5">
            <Wordmark light />
            {hasProfile && (
              <button type="button" onClick={() => go('results')} className="text-sm font-semibold underline underline-offset-4">
                See my fits
              </button>
            )}
          </header>

          <div className="pt-6 pb-14 sm:pt-12 sm:pb-20">
            <SizeLadder />
            <div className="mt-10 grid gap-8 sm:mt-14 lg:grid-cols-[minmax(0,1.15fr)_minmax(0,1fr)] lg:items-end">
              <h1 className="font-expanded text-[clamp(2rem,4.6vw,4rem)] leading-[1.02] font-extrabold tracking-tight">
                Every size, checked against your body.
              </h1>
              <div className="max-w-[46ch]">
                <p className="text-lg leading-relaxed text-sheet/90">
                  Tell us your measurements once. FitFinder reads each brand’s own size chart and shows you the size that
                  fits{total ? `, across ${total.toLocaleString('en-IN')} pieces from ${brands.length} Indian labels` : ''}.
                </p>
                <div className="mt-6 flex flex-wrap items-center gap-x-6 gap-y-3">
                  <button
                    type="button"
                    onClick={() => go('fit')}
                    className="rounded-full bg-blush px-7 py-3.5 text-lg font-bold text-ink transition-transform hover:-translate-y-0.5"
                  >
                    {hasProfile ? 'Update my measurements' : 'Find my fit'}
                  </button>
                  <button type="button" onClick={() => go('results')} className="font-semibold underline underline-offset-4">
                    {hasProfile ? 'See my fits' : 'Browse everything'}
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-[96rem] px-5 py-16 sm:px-8 sm:py-24" aria-labelledby="how">
        <h2 id="how" className="font-expanded text-2xl font-extrabold tracking-tight sm:text-3xl">
          How it works
        </h2>
        <ol className="mt-8 grid gap-10 sm:grid-cols-3 sm:gap-8">
          {STEPS.map((s, i) => (
            <li key={s.title} className="border-t-2 border-ink pt-4">
              <span className="font-condensed text-6xl leading-none font-black text-cobalt">{i + 1}</span>
              <h3 className="mt-3 text-xl font-bold">{s.title}</h3>
              <p className="mt-2 max-w-[38ch] text-ink-soft">{s.text}</p>
            </li>
          ))}
        </ol>
      </section>

      <section className="bg-blush">
        <div className="mx-auto grid max-w-[96rem] gap-6 px-5 py-16 sm:px-8 sm:py-20 lg:grid-cols-[minmax(0,1.3fr)_minmax(0,1fr)] lg:items-end">
          <p className="font-expanded text-[clamp(1.75rem,3.8vw,3.25rem)] leading-[1.08] font-extrabold tracking-tight">
            Janasya cuts a medium for a 33–35 inch waist. Angrakhaa cuts one for about 30.
          </p>
          <p className="max-w-[44ch] text-lg text-ink-soft">
            The same label can be two sizes apart from one brand to the next. That’s why FitFinder ignores the label and
            checks your measurements against each chart.
          </p>
        </div>
      </section>

      {brands.length > 0 && (
        <section className="mx-auto max-w-[96rem] px-5 py-16 sm:px-8 sm:py-24" aria-labelledby="labels">
          <h2 id="labels" className="font-expanded text-2xl font-extrabold tracking-tight sm:text-3xl">
            The labels
          </h2>
          <ul className="mt-6 flex flex-wrap gap-x-8 gap-y-2">
            {brands.map((b) => (
              <li key={b.name} className="flex items-baseline gap-2">
                <span className="font-semi-condensed text-[clamp(1.6rem,3.2vw,2.75rem)] font-black tracking-tight">{b.name}</span>
                <span className="text-sm text-ink-faint">{b.count}</span>
              </li>
            ))}
          </ul>
          <button
            type="button"
            onClick={() => go('fit')}
            className="mt-12 rounded-full bg-cobalt px-7 py-3.5 text-lg font-bold text-sheet hover:bg-cobalt-deep"
          >
            {hasProfile ? 'Update my measurements' : 'Find my fit'}
          </button>
        </section>
      )}

      <footer className="border-t border-ink/15">
        <p className="mx-auto max-w-[96rem] px-5 py-6 text-sm text-ink-faint sm:px-8">
          Products and size charts come from the brands’ own stores. Prices and stock may have changed since they were collected.
        </p>
      </footer>
    </div>
  )
}
