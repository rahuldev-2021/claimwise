/** Decorative card art matching the dealer dashboard mockup. */

export function SubmitClaimIllustration({ className = "" }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 200 160"
      className={className}
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden
    >
      <rect x="36" y="28" width="108" height="132" rx="10" fill="rgb(30 41 59 / 0.6)" stroke="rgb(59 130 246 / 0.35)" />
      <rect x="52" y="48" width="76" height="6" rx="3" fill="rgb(148 163 184 / 0.35)" />
      <rect x="52" y="62" width="56" height="4" rx="2" fill="rgb(148 163 184 / 0.25)" />
      <rect x="52" y="72" width="64" height="4" rx="2" fill="rgb(148 163 184 / 0.25)" />
      <circle cx="148" cy="118" r="22" fill="rgb(16 185 129 / 0.2)" stroke="rgb(16 185 129 / 0.6)" strokeWidth="2" />
      <path
        d="M140 118l6 6 14-16"
        stroke="rgb(52 211 153)"
        strokeWidth="3"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <ellipse cx="94" cy="102" rx="28" ry="14" fill="rgb(59 130 246 / 0.15)" />
      <path
        d="M78 102h32l4 8H74l4-8z"
        fill="rgb(59 130 246 / 0.5)"
        stroke="rgb(96 165 250 / 0.6)"
        strokeWidth="1"
      />
      <circle cx="82" cy="110" r="4" fill="rgb(30 41 59)" stroke="rgb(148 163 184 / 0.5)" />
      <circle cx="106" cy="110" r="4" fill="rgb(30 41 59)" stroke="rgb(148 163 184 / 0.5)" />
    </svg>
  );
}

export function TrackClaimsIllustration({ className = "" }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 200 160"
      className={className}
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden
    >
      <rect x="24" y="36" width="152" height="100" rx="8" fill="rgb(30 41 59 / 0.5)" stroke="rgb(59 130 246 / 0.3)" />
      <rect x="24" y="36" width="152" height="14" rx="8" fill="rgb(51 65 85 / 0.8)" />
      <circle cx="38" cy="43" r="3" fill="rgb(248 113 113 / 0.8)" />
      <circle cx="50" cy="43" r="3" fill="rgb(250 204 21 / 0.8)" />
      <circle cx="62" cy="43" r="3" fill="rgb(74 222 128 / 0.8)" />
      <rect x="44" y="64" width="88" height="52" rx="6" fill="rgb(15 23 42 / 0.7)" stroke="rgb(71 85 105 / 0.5)" />
      <rect x="56" y="76" width="48" height="4" rx="2" fill="rgb(148 163 184 / 0.35)" />
      <rect x="56" y="86" width="36" height="3" rx="1.5" fill="rgb(148 163 184 / 0.25)" />
      <rect x="56" y="94" width="42" height="3" rx="1.5" fill="rgb(148 163 184 / 0.25)" />
      <circle cx="148" cy="118" r="20" fill="rgb(16 185 129 / 0.2)" stroke="rgb(16 185 129 / 0.55)" strokeWidth="2" />
      <path
        d="M141 118l5 5 12-14"
        stroke="rgb(52 211 153)"
        strokeWidth="2.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}
