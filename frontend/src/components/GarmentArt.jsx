import { colorHex } from '../lib/look'

// Flat garment drawings for products without photos (the demo catalog).
const SHAPES = {
  tshirt: {
    body: 'M72 30 L46 38 L20 66 L38 88 L58 74 L58 172 L142 172 L142 74 L162 88 L180 66 L154 38 L128 30 Q100 54 72 30 Z',
    lines: ['M72 30 Q100 54 128 30'],
  },
  shirt: {
    body: 'M74 28 L48 38 L30 124 L50 128 L60 82 L60 174 L140 174 L140 82 L150 128 L170 124 L152 38 L126 28 L100 56 Z',
    lines: ['M74 28 L88 50 L100 56 L112 50 L126 28', 'M100 56 L100 174', 'M30 116 L50 120', 'M150 120 L170 116'],
    dots: [[100, 76], [100, 100], [100, 124], [100, 148]],
  },
  polo: {
    body: 'M72 30 L46 38 L20 66 L38 88 L58 74 L58 172 L142 172 L142 74 L162 88 L180 66 L154 38 L128 30 L100 46 Z',
    lines: ['M72 30 L84 46 L100 46 L116 46 L128 30', 'M100 46 L100 82', 'M58 160 L142 160'],
    dots: [[100, 58], [100, 72]],
  },
  hoodie: {
    body: 'M74 32 L48 42 L30 130 L52 134 L62 86 L60 176 L140 176 L138 86 L148 134 L170 130 L152 42 L126 32 Q100 50 74 32 Z',
    lines: ['M74 32 Q76 4 100 6 Q124 4 126 32', 'M70 132 L130 132 L136 160 L64 160 Z', 'M30 122 L52 126', 'M148 126 L170 122', 'M60 166 L140 166', 'M94 42 L92 72', 'M106 42 L108 72'],
  },
  jacket: {
    body: 'M72 28 L46 40 L28 128 L50 132 L60 84 L58 176 L142 176 L140 84 L150 132 L172 128 L154 40 L128 28 L100 70 Z',
    lines: ['M72 28 L84 60 L100 70 L116 60 L128 28', 'M100 70 L100 176', 'M66 140 L88 140', 'M112 140 L134 140', 'M28 120 L50 124', 'M150 124 L172 120'],
    dots: [[100, 104], [100, 132]],
  },
  kurta: {
    body: 'M76 24 L52 32 L34 100 L52 104 L62 66 L58 188 L142 188 L138 66 L148 104 L166 100 L148 32 L124 24 Q100 36 76 24 Z',
    lines: ['M100 30 L100 78', 'M60 150 L60 188', 'M140 150 L140 188', 'M76 24 Q100 36 124 24'],
    dots: [[100, 46], [100, 60]],
  },
  top: {
    body: 'M80 30 L66 34 L62 74 L60 120 Q56 150 50 164 Q100 178 150 164 Q144 150 140 120 L138 74 L134 34 L120 30 Q100 56 80 30 Z',
    lines: ['M80 30 Q100 56 120 30', 'M60 120 Q100 128 140 120'],
  },
  dress: {
    body: 'M80 22 L68 26 L66 66 Q70 84 76 94 L38 184 Q100 198 162 184 L124 94 Q130 84 134 66 L132 26 L120 22 Q100 46 80 22 Z',
    lines: ['M80 22 Q100 46 120 22', 'M76 94 Q100 102 124 94'],
  },
  jeans: {
    body: 'M58 22 L142 22 L150 184 L110 184 L100 72 L90 184 L50 184 Z',
    lines: ['M58 36 L142 36', 'M100 36 L100 72', 'M62 44 Q74 60 88 44', 'M138 44 Q126 60 112 44', 'M52 168 L88 168', 'M112 168 L148 168'],
  },
  trousers: {
    body: 'M60 22 L140 22 L148 184 L110 184 L100 70 L90 184 L52 184 Z',
    lines: ['M60 34 L140 34', 'M100 34 L100 70', 'M76 34 L72 184', 'M124 34 L128 184'],
  },
  joggers: {
    body: 'M60 22 L140 22 L146 164 L140 186 L110 186 L106 166 L100 72 L94 166 L90 186 L60 186 L54 164 Z',
    lines: ['M60 38 L140 38', 'M56 166 L92 166', 'M108 166 L144 166', 'M68 80 L84 80 L84 108 L66 108'],
  },
  shorts: {
    body: 'M56 44 L144 44 L154 132 L110 138 L100 92 L90 138 L46 132 Z',
    lines: ['M56 58 L144 58', 'M100 58 L100 92', 'M48 120 L90 124', 'M110 124 L152 120'],
  },
}

export default function GarmentArt({ category, color, className = '' }) {
  const shape = SHAPES[category] || SHAPES.tshirt
  const fill = colorHex(color)
  return (
    <svg viewBox="0 0 200 200" className={className} aria-hidden="true">
      <g stroke="var(--color-ink)" strokeWidth="3" strokeLinejoin="round" strokeLinecap="round">
        <path d={shape.body} fill={fill} />
        {shape.lines.map((d) => (
          <path key={d} d={d} fill="none" strokeOpacity="0.55" strokeWidth="2.2" />
        ))}
        {(shape.dots || []).map(([cx, cy]) => (
          <circle key={`${cx}-${cy}`} cx={cx} cy={cy} r="2.6" fill="var(--color-ink)" stroke="none" fillOpacity="0.6" />
        ))}
      </g>
    </svg>
  )
}
