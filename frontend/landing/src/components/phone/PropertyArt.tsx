// Flat property illustrations shown on the mock listing cards.

export function BuildingArt({ className }: { className?: string }) {
  const windows = [0, 1, 2].flatMap((row) => [0, 1, 2].map((col) => ({ row, col })));

  return (
    <svg viewBox="0 0 300 120" className={className} aria-hidden preserveAspectRatio="xMidYMax slice">
      <rect width="300" height="120" fill="#dcefdc" />
      <rect x="0" y="108" width="300" height="12" fill="#7cc58a" />
      {/* main block */}
      <rect x="95" y="22" width="110" height="86" fill="#14672a" />
      <rect x="95" y="22" width="110" height="8" fill="#0f5622" />
      {windows.map(({ row, col }) => (
        <rect key={`${row}-${col}`} x={108 + col * 32} y={38 + row * 20} width="20" height="11" rx="1" fill="#bfe6c4" />
      ))}
      <rect x="140" y="96" width="20" height="12" fill="#0b4419" />
      {/* side block */}
      <rect x="205" y="50" width="52" height="58" fill="#2f8a43" />
      {[0, 1].flatMap((row) => [0, 1].map((col) => (
        <rect key={`s-${row}-${col}`} x={214 + col * 20} y={60 + row * 20} width="12" height="10" rx="1" fill="#d6f0d9" />
      )))}
      {/* tree */}
      <rect x="62" y="88" width="4" height="20" fill="#0b4419" />
      <circle cx="64" cy="82" r="13" fill="#04a417" />
    </svg>
  );
}

export function HouseArt({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 300 120" className={className} aria-hidden preserveAspectRatio="xMidYMax slice">
      <rect width="300" height="120" fill="#e6f3e6" />
      <rect x="0" y="108" width="300" height="12" fill="#7cc58a" />
      <circle cx="58" cy="36" r="13" fill="#ffffff" opacity="0.9" />
      {/* house */}
      <rect x="95" y="62" width="110" height="46" fill="#ffffff" />
      <path d="M82 64 150 22l68 42z" fill="#14672a" />
      <rect x="140" y="80" width="18" height="28" fill="#14672a" />
      <rect x="110" y="74" width="20" height="14" fill="#9fd8a8" />
      <rect x="170" y="74" width="20" height="14" fill="#9fd8a8" />
      {/* tree */}
      <rect x="244" y="74" width="4" height="34" fill="#5b3b1d" />
      <circle cx="246" cy="66" r="12" fill="#04a417" />
    </svg>
  );
}
