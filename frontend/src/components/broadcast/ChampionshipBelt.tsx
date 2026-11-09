/** Decorative championship belt mark — original geometric graphic, not a licensed asset. */
export function ChampionshipBelt({ label }: { label?: string | null }) {
  return (
    <div className="bc-belt-wrap" title={label || "Championship"}>
      <svg className="bc-belt" viewBox="0 0 64 40" aria-hidden>
        <defs>
          <linearGradient id="beltGold" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#f3e0a0" />
            <stop offset="45%" stopColor="#d4af37" />
            <stop offset="100%" stopColor="#8a6a12" />
          </linearGradient>
        </defs>
        <rect x="2" y="14" width="14" height="12" rx="2" fill="#1a1a1f" stroke="#d4af37" strokeWidth="1.5" />
        <rect x="48" y="14" width="14" height="12" rx="2" fill="#1a1a1f" stroke="#d4af37" strokeWidth="1.5" />
        <ellipse cx="32" cy="20" rx="16" ry="14" fill="url(#beltGold)" stroke="#fff6c8" strokeWidth="1" />
        <ellipse cx="32" cy="20" rx="8" ry="7" fill="#1a1204" stroke="#f3e0a0" strokeWidth="1" />
        <path d="M28 20 L32 16 L36 20 L32 24 Z" fill="#d4af37" />
      </svg>
    </div>
  );
}
