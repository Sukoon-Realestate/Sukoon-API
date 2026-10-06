import React from "react";

// ─── Brand palette ─────────────────────────────────────────────────────
const T   = "#0F766E";   // teal
const T2  = "#0D9488";
const T3  = "#134E4A";
const N   = "#0B1628";   // navy
const N2  = "#0E2040";
const N3  = "#162032";
const G   = "#D4A84B";   // gold
const G2  = "#B8912F";
const CR  = "#F8F4EF";   // cream
const CR2 = "#EDE8E1";
const W   = "#FFFFFF";
const SL  = "#64748B";
const BG  = "#07101E";   // board background

const TJ:   React.CSSProperties = { fontFamily: "'Tajawal', sans-serif" };
const MONO: React.CSSProperties = { fontFamily: "'DM Mono', monospace" };
const INT:  React.CSSProperties = { fontFamily: "'Inter', sans-serif" };

// ══════════════════════════════════════════════════════════════════════
// ① FUTURE GRAPHICS — 12 concepts at 1024×512 (shown at 50% → 512×256)
// ══════════════════════════════════════════════════════════════════════

// Each graphic is an SVG at 1024×512 — displayed at half scale via a wrapper

function Graphic({ children, n, title, sub }: {
  children: React.ReactNode; n: number; title: string; sub: string;
}) {
  return (
    <div style={{ display: "flex", flexDirection: "column" }}>
      <div style={{
        width: 512, height: 256, borderRadius: 16, overflow: "hidden", flexShrink: 0,
        boxShadow: "0 8px 40px rgba(0,0,0,0.55), 0 0 0 1px rgba(255,255,255,0.05)",
      }}>
        <div style={{ transform: "scale(0.5)", transformOrigin: "top left", width: 1024, height: 512 }}>
          {children}
        </div>
      </div>
      <div style={{ paddingTop: 12 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <span style={{ fontSize: 9, color: G, letterSpacing: 3, ...MONO }}>{String(n).padStart(2,"0")}</span>
          <span style={{ fontSize: 13, fontWeight: 700, color: W, ...INT }}>{title}</span>
        </div>
        <div style={{ fontSize: 10.5, color: SL, marginTop: 3, ...INT }}>{sub}</div>
        <div style={{ fontSize: 8.5, color: `${SL}70`, marginTop: 2, ...MONO }}>1024 × 512 px · Export-ready</div>
      </div>
    </div>
  );
}

// 01 — Typography Hero (split field)
const FG01 = () => (
  <svg width="1024" height="512" viewBox="0 0 1024 512">
    <rect x="0" y="0" width="512" height="512" fill={T} />
    <rect x="512" y="0" width="512" height="512" fill={CR} />
    <line x1="512" y1="0" x2="512" y2="512" stroke="rgba(255,255,255,0.12)" strokeWidth="2" />
    {/* Massive Arabic text bridging the split */}
    <text x="512" y="290" textAnchor="middle" dominantBaseline="central"
      style={{ fontFamily:"'Tajawal',sans-serif", fontWeight:900, fontSize:"260px",
        fill:"transparent", stroke:W, strokeWidth:"1px" } as React.CSSProperties}>سكون</text>
    <text x="512" y="290" textAnchor="middle" dominantBaseline="central"
      style={{ fontFamily:"'Tajawal',sans-serif", fontWeight:900, fontSize:"260px",
        fill:W, clipPath:"inset(0 512px 0 0)" } as React.CSSProperties}>سكون</text>
    <text x="512" y="290" textAnchor="middle" dominantBaseline="central"
      style={{ fontFamily:"'Tajawal',sans-serif", fontWeight:900, fontSize:"260px",
        fill:T, clipPath:"inset(0 0 0 512px)" } as React.CSSProperties}>سكون</text>
    {/* EN label */}
    <text x="512" y="434" textAnchor="middle"
      style={{ fontFamily:"'DM Mono',monospace", fontSize:"22px", fill:W, opacity:0.45, letterSpacing:"10px" } as React.CSSProperties}>
      SOKOON
    </text>
  </svg>
);

// 02 — Logo + Radial Rings on Navy
const FG02 = () => (
  <svg width="1024" height="512" viewBox="0 0 1024 512">
    <rect width="1024" height="512" fill={N} />
    {[80,135,200,280,368].map((r,i) => (
      <circle key={r} cx="512" cy="256" r={r} fill="none" stroke={G}
        strokeWidth={i===0 ? 1.5 : 0.6} opacity={0.08+i*0.04} />
    ))}
    {Array.from({length:36},(_,i)=>{
      const angle=(i*10)*Math.PI/180, r=280;
      return <circle key={i} cx={512+r*Math.cos(angle)} cy={256+r*Math.sin(angle)}
        r={2} fill={G} opacity={0.18} />;
    })}
    <text x="512" y="240" textAnchor="middle" dominantBaseline="central"
      style={{ fontFamily:"'Tajawal',sans-serif", fontWeight:900, fontSize:"190px", fill:W } as React.CSSProperties}>
      سكون
    </text>
    <text x="512" y="358" textAnchor="middle"
      style={{ fontFamily:"'DM Mono',monospace", fontSize:"22px", fill:G, letterSpacing:"12px" } as React.CSSProperties}>
      SOKOON
    </text>
    <text x="512" y="400" textAnchor="middle"
      style={{ fontFamily:"'Tajawal',sans-serif", fontSize:"26px", fill:`${W}40` } as React.CSSProperties}>
      منصة العقارات والإيجار
    </text>
  </svg>
);

// 03 — Architecture Lines on Cream
const FG03 = () => (
  <svg width="1024" height="512" viewBox="0 0 1024 512">
    <rect width="1024" height="512" fill={CR2} />
    <line x1="0" y1="460" x2="1024" y2="460" stroke={T} strokeWidth="2" opacity="0.2" />
    {/* Tower 1 */}
    <rect x="60" y="160" width="88" height="300" fill="none" stroke={T} strokeWidth="2"/>
    {[180,210,240,270,300,330,360,390].map(y=>[74,106].map(x=>(
      <rect key={`${x}-${y}`} x={x} y={y} width="16" height="18" fill="none" stroke={T} strokeWidth="1" opacity="0.4"/>
    )))}
    {/* Tower 2 arch facade */}
    <rect x="240" y="210" width="140" height="250" fill="none" stroke={T} strokeWidth="2"/>
    <path d="M268,210 L268,256 Q310,228 352,256 L352,210" fill="none" stroke={T} strokeWidth="2"/>
    {[230,260,290,320,360,400].map(y=>(
      <line key={y} x1="254" y1={y} x2="366" y2={y} stroke={T} strokeWidth="1" opacity="0.25"/>
    ))}
    {/* Tower 3 stepped */}
    <rect x="450" y="120" width="60" height="340" fill="none" stroke={T} strokeWidth="1.5"/>
    <rect x="420" y="160" width="120" height="300" fill="none" stroke={T} strokeWidth="1.5"/>
    <rect x="390" y="230" width="180" height="230" fill="none" stroke={T} strokeWidth="2"/>
    {[240,270,300,330,370,410].map(y=>[402,432,462,492,522,540].map(x=>(
      <rect key={`${x}-${y}`} x={x} y={y} width="14" height="17" fill="none" stroke={T} strokeWidth="0.8" opacity="0.35"/>
    )))}
    {/* Tower 4 dome */}
    <rect x="640" y="200" width="180" height="260" fill="none" stroke={T} strokeWidth="2"/>
    <path d="M640,200 Q730,100 820,200" fill="none" stroke={T} strokeWidth="2.5"/>
    {[220,260,300,340,390,430].map(y=>[654,688,724,760,796].map(x=>(
      <rect key={`${x}-${y}`} x={x} y={y} width="14" height="17" fill="none" stroke={T} strokeWidth="0.8" opacity="0.4"/>
    )))}
    {/* Tower 5 minimal */}
    <rect x="860" y="170" width="110" height="290" fill="none" stroke={T} strokeWidth="2"/>
    <rect x="890" y="100" width="50" height="70" fill="none" stroke={T} strokeWidth="1.5"/>
    {/* Brand */}
    <text x="512" y="495" textAnchor="middle"
      style={{ fontFamily:"'Tajawal',sans-serif", fontWeight:900, fontSize:"36px", fill:N } as React.CSSProperties}>
      سكون للعقارات
    </text>
  </svg>
);

// 04 — Premium Abstract (vanishing-point gold lines)
const FG04 = () => (
  <svg width="1024" height="512" viewBox="0 0 1024 512">
    <rect width="1024" height="512" fill={N} />
    <defs>
      <linearGradient id="fg04g" x1="0%" y1="0%" x2="100%" y2="0%">
        <stop offset="0%" stopColor={G} stopOpacity="0.5"/>
        <stop offset="100%" stopColor={T} stopOpacity="0.3"/>
      </linearGradient>
    </defs>
    {[-60,-30,0,30,60,100,140,180,220,260,300,340,380,420,460,500,540,580].map((y,i)=>(
      <line key={i} x1="0" y1={y} x2="1024" y2="256" stroke={G} strokeWidth="0.5" opacity="0.07"/>
    ))}
    <line x1="0" y1="0"   x2="1024" y2="256" stroke={G} strokeWidth="2" opacity="0.22"/>
    <line x1="0" y1="512" x2="1024" y2="256" stroke={G} strokeWidth="2" opacity="0.22"/>
    <line x1="0" y1="170" x2="1024" y2="256" stroke={G} strokeWidth="0.8" opacity="0.3"/>
    <line x1="0" y1="342" x2="1024" y2="256" stroke={G} strokeWidth="0.8" opacity="0.3"/>
    <line x1="240" y1="0" x2="240" y2="512" stroke={G} strokeWidth="0.8" opacity="0.15"/>
    {/* Diamond */}
    <polygon points="512,160 600,256 512,352 424,256"
      fill="none" stroke={G} strokeWidth="2" opacity="0.5"/>
    <polygon points="512,186 572,256 512,326 452,256"
      fill={`${G}18`} stroke={G} strokeWidth="1" opacity="0.4"/>
    <text x="512" y="248" textAnchor="middle" dominantBaseline="central"
      style={{ fontFamily:"'Tajawal',sans-serif", fontWeight:900, fontSize:"42px", fill:G } as React.CSSProperties}>
      سكون
    </text>
    <text x="120" y="456" textAnchor="middle"
      style={{ fontFamily:"'Tajawal',sans-serif", fontWeight:300, fontSize:"24px", fill:`${W}40` } as React.CSSProperties}>
      منصة موثوقة للعقارات
    </text>
  </svg>
);

// 05 — Trust & Verification
const FG05 = () => (
  <svg width="1024" height="512" viewBox="0 0 1024 512">
    <rect width="1024" height="512" fill="#0A1F18" />
    <defs>
      <radialGradient id="fg05glow" cx="50%" cy="50%" r="40%">
        <stop offset="0%" stopColor={T} stopOpacity="0.28"/>
        <stop offset="100%" stopColor={T} stopOpacity="0"/>
      </radialGradient>
    </defs>
    <ellipse cx="512" cy="256" rx="320" ry="240" fill="url(#fg05glow)"/>
    {[70,120,180,250].map(r=>(
      <circle key={r} cx="512" cy="256" r={r} fill="none" stroke={T} strokeWidth="0.8" opacity="0.1+r/500"/>
    ))}
    {/* Shield */}
    <path d="M512,88 L620,128 L620,280 Q620,370 512,404 Q404,370 404,280 L404,128 Z"
      fill={`${T}14`} stroke={T} strokeWidth="2.5"/>
    <path d="M512,110 L598,144 L598,274 Q598,352 512,382 Q426,352 426,274 L426,144 Z"
      fill={`${T}08`} stroke={T} strokeWidth="1" opacity="0.5"/>
    {/* Checkmark */}
    <polyline points="456,256 492,294 574,210"
      fill="none" stroke={T} strokeWidth="9" strokeLinecap="round" strokeLinejoin="round"/>
    <text x="512" y="438" textAnchor="middle"
      style={{ fontFamily:"'Tajawal',sans-serif", fontWeight:700, fontSize:"30px", fill:W } as React.CSSProperties}>
      تم التحقق من إثبات الملكية
    </text>
    <text x="512" y="478" textAnchor="middle"
      style={{ fontFamily:"'Tajawal',sans-serif", fontWeight:300, fontSize:"20px", fill:`${T2}` } as React.CSSProperties}>
      موثّق ومعتمد من سكون
    </text>
    {/* Brand */}
    <text x="940" y="52" textAnchor="end"
      style={{ fontFamily:"'Tajawal',sans-serif", fontWeight:900, fontSize:"28px", fill:`${W}50` } as React.CSSProperties}>
      سكون
    </text>
  </svg>
);

// 06 — Shelter Arch on Cream
const FG06 = () => (
  <svg width="1024" height="512" viewBox="0 0 1024 512">
    <rect width="1024" height="512" fill={CR} />
    {/* Ground */}
    <line x1="80" y1="490" x2="944" y2="490" stroke={T} strokeWidth="2" opacity="0.15"/>
    {/* Outer arch */}
    <path d="M192,492 L192,240 Q192,30 512,30 Q832,30 832,240 L832,492"
      fill={`${T}10`} stroke={T} strokeWidth="4" strokeLinecap="round"/>
    {/* Middle arch */}
    <path d="M260,492 L260,260 Q260,100 512,100 Q764,100 764,260 L764,492"
      fill={`${T}07`} stroke={T} strokeWidth="2.5" strokeLinecap="round" opacity="0.65"/>
    {/* Inner arch / doorway */}
    <path d="M380,492 L380,310 Q380,175 512,175 Q644,175 644,310 L644,492"
      fill={`${N}05`} stroke={N} strokeWidth="1.5" opacity="0.2"/>
    {/* Brand in arch */}
    <text x="512" y="360" textAnchor="middle" dominantBaseline="central"
      style={{ fontFamily:"'Tajawal',sans-serif", fontWeight:900, fontSize:"130px", fill:N } as React.CSSProperties}>
      سكون
    </text>
    <text x="512" y="454" textAnchor="middle"
      style={{ fontFamily:"'Tajawal',sans-serif", fontWeight:300, fontSize:"24px", fill:T } as React.CSSProperties}>
      مسكنك أقرب مما تتخيل
    </text>
    <circle cx="512" cy="50" r="8" fill={G} opacity="0.7"/>
  </svg>
);

// 07 — Minimal Dot Grid
const FG07 = () => {
  const dots: React.ReactNode[] = [];
  for (let r=0; r<20; r++) for (let c=0; c<44; c++) {
    const x=18+c*23, y=18+r*25;
    const dx=x-512, dy=y-256;
    const dist=Math.sqrt(dx*dx+dy*dy);
    const fade=dist<180?0:dist<300?(dist-180)/120:1;
    dots.push(<circle key={`${r}-${c}`} cx={x} cy={y} r={2.2} fill={T} opacity={fade*0.16}/>);
  }
  return (
    <svg width="1024" height="512" viewBox="0 0 1024 512">
      <rect width="1024" height="512" fill="#F2EEE8"/>
      {dots}
      <line x1="512" y1="140" x2="512" y2="372" stroke={T} strokeWidth="0.8" opacity="0.18"/>
      <line x1="312" y1="256" x2="712" y2="256" stroke={T} strokeWidth="0.8" opacity="0.18"/>
      <text x="512" y="240" textAnchor="middle" dominantBaseline="central"
        style={{ fontFamily:"'Tajawal',sans-serif", fontWeight:900, fontSize:"180px", fill:N } as React.CSSProperties}>
        سكون
      </text>
      <line x1="378" y1="330" x2="646" y2="330" stroke={T} strokeWidth="1.5" opacity="0.35"/>
      <text x="512" y="370" textAnchor="middle"
        style={{ fontFamily:"'DM Mono',monospace", fontSize:"18px", fill:T, letterSpacing:"14px" } as React.CSSProperties}>
        SOKOON
      </text>
      <text x="512" y="420" textAnchor="middle"
        style={{ fontFamily:"'Tajawal',sans-serif", fontWeight:300, fontSize:"20px", fill:`${N}60` } as React.CSSProperties}>
        منصة العقارات والإيجار
      </text>
    </svg>
  );
};

// 08 — Luxury Editorial Split
const FG08 = () => (
  <svg width="1024" height="512" viewBox="0 0 1024 512">
    <rect width="512" height="512" fill={N} />
    <rect x="512" y="0" width="512" height="512" fill={CR} />
    <rect x="510" y="0" width="4" height="512" fill={G} />
    {/* Left panel */}
    <text x="256" y="200" textAnchor="middle"
      style={{ fontFamily:"'Tajawal',sans-serif", fontWeight:900, fontSize:"104px", fill:W } as React.CSSProperties}>
      سكون
    </text>
    <text x="256" y="276" textAnchor="middle"
      style={{ fontFamily:"'DM Mono',monospace", fontSize:"18px", fill:G, letterSpacing:"10px" } as React.CSSProperties}>
      SOKOON
    </text>
    <line x1="80" y1="308" x2="432" y2="308" stroke={G} strokeWidth="1" opacity="0.3"/>
    <text x="256" y="344" textAnchor="middle"
      style={{ fontFamily:"'Tajawal',sans-serif", fontWeight:300, fontSize:"22px", fill:`${W}65` } as React.CSSProperties}>
      منصة العقارات</text>
    <text x="256" y="378" textAnchor="middle"
      style={{ fontFamily:"'Tajawal',sans-serif", fontWeight:300, fontSize:"22px", fill:`${W}45` } as React.CSSProperties}>
      والإيجار المميز</text>
    {/* Right panel */}
    <text x="768" y="140" textAnchor="middle"
      style={{ fontFamily:"'Tajawal',sans-serif", fontWeight:700, fontSize:"28px", fill:N } as React.CSSProperties}>
      ابحث عن مسكنك المثالي</text>
    <line x1="536" y1="170" x2="1000" y2="170" stroke={N} strokeWidth="0.8" opacity="0.15"/>
    {/* Property card mockup */}
    <rect x="548" y="188" width="424" height="200" rx="20" fill={`${N}08`} stroke={`${N}12`} strokeWidth="1.5"/>
    <rect x="568" y="208" width="130" height="90" rx="12" fill={T} opacity="0.12"/>
    <text x="623" y="258" textAnchor="middle"
      style={{ fontFamily:"'Tajawal',sans-serif", fontSize:"30px" } as React.CSSProperties}>🏠</text>
    <text x="760" y="234" textAnchor="middle"
      style={{ fontFamily:"'Tajawal',sans-serif", fontWeight:700, fontSize:"22px", fill:N } as React.CSSProperties}>
      شقة مفروشة</text>
    <text x="760" y="268" textAnchor="middle"
      style={{ fontFamily:"'Tajawal',sans-serif", fontWeight:300, fontSize:"18px", fill:`${N}70` } as React.CSSProperties}>
      مدينة نصر — القاهرة</text>
    <text x="760" y="306" textAnchor="middle"
      style={{ fontFamily:"'Tajawal',sans-serif", fontWeight:700, fontSize:"20px", fill:T } as React.CSSProperties}>
      ٣٥٠٠ ر.س / شهر</text>
    {["٣ غرف","٢ حمام","١٢٠م²"].map((f,i)=>(
      <g key={f}>
        <rect x={548+i*140} y="412" width="128" height="40" rx="20" fill={`${T}12`} stroke={`${T}20`} strokeWidth="1"/>
        <text x={612+i*140} y="437" textAnchor="middle"
          style={{ fontFamily:"'Tajawal',sans-serif", fontSize:"17px", fill:T, fontWeight:600 } as React.CSSProperties}>{f}</text>
      </g>
    ))}
    <text x="768" y="490" textAnchor="middle"
      style={{ fontFamily:"'DM Mono',monospace", fontSize:"14px", fill:SL, letterSpacing:"5px" } as React.CSSProperties}>
      FIND YOUR PERFECT HOME</text>
  </svg>
);

// 09 — Golden Gradient Hero
const FG09 = () => (
  <svg width="1024" height="512" viewBox="0 0 1024 512">
    <defs>
      <linearGradient id="fg09a" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stopColor={N}/>
        <stop offset="100%" stopColor="#0A2218"/>
      </linearGradient>
      <linearGradient id="fg09b" x1="0%" y1="0%" x2="100%" y2="0%">
        <stop offset="0%" stopColor={G}/>
        <stop offset="100%" stopColor={T2}/>
      </linearGradient>
    </defs>
    <rect width="1024" height="512" fill="url(#fg09a)"/>
    {Array.from({length:18},(_,i)=>(
      <line key={i} x1="0" y1={10+i*28} x2="1024" y2={10+i*28} stroke={G} strokeWidth="0.3" opacity="0.04"/>
    ))}
    <line x1="0" y1="512" x2="1024" y2="0" stroke={G} strokeWidth="120" opacity="0.07"/>
    <defs>
      <radialGradient id="fg09orb" cx="30%" cy="50%" r="45%">
        <stop offset="0%" stopColor={G} stopOpacity="0.22"/>
        <stop offset="100%" stopColor={G} stopOpacity="0"/>
      </radialGradient>
    </defs>
    <ellipse cx="310" cy="256" rx="420" ry="280" fill="url(#fg09orb)"/>
    <text x="640" y="248" textAnchor="middle"
      style={{ fontFamily:"'Tajawal',sans-serif", fontWeight:900, fontSize:"222px", fill:"url(#fg09b)" } as React.CSSProperties}>
      سكون
    </text>
    <text x="188" y="196" textAnchor="middle"
      style={{ fontFamily:"'Tajawal',sans-serif", fontWeight:700, fontSize:"40px", fill:W } as React.CSSProperties}>
      السكن</text>
    <text x="188" y="248" textAnchor="middle"
      style={{ fontFamily:"'Tajawal',sans-serif", fontWeight:300, fontSize:"30px", fill:`${W}65` } as React.CSSProperties}>
      المثالي</text>
    <text x="188" y="296" textAnchor="middle"
      style={{ fontFamily:"'Tajawal',sans-serif", fontWeight:300, fontSize:"30px", fill:`${W}40` } as React.CSSProperties}>
      يبدأ من هنا</text>
    <line x1="70" y1="330" x2="306" y2="330" stroke={G} strokeWidth="2" strokeLinecap="round" opacity="0.5"/>
    <rect x="0" y="462" width="1024" height="50" fill={`${W}04`}/>
    <line x1="0" y1="462" x2="1024" y2="462" stroke={G} strokeWidth="0.8" opacity="0.2"/>
    <text x="110" y="494" textAnchor="middle"
      style={{ fontFamily:"'DM Mono',monospace", fontSize:"16px", fill:G, letterSpacing:"8px" } as React.CSSProperties}>
      SOKOON</text>
    <text x="600" y="494" textAnchor="middle"
      style={{ fontFamily:"'Tajawal',sans-serif", fontWeight:300, fontSize:"18px", fill:`${W}35` } as React.CSSProperties}>
      منصة العقارات والإيجار — مميز وموثوق</text>
  </svg>
);

// 10 — App Store Marketing
const FG10 = () => (
  <svg width="1024" height="512" viewBox="0 0 1024 512">
    <rect width="1024" height="512" fill={T3}/>
    <defs>
      <radialGradient id="fg10top" cx="50%" cy="0%" r="60%">
        <stop offset="0%" stopColor={T} stopOpacity="0.6"/>
        <stop offset="100%" stopColor={T} stopOpacity="0"/>
      </radialGradient>
    </defs>
    <rect width="1024" height="512" fill="url(#fg10top)"/>
    {[200,400,600,800].map(x=>(
      <line key={x} x1={x} y1="0" x2={x} y2="512" stroke={W} strokeWidth="0.5" opacity="0.04"/>
    ))}
    <text x="512" y="80" textAnchor="middle"
      style={{ fontFamily:"'Tajawal',sans-serif", fontWeight:900, fontSize:"74px", fill:W } as React.CSSProperties}>
      سكون</text>
    <text x="512" y="122" textAnchor="middle"
      style={{ fontFamily:"'DM Mono',monospace", fontSize:"16px", fill:`${W}55`, letterSpacing:"12px" } as React.CSSProperties}>
      SOKOON PLATFORM</text>
    <line x1="100" y1="148" x2="924" y2="148" stroke={W} strokeWidth="0.8" opacity="0.12"/>
    {[
      { icon:"🔍", ar:"ابحث بسهولة", en:"SMART SEARCH", x:171 },
      { icon:"✅", ar:"عقارات موثّقة", en:"VERIFIED ONLY", x:512 },
      { icon:"📍", ar:"موقع دقيق", en:"PRECISE LOCATION", x:853 },
    ].map(f=>(
      <g key={f.en}>
        <rect x={f.x-120} y="168" width="240" height="216" rx="28" fill={`${W}08`} stroke={`${W}10`} strokeWidth="1.5"/>
        <circle cx={f.x} cy="230" r="48" fill={`${W}12`}/>
        <text x={f.x} y="240" textAnchor="middle"
          style={{ fontSize:"36px" } as React.CSSProperties}>{f.icon}</text>
        <text x={f.x} y="300" textAnchor="middle"
          style={{ fontFamily:"'Tajawal',sans-serif", fontWeight:700, fontSize:"24px", fill:W } as React.CSSProperties}>
          {f.ar}</text>
        <text x={f.x} y="334" textAnchor="middle"
          style={{ fontFamily:"'DM Mono',monospace", fontSize:"12px", fill:`${W}45`, letterSpacing:"4px" } as React.CSSProperties}>
          {f.en}</text>
      </g>
    ))}
    <rect x="388" y="420" width="248" height="64" rx="32" fill={G}/>
    <text x="512" y="460" textAnchor="middle"
      style={{ fontFamily:"'Tajawal',sans-serif", fontWeight:700, fontSize:"26px", fill:N } as React.CSSProperties}>
      حمّل التطبيق الآن</text>
    <text x="512" y="504" textAnchor="middle"
      style={{ fontFamily:"'DM Mono',monospace", fontSize:"13px", fill:`${W}30`, letterSpacing:"5px" } as React.CSSProperties}>
      APP STORE · GOOGLE PLAY</text>
  </svg>
);

// 11 — Brand Manifesto (editorial text)
const FG11 = () => (
  <svg width="1024" height="512" viewBox="0 0 1024 512">
    <rect width="1024" height="512" fill={CR}/>
    <rect x="0" y="0" width="8" height="512" fill={`linear-gradient(180deg,${T},${T3})`}/>
    <rect x="0" y="0" width="8" height="512" fill={T}/>
    {/* Large watermark */}
    <text x="820" y="400" textAnchor="middle"
      style={{ fontFamily:"'Tajawal',sans-serif", fontWeight:900, fontSize:"480px", fill:T, opacity:0.04 } as React.CSSProperties}>
      س</text>
    {/* Brand */}
    <text x="60" y="88" textAnchor="start"
      style={{ fontFamily:"'Tajawal',sans-serif", fontWeight:900, fontSize:"54px", fill:T } as React.CSSProperties}>
      سكون</text>
    <text x="60" y="118" textAnchor="start"
      style={{ fontFamily:"'DM Mono',monospace", fontSize:"15px", fill:SL, letterSpacing:"8px" } as React.CSSProperties}>
      SOKOON REAL ESTATE</text>
    <line x1="60" y1="136" x2="580" y2="136" stroke={T} strokeWidth="1.2" opacity="0.2"/>
    {[
      { t:"نؤمن أن كل شخص يستحق", y:188, s:30, w:700, f:N },
      { t:"مسكناً آمناً وموثوقاً.", y:228, s:30, w:700, f:N },
      { t:"لهذا بنينا سكون — منصة تجمع", y:296, s:24, w:300, f:`${N}75` },
      { t:"الملاك والمستأجرين بشكل شفاف،", y:330, s:24, w:300, f:`${N}75` },
      { t:"موثوق، وإنساني.", y:364, s:24, w:300, f:`${N}75` },
    ].map((l,i)=>(
      <text key={i} x="60" y={l.y} textAnchor="start"
        style={{ fontFamily:"'Tajawal',sans-serif", fontWeight:l.w, fontSize:`${l.s}px`, fill:l.f } as React.CSSProperties}>
        {l.t}</text>
    ))}
    <line x1="60" y1="406" x2="240" y2="406" stroke={G} strokeWidth="4" strokeLinecap="round"/>
    <text x="60" y="480" textAnchor="start"
      style={{ fontFamily:"'Tajawal',sans-serif", fontWeight:300, fontSize:"20px", fill:SL } as React.CSSProperties}>
      ابحث · تحقق · انتقل</text>
    <text x="960" y="480" textAnchor="end"
      style={{ fontFamily:"'DM Mono',monospace", fontSize:"14px", fill:T, letterSpacing:"5px" } as React.CSSProperties}>
      2024 · SOKOON.COM</text>
  </svg>
);

// 12 — Stats Infographic
const FG12 = () => (
  <svg width="1024" height="512" viewBox="0 0 1024 512">
    <rect width="1024" height="512" fill={CR}/>
    <rect x="0" y="0" width="1024" height="128" fill={N}/>
    <rect x="0" y="0" width="10" height="128" fill={G}/>
    <text x="84" y="52" textAnchor="start"
      style={{ fontFamily:"'Tajawal',sans-serif", fontWeight:900, fontSize:"44px", fill:W } as React.CSSProperties}>
      سكون</text>
    <text x="84" y="94" textAnchor="start"
      style={{ fontFamily:"'Tajawal',sans-serif", fontWeight:300, fontSize:"22px", fill:`${W}55` } as React.CSSProperties}>
      أرقام تعكس ثقة عملائنا</text>
    <text x="970" y="66" textAnchor="end"
      style={{ fontFamily:"'DM Mono',monospace", fontSize:"16px", fill:`${W}25`, letterSpacing:"6px" } as React.CSSProperties}>
      2024 STATS</text>
    {[
      { n:"٢٠٠٠+", label:"عقار موثّق", en:"VERIFIED", x:171 },
      { n:"٥٠+",   label:"مدينة ومنطقة", en:"CITIES", x:512 },
      { n:"٩٨٪",   label:"رضا العملاء", en:"SATISFACTION", x:853 },
    ].map((s,i)=>(
      <g key={s.en}>
        {i>0&&<line x1={s.x-170} y1="148" x2={s.x-170} y2="420" stroke={N} strokeWidth="0.8" opacity="0.1"/>}
        <text x={s.x} y="270" textAnchor="middle"
          style={{ fontFamily:"'Tajawal',sans-serif", fontWeight:900, fontSize:"96px", fill:T } as React.CSSProperties}>
          {s.n}</text>
        <text x={s.x} y="338" textAnchor="middle"
          style={{ fontFamily:"'Tajawal',sans-serif", fontWeight:500, fontSize:"24px", fill:N } as React.CSSProperties}>
          {s.label}</text>
        <text x={s.x} y="374" textAnchor="middle"
          style={{ fontFamily:"'DM Mono',monospace", fontSize:"13px", fill:SL, letterSpacing:"5px" } as React.CSSProperties}>
          {s.en}</text>
        <rect x={s.x-90} y="398" width="180" height="7" rx="3.5" fill={`${T}18`}/>
        <rect x={s.x-90} y="398" width={i===0?180:i===1?126:176} height="7" rx="3.5" fill={T}/>
      </g>
    ))}
    <line x1="60" y1="438" x2="964" y2="438" stroke={N} strokeWidth="0.8" opacity="0.1"/>
    <text x="512" y="476" textAnchor="middle"
      style={{ fontFamily:"'Tajawal',sans-serif", fontWeight:300, fontSize:"20px", fill:SL } as React.CSSProperties}>
      ابحث · تحقق · انتقل إلى مسكنك الجديد</text>
  </svg>
);

// ─── Future Graphics section export ──────────────────────────────────
const FUTURE_GRAPHICS = [
  { n:1,  C:FG01, title:"Typography Hero",         sub:"Split-field teal/cream · Massive Arabic type" },
  { n:2,  C:FG02, title:"Logo Centered + Rings",   sub:"Concentric gold rings · Dark navy" },
  { n:3,  C:FG03, title:"Architecture Lines",       sub:"SVG building facades · Cream background" },
  { n:4,  C:FG04, title:"Premium Abstract",         sub:"Vanishing-point gold lines · Navy" },
  { n:5,  C:FG05, title:"Trust & Verification",     sub:"Shield mark · Ownership badge" },
  { n:6,  C:FG06, title:"Shelter Arch Hero",        sub:"Nested arches · Warm cream" },
  { n:7,  C:FG07, title:"Minimal Dot Grid",         sub:"Systematic dots · Breathing space" },
  { n:8,  C:FG08, title:"Luxury Editorial Split",   sub:"NAVY | CREAM hard divide · Editorial type" },
  { n:9,  C:FG09, title:"Golden Gradient Hero",     sub:"Gold-to-teal gradient · Premium warm" },
  { n:10, C:FG10, title:"App Store Marketing",      sub:"Feature highlights + CTA" },
  { n:11, C:FG11, title:"Brand Manifesto",          sub:"Mission statement · Editorial text" },
  { n:12, C:FG12, title:"Stats Infographic",        sub:"Numbers-forward · Data-driven brand" },
];

export function FutureGraphicsTab() {
  return (
    <div style={{ padding: "52px 48px 80px" }}>
      <div style={{ marginBottom: 40 }}>
        <div style={{ fontSize: 11, fontWeight: 800, color: "#0D9488", letterSpacing: 1, textTransform: "uppercase" as const, marginBottom: 8 }}>
          Future Graphics — Brand Marketing Concepts
        </div>
        <h2 style={{ fontSize: 24, fontWeight: 900, color: "#E2E8F0", margin: "0 0 6px" }}>12 Graphic Directions</h2>
        <p style={{ color: "#334155", fontSize: 13, margin: "0 0 6px" }}>
          1024 × 512 px · Export-ready SVG · Arabic RTL · Feature Graphics · Hero Banners · Promo Covers
        </p>
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap" as const, marginTop: 12 }}>
          {["Typography","Logo-Centered","Architecture","Abstract","Trust","Shelter","Minimal","Editorial","Gradient","App-Marketing","Manifesto","Infographic"].map(t => (
            <span key={t} style={{ fontSize: 10, fontWeight: 600, color: "#0D9488", background: "#0D948818", border: "1px solid #0D948830", borderRadius: 20, padding: "2px 10px" }}>{t}</span>
          ))}
        </div>
      </div>

      <div style={{ display: "flex", gap: 32, flexWrap: "wrap" as const }}>
        {FUTURE_GRAPHICS.map(g => (
          <Graphic key={g.n} n={g.n} title={g.title} sub={g.sub}>
            <g.C />
          </Graphic>
        ))}
      </div>
    </div>
  );
}

// ══════════════════════════════════════════════════════════════════════
// ② LOGO CONCEPTS — 20 concepts at 512×512 (shown at 220×220)
// ══════════════════════════════════════════════════════════════════════

function LogoCard({ bg = W, children, size = 220 }: {
  bg?: string; children: React.ReactNode; size?: number;
}) {
  return (
    <div style={{
      width: size, height: size, background: bg, borderRadius: 20, flexShrink: 0,
      display: "flex", alignItems: "center", justifyContent: "center", overflow: "hidden",
      boxShadow: "0 6px 32px rgba(0,0,0,0.5), 0 0 0 1px rgba(255,255,255,0.05)",
    }}>
      {children}
    </div>
  );
}

function LogoConcept({ n, name, bg, children }: {
  n: number; name: string; bg?: string; children: React.ReactNode;
}) {
  return (
    <div style={{ display: "flex", flexDirection: "column" }}>
      <LogoCard bg={bg}>{children}</LogoCard>
      <div style={{ paddingTop: 10 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <span style={{ fontSize: 9, color: G, letterSpacing: 3, ...MONO }}>{String(n).padStart(2,"0")}</span>
          <span style={{ fontSize: 11.5, color: W, ...INT }}>{name}</span>
        </div>
        <div style={{ fontSize: 8.5, color: SL, marginTop: 2, ...MONO }}>512 × 512 px</div>
      </div>
    </div>
  );
}

function SectionDivider({ id, label }: { id: string; label: string }) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 16, margin: "48px 0 24px" }}>
      <span style={{ fontSize: 9, color: G, letterSpacing: 4, ...MONO }}>{id}</span>
      <div style={{ flex: 1, height: 1, background: `linear-gradient(90deg, ${G}30, transparent)` }}/>
      <span style={{ fontSize: 10.5, color: SL, ...INT }}>{label}</span>
    </div>
  );
}

