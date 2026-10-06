import React, { useState, useEffect, useRef } from "react";

// ── Design tokens ────────────────────────────────────────────────────────
const TEAL   = "#0F766E";
const TEAL_D = "#0B5E57";
const TEAL_L = "#CCFBF1";
const NAVY   = "#111827";
const GOLD   = "#D6A84F";
const BLUE   = "#2563EB";
const GREEN  = "#22C55E";
const ROSE   = "#E11D48";
const BG     = "#FAFAF8";
const WHITE  = "#FFFFFF";
const BORDER = "#EEF0F3";
const SUB    = "#6B7280";
const TJ: React.CSSProperties = { fontFamily: "Tajawal, sans-serif" };

// ── Sokoon Logo ─────────────────────────────────────────────────────────
function SokoonLogo({ size = 36, color = WHITE }: { size?: number; color?: string }) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
      <div style={{ width: size, height: size, borderRadius: size * 0.38, background: TEAL, display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
        <svg width={size * 0.7} height={size * 0.7} viewBox="0 0 18 18" fill="none">
          <path d="M9,2 L16,8 L14,8 L14,16 L4,16 L4,8 L2,8 Z" fill="white" />
          <rect x="5.5" y="10" width="2.5" height="2" rx="0.7" fill={TEAL} />
          <rect x="10" y="10" width="2.5" height="2" rx="0.7" fill={TEAL} />
          <path d="M7,16 L7,13 Q9,11.5 11,13 L11,16 Z" fill={TEAL} />
        </svg>
      </div>
      <div style={{ lineHeight: 1 }}>
        <div style={{ fontSize: size * 0.56, fontWeight: 900, color: NAVY, letterSpacing: -0.3, ...TJ }}>سكون</div>
        <div style={{ fontSize: size * 0.33, fontWeight: 600, color: SUB, letterSpacing: 0.5 }}>Sokoon</div>
      </div>
    </div>
  );
}

// ── Phone Mockup (inline SVG screens) ──────────────────────────────────
function PhoneMockup({ variant, scale = 1 }: { variant: "tenant" | "owner"; scale?: number }) {
  const W = 280, H = 580;
  const iW = 252, iH = 520;
  return (
    <div style={{
      width: W * scale, height: H * scale, flexShrink: 0,
      background: "#111113", borderRadius: 42 * scale,
      boxShadow: `0 0 0 ${2 * scale}px #3A3A3C, 0 0 0 ${3.5 * scale}px #222, 0 ${24 * scale}px ${70 * scale}px rgba(0,0,0,0.55)`,
      display: "flex", flexDirection: "column", alignItems: "center",
      padding: `${14 * scale}px ${14 * scale}px ${18 * scale}px`, boxSizing: "border-box", position: "relative",
    }}>
      {/* Side buttons */}
      <div style={{ position: "absolute", left: -2 * scale, top: 90 * scale, width: 3 * scale, height: 32 * scale, background: "#2A2A2C", borderRadius: `0 2px 2px 0` }} />
      <div style={{ position: "absolute", left: -2 * scale, top: 132 * scale, width: 3 * scale, height: 46 * scale, background: "#2A2A2C", borderRadius: `0 2px 2px 0` }} />
      <div style={{ position: "absolute", right: -2 * scale, top: 110 * scale, width: 3 * scale, height: 68 * scale, background: "#2A2A2C", borderRadius: `2px 0 0 2px` }} />
      {/* Notch */}
      <div style={{ width: 70 * scale, height: 9 * scale, background: "#000", borderRadius: 9 * scale, marginBottom: 5 * scale, flexShrink: 0 }} />
      {/* Screen */}
      <div style={{ width: iW * scale, height: iH * scale, borderRadius: 10 * scale, overflow: "hidden", background: BG, flexShrink: 0 }}>
        {variant === "tenant" ? <TenantHomePreview scale={scale * (iW / 390)} /> : <OwnerDashPreview scale={scale * (iW / 390)} />}
      </div>
      {/* Home bar */}
      <div style={{ width: 64 * scale, height: 4 * scale, background: "#3A3A3C", borderRadius: 4 * scale, marginTop: 10 * scale, flexShrink: 0 }} />
    </div>
  );
}

