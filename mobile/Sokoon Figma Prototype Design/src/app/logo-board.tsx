import React from "react";

const TEAL  = "#0F766E";
const TEAL2 = "#0D9488";
const NAVY  = "#0B1628";
const NAVY2 = "#0E2040";
const GOLD  = "#D4A84B";
const CREAM = "#F8F4EF";
const WHITE = "#FFFFFF";
const SLATE = "#64748B";

const TJ   = { fontFamily: "'Tajawal', sans-serif" } as React.CSSProperties;
const MONO = { fontFamily: "'DM Mono', monospace" } as React.CSSProperties;

// ─── Shared primitives ────────────────────────────────────────────────
function IconHouse({ c = TEAL, d = WHITE, s = 42 }: { c?: string; d?: string; s?: number }) {
  return (
    <svg width={s} height={s * 0.9} viewBox="0 0 40 36">
      <polygon points="20,2 39,18 1,18" fill={c} />
      <rect x="5" y="17" width="30" height="18" fill={c} />
      <rect x="14" y="23" width="12" height="11" rx="1.5" fill={d} />
    </svg>
  );
}
function IconArch({ c = TEAL, s = 44 }: { c?: string; s?: number }) {
  return (
    <svg width={s} height={s} viewBox="0 0 40 40">
      <path d="M5,38 L5,20 Q5,4 20,4 Q35,4 35,20 L35,38" fill="none" stroke={c} strokeWidth="3.5" strokeLinecap="round" />
      <line x1="1" y1="38" x2="39" y2="38" stroke={c} strokeWidth="3.5" strokeLinecap="round" />
    </svg>
  );
}
function IconPin({ c = TEAL, s = 40 }: { c?: string; s?: number }) {
  return (
    <svg width={s * 0.65} height={s} viewBox="0 0 26 40">
      <path d="M13,1C5.8,1 1,6.5 1,13C1,21 13,39 13,39C13,39 25,21 25,13C25,6.5 20.2,1 13,1Z" fill={c} />
      <circle cx="13" cy="13" r="4.5" fill="white" />
    </svg>
  );
}
function IconKey({ c = TEAL, s = 34 }: { c?: string; s?: number }) {
  return (
    <svg width={s * 1.65} height={s} viewBox="0 0 53 32">
      <circle cx="12" cy="14" r="10" fill="none" stroke={c} strokeWidth="3" />
      <circle cx="12" cy="14" r="3.5" fill={c} />
      <line x1="21" y1="16" x2="51" y2="16" stroke={c} strokeWidth="3" strokeLinecap="round" />
      <line x1="42" y1="16" x2="42" y2="23" stroke={c} strokeWidth="3" strokeLinecap="round" />
      <line x1="49" y1="16" x2="49" y2="21" stroke={c} strokeWidth="3" strokeLinecap="round" />
    </svg>
  );
}
function IconSinArch({ c = TEAL, s = 56 }: { c?: string; s?: number }) {
  return (
    <svg width={s} height={s} viewBox="0 0 60 60">
      <path d="M8,46 L8,24 Q8,6 30,6 Q52,6 52,24 L52,46" fill="none" stroke={c} strokeWidth="4.5" strokeLinecap="round" />
      <circle cx="15" cy="55" r="3" fill={c} />
      <circle cx="30" cy="55" r="3" fill={c} />
      <circle cx="45" cy="55" r="3" fill={c} />
    </svg>
  );
}
function IconHomeLines({ c = TEAL, s = 44 }: { c?: string; s?: number }) {
  return (
    <svg width={s * 1.1} height={s} viewBox="0 0 44 40">
      <polyline points="2,22 22,4 42,22" fill="none" stroke={c} strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" />
      <polyline points="8,22 8,38 36,38 36,22" fill="none" stroke={c} strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" />
      <rect x="17" y="26" width="10" height="12" rx="0.5" fill="none" stroke={c} strokeWidth="3" />
    </svg>
  );
}

