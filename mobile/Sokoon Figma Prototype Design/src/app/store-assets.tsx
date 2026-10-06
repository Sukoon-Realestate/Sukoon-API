import React from "react";

const TEAL  = "#0F766E";
const TEAL2 = "#0D9488";
const TEAL3 = "#134E4A";
const NAVY  = "#0B1628";
const GOLD  = "#D4A84B";
const CREAM = "#F8F4EF";
const WHITE = "#FFFFFF";
const SLATE = "#64748B";

const TJ   = { fontFamily: "'Tajawal', sans-serif" } as React.CSSProperties;
const MONO = { fontFamily: "'DM Mono', monospace" } as React.CSSProperties;
const INT  = { fontFamily: "'Inter', sans-serif" } as React.CSSProperties;

// ─── App Icon — master & size grid ────────────────────────────────────

function AppIconSvg({ size, bg = TEAL, style }: { size: number; bg?: string; style?: React.CSSProperties }) {
  const r = size * 0.22;
  return (
    <svg width={size} height={size} viewBox="0 0 100 100" style={{ borderRadius: r, display: "block", flexShrink: 0, ...style }}>
      <defs>
        <linearGradient id={`iconGrad${size}`} x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor={bg === TEAL ? TEAL2 : bg} />
          <stop offset="100%" stopColor={bg === TEAL ? TEAL3 : NAVY} />
        </linearGradient>
      </defs>
      <rect x="0" y="0" width="100" height="100" fill={`url(#iconGrad${size})`} />
      {/* Subtle top glow */}
      <ellipse cx="50" cy="10" rx="45" ry="22" fill={WHITE} opacity="0.07" />
      {/* House shape */}
      <polygon points="50,18 78,38 22,38" fill={WHITE} opacity="0.92" />
      <rect x="26" y="37" width="48" height="30" rx="2" fill={WHITE} opacity="0.92" />
      <rect x="40" y="47" width="20" height="20" rx="3" fill={bg === TEAL ? TEAL3 : NAVY} opacity="0.5" />
      {/* Brand text */}
      <text x="50" y="86" textAnchor="middle"
        style={{ fontFamily: "'Tajawal',sans-serif", fontWeight: 900, fontSize: "13px", fill: WHITE, opacity: 0.9 } as React.CSSProperties}>
        سكون
      </text>
    </svg>
  );
}

function AssetLabel({ title, sub }: { title: string; sub?: string }) {
  return (
    <div style={{ marginTop: 10 }}>
      <div style={{ fontSize: 12, fontWeight: 600, color: WHITE, ...INT }}>{title}</div>
      {sub && <div style={{ fontSize: 10, color: SLATE, marginTop: 2, ...MONO }}>{sub}</div>}
    </div>
  );
}

function SectionDivider({ label }: { label: string }) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 16, marginBottom: 28, marginTop: 8 }}>
      <span style={{ fontSize: 9, color: GOLD, letterSpacing: 4, ...MONO }}>{label}</span>
      <div style={{ flex: 1, height: 1, background: `linear-gradient(90deg, ${GOLD}30, transparent)` }} />
    </div>
  );
}

// ─── iOS Screenshot marketing frames ─────────────────────────────────