export function LogoConceptsTab() {
  return (
    <div style={{ padding: "52px 48px 80px" }}>
      <div style={{ marginBottom: 8 }}>
        <div style={{ fontSize: 11, fontWeight: 800, color: "#0D9488", letterSpacing: 1, textTransform: "uppercase" as const, marginBottom: 8 }}>
          Logo Exploration — 20 Original Concepts
        </div>
        <h2 style={{ fontSize: 24, fontWeight: 900, color: "#E2E8F0", margin: "0 0 6px" }}>سكون | Sokoon — Brand Identity</h2>
        <p style={{ color: "#334155", fontSize: 13, margin: 0 }}>
          512 × 512 px · 6 categories · Arabic Wordmark · Bilingual · Icon+Mark · Symbolic · Badge · App Icon
        </p>
      </div>

      {/* Section A — Arabic Wordmark */}
      <SectionDivider id="A / 01–04" label="Arabic Wordmark" />
      <div style={{ display: "flex", gap: 20, flexWrap: "wrap" as const }}>

        <LogoConcept n={1} name="Classic Bold" bg={W}>
          <svg width="220" height="220" viewBox="0 0 512 512">
            <text x="256" y="256" textAnchor="middle" dominantBaseline="central"
              style={{ fontFamily:"'Tajawal',sans-serif", fontWeight:900, fontSize:"190px", fill:T } as React.CSSProperties}>سكون</text>
            <line x1="140" y1="340" x2="372" y2="340" stroke={T} strokeWidth="8" strokeLinecap="round"/>
          </svg>
        </LogoConcept>

        <LogoConcept n={2} name="Thin Elegant" bg={CR}>
          <svg width="220" height="220" viewBox="0 0 512 512">
            <text x="256" y="248" textAnchor="middle" dominantBaseline="central"
              style={{ fontFamily:"'Tajawal',sans-serif", fontWeight:300, fontSize:"170px", fill:N, letterSpacing:"8px" } as React.CSSProperties}>سكون</text>
            <line x1="164" y1="340" x2="348" y2="340" stroke={G} strokeWidth="2"/>
            <circle cx="256" cy="340" r="4" fill={G}/>
          </svg>
        </LogoConcept>

        <LogoConcept n={3} name="Weight Drama" bg={W}>
          <svg width="220" height="220" viewBox="0 0 512 512">
            <text x="330" y="256" textAnchor="middle" dominantBaseline="central"
              style={{ fontFamily:"'Tajawal',sans-serif", fontWeight:900, fontSize:"220px", fill:T } as React.CSSProperties}>سـ</text>
            <text x="148" y="264" textAnchor="middle" dominantBaseline="central"
              style={{ fontFamily:"'Tajawal',sans-serif", fontWeight:300, fontSize:"140px", fill:N } as React.CSSProperties}>كون</text>
            <line x1="220" y1="60" x2="220" y2="440" stroke="#E2E8F0" strokeWidth="2"/>
          </svg>
        </LogoConcept>

        <LogoConcept n={4} name="Night Reverse" bg={N}>
          <svg width="220" height="220" viewBox="0 0 512 512">
            <text x="256" y="244" textAnchor="middle" dominantBaseline="central"
              style={{ fontFamily:"'Tajawal',sans-serif", fontWeight:900, fontSize:"186px", fill:W } as React.CSSProperties}>سكون</text>
            <rect x="176" y="330" width="160" height="10" rx="5" fill={T}/>
          </svg>
        </LogoConcept>

      </div>

      {/* Section B — Bilingual Lockup */}
      <SectionDivider id="B / 05–07" label="Bilingual Lockup" />
      <div style={{ display: "flex", gap: 20, flexWrap: "wrap" as const }}>

        <LogoConcept n={5} name="Stacked Bilingual" bg={W}>
          <svg width="220" height="220" viewBox="0 0 512 512">
            <text x="256" y="210" textAnchor="middle" dominantBaseline="central"
              style={{ fontFamily:"'Tajawal',sans-serif", fontWeight:900, fontSize:"172px", fill:N } as React.CSSProperties}>سكون</text>
            <line x1="80" y1="280" x2="432" y2="280" stroke={T} strokeWidth="3"/>
            <text x="256" y="334" textAnchor="middle"
              style={{ fontFamily:"'DM Mono',monospace", fontSize:"40px", fill:SL, letterSpacing:"14px" } as React.CSSProperties}>SOKOON</text>
            <text x="256" y="388" textAnchor="middle"
              style={{ fontFamily:"'DM Mono',monospace", fontSize:"22px", fill:`${SL}70`, letterSpacing:"5px" } as React.CSSProperties}>Real Estate</text>
          </svg>
        </LogoConcept>

        <LogoConcept n={6} name="Horizontal Split" bg={CR}>
          <svg width="220" height="220" viewBox="0 0 512 512">
            <text x="328" y="256" textAnchor="middle" dominantBaseline="central"
              style={{ fontFamily:"'Tajawal',sans-serif", fontWeight:700, fontSize:"158px", fill:T } as React.CSSProperties}>سكون</text>
            <line x1="220" y1="90" x2="220" y2="410" stroke={G} strokeWidth="3"/>
            <text x="120" y="240" textAnchor="middle"
              style={{ fontFamily:"'Inter',sans-serif", fontWeight:300, fontSize:"52px", fill:N, letterSpacing:"4px" } as React.CSSProperties}>Sokoon</text>
            <text x="120" y="298" textAnchor="middle"
              style={{ fontFamily:"'DM Mono',monospace", fontSize:"22px", fill:SL, letterSpacing:"4px" } as React.CSSProperties}>REAL ESTATE</text>
          </svg>
        </LogoConcept>

        <LogoConcept n={7} name="Asymmetric Tag" bg={W}>
          <svg width="220" height="220" viewBox="0 0 512 512">
            <text x="280" y="240" textAnchor="middle" dominantBaseline="central"
              style={{ fontFamily:"'Tajawal',sans-serif", fontWeight:900, fontSize:"188px", fill:N } as React.CSSProperties}>سكون</text>
            <line x1="50" y1="338" x2="260" y2="338" stroke={T} strokeWidth="2"/>
            <text x="155" y="376" textAnchor="middle"
              style={{ fontFamily:"'Inter',sans-serif", fontWeight:300, fontSize:"24px", fill:T, letterSpacing:"5px" } as React.CSSProperties}>Sokoon Real Estate</text>
          </svg>
        </LogoConcept>

      </div>

      {/* Section C — Icon + Wordmark */}
      <SectionDivider id="C / 08–11" label="Icon + Wordmark" />
      <div style={{ display: "flex", gap: 20, flexWrap: "wrap" as const }}>

        <LogoConcept n={8} name="House Wordmark" bg={W}>
          <svg width="220" height="220" viewBox="0 0 512 512">
            <polygon points="160,220 256,100 352,220" fill={T}/>
            <rect x="170" y="219" width="184" height="130" fill={T}/>
            <rect x="220" y="265" width="72" height="84" rx="6" fill={W}/>
            <text x="256" y="420" textAnchor="middle"
              style={{ fontFamily:"'Tajawal',sans-serif", fontWeight:900, fontSize:"88px", fill:N } as React.CSSProperties}>سكون</text>
            <text x="256" y="466" textAnchor="middle"
              style={{ fontFamily:"'DM Mono',monospace", fontSize:"20px", fill:SL, letterSpacing:"10px" } as React.CSSProperties}>SOKOON</text>
          </svg>
        </LogoConcept>

        <LogoConcept n={9} name="Arch + Wordmark" bg={CR}>
          <svg width="220" height="220" viewBox="0 0 512 512">
            <path d="M160,290 L160,180 Q160,60 256,60 Q352,60 352,180 L352,290"
              fill="none" stroke={T} strokeWidth="20" strokeLinecap="round"/>
            <line x1="120" y1="290" x2="392" y2="290" stroke={T} strokeWidth="20" strokeLinecap="round"/>
            <text x="256" y="390" textAnchor="middle"
              style={{ fontFamily:"'Tajawal',sans-serif", fontWeight:900, fontSize:"110px", fill:N } as React.CSSProperties}>سكون</text>
            <text x="256" y="448" textAnchor="middle"
              style={{ fontFamily:"'DM Mono',monospace", fontSize:"22px", fill:T, letterSpacing:"10px" } as React.CSSProperties}>SOKOON</text>
          </svg>
        </LogoConcept>

        <LogoConcept n={10} name="Pin Wordmark" bg={W}>
          <svg width="220" height="220" viewBox="0 0 512 512">
            <path d="M256,40 C188,40 120,96 120,180 C120,290 256,440 256,440 C256,440 392,290 392,180 C392,96 324,40 256,40Z" fill={T}/>
            <circle cx="256" cy="175" r="52" fill={W}/>
            <text x="256" y="488" textAnchor="middle"
              style={{ fontFamily:"'Tajawal',sans-serif", fontWeight:900, fontSize:"110px", fill:T } as React.CSSProperties}>سكون</text>
          </svg>
        </LogoConcept>

        <LogoConcept n={11} name="Key Wordmark" bg={N2}>
          <svg width="220" height="220" viewBox="0 0 512 512">
            <circle cx="180" cy="200" r="90" fill="none" stroke={G} strokeWidth="22"/>
            <circle cx="180" cy="200" r="34" fill={G}/>
            <line x1="264" y1="208" x2="460" y2="208" stroke={G} strokeWidth="22" strokeLinecap="round"/>
            <line x1="400" y1="208" x2="400" y2="268" stroke={G} strokeWidth="22" strokeLinecap="round"/>
            <line x1="446" y1="208" x2="446" y2="254" stroke={G} strokeWidth="22" strokeLinecap="round"/>
            <text x="256" y="390" textAnchor="middle"
              style={{ fontFamily:"'Tajawal',sans-serif", fontWeight:900, fontSize:"110px", fill:W } as React.CSSProperties}>سكون</text>
            <text x="256" y="448" textAnchor="middle"
              style={{ fontFamily:"'DM Mono',monospace", fontSize:"18px", fill:G, letterSpacing:"10px" } as React.CSSProperties}>SOKOON</text>
          </svg>
        </LogoConcept>

      </div>

      {/* Section D — Symbolic / Monogram */}
      <SectionDivider id="D / 12–14" label="Symbolic / Monogram" />
      <div style={{ display: "flex", gap: 20, flexWrap: "wrap" as const }}>

        <LogoConcept n={12} name="Sin Arch Mark" bg={W}>
          <svg width="220" height="220" viewBox="0 0 512 512">
            <path d="M80,400 L80,200 Q80,40 256,40 Q432,40 432,200 L432,400"
              fill="none" stroke={T} strokeWidth="28" strokeLinecap="round"/>
            <circle cx="130" cy="460" r="20" fill={T}/>
            <circle cx="256" cy="460" r="20" fill={T}/>
            <circle cx="382" cy="460" r="20" fill={T}/>
            <text x="256" y="278" textAnchor="middle"
              style={{ fontFamily:"'DM Mono',monospace", fontSize:"16px", fill:SL, letterSpacing:"7px" } as React.CSSProperties}>SOKOON</text>
          </svg>
        </LogoConcept>

        <LogoConcept n={13} name="Curved Shelter" bg={N}>
          <svg width="220" height="220" viewBox="0 0 512 512">
            <path d="M60,380 L60,220 Q60,40 256,40 Q452,40 452,220 L452,380"
              fill="none" stroke={T} strokeWidth="30" strokeLinecap="round"/>
            <line x1="20" y1="380" x2="492" y2="380" stroke={T} strokeWidth="30" strokeLinecap="round"/>
            <rect x="206" y="380" width="100" height="100" fill={T}/>
            <path d="M206,380 Q256,320 306,380Z" fill={T}/>
            <text x="256" y="500" textAnchor="middle"
              style={{ fontFamily:"'Tajawal',sans-serif", fontWeight:700, fontSize:"60px", fill:W } as React.CSSProperties}>سكون</text>
          </svg>
        </LogoConcept>

        <LogoConcept n={14} name="Gold Home Lines" bg="#0A1520">
          <svg width="220" height="220" viewBox="0 0 512 512">
            <polyline points="50,280 256,80 462,280"
              fill="none" stroke={G} strokeWidth="22" strokeLinecap="round" strokeLinejoin="round"/>
            <polyline points="110,280 110,440 402,440 402,280"
              fill="none" stroke={G} strokeWidth="22" strokeLinecap="round" strokeLinejoin="round"/>
            <rect x="206" y="320" width="100" height="120" rx="4"
              fill="none" stroke={G} strokeWidth="22"/>
            <text x="256" y="496" textAnchor="middle"
              style={{ fontFamily:"'Tajawal',sans-serif", fontWeight:900, fontSize:"68px", fill:G } as React.CSSProperties}>سكون</text>
          </svg>
        </LogoConcept>

      </div>

      {/* Section E — Badge / Framed */}
      <SectionDivider id="E / 15–17" label="Badge / Framed" />
      <div style={{ display: "flex", gap: 20, flexWrap: "wrap" as const }}>

        <LogoConcept n={15} name="Oval Frame" bg={W}>
          <svg width="220" height="220" viewBox="0 0 512 512">
            <ellipse cx="256" cy="256" rx="228" ry="130" fill="none" stroke={T} strokeWidth="5"/>
            <ellipse cx="256" cy="256" rx="240" ry="142" fill="none" stroke={T} strokeWidth="2" opacity="0.2"/>
            <text x="256" y="256" textAnchor="middle" dominantBaseline="central"
              style={{ fontFamily:"'Tajawal',sans-serif", fontWeight:900, fontSize:"148px", fill:N } as React.CSSProperties}>سكون</text>
            <text x="256" y="366" textAnchor="middle"
              style={{ fontFamily:"'DM Mono',monospace", fontSize:"20px", fill:T, letterSpacing:"14px" } as React.CSSProperties}>SOKOON</text>
          </svg>
        </LogoConcept>

        <LogoConcept n={16} name="Corner Brackets" bg={CR}>
          <svg width="220" height="220" viewBox="0 0 512 512">
            <path d="M60,20 L20,20 L20,60" fill="none" stroke={G} strokeWidth="12" strokeLinecap="round"/>
            <path d="M452,20 L492,20 L492,60" fill="none" stroke={G} strokeWidth="12" strokeLinecap="round"/>
            <path d="M20,452 L20,492 L60,492" fill="none" stroke={G} strokeWidth="12" strokeLinecap="round"/>
            <path d="M452,492 L492,492 L492,452" fill="none" stroke={G} strokeWidth="12" strokeLinecap="round"/>
            <text x="256" y="256" textAnchor="middle" dominantBaseline="central"
              style={{ fontFamily:"'Tajawal',sans-serif", fontWeight:900, fontSize:"168px", fill:N } as React.CSSProperties}>سكون</text>
            <line x1="140" y1="320" x2="372" y2="320" stroke={G} strokeWidth="3"/>
            <text x="256" y="368" textAnchor="middle"
              style={{ fontFamily:"'DM Mono',monospace", fontSize:"26px", fill:G, letterSpacing:"12px" } as React.CSSProperties}>SOKOON</text>
          </svg>
        </LogoConcept>

        <LogoConcept n={17} name="Circular Seal" bg={N}>
          <svg width="220" height="220" viewBox="0 0 512 512">
            <circle cx="256" cy="256" r="230" fill="none" stroke={G} strokeWidth="5"/>
            <circle cx="256" cy="256" r="198" fill="none" stroke={G} strokeWidth="1.5" opacity="0.3"/>
            <defs>
              <path id="sealR17" d="M256,256 m-172,0 a172,172 0 1,1 344,0 a172,172 0 1,1 -344,0"/>
            </defs>
            <text style={{ fontFamily:"'DM Mono',monospace", fontSize:"22px", fill:G, letterSpacing:"8px" } as React.CSSProperties}>
              <textPath href="#sealR17" startOffset="0%">
                SOKOON REAL ESTATE · سكون للعقارات ·
              </textPath>
            </text>
            <text x="256" y="256" textAnchor="middle" dominantBaseline="central"
              style={{ fontFamily:"'Tajawal',sans-serif", fontWeight:900, fontSize:"148px", fill:W } as React.CSSProperties}>سكون</text>
          </svg>
        </LogoConcept>

      </div>

      {/* Section F — App Icon */}
      <SectionDivider id="F / 18–20" label="App Icon · 512×512" />
      <div style={{ display: "flex", gap: 20, flexWrap: "wrap" as const }}>

        <LogoConcept n={18} name="App — Teal House" bg={T}>
          <svg width="220" height="220" viewBox="0 0 512 512">
            <defs>
              <linearGradient id="lc18" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor={T2}/><stop offset="100%" stopColor={T3}/>
              </linearGradient>
            </defs>
            <rect width="512" height="512" fill="url(#lc18)"/>
            <ellipse cx="256" cy="60" rx="240" ry="80" fill={W} opacity="0.07"/>
            <polygon points="256,100 390,210 122,210" fill={W} opacity="0.94"/>
            <rect x="136" y="208" width="240" height="160" rx="8" fill={W} opacity="0.94"/>
            <rect x="200" y="240" width="112" height="128" rx="8" fill={T3} opacity="0.45"/>
            <text x="256" y="432" textAnchor="middle"
              style={{ fontFamily:"'Tajawal',sans-serif", fontWeight:900, fontSize:"76px", fill:W } as React.CSSProperties}>سكون</text>
            <text x="256" y="484" textAnchor="middle"
              style={{ fontFamily:"'DM Mono',monospace", fontSize:"18px", fill:`${W}60`, letterSpacing:"6px" } as React.CSSProperties}>SOKOON</text>
          </svg>
        </LogoConcept>

        <LogoConcept n={19} name="App — Navy Gold" bg={N}>
          <svg width="220" height="220" viewBox="0 0 512 512">
            <defs>
              <linearGradient id="lc19" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor={N}/><stop offset="100%" stopColor={N2}/>
              </linearGradient>
            </defs>
            <rect width="512" height="512" fill="url(#lc19)"/>
            <path d="M120,350 L120,230 Q120,80 256,80 Q392,80 392,230 L392,350"
              fill="none" stroke={G} strokeWidth="28" strokeLinecap="round"/>
            <circle cx="175" cy="410" r="16" fill={G}/>
            <circle cx="256" cy="410" r="16" fill={G}/>
            <circle cx="337" cy="410" r="16" fill={G}/>
            <text x="256" y="496" textAnchor="middle"
              style={{ fontFamily:"'Tajawal',sans-serif", fontWeight:700, fontSize:"64px", fill:G } as React.CSSProperties}>سكون</text>
          </svg>
        </LogoConcept>

        <LogoConcept n={20} name="App — Cream Minimal" bg={CR}>
          <svg width="220" height="220" viewBox="0 0 512 512">
            <text x="256" y="272" textAnchor="middle" dominantBaseline="central"
              style={{ fontFamily:"'Tajawal',sans-serif", fontWeight:900, fontSize:"196px", fill:N } as React.CSSProperties}>سكون</text>
            <rect x="168" y="348" width="176" height="10" rx="5" fill={G}/>
            <text x="256" y="412" textAnchor="middle"
              style={{ fontFamily:"'DM Mono',monospace", fontSize:"24px", fill:N, letterSpacing:"10px" } as React.CSSProperties}>SOKOON</text>
          </svg>
        </LogoConcept>

      </div>

    </div>
  );
}