function Card({ bg = WHITE, w = 280, h = 180, children }: { bg?: string; w?: number; h?: number; children: React.ReactNode }) {
  return (
    <div style={{ width: w, height: h, background: bg, borderRadius: 18, display: "flex", alignItems: "center", justifyContent: "center", boxShadow: "0 4px 36px rgba(0,0,0,0.5), 0 0 0 1px rgba(255,255,255,0.04)", overflow: "hidden", flexShrink: 0 }}>
      {children}
    </div>
  );
}
function Label({ n, name }: { n: number; name: string }) {
  return (
    <div style={{ paddingTop: 10 }}>
      <span style={{ fontSize: 9.5, fontWeight: 400, color: GOLD, letterSpacing: 2.5, ...MONO }}>{String(n).padStart(2, "0")} ·</span>
      <div style={{ fontSize: 11.5, color: SLATE, marginTop: 3, fontFamily: "'Inter', sans-serif" }}>{name}</div>
    </div>
  );
}
function Section({ id, label, children }: { id: string; label: string; children: React.ReactNode }) {
  return (
    <div style={{ marginBottom: 52 }}>
      <div style={{ display: "flex", alignItems: "center", gap: 18, marginBottom: 26 }}>
        <span style={{ fontSize: 9, fontWeight: 400, color: GOLD, letterSpacing: 3.5, ...MONO }}>{id}</span>
        <div style={{ height: "1px", flex: 1, background: `linear-gradient(90deg, ${GOLD}35, transparent)` }} />
        <span style={{ fontSize: 10.5, color: SLATE, letterSpacing: 0.5, fontFamily: "'Inter', sans-serif" }}>{label}</span>
      </div>
      <div style={{ display: "flex", gap: 22, flexWrap: "wrap" }}>{children}</div>
    </div>
  );
}

// ─── 20 logo concepts ────────────────────────────────────────────────