function TenantHomePreview({ scale }: { scale: number }) {
  const S = (n: number) => n * scale;
  return (
    <div style={{ width: 390, height: 520 / scale, transform: `scale(${scale})`, transformOrigin: "top left", background: BG, ...TJ, direction: "rtl", overflow: "hidden" }}>
      {/* Status bar */}
      <div style={{ height: S(40), background: TEAL, display: "flex", alignItems: "center", justifyContent: "space-between", padding: `0 ${S(20)}px` }}>
        <span style={{ fontSize: S(13), fontWeight: 700, color: WHITE }}>9:41</span>
        <div style={{ display: "flex", gap: S(4) }}>
          {[0, 0, 0].map((_, i) => <div key={i} style={{ width: S(5), height: S(5), borderRadius: S(3), background: "rgba(255,255,255,0.8)" }} />)}
        </div>
      </div>
      {/* Header */}
      <div style={{ background: TEAL, padding: `${S(10)}px ${S(20)}px ${S(18)}px` }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: S(12) }}>
          <div style={{ width: S(32), height: S(32), borderRadius: S(16), background: "rgba(255,255,255,0.2)", display: "flex", alignItems: "center", justifyContent: "center" }}>
            <svg width={S(16)} height={S(16)} viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2" strokeLinecap="round"><path d="M18 8A6 6 0 006 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 01-3.46 0"/></svg>
          </div>
          <div>
            <div style={{ fontSize: S(13), color: "rgba(255,255,255,0.7)", textAlign: "right" }}>مرحبًا،</div>
            <div style={{ fontSize: S(16), fontWeight: 800, color: WHITE }}>أحمد محمد 👋</div>
          </div>
          <div style={{ width: S(36), height: S(36), borderRadius: S(18), background: "rgba(255,255,255,0.25)" }} />
        </div>
        {/* Search bar */}
        <div style={{ background: WHITE, borderRadius: S(12), padding: `${S(10)}px ${S(14)}px`, display: "flex", alignItems: "center", gap: S(8) }}>
          <svg width={S(16)} height={S(16)} viewBox="0 0 24 24" fill="none" stroke={SUB} strokeWidth="2" strokeLinecap="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
          <span style={{ fontSize: S(13), color: SUB, flex: 1, textAlign: "right" }}>دور على شقة، ستوديو، غرفة...</span>
        </div>
      </div>
      {/* Content */}
      <div style={{ padding: `${S(14)}px ${S(16)}px` }}>
        <div style={{ fontSize: S(14), fontWeight: 800, color: NAVY, marginBottom: S(10) }}>عقارات قريبة منك</div>
        {[
          { title: "شقة في الشيخ زايد", price: "3,500 جنيه", area: "المهندسين", rooms: "3 غرف", color: "#CBD5E1" },
          { title: "ستوديو في مدينة نصر", price: "2,200 جنيه", area: "مدينة نصر", rooms: "1 غرفة", color: "#BFDBFE" },
        ].map((p, i) => (
          <div key={i} style={{ background: WHITE, borderRadius: S(14), marginBottom: S(10), overflow: "hidden", boxShadow: `0 ${S(2)}px ${S(8)}px rgba(0,0,0,0.06)` }}>
            <div style={{ height: S(90), background: p.color, display: "flex", alignItems: "center", justifyContent: "center", position: "relative" }}>
              <svg width={S(28)} height={S(28)} viewBox="0 0 24 24" fill="none" stroke="rgba(255,255,255,0.7)" strokeWidth="1.5" strokeLinecap="round"><rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/></svg>
              <div style={{ position: "absolute", top: S(8), left: S(8), background: TEAL, borderRadius: S(8), padding: `${S(3)}px ${S(8)}px`, display: "flex", alignItems: "center", gap: S(4) }}>
                <svg width={S(8)} height={S(8)} viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="3" strokeLinecap="round"><polyline points="20 6 9 17 4 12"/></svg>
                <span style={{ fontSize: S(9), fontWeight: 700, color: WHITE }}>موثق</span>
              </div>
            </div>
            <div style={{ padding: `${S(8)}px ${S(10)}px` }}>
              <div style={{ fontSize: S(13), fontWeight: 700, color: NAVY }}>{p.title}</div>
              <div style={{ fontSize: S(11), color: SUB, marginTop: S(2) }}>{p.area} · {p.rooms}</div>
              <div style={{ fontSize: S(14), fontWeight: 900, color: TEAL, marginTop: S(4) }}>{p.price} <span style={{ fontSize: S(10), fontWeight: 400, color: SUB }}>/شهر</span></div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function OwnerDashPreview({ scale }: { scale: number }) {
  const S = (n: number) => n * scale;
  return (
    <div style={{ width: 390, height: 520 / scale, transform: `scale(${scale})`, transformOrigin: "top left", background: BG, ...TJ, direction: "rtl", overflow: "hidden" }}>
      <div style={{ height: S(40), background: GOLD, display: "flex", alignItems: "center", justifyContent: "space-between", padding: `0 ${S(20)}px` }}>
        <span style={{ fontSize: S(13), fontWeight: 700, color: WHITE }}>9:41</span>
        <div style={{ display: "flex", gap: S(4) }}>
          {[0, 0, 0].map((_, i) => <div key={i} style={{ width: S(5), height: S(5), borderRadius: S(3), background: "rgba(255,255,255,0.8)" }} />)}
        </div>
      </div>
      <div style={{ background: GOLD, padding: `${S(10)}px ${S(20)}px ${S(20)}px` }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <div style={{ width: S(36), height: S(36), borderRadius: S(18), background: "rgba(255,255,255,0.2)" }} />
          <div style={{ textAlign: "right" }}>
            <div style={{ fontSize: S(12), color: "rgba(255,255,255,0.7)" }}>لوحة المالك</div>
            <div style={{ fontSize: S(16), fontWeight: 800, color: WHITE }}>كريم علي</div>
          </div>
          <div style={{ width: S(32), height: S(32), borderRadius: S(10), background: "rgba(255,255,255,0.2)", display: "flex", alignItems: "center", justifyContent: "center" }}>
            <svg width={S(16)} height={S(16)} viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2" strokeLinecap="round"><path d="M18 8A6 6 0 006 8c0 7-3 9-3 9h18s-3-2-3-9"/></svg>
          </div>
        </div>
      </div>
      <div style={{ padding: `${S(14)}px ${S(16)}px` }}>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: S(10), marginBottom: S(14) }}>
          {[
            { label: "مشاهدات", val: "1,234", icon: "👁" },
            { label: "طلبات زيارة", val: "8", icon: "📅" },
            { label: "رسائل", val: "12", icon: "💬" },
            { label: "عقارات نشطة", val: "3", icon: "🏠" },
          ].map((m, i) => (
            <div key={i} style={{ background: WHITE, borderRadius: S(12), padding: `${S(10)}px ${S(12)}px`, border: `1px solid ${BORDER}` }}>
              <div style={{ fontSize: S(16) }}>{m.icon}</div>
              <div style={{ fontSize: S(20), fontWeight: 900, color: NAVY, marginTop: S(4) }}>{m.val}</div>
              <div style={{ fontSize: S(10), color: SUB, marginTop: S(2) }}>{m.label}</div>
            </div>
          ))}
        </div>
        <div style={{ background: WHITE, borderRadius: S(14), padding: `${S(10)}px ${S(12)}px`, border: `1px solid ${BORDER}` }}>
          <div style={{ fontSize: S(12), fontWeight: 700, color: NAVY, marginBottom: S(8) }}>آخر الطلبات</div>
          {["محمد أحمد — شقة الشيخ زايد", "سارة علي — ستوديو نصر"].map((req, i) => (
            <div key={i} style={{ display: "flex", alignItems: "center", gap: S(8), padding: `${S(6)}px 0`, borderBottom: i === 0 ? `1px solid ${BORDER}` : "none" }}>
              <div style={{ width: S(28), height: S(28), borderRadius: S(14), background: TEAL_L, display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
                <span style={{ fontSize: S(10), fontWeight: 700, color: TEAL }}>{req[0]}</span>
              </div>
              <div style={{ flex: 1, fontSize: S(11), color: NAVY, textAlign: "right" }}>{req}</div>
              <div style={{ background: TEAL_L, borderRadius: S(6), padding: `${S(2)}px ${S(8)}px` }}>
                <span style={{ fontSize: S(9), fontWeight: 700, color: TEAL }}>جديد</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// ── Section header ──────────────────────────────────────────────────────
function SectionTag({ text, color = TEAL }: { text: string; color?: string }) {
  return (
    <div style={{ display: "inline-flex", alignItems: "center", gap: 8, background: color + "12", border: `1px solid ${color}28`, borderRadius: 100, padding: "5px 14px", marginBottom: 16 }}>
      <div style={{ width: 6, height: 6, borderRadius: 3, background: color }} />
      <span style={{ fontSize: 13, fontWeight: 700, color, ...TJ }}>{text}</span>
    </div>
  );
}

// ── FAQ Accordion ────────────────────────────────────────────────────────
const FAQ_ITEMS = [
  { q: "هل رقم الموبايل بيظهر للمالك أو المستأجر؟", a: "لأ، رقم الموبايل مش بيظهر لأي طرف. التواصل بيتم داخل المنصة بالكامل وبموافقة صريحة فقط." },
  { q: "إزاي أوثق حسابي؟", a: "من قسم الملف الشخصي، ابعت صورة بطاقة الهوية الوطنية. الفريق هيراجع البيانات في خلال 24 ساعة." },
  { q: "هل مستندات البطاقة بتظهر لأي مستخدم؟", a: "لأ. مستندات الهوية للمراجعة الداخلية فقط ولا تُشارك مع أي مستخدم آخر على الإطلاق." },
  { q: "إزاي أحجز زيارة للعقار؟", a: "من صفحة تفاصيل العقار، اضغط على 'احجز زيارة'، اختار اليوم والوقت المناسب، وانتظر تأكيد المالك." },
  { q: "إزاي المالك يضيف عقار؟", a: "من لوحة المالك، اضغط على 'إضافة عقار' واتبع الخطوات: البيانات، الصور والفيديو، التسعير، وإثبات الملكية." },
  { q: "إيه المستندات المطلوبة لإثبات الملكية؟", a: "وصل كهرباء أو مياه حديث، أو عقد ملكية أو إيجار. المستند للمراجعة الداخلية فقط." },
  { q: "هل ممكن استخدم التطبيق كزائر؟", a: "أيوه، تقدر تتصفح العقارات بدون تسجيل. بس محتاج حساب موثق عشان تتواصل أو تحجز زيارة." },
  { q: "إيه اللي يحصل لو العقار اترفض في المراجعة؟", a: "هتوصلك إشعار بسبب الرفض مع تفاصيل التعديلات المطلوبة، وتقدر تعيد الرفع بعد التصحيح." },
];

function FaqSection() {
  const [open, setOpen] = useState<number | null>(0);
  return (
    <div style={{ maxWidth: 760, margin: "0 auto", display: "flex", flexDirection: "column", gap: 0 }}>
      {FAQ_ITEMS.map((item, i) => (
        <div key={i} style={{ borderBottom: `1px solid ${BORDER}`, overflow: "hidden" }}>
          <button
            onClick={() => setOpen(open === i ? null : i)}
            style={{ width: "100%", padding: "18px 0", background: "none", border: "none", cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "space-between", gap: 16, direction: "rtl" }}>
            <span style={{ fontSize: 16, fontWeight: 700, color: NAVY, textAlign: "right", ...TJ }}>{item.q}</span>
            <div style={{ width: 28, height: 28, borderRadius: 14, background: open === i ? TEAL : "#F3F4F6", display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0, transition: "background 0.2s" }}>
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke={open === i ? "white" : SUB} strokeWidth="2.5" strokeLinecap="round" style={{ transition: "transform 0.2s", transform: open === i ? "rotate(180deg)" : "none" }}>
                <polyline points="6 9 12 15 18 9" />
              </svg>
            </div>
          </button>
          {open === i && (
            <div style={{ padding: "0 0 18px", direction: "rtl" }}>
              <p style={{ fontSize: 15, color: SUB, lineHeight: 1.8, margin: 0, ...TJ }}>{item.a}</p>
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

// ── How It Works Tabs ────────────────────────────────────────────────────
const TENANT_STEPS = [
  { n: "01", title: "حدد المنطقة ونوع السكن", body: "اختار المحافظة والمنطقة وفلتر حسب النوع، السعر، عدد الغرف، والفترة." },
  { n: "02", title: "راجع التفاصيل والتوثيق", body: "شوف الصور والفيديو، تحقق من وضع التوثيق، واطلع على كل بيانات العقار." },
  { n: "03", title: "احفظ العقارات المناسبة", body: "احفظ العقارات اللي عجبتك وارجع إليها وقت ما تريد للمقارنة." },
  { n: "04", title: "تواصل واحجز زيارة", body: "ابعت رسالة من داخل المنصة أو احجز موعد زيارة مباشرة من صفحة العقار." },
];
const OWNER_STEPS = [
  { n: "01", title: "أضف بيانات العقار", body: "سجل نوع العقار، المنطقة على الخريطة، الغرف، السعر، والمرافق." },
  { n: "02", title: "ارفع الصور والفيديو", body: "ارفع صور واضحة مع أسماء وأوصاف، وفيديو لا يزيد عن دقيقة لعرض العقار." },
  { n: "03", title: "انتظر مراجعة سكون", body: "فريقنا يراجع البيانات وإثبات الملكية. بتوصلك إشعار بالنتيجة." },
  { n: "04", title: "استقبل الطلبات وأدر عقارك", body: "اقبل أو ارفض طلبات الزيارة، تواصل مع المستأجرين، وتابع أداء العقار." },
];

function HowItWorksSection() {
  const [tab, setTab] = useState<"tenant" | "owner">("tenant");
  const steps = tab === "tenant" ? TENANT_STEPS : OWNER_STEPS;
  const color = tab === "tenant" ? TEAL : GOLD;
  return (
    <div>
      {/* Tabs */}
      <div style={{ display: "flex", background: "#F3F4F6", borderRadius: 16, padding: 4, maxWidth: 320, margin: "0 auto 48px", direction: "rtl" }}>
        {(["tenant", "owner"] as const).map(t => (
          <button key={t} onClick={() => setTab(t)} style={{ flex: 1, height: 44, borderRadius: 12, border: "none", cursor: "pointer", background: tab === t ? (t === "tenant" ? TEAL : GOLD) : "transparent", color: tab === t ? WHITE : SUB, fontSize: 15, fontWeight: 700, transition: "all 0.2s", ...TJ }}>
            {t === "tenant" ? "أنا مستأجر" : "أنا مالك"}
          </button>
        ))}
      </div>
      {/* Steps */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: 24, maxWidth: 1000, margin: "0 auto" }}>
        {steps.map((step, i) => (
          <div key={i} style={{ background: WHITE, border: `1px solid ${BORDER}`, borderRadius: 22, padding: "28px 24px", position: "relative", direction: "rtl" }}>
            <div style={{ fontSize: 36, fontWeight: 900, color: color + "25", lineHeight: 1, marginBottom: 14 }}>{step.n}</div>
            <div style={{ position: "absolute", top: 24, left: 24, width: 32, height: 32, borderRadius: 10, background: color + "15", display: "flex", alignItems: "center", justifyContent: "center" }}>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2.5" strokeLinecap="round"><polyline points="20 6 9 17 4 12" /></svg>
            </div>
            <div style={{ fontSize: 17, fontWeight: 800, color: NAVY, marginBottom: 10, ...TJ }}>{step.title}</div>
            <div style={{ fontSize: 14, color: SUB, lineHeight: 1.7, ...TJ }}>{step.body}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ── Property Cards ───────────────────────────────────────────────────────
const PROPERTIES = [
  { title: "شقة فاخرة في الشيخ زايد", area: "الشيخ زايد، الجيزة", price: "5,500", unit: "جنيه/شهر", rooms: "3", sqm: "120", type: "عائلات", color: "#CBD5E1", badge: true },
  { title: "ستوديو مؤثث في مدينة نصر", area: "مدينة نصر، القاهرة", price: "2,800", unit: "جنيه/شهر", rooms: "1", sqm: "55", type: "أفراد", color: "#BFDBFE", badge: true },
  { title: "غرفة في سكن مشترك", area: "المعادي، القاهرة", price: "1,400", unit: "جنيه/شهر", rooms: "1", sqm: "25", type: "أفراد", color: "#BBF7D0", badge: false },
  { title: "شقة في الرحاب", area: "الرحاب، القاهرة الجديدة", price: "4,200", unit: "جنيه/شهر", rooms: "2", sqm: "95", type: "عائلات", color: "#FDE68A", badge: true },
];

function PropertyCard({ p }: { p: typeof PROPERTIES[0] }) {
  const [saved, setSaved] = useState(false);
  return (
    <div style={{ background: WHITE, borderRadius: 20, overflow: "hidden", border: `1px solid ${BORDER}`, boxShadow: "0 2px 16px rgba(0,0,0,0.05)", ...TJ }}>
      <div style={{ height: 180, background: p.color, position: "relative", display: "flex", alignItems: "center", justifyContent: "center" }}>
        <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="rgba(255,255,255,0.6)" strokeWidth="1.5" strokeLinecap="round"><rect x="3" y="3" width="18" height="18" rx="2" /><circle cx="8.5" cy="8.5" r="1.5" /><polyline points="21 15 16 10 5 21" /></svg>
        {p.badge && (
          <div style={{ position: "absolute", top: 12, right: 12, background: TEAL, borderRadius: 8, padding: "4px 10px", display: "flex", alignItems: "center", gap: 5 }}>
            <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="3" strokeLinecap="round"><polyline points="20 6 9 17 4 12" /></svg>
            <span style={{ fontSize: 11, fontWeight: 700, color: WHITE }}>موثق</span>
          </div>
        )}
        <button onClick={() => setSaved(!saved)} style={{ position: "absolute", top: 10, left: 10, width: 36, height: 36, borderRadius: 18, background: "rgba(255,255,255,0.92)", border: "none", cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center" }}>
          <svg width="16" height="16" viewBox="0 0 24 24" fill={saved ? ROSE : "none"} stroke={saved ? ROSE : "#9CA3AF"} strokeWidth="2" strokeLinecap="round"><path d="M20.84 4.61a5.5 5.5 0 00-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 00-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 000-7.78z" /></svg>
        </button>
        <div style={{ position: "absolute", bottom: 10, right: 12, background: TEAL + "14", border: `1px solid ${TEAL}30`, borderRadius: 8, padding: "3px 10px" }}>
          <span style={{ fontSize: 11, fontWeight: 700, color: TEAL }}>{p.type}</span>
        </div>
      </div>
      <div style={{ padding: "16px 16px", direction: "rtl" }}>
        <div style={{ fontSize: 16, fontWeight: 800, color: NAVY, marginBottom: 6 }}>{p.title}</div>
        <div style={{ display: "flex", alignItems: "center", gap: 5, marginBottom: 12 }}>
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke={SUB} strokeWidth="2" strokeLinecap="round"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0118 0z" /><circle cx="12" cy="10" r="3" /></svg>
          <span style={{ fontSize: 13, color: SUB }}>{p.area}</span>
        </div>
        <div style={{ display: "flex", gap: 14, marginBottom: 14 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 5 }}>
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke={SUB} strokeWidth="2" strokeLinecap="round"><path d="M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z" /><polyline points="9 22 9 12 15 12 15 22" /></svg>
            <span style={{ fontSize: 13, color: SUB }}>{p.rooms} غرف</span>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 5 }}>
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke={SUB} strokeWidth="2" strokeLinecap="round"><rect x="3" y="3" width="18" height="18" rx="2" /></svg>
            <span style={{ fontSize: 13, color: SUB }}>{p.sqm} م²</span>
          </div>
        </div>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
          <div>
            <span style={{ fontSize: 20, fontWeight: 900, color: TEAL }}>{p.price}</span>
            <span style={{ fontSize: 12, color: SUB, marginRight: 4 }}>{p.unit}</span>
          </div>
          <button style={{ height: 36, padding: "0 16px", background: TEAL, border: "none", borderRadius: 10, color: WHITE, fontSize: 13, fontWeight: 700, cursor: "pointer", ...TJ }}>تفاصيل</button>
        </div>
      </div>
    </div>
  );
}

// ── App Carousel ─────────────────────────────────────────────────────────
const CAROUSEL_SCREENS = [
  { label: "الرئيسية — مستأجر", variant: "tenant" as const },
  { label: "لوحة المالك", variant: "owner" as const },
  { label: "الرئيسية — مستأجر", variant: "tenant" as const },
  { label: "لوحة المالك", variant: "owner" as const },
];

function AppCarousel() {
  const [idx, setIdx] = useState(0);
  return (
    <div style={{ textAlign: "center" }}>
      <div style={{ display: "flex", gap: 32, justifyContent: "center", alignItems: "center", marginBottom: 32, overflowX: "hidden" }}>
        {CAROUSEL_SCREENS.map((s, i) => {
          const dist = i - idx;
          const active = dist === 0;
          const visible = Math.abs(dist) <= 1;
          return (
            <div key={i} onClick={() => setIdx(i)} style={{
              cursor: "pointer", transition: "transform 0.35s, opacity 0.35s",
              transform: `scale(${active ? 1 : 0.78}) translateX(${dist * -20}px)`,
              opacity: active ? 1 : visible ? 0.5 : 0,
              pointerEvents: visible ? "auto" : "none",
              display: Math.abs(dist) > 1 ? "none" : "block",
            }}>
              <PhoneMockup variant={s.variant} scale={0.65} />
            </div>
          );
        })}
      </div>
      <div style={{ fontSize: 15, fontWeight: 700, color: NAVY, marginBottom: 16, ...TJ }}>{CAROUSEL_SCREENS[idx].label}</div>
      <div style={{ display: "flex", gap: 8, justifyContent: "center" }}>
        {CAROUSEL_SCREENS.map((_, i) => (
          <button key={i} onClick={() => setIdx(i)} style={{ width: i === idx ? 24 : 8, height: 8, borderRadius: 4, background: i === idx ? TEAL : BORDER, border: "none", cursor: "pointer", transition: "width 0.2s, background 0.2s" }} />
        ))}
      </div>
      <div style={{ display: "flex", gap: 16, justifyContent: "center", marginTop: 24 }}>
        <button onClick={() => setIdx(Math.max(0, idx - 1))} style={{ width: 44, height: 44, borderRadius: 22, background: WHITE, border: `1.5px solid ${BORDER}`, cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center" }}>
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke={NAVY} strokeWidth="2" strokeLinecap="round"><polyline points="9 18 15 12 9 6" /></svg>
        </button>
        <button onClick={() => setIdx(Math.min(CAROUSEL_SCREENS.length - 1, idx + 1))} style={{ width: 44, height: 44, borderRadius: 22, background: TEAL, border: "none", cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center" }}>
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2" strokeLinecap="round"><polyline points="15 18 9 12 15 6" /></svg>
        </button>
      </div>
    </div>
  );
}

// ── Main Landing Page ────────────────────────────────────────────────────
export function LandingPage() {
  const [menuOpen, setMenuOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);
  const [featureTab, setFeatureTab] = useState<"tenant" | "owner">("tenant");
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = scrollRef.current;
    if (!el) return;
    const handler = () => setScrolled(el.scrollTop > 60);
    el.addEventListener("scroll", handler);
    return () => el.removeEventListener("scroll", handler);
  }, []);

  function scrollTo(id: string) {
    const el = scrollRef.current;
    if (!el) return;
    const target = el.querySelector(`#${id}`);
    if (target) target.scrollIntoView({ behavior: "smooth", block: "start" });
    setMenuOpen(false);
  }

  const NAV = ["الرئيسية","للمستأجر","للمالك","الأمان والتوثيق","كيف يعمل؟","الأسئلة الشائعة"];
  const NAV_IDS = ["hero","tenant-section","owner-section","trust-section","how-section","faq-section"];

  const TENANT_FEATURES = [
    { icon: "🔍", title: "بحث وفلاتر ذكية", items: ["نوع العقار والمنطقة","السعر وفترة التأجير","مناسب لعائلات أو أفراد","المرافق والتدخين"] },
    { icon: "🏠", title: "تفاصيل عقار كاملة", items: ["الصور والفيديو والموقع","الغرف والمساحة","قواعد السكن","وضع التوثيق"] },
    { icon: "❤️", title: "حفظ ومقارنة", items: ["حفظ العقارات المفضلة","الرجوع إليها بسهولة","مقارنة الخيارات"] },
    { icon: "💬", title: "شات آمن", items: ["أرقام الهاتف مخفية","صور ورسائل صوتية","قيود على الحسابات غير الموثقة"] },
    { icon: "📅", title: "حجز زيارة", items: ["اختار اليوم والوقت","تابع حالة الطلب","عدّل أو ألغِ الموعد"] },
  ];
  const OWNER_FEATURES = [
    { icon: "📋", title: "إضافة عقار منظمة", items: ["بيانات كاملة وموقع على الخريطة","الغرف والمساحة والمرافق","فترة التأجير ومناسب لمن","قواعد التدخين"] },
    { icon: "📸", title: "صور وفيديو واضح", items: ["اسم ووصف لكل صورة","فيديو لا يزيد عن دقيقة","معاينة قبل النشر"] },
    { icon: "📄", title: "إثبات الملكية", items: ["وصل كهرباء أو مياه","عقد ملكية أو إيجار","للمراجعة الداخلية فقط"] },
    { icon: "📬", title: "إدارة طلبات الزيارة", items: ["قبول أو رفض الطلبات","فتح شات مع المستأجر","متابعة المواعيد"] },
    { icon: "📊", title: "متابعة الأداء", items: ["المشاهدات ومرات الحفظ","الرسائل وطلبات الزيارة","تحليل شهري"] },
    { icon: "🔧", title: "إدارة حالة العقار", items: ["قيد المراجعة، مقبول، مرفوض","إخفاء أو تعديل العقار","متابعة سجل التغييرات"] },
  ];
  const features = featureTab === "tenant" ? TENANT_FEATURES : OWNER_FEATURES;
  const fColor = featureTab === "tenant" ? TEAL : GOLD;

  return (
    <div ref={scrollRef} style={{ width: "100%", height: "100%", overflowY: "auto", overflowX: "hidden", background: BG, ...TJ, direction: "rtl", scrollBehavior: "smooth" }}>

      {/* ══ HEADER ══════════════════════════════════════════════════════════ */}
      <header style={{ position: "sticky", top: 0, zIndex: 100, background: scrolled ? "rgba(250,250,248,0.96)" : "transparent", backdropFilter: scrolled ? "blur(12px)" : "none", borderBottom: scrolled ? `1px solid ${BORDER}` : "none", transition: "all 0.3s" }}>
        <div style={{ maxWidth: 1200, margin: "0 auto", padding: "0 24px", height: 68, display: "flex", alignItems: "center", justifyContent: "space-between" }}>
          <SokoonLogo size={38} />
          {/* Desktop nav */}
          <nav style={{ display: "flex", gap: 28, alignItems: "center" }}>
            {NAV.map((link, i) => (
              <button key={i} onClick={() => scrollTo(NAV_IDS[i])} style={{ background: "none", border: "none", cursor: "pointer", fontSize: 14, fontWeight: 600, color: scrolled ? NAVY : NAVY, ...TJ, whiteSpace: "nowrap" }}>{link}</button>
            ))}
          </nav>
          <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
            <button onClick={() => scrollTo("hero")} style={{ height: 40, padding: "0 18px", background: "transparent", border: `1.5px solid ${BORDER}`, borderRadius: 10, fontSize: 14, fontWeight: 600, color: NAVY, cursor: "pointer", ...TJ }}>تسجيل الدخول</button>
            <button onClick={() => scrollTo("hero")} style={{ height: 40, padding: "0 18px", background: TEAL, border: "none", borderRadius: 10, fontSize: 14, fontWeight: 700, color: WHITE, cursor: "pointer", ...TJ }}>ابدأ الآن</button>
          </div>
        </div>
      </header>

      {/* ══ HERO ════════════════════════════════════════════════════════════ */}
      <section id="hero" style={{ background: `linear-gradient(160deg, #F0FDFA 0%, #FAFAF8 50%, #FEF9F0 100%)`, padding: "80px 24px 60px", position: "relative", overflow: "hidden" }}>
        {/* Subtle background shapes */}
        <svg style={{ position: "absolute", top: -40, left: "5%", opacity: 0.06 }} width="400" height="400" viewBox="0 0 400 400">
          <path d="M200 20 L370 160 L340 160 L340 380 L60 380 L60 160 L30 160 Z" fill={TEAL} />
        </svg>
        <svg style={{ position: "absolute", bottom: 0, right: "2%", opacity: 0.05 }} width="300" height="300" viewBox="0 0 300 300">
          <circle cx="150" cy="150" r="120" fill="none" stroke={TEAL} strokeWidth="40" />
        </svg>

        <div style={{ maxWidth: 1200, margin: "0 auto", display: "grid", gridTemplateColumns: "1fr auto", gap: 48, alignItems: "center" }}>
          {/* Text */}
          <div style={{ maxWidth: 560 }}>
            <SectionTag text="منصة الإيجار الموثوقة في مصر" />
            <h1 style={{ fontSize: "clamp(36px, 5vw, 60px)", fontWeight: 900, color: NAVY, lineHeight: 1.2, margin: "0 0 20px", ...TJ }}>
              سكنك المناسب،<br />
              <span style={{ color: TEAL }}>بطريقة أسهل وأأمن</span>
            </h1>
            <p style={{ fontSize: 18, color: SUB, lineHeight: 1.8, margin: "0 0 36px", ...TJ }}>
              دور على شقة أو ستوديو أو غرفة، أو اعرض عقارك وتابع الطلبات من مكان واحد.
            </p>
            <div style={{ display: "flex", gap: 14, flexWrap: "wrap", alignItems: "center" }}>
              <button onClick={() => scrollTo("tenant-section")} style={{ height: 52, padding: "0 28px", background: TEAL, border: "none", borderRadius: 14, color: WHITE, fontSize: 16, fontWeight: 700, cursor: "pointer", display: "flex", alignItems: "center", gap: 10, ...TJ }}>
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2" strokeLinecap="round"><circle cx="11" cy="11" r="8" /><line x1="21" y1="21" x2="16.65" y2="16.65" /></svg>
                ابحث عن سكن
              </button>
              <button onClick={() => scrollTo("owner-section")} style={{ height: 52, padding: "0 28px", background: WHITE, border: `1.5px solid ${BORDER}`, borderRadius: 14, color: NAVY, fontSize: 16, fontWeight: 700, cursor: "pointer", ...TJ }}>اعرض عقارك</button>
              <button onClick={() => scrollTo("property-section")} style={{ background: "none", border: "none", color: TEAL, fontSize: 14, fontWeight: 600, cursor: "pointer", textDecoration: "underline", ...TJ }}>تصفح كزائر</button>
            </div>
          </div>
          {/* Phones */}
          <div style={{ display: "flex", gap: 20, alignItems: "flex-end", flexShrink: 0 }}>
            <div style={{ transform: "translateY(20px)" }}>
              <PhoneMockup variant="tenant" scale={0.72} />
            </div>
            <div style={{ transform: "translateY(-10px)" }}>
              <PhoneMockup variant="owner" scale={0.72} />
            </div>
          </div>
        </div>
      </section>

      {/* ══ TRUST STRIP ═════════════════════════════════════════════════════ */}
      <section style={{ background: WHITE, borderTop: `1px solid ${BORDER}`, borderBottom: `1px solid ${BORDER}`, padding: "32px 24px" }}>
        <div style={{ maxWidth: 1200, margin: "0 auto", display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: 24 }}>
          {[
            { icon: <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke={TEAL} strokeWidth="2" strokeLinecap="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><polyline points="9 12 11 14 15 10"/></svg>, title: "حسابات موثقة", sub: "توثيق الهوية يقلل الحسابات الوهمية" },
            { icon: <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke={BLUE} strokeWidth="2" strokeLinecap="round"><path d="M17.94 17.94A10.07 10.07 0 0112 20c-7 0-11-8-11-8a18.45 18.45 0 015.06-5.94M9.9 4.24A9.12 9.12 0 0112 4c7 0 11 8 11 8a18.5 18.5 0 01-2.16 3.19m-6.72-1.07a3 3 0 11-4.24-4.24"/><line x1="1" y1="1" x2="23" y2="23"/></svg>, title: "أرقام مخفية", sub: "رقمك مش بيظهر غير بموافقتك" },
            { icon: <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke={GOLD} strokeWidth="2" strokeLinecap="round"><path d="M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/><circle cx="12" cy="8" r="1.5" fill={GOLD}/></svg>, title: "عقارات تحت المراجعة", sub: "بيانات العقار وإثبات الملكية تخضع للمراجعة" },
            { icon: <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke={GREEN} strokeWidth="2" strokeLinecap="round"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>, title: "طلبات زيارة منظمة", sub: "احجز وتابع الموعد من داخل التطبيق" },
          ].map((item, i) => (
            <div key={i} style={{ display: "flex", alignItems: "flex-start", gap: 14, direction: "rtl" }}>
              <div style={{ width: 44, height: 44, borderRadius: 12, background: "#F3F4F6", display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>{item.icon}</div>
              <div>
                <div style={{ fontSize: 15, fontWeight: 800, color: NAVY, marginBottom: 4, ...TJ }}>{item.title}</div>
                <div style={{ fontSize: 13, color: SUB, lineHeight: 1.5, ...TJ }}>{item.sub}</div>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* ══ TENANT / OWNER FEATURES ═════════════════════════════════════════ */}
      <section id="tenant-section" style={{ padding: "80px 24px" }}>
        <div style={{ maxWidth: 1200, margin: "0 auto" }}>
          {/* Tabs */}
          <div style={{ textAlign: "center", marginBottom: 52 }}>
            <SectionTag text="كل ما تحتاجه في مكان واحد" />
            <h2 style={{ fontSize: "clamp(28px, 4vw, 44px)", fontWeight: 900, color: NAVY, margin: "0 0 24px", ...TJ }}>مصمم لك، سواء مستأجر أو مالك</h2>
            <div style={{ display: "inline-flex", background: "#F3F4F6", borderRadius: 16, padding: 4, gap: 4 }}>
              {(["tenant", "owner"] as const).map(t => (
                <button key={t} onClick={() => setFeatureTab(t)} style={{ height: 44, padding: "0 24px", borderRadius: 12, border: "none", cursor: "pointer", background: featureTab === t ? (t === "tenant" ? TEAL : GOLD) : "transparent", color: featureTab === t ? WHITE : SUB, fontSize: 15, fontWeight: 700, transition: "all 0.2s", ...TJ }}>
                  {t === "tenant" ? "🔑 للمستأجر" : "🏠 للمالك"}
                </button>
              ))}
            </div>
          </div>

          {featureTab === "tenant" && (
            <div style={{ marginBottom: 20 }}>
              <div style={{ textAlign: "center", marginBottom: 40 }}>
                <h3 style={{ fontSize: 28, fontWeight: 800, color: NAVY, margin: "0 0 12px", ...TJ }}>دور، قارن، واحجز زيارة بسهولة</h3>
                <p style={{ fontSize: 16, color: SUB, margin: 0, ...TJ }}>كل الأدوات اللي تحتاجها عشان تلاقي السكن المناسب وتتعامل بأمان مع المالك.</p>
              </div>
            </div>
          )}
          {featureTab === "owner" && (
            <div style={{ marginBottom: 20 }}>
              <div style={{ textAlign: "center", marginBottom: 40 }}>
                <h3 id="owner-section" style={{ fontSize: 28, fontWeight: 800, color: NAVY, margin: "0 0 12px", ...TJ }}>اعرض عقارك وأدر كل شيء من مكان واحد</h3>
                <p style={{ fontSize: 16, color: SUB, margin: 0, ...TJ }}>أضف بيانات العقار، ارفع الصور والفيديو، وتابع المشاهدات وطلبات الزيارة.</p>
              </div>
            </div>
          )}

          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))", gap: 20, marginBottom: 40 }}>
            {features.map((f, i) => (
              <div key={i} style={{ background: WHITE, border: `1px solid ${BORDER}`, borderRadius: 20, padding: "24px 22px", direction: "rtl" }}>
                <div style={{ width: 46, height: 46, borderRadius: 14, background: fColor + "12", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 22, marginBottom: 14 }}>{f.icon}</div>
                <div style={{ fontSize: 17, fontWeight: 800, color: NAVY, marginBottom: 12, ...TJ }}>{f.title}</div>
                <div style={{ display: "flex", flexDirection: "column", gap: 7 }}>
                  {f.items.map((item, j) => (
                    <div key={j} style={{ display: "flex", alignItems: "center", gap: 8 }}>
                      <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke={fColor} strokeWidth="2.5" strokeLinecap="round"><polyline points="20 6 9 17 4 12" /></svg>
                      <span style={{ fontSize: 14, color: SUB, ...TJ }}>{item}</span>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>

          <div style={{ textAlign: "center" }}>
            <button onClick={() => scrollTo("hero")} style={{ height: 52, padding: "0 32px", background: fColor, border: "none", borderRadius: 14, color: WHITE, fontSize: 16, fontWeight: 700, cursor: "pointer", ...TJ }}>
              {featureTab === "tenant" ? "ابدأ البحث عن سكن" : "ابدأ عرض عقارك"}
            </button>
          </div>
        </div>
      </section>

      {/* ══ HOW IT WORKS ════════════════════════════════════════════════════ */}
      <section id="how-section" style={{ background: "#F8FAFC", padding: "80px 24px" }}>
        <div style={{ maxWidth: 1200, margin: "0 auto" }}>
          <div style={{ textAlign: "center", marginBottom: 52 }}>
            <SectionTag text="خطوات بسيطة" />
            <h2 style={{ fontSize: "clamp(28px, 4vw, 44px)", fontWeight: 900, color: NAVY, margin: 0, ...TJ }}>سكون بيشتغل إزاي؟</h2>
          </div>
          <HowItWorksSection />
        </div>
      </section>

      {/* ══ PROPERTY SHOWCASE ═══════════════════════════════════════════════ */}
      <section id="property-section" style={{ padding: "80px 24px" }}>
        <div style={{ maxWidth: 1200, margin: "0 auto" }}>
          <div style={{ textAlign: "center", marginBottom: 52 }}>
            <SectionTag text="عقارات متنوعة" />
            <h2 style={{ fontSize: "clamp(28px, 4vw, 44px)", fontWeight: 900, color: NAVY, margin: "0 0 16px", ...TJ }}>خيارات سكن تناسب احتياجات مختلفة</h2>
            <p style={{ fontSize: 16, color: SUB, margin: 0, ...TJ }}>عقارات موثقة في أرقى مناطق القاهرة والجيزة</p>
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(260px, 1fr))", gap: 24, marginBottom: 40 }}>
            {PROPERTIES.map((p, i) => <PropertyCard key={i} p={p} />)}
          </div>
          <div style={{ textAlign: "center" }}>
            <button onClick={() => scrollTo("hero")} style={{ height: 52, padding: "0 32px", background: WHITE, border: `1.5px solid ${TEAL}`, borderRadius: 14, color: TEAL, fontSize: 16, fontWeight: 700, cursor: "pointer", ...TJ }}>استكشف المزيد من العقارات</button>
          </div>
        </div>
      </section>

      {/* ══ PRIVACY & TRUST ═════════════════════════════════════════════════ */}
      <section id="trust-section" style={{ background: `linear-gradient(135deg, ${TEAL_D} 0%, ${TEAL} 60%, #0A8A80 100%)`, padding: "80px 24px" }}>
        <div style={{ maxWidth: 1200, margin: "0 auto" }}>
          <div style={{ textAlign: "center", marginBottom: 52 }}>
            <div style={{ display: "inline-flex", alignItems: "center", gap: 8, background: "rgba(255,255,255,0.15)", border: "1px solid rgba(255,255,255,0.25)", borderRadius: 100, padding: "5px 16px", marginBottom: 16 }}>
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5" strokeLinecap="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
              <span style={{ fontSize: 13, fontWeight: 700, color: WHITE, ...TJ }}>الأمان والخصوصية</span>
            </div>
            <h2 style={{ fontSize: "clamp(28px, 4vw, 44px)", fontWeight: 900, color: WHITE, margin: 0, ...TJ }}>خصوصيتك وثقتك جزء من التجربة</h2>
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(250px, 1fr))", gap: 20 }}>
            {[
              { icon: <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="1.8" strokeLinecap="round"><path d="M17.94 17.94A10.07 10.07 0 0112 20c-7 0-11-8-11-8a18.45 18.45 0 015.06-5.94M9.9 4.24A9 9 0 0112 4c7 0 11 8 11 8a18.5 18.5 0 01-2.16 3.19m-6.72-1.07a3 3 0 11-4.24-4.24"/><line x1="1" y1="1" x2="23" y2="23"/></svg>, title: "رقمك مخفي", body: "مش بيظهر لأي طرف غير بموافقة واضحة" },
              { icon: <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="1.8" strokeLinecap="round"><rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0110 0v4"/><circle cx="12" cy="16" r="1.5" fill="white"/></svg>, title: "مستندات الهوية خاصة", body: "صور البطاقة للمراجعة الداخلية فقط، لا تظهر للمستخدمين" },
              { icon: <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="1.8" strokeLinecap="round"><path d="M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z"/><path d="M12 22s8-4 8-10V5l-8-3-8 3v7"/></svg>, title: "إثبات الملكية محمي", body: "مستندات الملكية لا تظهر للمستأجرين، يظهر فقط وضع التحقق" },
              { icon: <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="1.8" strokeLinecap="round"><path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z"/></svg>, title: "الشات داخل سكون", body: "التواصل داخل المنصة يساعد في تقليل الاحتيال وحماية الطرفين" },
            ].map((item, i) => (
              <div key={i} style={{ background: "rgba(255,255,255,0.1)", border: "1px solid rgba(255,255,255,0.18)", borderRadius: 22, padding: "28px 22px", direction: "rtl", backdropFilter: "blur(8px)" }}>
                <div style={{ width: 52, height: 52, borderRadius: 16, background: "rgba(255,255,255,0.15)", display: "flex", alignItems: "center", justifyContent: "center", marginBottom: 16 }}>{item.icon}</div>
                <div style={{ fontSize: 18, fontWeight: 800, color: WHITE, marginBottom: 10, ...TJ }}>{item.title}</div>
                <div style={{ fontSize: 14, color: "rgba(255,255,255,0.75)", lineHeight: 1.7, ...TJ }}>{item.body}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ══ APP SHOWCASE ════════════════════════════════════════════════════ */}
      <section style={{ padding: "80px 24px", background: BG }}>
        <div style={{ maxWidth: 1200, margin: "0 auto" }}>
          <div style={{ textAlign: "center", marginBottom: 52 }}>
            <SectionTag text="التطبيق" />
            <h2 style={{ fontSize: "clamp(28px, 4vw, 44px)", fontWeight: 900, color: NAVY, margin: 0, ...TJ }}>كل احتياجاتك في تطبيق واحد</h2>
          </div>
          <AppCarousel />
        </div>
      </section>

      {/* ══ FINAL CTA ═══════════════════════════════════════════════════════ */}
      <section style={{ padding: "80px 24px", background: "#F0FDFA" }}>
        <div style={{ maxWidth: 700, margin: "0 auto", textAlign: "center" }}>
          <div style={{ width: 72, height: 72, borderRadius: 20, background: TEAL + "18", display: "flex", alignItems: "center", justifyContent: "center", margin: "0 auto 24px" }}>
            <svg width="32" height="32" viewBox="0 0 18 18" fill="none">
              <path d="M9,2 L16,8 L14,8 L14,16 L4,16 L4,8 L2,8 Z" fill={TEAL} />
              <rect x="5.5" y="10" width="2.5" height="2" rx="0.7" fill={WHITE} />
              <rect x="10" y="10" width="2.5" height="2" rx="0.7" fill={WHITE} />
            </svg>
          </div>
          <h2 style={{ fontSize: "clamp(28px, 5vw, 46px)", fontWeight: 900, color: NAVY, margin: "0 0 16px", ...TJ }}>ابدأ تجربتك مع سكون</h2>
          <p style={{ fontSize: 17, color: SUB, margin: "0 0 40px", lineHeight: 1.7, ...TJ }}>سواء بتدور على سكن أو عايز تعرض عقارك، سكون بيجمعلك كل الخطوات في مكان واحد.</p>
          <div style={{ display: "flex", gap: 16, justifyContent: "center", flexWrap: "wrap", marginBottom: 40 }}>
            <button onClick={() => scrollTo("hero")} style={{ height: 56, padding: "0 32px", background: TEAL, border: "none", borderRadius: 16, color: WHITE, fontSize: 17, fontWeight: 700, cursor: "pointer", ...TJ }}>ابدأ كمستأجر</button>
            <button onClick={() => scrollTo("hero")} style={{ height: 56, padding: "0 32px", background: GOLD, border: "none", borderRadius: 16, color: WHITE, fontSize: 17, fontWeight: 700, cursor: "pointer", ...TJ }}>ابدأ كمالك</button>
          </div>
          {/* Store badges */}
          <div style={{ display: "flex", gap: 14, justifyContent: "center", flexWrap: "wrap" }}>
            {[
              { label: "App Store", sub: "قريبًا على", icon: <svg width="22" height="22" viewBox="0 0 24 24" fill="white"><path d="M18.71 19.5c-.83 1.24-1.71 2.45-3.05 2.47-1.34.03-1.77-.79-3.29-.79-1.53 0-2 .77-3.27.82-1.31.05-2.3-1.32-3.14-2.53C4.25 17 2.94 12.45 4.7 9.39c.87-1.52 2.43-2.48 4.12-2.51 1.28-.02 2.5.87 3.29.87.78 0 2.26-1.07 3.8-.91.65.03 2.47.26 3.64 1.98-.09.06-2.17 1.28-2.15 3.81.03 3.02 2.65 4.03 2.68 4.04-.03.07-.42 1.44-1.38 2.83M13 3.5c.73-.83 1.94-1.46 2.94-1.5.13 1.17-.34 2.35-1.04 3.19-.69.85-1.83 1.51-2.95 1.42-.15-1.15.41-2.35 1.05-3.11z"/></svg> },
              { label: "Google Play", sub: "قريبًا على", icon: <svg width="22" height="22" viewBox="0 0 24 24" fill="white"><path d="M3 20.5v-17c0-.83.94-1.3 1.6-.8l14 8.5c.6.37.6 1.23 0 1.6l-14 8.5c-.66.5-1.6.03-1.6-.8z"/></svg> },
            ].map((b, i) => (
              <div key={i} style={{ display: "flex", alignItems: "center", gap: 12, background: NAVY, borderRadius: 14, padding: "10px 20px", cursor: "pointer" }}>
                {b.icon}
                <div style={{ textAlign: "right" }}>
                  <div style={{ fontSize: 11, color: "rgba(255,255,255,0.6)", ...TJ }}>{b.sub}</div>
                  <div style={{ fontSize: 16, fontWeight: 800, color: WHITE, ...TJ }}>{b.label}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ══ FAQ ═════════════════════════════════════════════════════════════ */}
      <section id="faq-section" style={{ padding: "80px 24px", background: WHITE }}>
        <div style={{ maxWidth: 900, margin: "0 auto" }}>
          <div style={{ textAlign: "center", marginBottom: 52 }}>
            <SectionTag text="أسئلة وأجوبة" />
            <h2 style={{ fontSize: "clamp(28px, 4vw, 44px)", fontWeight: 900, color: NAVY, margin: 0, ...TJ }}>أسئلة شائعة</h2>
          </div>
          <FaqSection />
        </div>
      </section>

      {/* ══ FOOTER ══════════════════════════════════════════════════════════ */}
      <footer style={{ background: NAVY, padding: "56px 24px 28px" }}>
        <div style={{ maxWidth: 1200, margin: "0 auto" }}>
          <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr 1fr 1fr", gap: 40, marginBottom: 48, direction: "rtl" }}>
            {/* Brand */}
            <div>
              <div style={{ marginBottom: 16 }}>
                <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 16 }}>
                  <div style={{ width: 40, height: 40, borderRadius: 12, background: TEAL, display: "flex", alignItems: "center", justifyContent: "center" }}>
                    <svg width="22" height="22" viewBox="0 0 18 18" fill="none"><path d="M9,2 L16,8 L14,8 L14,16 L4,16 L4,8 L2,8 Z" fill="white" /></svg>
                  </div>
                  <div>
                    <div style={{ fontSize: 20, fontWeight: 900, color: WHITE, ...TJ }}>سكون</div>
                    <div style={{ fontSize: 12, color: "rgba(255,255,255,0.5)" }}>Sokoon</div>
                  </div>
                </div>
              </div>
              <p style={{ fontSize: 14, color: "rgba(255,255,255,0.55)", lineHeight: 1.8, margin: "0 0 20px", ...TJ }}>منصة عقارات للإيجار تساعد المستأجر والمالك يتعاملوا بسهولة وثقة.</p>
              <div style={{ display: "flex", gap: 10 }}>
                {[
                  <svg key="fb" width="18" height="18" viewBox="0 0 24 24" fill="white"><path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/></svg>,
                  <svg key="ig" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="1.8" strokeLinecap="round"><rect x="2" y="2" width="20" height="20" rx="5" ry="5"/><path d="M16 11.37A4 4 0 1112.63 8 4 4 0 0116 11.37z"/><line x1="17.5" y1="6.5" x2="17.51" y2="6.5"/></svg>,
                  <svg key="li" width="18" height="18" viewBox="0 0 24 24" fill="white"><path d="M16 8a6 6 0 016 6v7h-4v-7a2 2 0 00-2-2 2 2 0 00-2 2v7h-4v-7a6 6 0 016-6zM2 9h4v12H2z"/><circle cx="4" cy="4" r="2"/></svg>,
                ].map((icon, i) => (
                  <button key={i} style={{ width: 36, height: 36, borderRadius: 10, background: "rgba(255,255,255,0.1)", border: "1px solid rgba(255,255,255,0.12)", cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center" }}>{icon}</button>
                ))}
              </div>
            </div>
            {/* Links */}
            {[
              { title: "المنصة", links: ["الرئيسية","للمستأجر","للمالك","كيف يعمل؟"] },
              { title: "المساعدة", links: ["مركز المساعدة","تواصل معنا","الأسئلة الشائعة"] },
              { title: "قانوني", links: ["الشروط والأحكام","سياسة الخصوصية"] },
            ].map((col, i) => (
              <div key={i}>
                <div style={{ fontSize: 14, fontWeight: 800, color: WHITE, marginBottom: 16, ...TJ }}>{col.title}</div>
                <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                  {col.links.map((link, j) => (
                    <button key={j} style={{ background: "none", border: "none", color: "rgba(255,255,255,0.55)", fontSize: 14, cursor: "pointer", textAlign: "right", ...TJ }}>{link}</button>
                  ))}
                </div>
              </div>
            ))}
          </div>
          {/* Bottom */}
          <div style={{ borderTop: "1px solid rgba(255,255,255,0.1)", paddingTop: 24, display: "flex", justifyContent: "space-between", alignItems: "center", direction: "rtl" }}>
            <span style={{ fontSize: 13, color: "rgba(255,255,255,0.4)", ...TJ }}>© Sokoon. All rights reserved.</span>
            <span style={{ fontSize: 13, color: "rgba(255,255,255,0.3)", ...TJ }}>مصر · Egypt</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