function IosScreenshot({
  title, subtitle, tag, screenBg = TEAL, children
}: {
  title: string; subtitle: string; tag: string; screenBg?: string; children: React.ReactNode;
}) {
  return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", flexShrink: 0 }}>
      {/* Outer device frame */}
      <div style={{
        width: 200, height: 390, borderRadius: 36,
        background: "#1A1A1C",
        boxShadow: "0 0 0 2px #3A3A3C, 0 20px 60px rgba(0,0,0,0.7), inset 0 0 0 1px rgba(255,255,255,0.06)",
        padding: 8, position: "relative", flexShrink: 0
      }}>
        {/* Screen */}
        <div style={{
          width: "100%", height: "100%", borderRadius: 28,
          background: screenBg, overflow: "hidden", position: "relative"
        }}>
          {/* Status bar */}
          <div style={{ height: 28, display: "flex", alignItems: "center", justifyContent: "space-between", padding: "0 18px 0 14px" }}>
            <span style={{ fontSize: 9, fontWeight: 700, color: screenBg === WHITE || screenBg === CREAM ? NAVY : WHITE, ...INT }}>9:41</span>
            <div style={{ display: "flex", gap: 4, alignItems: "center" }}>
              <div style={{ width: 12, height: 8, borderRadius: 1.5, border: `1.5px solid ${screenBg === WHITE || screenBg === CREAM ? NAVY : WHITE}`, opacity: 0.7 }}>
                <div style={{ width: "70%", height: "100%", background: screenBg === WHITE || screenBg === CREAM ? NAVY : WHITE, borderRadius: 1 }} />
              </div>
              <div style={{ width: 10, height: 10, opacity: 0.6 }}>
                <svg viewBox="0 0 10 10"><path d="M1,5 C1,2.8 2.8,1 5,1 C7.2,1 9,2.8 9,5" stroke={screenBg === WHITE || screenBg === CREAM ? NAVY : WHITE} strokeWidth="1.5" fill="none" /></svg>
              </div>
            </div>
          </div>
          {/* Dynamic island */}
          <div style={{ width: 60, height: 14, background: "#1A1A1C", borderRadius: 7, margin: "0 auto 4px", display: "block" }} />
          {/* Screen content */}
          {children}
        </div>
      </div>
      {/* Caption below device */}
      <div style={{ textAlign: "center", marginTop: 18, maxWidth: 200 }}>
        <div style={{ fontSize: 12, fontWeight: 700, color: WHITE, lineHeight: 1.3, ...TJ }}>{title}</div>
        <div style={{ fontSize: 10, color: SLATE, marginTop: 4, lineHeight: 1.4, ...TJ }}>{subtitle}</div>
        <div style={{ fontSize: 8, color: GOLD, letterSpacing: 3, marginTop: 6, ...MONO }}>{tag}</div>
      </div>
    </div>
  );
}