export function LogoBoard() {
  return (
    <div style={{ padding: "0 0 40px" }}>

      {/* Section A — Arabic Wordmark */}
      <Section id="A / 01–04" label="Arabic Wordmark">
        <div>
          <Card bg={WHITE}>
            <svg width="248" height="90" viewBox="0 0 248 90">
              <text x="124" y="43" textAnchor="middle" dominantBaseline="central"
                style={{ fontFamily: "'Tajawal',sans-serif", fontWeight: 900, fontSize: "60px", fill: TEAL } as React.CSSProperties}>سكون</text>
              <line x1="70" y1="76" x2="178" y2="76" stroke={TEAL} strokeWidth="3.5" strokeLinecap="round" />
            </svg>
          </Card>
          <Label n={1} name="Classic Bold" />
        </div>
        <div>
          <Card bg={CREAM}>
            <svg width="248" height="90" viewBox="0 0 248 90">
              <text x="124" y="40" textAnchor="middle" dominantBaseline="central"
                style={{ fontFamily: "'Tajawal',sans-serif", fontWeight: 300, fontSize: "52px", fill: NAVY, letterSpacing: "5px" } as React.CSSProperties}>سكون</text>
              <line x1="82" y1="74" x2="166" y2="74" stroke={GOLD} strokeWidth="1" />
              <circle cx="124" cy="74" r="2" fill={GOLD} />
            </svg>
          </Card>
          <Label n={2} name="Thin Elegant" />
        </div>
        <div>
          <Card bg={WHITE}>
            <svg width="248" height="90" viewBox="0 0 248 90">
              <text x="156" y="47" textAnchor="middle" dominantBaseline="central"
                style={{ fontFamily: "'Tajawal',sans-serif", fontWeight: 900, fontSize: "72px", fill: TEAL } as React.CSSProperties}>سـ</text>
              <text x="76" y="50" textAnchor="middle" dominantBaseline="central"
                style={{ fontFamily: "'Tajawal',sans-serif", fontWeight: 300, fontSize: "46px", fill: NAVY } as React.CSSProperties}>كون</text>
              <line x1="100" y1="20" x2="100" y2="70" stroke="#E2E8F0" strokeWidth="1" />
            </svg>
          </Card>
          <Label n={3} name="Weight Drama" />
        </div>
        <div>
          <Card bg={NAVY}>
            <svg width="248" height="90" viewBox="0 0 248 90">
              <text x="124" y="42" textAnchor="middle" dominantBaseline="central"
                style={{ fontFamily: "'Tajawal',sans-serif", fontWeight: 900, fontSize: "58px", fill: WHITE } as React.CSSProperties}>سكون</text>
              <rect x="86" y="68" width="76" height="3.5" rx="1.75" fill={TEAL} />
            </svg>
          </Card>
          <Label n={4} name="Night Reverse" />
        </div>
      </Section>

      {/* Section B — Bilingual Lockup */}
      <Section id="B / 05–07" label="Bilingual Lockup">
        <div>
          <Card bg={WHITE}>
            <svg width="248" height="116" viewBox="0 0 248 116">
              <text x="124" y="40" textAnchor="middle" dominantBaseline="central"
                style={{ fontFamily: "'Tajawal',sans-serif", fontWeight: 900, fontSize: "54px", fill: NAVY } as React.CSSProperties}>سكون</text>
              <line x1="36" y1="64" x2="212" y2="64" stroke={TEAL} strokeWidth="1.5" />
              <text x="124" y="84" textAnchor="middle" dominantBaseline="central"
                style={{ fontFamily: "'DM Mono',monospace", fontWeight: 400, fontSize: "13px", fill: SLATE, letterSpacing: "7px" } as React.CSSProperties}>SOKOON</text>
              <text x="124" y="104" textAnchor="middle" dominantBaseline="central"
                style={{ fontFamily: "'DM Mono',monospace", fontWeight: 300, fontSize: "9px", fill: `${SLATE}80`, letterSpacing: "2px" } as React.CSSProperties}>Real Estate Platform</text>
            </svg>
          </Card>
          <Label n={5} name="Stacked Bilingual" />
        </div>
        <div>
          <Card bg={CREAM}>
            <svg width="248" height="90" viewBox="0 0 248 90">
              <text x="158" y="44" textAnchor="middle" dominantBaseline="central"
                style={{ fontFamily: "'Tajawal',sans-serif", fontWeight: 700, fontSize: "50px", fill: TEAL } as React.CSSProperties}>سكون</text>
              <line x1="108" y1="16" x2="108" y2="74" stroke={GOLD} strokeWidth="1.5" />
              <text x="60" y="40" textAnchor="middle" dominantBaseline="central"
                style={{ fontFamily: "'Inter',sans-serif", fontWeight: 300, fontSize: "20px", fill: NAVY, letterSpacing: "2px" } as React.CSSProperties}>Sokoon</text>
              <text x="60" y="60" textAnchor="middle" dominantBaseline="central"
                style={{ fontFamily: "'DM Mono',monospace", fontWeight: 300, fontSize: "8.5px", fill: `${SLATE}90`, letterSpacing: "2px" } as React.CSSProperties}>REAL ESTATE</text>
            </svg>
          </Card>
          <Label n={6} name="Horizontal Split" />
        </div>
        <div>
          <Card bg={WHITE}>
            <svg width="248" height="116" viewBox="0 0 248 116">
              <text x="136" y="50" textAnchor="middle" dominantBaseline="central"
                style={{ fontFamily: "'Tajawal',sans-serif", fontWeight: 900, fontSize: "60px", fill: NAVY } as React.CSSProperties}>سكون</text>
              <line x1="18" y1="88" x2="118" y2="88" stroke={TEAL} strokeWidth="1" />
              <text x="68" y="100" textAnchor="middle" dominantBaseline="central"
                style={{ fontFamily: "'Inter',sans-serif", fontWeight: 300, fontSize: "9.5px", fill: TEAL, letterSpacing: "2.5px" } as React.CSSProperties}>Sokoon Real Estate</text>
            </svg>
          </Card>
          <Label n={7} name="Asymmetric Tag" />
        </div>
      </Section>

      {/* Section C — Icon + Wordmark */}
      <Section id="C / 08–11" label="Icon + Wordmark">
        <div>
          <Card bg={WHITE}>
            <div style={{ display: "flex", alignItems: "center", gap: 18, padding: "0 28px" }}>
              <IconHouse s={46} />
              <div>
                <div style={{ fontSize: 44, fontWeight: 900, color: NAVY, lineHeight: 1.1, ...TJ }}>سكون</div>
                <div style={{ fontSize: 9, color: SLATE, letterSpacing: 4.5, marginTop: 4, ...MONO }}>SOKOON</div>
              </div>
            </div>
          </Card>
          <Label n={8} name="House Wordmark" />
        </div>
        <div>
          <Card bg={CREAM}>
            <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 8 }}>
              <IconArch s={50} c={TEAL} />
              <div style={{ fontSize: 40, fontWeight: 900, color: NAVY, lineHeight: 1, ...TJ }}>سكون</div>
              <div style={{ fontSize: 9, color: TEAL, letterSpacing: 6, ...MONO }}>SOKOON</div>
            </div>
          </Card>
          <Label n={9} name="Arch Wordmark" />
        </div>
        <div>
          <Card bg={WHITE}>
            <div style={{ display: "flex", alignItems: "center", gap: 16, padding: "0 24px" }}>
              <IconPin s={46} c={TEAL} />
              <div>
                <div style={{ fontSize: 42, fontWeight: 900, color: TEAL, lineHeight: 1.1, ...TJ }}>سكون</div>
                <div style={{ fontSize: 9, color: NAVY, letterSpacing: 3.5, marginTop: 4, ...MONO }}>Sokoon</div>
              </div>
            </div>
          </Card>
          <Label n={10} name="Pin Wordmark" />
        </div>
        <div>
          <Card bg={NAVY2}>
            <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 12 }}>
              <IconKey c={GOLD} s={36} />
              <div style={{ fontSize: 40, fontWeight: 900, color: WHITE, lineHeight: 1, ...TJ }}>سكون</div>
              <div style={{ fontSize: 8, color: GOLD, letterSpacing: 5, ...MONO }}>SOKOON</div>
            </div>
          </Card>
          <Label n={11} name="Key Wordmark" />
        </div>
      </Section>

      {/* Section D — Symbolic / Monogram */}
      <Section id="D / 12–14" label="Symbolic / Monogram">
        <div>
          <Card bg={WHITE}>
            <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 10 }}>
              <IconSinArch s={60} c={TEAL} />
              <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <div style={{ height: 1, width: 20, background: TEAL, opacity: 0.4 }} />
                <span style={{ fontSize: 9, color: SLATE, letterSpacing: 5, ...MONO }}>SOKOON</span>
                <div style={{ height: 1, width: 20, background: TEAL, opacity: 0.4 }} />
              </div>
            </div>
          </Card>
          <Label n={12} name="Sin Shelter Mark" />
        </div>
        <div>
          <Card bg={NAVY}>
            <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 10 }}>
              <svg width="96" height="78" viewBox="0 0 96 78">
                <path d="M6,52 L6,28 Q6,4 48,4 Q90,4 90,28 L90,52" fill="none" stroke={TEAL} strokeWidth="4" strokeLinecap="round" />
                <line x1="2" y1="52" x2="94" y2="52" stroke={TEAL} strokeWidth="4" strokeLinecap="round" />
                <rect x="38" y="52" width="20" height="24" fill={TEAL} />
                <path d="M38,52 Q48,40 58,52Z" fill={TEAL} />
                <line x1="8" y1="76" x2="88" y2="76" stroke={TEAL} strokeWidth="1.5" strokeLinecap="round" opacity="0.25" />
              </svg>
              <div style={{ fontSize: 28, fontWeight: 700, color: WHITE, ...TJ }}>سكون</div>
            </div>
          </Card>
          <Label n={13} name="Curved Shelter" />
        </div>
        <div>
          <Card bg="#0A1520">
            <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 14 }}>
              <IconHomeLines c={GOLD} s={46} />
              <div style={{ fontSize: 38, fontWeight: 900, color: GOLD, lineHeight: 1, ...TJ }}>سكون</div>
            </div>
          </Card>
          <Label n={14} name="Gold Architecture" />
        </div>
      </Section>

      {/* Section E — Badge / Framed */}
      <Section id="E / 15–17" label="Badge / Framed">
        <div>
          <Card bg={WHITE}>
            <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 10 }}>
              <div style={{ position: "relative", display: "flex", alignItems: "center", justifyContent: "center" }}>
                <svg width="212" height="72" viewBox="0 0 212 72" style={{ position: "absolute" }}>
                  <ellipse cx="106" cy="36" rx="102" ry="32" fill="none" stroke={TEAL} strokeWidth="1.5" />
                  <ellipse cx="106" cy="36" rx="106" ry="36" fill="none" stroke={TEAL} strokeWidth="0.5" opacity="0.2" />
                </svg>
                <div style={{ fontSize: 42, fontWeight: 900, color: NAVY, padding: "10px 46px", ...TJ }}>سكون</div>
              </div>
              <div style={{ fontSize: 8.5, color: TEAL, letterSpacing: 5.5, ...MONO }}>SOKOON</div>
            </div>
          </Card>
          <Label n={15} name="Oval Frame" />
        </div>
        <div>
          <Card bg={CREAM}>
            <div style={{ position: "relative", display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", width: 220, height: 130 }}>
              <svg style={{ position: "absolute", inset: 0, width: "100%", height: "100%" }} viewBox="0 0 220 130" preserveAspectRatio="none">
                <path d="M16,3 L3,3 L3,16" fill="none" stroke={GOLD} strokeWidth="2" strokeLinecap="round" />
                <path d="M204,3 L217,3 L217,16" fill="none" stroke={GOLD} strokeWidth="2" strokeLinecap="round" />
                <path d="M3,114 L3,127 L16,127" fill="none" stroke={GOLD} strokeWidth="2" strokeLinecap="round" />
                <path d="M204,127 L217,127 L217,114" fill="none" stroke={GOLD} strokeWidth="2" strokeLinecap="round" />
              </svg>
              <div style={{ fontSize: 48, fontWeight: 900, color: NAVY, lineHeight: 1, ...TJ }}>سكون</div>
              <div style={{ display: "flex", alignItems: "center", gap: 10, marginTop: 6 }}>
                <div style={{ width: 32, height: 1, background: GOLD }} />
                <span style={{ fontSize: 8.5, color: GOLD, letterSpacing: 4, ...MONO }}>SOKOON</span>
                <div style={{ width: 32, height: 1, background: GOLD }} />
              </div>
            </div>
          </Card>
          <Label n={16} name="Corner Brackets" />
        </div>
        <div>
          <Card bg={NAVY}>
            <div style={{ position: "relative", width: 160, height: 160, display: "flex", alignItems: "center", justifyContent: "center" }}>
              <svg width="160" height="160" viewBox="0 0 160 160" style={{ position: "absolute" }}>
                <circle cx="80" cy="80" r="74" fill="none" stroke={GOLD} strokeWidth="1.5" />
                <circle cx="80" cy="80" r="63" fill="none" stroke={GOLD} strokeWidth="0.5" opacity="0.3" />
                <defs>
                  <path id="sealRingLB" d="M80,80 m-54,0 a54,54 0 1,1 108,0 a54,54 0 1,1 -108,0" />
                </defs>
                <text style={{ fontFamily: "'DM Mono',monospace", fontSize: "8.5px", fill: GOLD, letterSpacing: "3.2px" } as React.CSSProperties}>
                  <textPath href="#sealRingLB" startOffset="0%">SOKOON REAL ESTATE · سكون للعقارات ·</textPath>
                </text>
              </svg>
              <div style={{ fontSize: 46, fontWeight: 900, color: WHITE, ...TJ }}>سكون</div>
            </div>
          </Card>
          <Label n={17} name="Circular Seal" />
        </div>
      </Section>

      {/* Section F — App Icon */}
      <Section id="F / 18–20" label="App Icon">
        <div>
          <Card bg={TEAL} w={168} h={168}>
            <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 10 }}>
              <IconHouse c={WHITE} d={TEAL} s={50} />
              <div style={{ fontSize: 24, fontWeight: 900, color: WHITE, lineHeight: 1, ...TJ }}>سكون</div>
            </div>
          </Card>
          <Label n={18} name="App — Teal House" />
        </div>
        <div>
          <Card bg={NAVY} w={168} h={168}>
            <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 10 }}>
              <IconSinArch c={GOLD} s={58} />
              <div style={{ fontSize: 22, fontWeight: 700, color: GOLD, lineHeight: 1, ...TJ }}>سكون</div>
            </div>
          </Card>
          <Label n={19} name="App — Navy Gold" />
        </div>
        <div>
          <Card bg={CREAM} w={168} h={168}>
            <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 4 }}>
              <div style={{ fontSize: 54, fontWeight: 900, color: NAVY, lineHeight: 1, ...TJ }}>سكون</div>
              <div style={{ width: 48, height: 3, background: GOLD, borderRadius: 2 }} />
              <div style={{ fontSize: 9, color: NAVY, letterSpacing: 5, marginTop: 4, ...MONO }}>SOKOON</div>
            </div>
          </Card>
          <Label n={20} name="App — Cream" />
        </div>
      </Section>

    </div>
  );
}