// Screen content helpers
function SearchScreenContent() {
  return (
    <div style={{ padding: "4px 10px", flex: 1 }}>
      <div style={{ fontSize: 13, fontWeight: 900, color: WHITE, ...TJ, marginBottom: 8 }}>اكتشف عقارك</div>
      <div style={{ background: "rgba(255,255,255,0.15)", borderRadius: 12, padding: "8px 12px", display: "flex", alignItems: "center", gap: 6, marginBottom: 10 }}>
        <span style={{ fontSize: 10 }}>🔍</span>
        <span style={{ fontSize: 10, color: "rgba(255,255,255,0.6)", ...TJ }}>ابحث في المدن والمناطق...</span>
      </div>
      {[
        { type: "شقة مفروشة", loc: "مدينة نصر", price: "٣٥٠٠", badge: true },
        { type: "ستوديو", loc: "المعادي", price: "٢٢٠٠", badge: false },
        { type: "غرفة مفردة", loc: "الزمالك", price: "١٨٠٠", badge: true },
      ].map((p, i) => (
        <div key={i} style={{ background: "rgba(255,255,255,0.1)", borderRadius: 12, padding: "8px 10px", marginBottom: 6 }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <span style={{ fontSize: 11, fontWeight: 700, color: WHITE, ...TJ }}>{p.type}</span>
            {p.badge && <span style={{ fontSize: 8, background: TEAL, color: WHITE, padding: "2px 7px", borderRadius: 10, ...TJ }}>موثّق ✓</span>}
          </div>
          <div style={{ fontSize: 9, color: "rgba(255,255,255,0.6)", ...TJ, marginTop: 2 }}>{p.loc}</div>
          <div style={{ fontSize: 10, fontWeight: 700, color: GOLD, marginTop: 4, ...TJ }}>{p.price} ر.س/شهر</div>
        </div>
      ))}
    </div>
  );
}

function DetailScreenContent() {
  return (
    <div style={{ flex: 1, background: WHITE }}>
      {/* Property image area */}
      <div style={{ height: 100, background: `linear-gradient(135deg, ${TEAL3}, ${NAVY})`, position: "relative" }}>
        <div style={{ position: "absolute", top: 8, right: 10, background: TEAL, borderRadius: 10, padding: "3px 8px" }}>
          <span style={{ fontSize: 8, color: WHITE, fontWeight: 700, ...TJ }}>موثّق ✓</span>
        </div>
        <div style={{ position: "absolute", bottom: 8, left: 10, display: "flex", gap: 4 }}>
          {[TEAL, GOLD, "#E2E8F0"].map((c, i) => (
            <div key={i} style={{ width: 24, height: 18, borderRadius: 5, background: c, opacity: 0.6 }} />
          ))}
          <div style={{ width: 24, height: 18, borderRadius: 5, background: "rgba(0,0,0,0.3)", display: "flex", alignItems: "center", justifyContent: "center" }}>
            <span style={{ fontSize: 7, color: WHITE }}>+٤</span>
          </div>
        </div>
      </div>
      <div style={{ padding: "8px 10px" }}>
        <div style={{ fontSize: 12, fontWeight: 900, color: NAVY, ...TJ }}>شقة مفروشة — مدينة نصر</div>
        <div style={{ fontSize: 13, fontWeight: 700, color: TEAL, marginTop: 3, ...TJ }}>٣٥٠٠ ر.س / شهر</div>
        <div style={{ display: "flex", gap: 6, marginTop: 6 }}>
          {["٣ غرف", "٢ حمام", "١٢٠م²"].map(s => (
            <span key={s} style={{ fontSize: 8, background: "#F1F5F9", color: NAVY, padding: "3px 7px", borderRadius: 8, ...TJ }}>{s}</span>
          ))}
        </div>
        <div style={{ marginTop: 8, display: "flex", gap: 5 }}>
          {["مفروشة", "أسانسير", "WiFi"].map(s => (
            <span key={s} style={{ fontSize: 7.5, background: `${TEAL}15`, color: TEAL, padding: "2px 6px", borderRadius: 8, ...TJ }}>{s}</span>
          ))}
        </div>
        <div style={{ marginTop: 8, background: "#F0FDF9", borderRadius: 10, padding: "6px 8px", display: "flex", alignItems: "center", gap: 5 }}>
          <span style={{ fontSize: 9 }}>✅</span>
          <span style={{ fontSize: 8, color: TEAL3, fontWeight: 600, ...TJ }}>تم التحقق من إثبات الملكية</span>
        </div>
        <div style={{ marginTop: 8, background: TEAL, borderRadius: 12, padding: "7px", textAlign: "center" }}>
          <span style={{ fontSize: 10, color: WHITE, fontWeight: 700, ...TJ }}>احجز زيارة</span>
        </div>
      </div>
    </div>
  );
}

function FilterScreenContent() {
  return (
    <div style={{ flex: 1, background: WHITE, padding: "8px 10px" }}>
      <div style={{ fontSize: 12, fontWeight: 900, color: NAVY, ...TJ, marginBottom: 10 }}>فلاتر البحث</div>
      {[
        { label: "نوع العقار", chips: ["شقة", "ستوديو", "غرفة"], active: 0 },
        { label: "فترة التأجير", chips: ["شهري", "سنوي", "يومي"], active: 0 },
        { label: "مناسب لـ", chips: ["عائلات", "أفراد", "مشاركة"], active: 0 },
      ].map((f, fi) => (
        <div key={fi} style={{ marginBottom: 10 }}>
          <div style={{ fontSize: 9, color: SLATE, marginBottom: 5, ...TJ }}>{f.label}</div>
          <div style={{ display: "flex", gap: 5, flexWrap: "wrap" }}>
            {f.chips.map((c, ci) => (
              <span key={ci} style={{
                fontSize: 8.5, padding: "4px 10px", borderRadius: 16,
                background: ci === f.active ? TEAL : "#F1F5F9",
                color: ci === f.active ? WHITE : NAVY, ...TJ
              }}>{c}</span>
            ))}
          </div>
        </div>
      ))}
      <div style={{ fontSize: 9, color: SLATE, marginBottom: 5, ...TJ }}>المرافق</div>
      <div style={{ display: "flex", gap: 5, flexWrap: "wrap" }}>
        {["WiFi", "أسانسير", "بلكونة", "تكييف"].map((a, i) => (
          <span key={a} style={{ fontSize: 8, padding: "3px 8px", borderRadius: 12, background: i < 2 ? `${TEAL}15` : "#F1F5F9", color: i < 2 ? TEAL : SLATE, border: i < 2 ? `1px solid ${TEAL}30` : "none", ...TJ }}>{a}</span>
        ))}
      </div>
      <div style={{ marginTop: 10, background: TEAL, borderRadius: 12, padding: "7px", textAlign: "center" }}>
        <span style={{ fontSize: 10, color: WHITE, fontWeight: 700, ...TJ }}>عرض ٢٤ عقار</span>
      </div>
    </div>
  );
}

function OnboardingScreenContent() {
  return (
    <div style={{ flex: 1, background: `linear-gradient(170deg, ${TEAL3} 0%, ${NAVY} 100%)`, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", padding: "20px 16px" }}>
      <svg width="64" height="54" viewBox="0 0 64 54" style={{ marginBottom: 12 }}>
        <polygon points="32,4 58,24 6,24" fill={WHITE} opacity="0.9" />
        <rect x="10" y="23" width="44" height="26" rx="3" fill={WHITE} opacity="0.9" />
        <rect x="23" y="31" width="18" height="18" rx="2" fill={TEAL} opacity="0.5" />
      </svg>
      <div style={{ fontSize: 20, fontWeight: 900, color: WHITE, ...TJ, marginBottom: 6, textAlign: "center" }}>أهلاً بك في سكون</div>
      <div style={{ fontSize: 10, color: "rgba(255,255,255,0.65)", ...TJ, textAlign: "center", lineHeight: 1.5, marginBottom: 16 }}>
        ابحث عن مسكنك المثالي بين آلاف العقارات الموثّقة
      </div>
      <div style={{ display: "flex", gap: 5, marginBottom: 16 }}>
        {[0,1,2].map(i => <div key={i} style={{ width: i === 0 ? 20 : 6, height: 6, borderRadius: 3, background: i === 0 ? WHITE : "rgba(255,255,255,0.3)" }} />)}
      </div>
      <div style={{ background: GOLD, borderRadius: 16, padding: "8px 24px" }}>
        <span style={{ fontSize: 11, fontWeight: 700, color: NAVY, ...TJ }}>ابدأ الآن</span>
      </div>
    </div>
  );
}

// ─── Feature Graphic (wide, Play Store / Banner) ─────────────────────

function FeatureGraphic({ variant = "teal" }: { variant?: "teal" | "navy" | "gold" }) {
  const bgs: Record<string, [string, string]> = {
    teal:  [TEAL2, TEAL3],
    navy:  [NAVY, "#0A1E38"],
    gold:  [TEAL3, NAVY],
  };
  const [c1, c2] = bgs[variant];

  return (
    <div style={{
      width: 520, height: 254, borderRadius: 20, overflow: "hidden", flexShrink: 0,
      boxShadow: "0 8px 40px rgba(0,0,0,0.6), 0 0 0 1px rgba(255,255,255,0.05)",
      position: "relative", background: `linear-gradient(135deg, ${c1}, ${c2})`
    }}>
      <svg style={{ position: "absolute", inset: 0 }} width="520" height="254" viewBox="0 0 520 254">
        {/* Background pattern circles */}
        <circle cx="440" cy="50" r="140" fill={WHITE} opacity="0.04" />
        <circle cx="440" cy="50" r="90" fill={WHITE} opacity="0.04" />
        {/* Horizontal rules */}
        {[60, 190].map(y => <line key={y} x1="0" y1={y} x2="520" y2={y} stroke={WHITE} strokeWidth="0.5" opacity="0.06" />)}

        {/* App icon area left */}
        <rect x="30" y="62" width="110" height="110" rx="28" fill={WHITE} opacity="0.1" />
        <polygon points="85,78 112,100 58,100" fill={WHITE} opacity="0.9" />
        <rect x="62" y="99" width="46" height="32" rx="3" fill={WHITE} opacity="0.9" />
        <rect x="74" y="107" width="22" height="24" rx="2" fill={c2} opacity="0.4" />

        {/* Brand text */}
        <text x="156" y="96" textAnchor="start"
          style={{ fontFamily: "'Tajawal',sans-serif", fontWeight: 900, fontSize: "42px", fill: WHITE } as React.CSSProperties}>
          سكون
        </text>
        <text x="156" y="118" textAnchor="start"
          style={{ fontFamily: "'DM Mono',monospace", fontWeight: 300, fontSize: "10px", fill: `${WHITE}60`, letterSpacing: "5px" } as React.CSSProperties}>
          SOKOON PLATFORM
        </text>
        <text x="156" y="144" textAnchor="start"
          style={{ fontFamily: "'Tajawal',sans-serif", fontWeight: 300, fontSize: "13px", fill: `${WHITE}80` } as React.CSSProperties}>
          {variant === "gold" ? "منصة العقارات الأولى في المنطقة" : "ابحث · تحقق · انتقل"}
        </text>

        {/* Feature pills */}
        {["عقارات موثّقة", "بحث ذكي", "خصوصية تامة"].map((f, i) => (
          <g key={f}>
            <rect x={156 + i * 110} y="162" width="100" height="24" rx="12"
              fill={WHITE} opacity="0.12" />
            <text x={206 + i * 110} y="178" textAnchor="middle"
              style={{ fontFamily: "'Tajawal',sans-serif", fontWeight: 500, fontSize: "10px", fill: WHITE } as React.CSSProperties}>
              {f}
            </text>
          </g>
        ))}

        {/* Gold accent rule */}
        <line x1="30" y1="195" x2="130" y2="195" stroke={GOLD} strokeWidth="1.5" strokeLinecap="round" />
        <text x="30" y="216" textAnchor="start"
          style={{ fontFamily: "'DM Mono',monospace", fontWeight: 300, fontSize: "8.5px", fill: `${WHITE}35`, letterSpacing: "3px" } as React.CSSProperties}>
          {variant === "teal" ? "APP STORE · GOOGLE PLAY" : variant === "navy" ? "2024 · TRUSTED PLATFORM" : "VERIFIED · SECURE · FAST"}
        </text>
      </svg>
    </div>
  );
}

// ─── App Icon grid ────────────────────────────────────────────────────

function AppIconGrid() {
  const sizes = [
    { px: 1024, label: "1024×1024", desc: "App Store Master" },
    { px: 180, label: "180×180", desc: "iOS @3x" },
    { px: 120, label: "120×120", desc: "iOS @2x" },
    { px: 76, label: "76×76", desc: "iPad" },
    { px: 60, label: "60×60", desc: "iPhone" },
    { px: 29, label: "29×29", desc: "Settings" },
  ];
  const display = [148, 100, 72, 56, 44, 30];
  return (
    <div style={{ display: "flex", gap: 20, flexWrap: "wrap", alignItems: "flex-end" }}>
      {sizes.map((s, i) => (
        <div key={s.px} style={{ display: "flex", flexDirection: "column", alignItems: "center" }}>
          <AppIconSvg size={display[i]} />
          <div style={{ marginTop: 8, textAlign: "center" }}>
            <div style={{ fontSize: 9, color: WHITE, ...MONO }}>{s.label}</div>
            <div style={{ fontSize: 8.5, color: SLATE, marginTop: 2, ...INT }}>{s.desc}</div>
          </div>
        </div>
      ))}
    </div>
  );
}

// ─── Main export ──────────────────────────────────────────────────────

export function StoreAssetsBoard() {
  return (
    <div style={{ padding: "0 0 40px" }}>

      {/* App Icons */}
      <SectionDivider label="01 / APP ICON — All Sizes" />
      <div style={{ marginBottom: 48 }}>
        <AppIconGrid />
        <div style={{ marginTop: 24, display: "flex", gap: 16 }}>
          {[TEAL, NAVY, "#2D6A4F"].map((bg, i) => (
            <div key={i}>
              <AppIconSvg size={80} bg={bg} />
              <div style={{ fontSize: 8.5, color: SLATE, marginTop: 6, textAlign: "center", ...MONO }}>
                {["Teal", "Navy", "Forest"][i]}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Feature Graphics */}
      <SectionDivider label="02 / FEATURE GRAPHIC — Google Play / Stores (1024×500)" />
      <div style={{ display: "flex", gap: 22, flexWrap: "wrap", marginBottom: 48 }}>
        <div>
          <FeatureGraphic variant="teal" />
          <AssetLabel title="Teal Primary" sub="1024 × 500 · Google Play Feature Graphic" />
        </div>
        <div>
          <FeatureGraphic variant="navy" />
          <AssetLabel title="Navy Dark" sub="1024 × 500 · Alternate" />
        </div>
      </div>

      {/* iOS Screenshots */}
      <SectionDivider label="03 / iOS APP STORE SCREENSHOTS — 6.7 inch (1290×2796)" />
      <div style={{ display: "flex", gap: 24, flexWrap: "wrap", marginBottom: 48 }}>
        <IosScreenshot
          title="اكتشف آلاف العقارات"
          subtitle="نتائج موثّقة ومرتّبة حسب احتياجك"
          tag="SCREENSHOT 1 OF 5"
          screenBg={TEAL}
        >
          <SearchScreenContent />
        </IosScreenshot>

        <IosScreenshot
          title="تفاصيل كاملة وشفافة"
          subtitle="كل ما تحتاج معرفته في شاشة واحدة"
          tag="SCREENSHOT 2 OF 5"
          screenBg={WHITE}
        >
          <DetailScreenContent />
        </IosScreenshot>

        <IosScreenshot
          title="فلتر دقيق، نتائج مثالية"
          subtitle="١٣ فئة لتضبط بحثك بدقة"
          tag="SCREENSHOT 3 OF 5"
          screenBg={WHITE}
        >
          <FilterScreenContent />
        </IosScreenshot>

        <IosScreenshot
          title="انطلق في رحلتك السكنية"
          subtitle="تجربة أولى سلسة وودودة"
          tag="SCREENSHOT 4 OF 5"
          screenBg={TEAL3}
        >
          <OnboardingScreenContent />
        </IosScreenshot>
      </div>

      {/* Google Play Screenshots */}
      <SectionDivider label="04 / GOOGLE PLAY SCREENSHOTS — Android (1080×1920)" />
      <div style={{ display: "flex", gap: 24, flexWrap: "wrap", marginBottom: 48 }}>
        {[
          { title: "ابحث بذكاء", sub: "مئات العقارات المصنّفة", tag: "ANDROID · 01" },
          { title: "ملف عقار كامل", sub: "شفافية تامة مع الموثّقين", tag: "ANDROID · 02" },
          { title: "فلاتر احترافية", sub: "١٣ خاصية للتصفية", tag: "ANDROID · 03" },
        ].map((s, i) => (
          <IosScreenshot key={i}
            title={s.title}
            subtitle={s.sub}
            tag={s.tag}
            screenBg={i === 0 ? TEAL : WHITE}
          >
            {i === 0 ? <SearchScreenContent /> : i === 1 ? <DetailScreenContent /> : <FilterScreenContent />}
          </IosScreenshot>
        ))}
      </div>

      {/* Promo Banner set */}
      <SectionDivider label="05 / PROMOTIONAL BANNERS — Social & Web" />
      <div style={{ display: "flex", gap: 20, flexWrap: "wrap" }}>
        {/* Wide banner */}
        <div>
          <div style={{
            width: 520, height: 130, borderRadius: 18, overflow: "hidden", flexShrink: 0,
            background: `linear-gradient(135deg, ${TEAL3}, ${NAVY})`,
            boxShadow: "0 4px 30px rgba(0,0,0,0.5), 0 0 0 1px rgba(255,255,255,0.04)",
            position: "relative"
          }}>
            <svg style={{ position: "absolute", inset: 0 }} width="520" height="130" viewBox="0 0 520 130">
              <circle cx="460" cy="65" r="90" fill={WHITE} opacity="0.03" />
              <text x="30" y="52" textAnchor="start"
                style={{ fontFamily: "'Tajawal',sans-serif", fontWeight: 900, fontSize: "32px", fill: WHITE } as React.CSSProperties}>
                سكون
              </text>
              <text x="30" y="76" textAnchor="start"
                style={{ fontFamily: "'Tajawal',sans-serif", fontWeight: 300, fontSize: "13px", fill: `${WHITE}70` } as React.CSSProperties}>
                منصة العقارات الأولى · ابحث وتحقق وانتقل
              </text>
              <rect x="30" y="92" width="116" height="26" rx="13" fill={GOLD} />
              <text x="88" y="109" textAnchor="middle"
                style={{ fontFamily: "'Tajawal',sans-serif", fontWeight: 700, fontSize: "11px", fill: NAVY } as React.CSSProperties}>
                ابدأ البحث مجاناً
              </text>
              <text x="490" y="72" textAnchor="end"
                style={{ fontFamily: "'DM Mono',monospace", fontWeight: 300, fontSize: "8.5px", fill: `${WHITE}25`, letterSpacing: "3px" } as React.CSSProperties}>
                SOKOON.COM
              </text>
            </svg>
          </div>
          <AssetLabel title="Wide Banner" sub="1040×260 px · Web / Email Header" />
        </div>

        {/* Square social */}
        <div>
          <div style={{
            width: 190, height: 190, borderRadius: 18, overflow: "hidden", flexShrink: 0,
            background: TEAL,
            boxShadow: "0 4px 30px rgba(0,0,0,0.5)",
            position: "relative"
          }}>
            <svg style={{ position: "absolute", inset: 0 }} width="190" height="190" viewBox="0 0 190 190">
              <circle cx="145" cy="50" r="75" fill={WHITE} opacity="0.05" />
              <text x="95" y="85" textAnchor="middle"
                style={{ fontFamily: "'Tajawal',sans-serif", fontWeight: 900, fontSize: "54px", fill: WHITE } as React.CSSProperties}>
                سكون
              </text>
              <rect x="60" y="104" width="70" height="3" rx="1.5" fill={GOLD} />
              <text x="95" y="126" textAnchor="middle"
                style={{ fontFamily: "'DM Mono',monospace", fontWeight: 300, fontSize: "8px", fill: `${WHITE}70`, letterSpacing: "4px" } as React.CSSProperties}>
                SOKOON
              </text>
              <text x="95" y="155" textAnchor="middle"
                style={{ fontFamily: "'Tajawal',sans-serif", fontWeight: 300, fontSize: "9px", fill: `${WHITE}50` } as React.CSSProperties}>
                منصة العقارات
              </text>
            </svg>
          </div>
          <AssetLabel title="Square Social" sub="1080×1080 · Instagram / Twitter" />
        </div>

        {/* Story vertical */}
        <div>
          <div style={{
            width: 110, height: 190, borderRadius: 18, overflow: "hidden", flexShrink: 0,
            background: `linear-gradient(170deg, ${TEAL2}, ${TEAL3} 50%, ${NAVY})`,
            boxShadow: "0 4px 30px rgba(0,0,0,0.5)",
            position: "relative"
          }}>
            <svg style={{ position: "absolute", inset: 0 }} width="110" height="190" viewBox="0 0 110 190">
              <circle cx="55" cy="55" r="36" fill={WHITE} opacity="0.08" />
              <polygon points="55,28 72,44 38,44" fill={WHITE} opacity="0.85" />
              <rect x="40" y="43" width="30" height="20" rx="2" fill={WHITE} opacity="0.85" />
              <rect x="48" y="49" width="14" height="14" rx="1.5" fill={TEAL3} opacity="0.5" />
              <text x="55" y="100" textAnchor="middle"
                style={{ fontFamily: "'Tajawal',sans-serif", fontWeight: 900, fontSize: "22px", fill: WHITE } as React.CSSProperties}>
                سكون
              </text>
              <text x="55" y="118" textAnchor="middle"
                style={{ fontFamily: "'DM Mono',monospace", fontSize: "6px", fill: `${WHITE}50`, letterSpacing: "3px" } as React.CSSProperties}>
                SOKOON
              </text>
              <rect x="18" y="150" width="74" height="22" rx="11" fill={GOLD} />
              <text x="55" y="165" textAnchor="middle"
                style={{ fontFamily: "'Tajawal',sans-serif", fontWeight: 700, fontSize: "9px", fill: NAVY } as React.CSSProperties}>
                ابدأ الآن
              </text>
            </svg>
          </div>
          <AssetLabel title="Story / Reel" sub="1080×1920 · Vertical" />
        </div>
      </div>

    </div>
  );
}
