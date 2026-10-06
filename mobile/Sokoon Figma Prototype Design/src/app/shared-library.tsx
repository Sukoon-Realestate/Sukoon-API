import React, { useState } from "react";

// ─── Board UI tokens (dark board background only) ─────────────────────
const BOARD   = "#07101E";
const PANEL   = "#0B1628";
const CARD_B  = "#0E1E30";
const BDR_B   = "#1A2F45";
const TEAL_B  = "#0F766E";
const GOLD_B  = "#D4A84B";
const PURP_B  = "#A855F7";
const BLUE_B  = "#3B82F6";
const GREEN_B = "#22C55E";
const ROSE_B  = "#F43F5E";
const SLATE_B = "#64748B";

// ─── App component tokens (light theme — exact match from real screens) ─
const TEAL  = "#0F766E";
const TEAL_L = "#CCFBF1";   // tealLight
const NAVY  = "#111827";    // text
const GRAY  = "#6B7280";    // sub
const LGRAY = "#9CA3AF";    // placeholder
const BDR   = "#E5E7EB";    // border
const BGAPP = "#F8FAFC";    // page bg
const WHITE = "#FFFFFF";    // card bg
const GREEN = "#16A34A";
const GREEN_L = "#DCFCE7";
const BLUE  = "#2563EB";
const BLUE_L = "#DBEAFE";
const AMBER = "#F59E0B";
const AMBER_L = "#FFFBEB";
const ROSE  = "#E11D48";
const ROSE_L = "#FEE2E2";
const F3    = "#F3F4F6";    // input bg / secondary btn bg

const TJ:   React.CSSProperties = { fontFamily: "'Tajawal', sans-serif" };
const MONO: React.CSSProperties = { fontFamily: "'DM Mono', monospace" };

// ══════════════════════════════════════════════════════════════════════
// BOARD HELPERS
// ══════════════════════════════════════════════════════════════════════
function GroupHeader({ letter, label, color = TEAL_B }: { letter: string; label: string; color?: string }) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 14, margin: "48px 0 24px" }}>
      <div style={{
        width: 30, height: 30, borderRadius: 8, background: `${color}20`,
        border: `1.5px solid ${color}40`, display: "flex", alignItems: "center",
        justifyContent: "center", fontSize: 12, fontWeight: 900, color, flexShrink: 0, ...MONO,
      }}>{letter}</div>
      <span style={{ fontSize: 14, fontWeight: 800, color: "#CBD5E1", letterSpacing: 0.5 }}>{label}</span>
      <div style={{ flex: 1, height: 1, background: `linear-gradient(90deg, ${color}30, transparent)` }} />
    </div>
  );
}

function CompWrapper({ id, name, ar, used, children, w = "auto" }: {
  id: string; name: string; ar: string; used: string[]; children: React.ReactNode; w?: number | string;
}) {
  return (
    <div style={{ flexShrink: 0, width: w }}>
      {/* real component on neutral bg */}
      <div style={{
        background: BGAPP, border: `1px solid ${BDR_B}`, borderRadius: 20,
        padding: 20, display: "flex", flexDirection: "column", gap: 0,
      }}>{children}</div>
      <div style={{ marginTop: 10 }}>
        <span style={{ fontSize: 8.5, color: GOLD_B, letterSpacing: 2, display: "block", ...MONO }}>{id}</span>
        <span style={{ fontSize: 12, fontWeight: 700, color: "#E2E8F0", display: "block", marginTop: 2, ...TJ }}>{name}</span>
        <span style={{ fontSize: 11, color: SLATE_B, display: "block", ...TJ }}>{ar}</span>
        <div style={{ display: "flex", flexWrap: "wrap", gap: 4, marginTop: 5 }}>
          {used.map(u => (
            <span key={u} style={{
              fontSize: 8.5, color: SLATE_B, background: "#0E1E30",
              border: `1px solid ${BDR_B}`, borderRadius: 10, padding: "1px 8px", ...TJ,
            }}>{u}</span>
          ))}
        </div>
      </div>
    </div>
  );
}

function Row({ children }: { children: React.ReactNode }) {
  return <div style={{ display: "flex", flexWrap: "wrap", gap: 20, alignItems: "flex-start" }}>{children}</div>;
}

// ══════════════════════════════════════════════════════════════════════
// A. NAVIGATION — exact from real screens
// ══════════════════════════════════════════════════════════════════════

// Tenant bottom nav — exact 5-tab structure from screens-tenant.tsx
function TenantBottomNavReal({ active = "home" }: { active?: string }) {
  const items = [
    { key: "home",    icon: "🏠", label: "الرئيسية" },
    { key: "search",  icon: "🔍", label: "بحث"      },
    { key: "saved",   icon: "❤️",  label: "المحفوظة" },
    { key: "chat",    icon: "💬",  label: "الدردشة"  },
    { key: "profile", icon: "👤",  label: "حسابي"    },
  ];
  return (
    <div style={{
      background: WHITE, borderTop: `1px solid ${BDR}`,
      display: "flex", justifyContent: "space-around", alignItems: "flex-end",
      padding: "10px 8px 16px", width: 320,
    }}>
      {items.map(it => (
        <div key={it.key} style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 3, minWidth: 48 }}>
          <div style={{
            width: 36, height: 36, borderRadius: 12, display: "flex", alignItems: "center", justifyContent: "center",
            background: active === it.key ? `${TEAL}14` : "transparent",
          }}>
            <span style={{ fontSize: 18 }}>{it.icon}</span>
          </div>
          <span style={{ fontSize: 9, fontWeight: active === it.key ? 800 : 500, color: active === it.key ? TEAL : LGRAY, ...TJ }}>{it.label}</span>
          {active === it.key && <div style={{ width: 4, height: 4, borderRadius: 2, background: TEAL }} />}
        </div>
      ))}
    </div>
  );
}

// Owner bottom nav — exact 4-tab structure from screens-owner.tsx
function OwnerBottomNavReal({ active = "home" }: { active?: string }) {
  const items = [
    { key: "home",       icon: "🏘️",  label: "لوحتي"    },
    { key: "properties", icon: "🏠",  label: "قوائمي"   },
    { key: "requests",   icon: "📋",  label: "الطلبات"  },
    { key: "chat",       icon: "💬",  label: "الدردشة"  },
    { key: "more",       icon: "☰",   label: "المزيد"   },
  ];
  return (
    <div style={{
      background: WHITE, borderTop: `1px solid ${BDR}`,
      display: "flex", justifyContent: "space-around", alignItems: "flex-end",
      padding: "10px 8px 16px", width: 320,
    }}>
      {items.map(it => (
        <div key={it.key} style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 3, minWidth: 44 }}>
          <div style={{
            width: 36, height: 36, borderRadius: 12, display: "flex", alignItems: "center", justifyContent: "center",
            background: active === it.key ? `${AMBER}18` : "transparent",
          }}>
            <span style={{ fontSize: 18 }}>{it.icon}</span>
          </div>
          <span style={{ fontSize: 9, fontWeight: active === it.key ? 800 : 500, color: active === it.key ? AMBER : LGRAY, ...TJ }}>{it.label}</span>
          {active === it.key && <div style={{ width: 4, height: 4, borderRadius: 2, background: AMBER }} />}
        </div>
      ))}
    </div>
  );
}

// Top header / back bar — exact from screens-updates.tsx
function TopHeaderReal({ title = "توثيق الهوية" }: { title?: string }) {
  return (
    <div style={{
      display: "flex", alignItems: "center", gap: 12,
      padding: "8px 16px 10px", background: WHITE, borderBottom: `1px solid ${BDR}`,
      width: 320,
    }}>
      <button style={{
        width: 36, height: 36, borderRadius: 18, border: "none",
        background: F3, cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center",
      }}>
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke={NAVY} strokeWidth="2.5" strokeLinecap="round">
          <polyline points="9 18 15 12 9 6"/>
        </svg>
      </button>
      <span style={{ fontSize: 17, fontWeight: 800, color: NAVY, flex: 1, ...TJ }}>{title}</span>
    </div>
  );
}

// Property Details overlay header — exact from screens-updates.tsx
function PropertyDetailHeader() {
  return (
    <div style={{ position: "relative", height: 140, background: "linear-gradient(135deg,#0D6B63,#0F766E)", borderRadius: 12, overflow: "hidden", width: 280 }}>
      <div style={{ position: "absolute", top: 0, left: 0, right: 0, display: "flex", alignItems: "center", justifyContent: "space-between", padding: "10px 14px", zIndex: 2 }}>
        <button style={{ width: 36, height: 36, borderRadius: 18, background: "rgba(0,0,0,0.35)", border: "none", cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center" }}>
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5" strokeLinecap="round"><polyline points="9 18 15 12 9 6"/></svg>
        </button>
        <div style={{ display: "flex", gap: 8 }}>
          <button style={{ width: 36, height: 36, borderRadius: 18, background: "rgba(0,0,0,0.35)", border: "none", cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center" }}>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2" strokeLinecap="round">
              <circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/>
              <line x1="8.59" y1="13.51" x2="15.42" y2="17.49"/><line x1="15.41" y1="6.51" x2="8.59" y2="10.49"/>
            </svg>
          </button>
          <button style={{ width: 36, height: 36, borderRadius: 18, background: "rgba(0,0,0,0.35)", border: "none", cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center" }}>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2" strokeLinecap="round">
              <path d="M20.84 4.61a5.5 5.5 0 00-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 00-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 000-7.78z"/>
            </svg>
          </button>
        </div>
      </div>
      <div style={{ position: "absolute", bottom: 12, left: 14 }}>
        <span style={{ background: TEAL, color: WHITE, fontSize: 11, fontWeight: 700, padding: "4px 10px", borderRadius: 8, ...TJ }}>موثّق ✓</span>
      </div>
      <div style={{ position: "absolute", bottom: 12, right: 14, fontSize: 11, color: "rgba(255,255,255,0.7)", ...TJ }}>
        صورة ١ من ٦ ▸
      </div>
    </div>
  );
}

// ══════════════════════════════════════════════════════════════════════
// B. CARDS — exact from real screens
// ══════════════════════════════════════════════════════════════════════

// Property Card — exact from SearchResultsScreen in screens-tenant.tsx
function PropertyCardReal() {
  return (
    <div style={{ background: WHITE, border: `1px solid ${BDR}`, borderRadius: 24, overflow: "hidden", width: 240 }}>
      <div style={{ position: "relative", height: 130, background: "#E2E8F0", display: "flex", alignItems: "center", justifyContent: "center" }}>
        <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="#94A3B8" strokeWidth="1.5" strokeLinecap="round"><path d="M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>
        <button style={{ position: "absolute", top: 10, left: 10, width: 32, height: 32, borderRadius: 16, background: "rgba(255,255,255,0.9)", border: "none", cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center" }}>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#9CA3AF" strokeWidth="2" strokeLinecap="round"><path d="M20.84 4.61a5.5 5.5 0 00-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 00-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 000-7.78z"/></svg>
        </button>
        <div style={{ position: "absolute", top: 10, right: 10, background: TEAL_L, border: `1px solid ${TEAL}30`, borderRadius: 10, padding: "2px 8px" }}>
          <span style={{ fontSize: 10, fontWeight: 700, color: TEAL, ...TJ }}>موثّق ✓</span>
        </div>
        <div style={{ position: "absolute", bottom: 10, right: 10, background: TEAL, borderRadius: 8, padding: "3px 8px" }}>
          <span style={{ fontSize: 11, fontWeight: 700, color: WHITE, ...TJ }}>٣٥٠٠ ج/شهر</span>
        </div>
      </div>
      <div style={{ padding: "12px 16px", direction: "rtl" }}>
        <p style={{ fontSize: 13, fontWeight: 900, color: NAVY, margin: "0 0 4px", ...TJ }}>شقة مفروشة — مدينة نصر</p>
        <div style={{ display: "flex", alignItems: "center", gap: 10, fontSize: 11, color: GRAY, marginBottom: 10 }}>
          <span style={TJ}>٣ غرفة</span><span>·</span>
          <span style={TJ}>١٢٠م²</span><span>·</span>
          <span style={{ display: "flex", alignItems: "center", gap: 2 }}>
            <svg width="10" height="10" viewBox="0 0 24 24" fill="#FBBF24" stroke="#FBBF24" strokeWidth="1"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>
            <span style={TJ}>٤.٨ (٢٤)</span>
          </span>
        </div>
        <button style={{ width: "100%", padding: "10px 0", borderRadius: 12, background: TEAL, border: "none", cursor: "pointer" }}>
          <span style={{ fontSize: 13, fontWeight: 700, color: WHITE, ...TJ }}>اعرض التفاصيل</span>
        </button>
      </div>
    </div>
  );
}

// Visit Request Card — exact from screens-owner.tsx
function VisitRequestCardReal() {
  return (
    <div style={{ background: WHITE, border: `1px solid ${BDR}`, borderRadius: 20, padding: 16, width: 280 }}>
      <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 12, direction: "rtl" }}>
        <div style={{ width: 40, height: 40, borderRadius: 20, background: TEAL_L, display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke={TEAL} strokeWidth="2" strokeLinecap="round"><path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
        </div>
        <div style={{ flex: 1 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
            <span style={{ fontSize: 13, fontWeight: 900, color: NAVY, ...TJ }}>محمد الأحمدي</span>
            <span style={{ fontSize: 9, fontWeight: 700, color: TEAL, background: TEAL_L, border: `1px solid ${TEAL}30`, borderRadius: 8, padding: "1px 6px", ...TJ }}>موثّق ✓</span>
          </div>
          <p style={{ fontSize: 11, color: GRAY, margin: 0, ...TJ }}>شقة مفروشة — مدينة نصر</p>
        </div>
        <span style={{ fontSize: 10, fontWeight: 700, color: GREEN, background: GREEN_L, borderRadius: 10, padding: "3px 8px", ...TJ }}>مقبول</span>
      </div>
      <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 8, paddingRight: 4, direction: "rtl" }}>
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke={TEAL} strokeWidth="2" strokeLinecap="round"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>
        <span style={{ fontSize: 11, fontWeight: 700, color: NAVY, ...TJ }}>الأربعاء، ١٠ يوليو — ٣:٠٠م</span>
      </div>
      <div style={{ background: GREEN_L, borderRadius: 12, padding: "8px 12px", marginBottom: 12, display: "flex", alignItems: "center", gap: 8, direction: "rtl" }}>
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke={GREEN} strokeWidth="2" strokeLinecap="round"><path d="M22 16.92v3a2 2 0 01-2.18 2 19.79 19.79 0 01-8.63-3.07A19.5 19.5 0 013.07 9.8a19.79 19.79 0 01-3.07-8.63A2 2 0 012 .18h3a2 2 0 012 1.72 12.84 12.84 0 00.7 2.81 2 2 0 01-.45 2.11L6.91 7.91a16 16 0 006.16 6.16l1.27-1.27a2 2 0 012.11-.45 12.84 12.84 0 002.81.7A2 2 0 0122 16.92z"/></svg>
        <span style={{ fontSize: 11, fontWeight: 700, color: "#166534", ...TJ }}>الرقم بعد القبول: ٠١٢ ٣٤٥ ٦٧٨٩</span>
      </div>
      <div style={{ display: "flex", gap: 8 }}>
        <button style={{ flex: 1, padding: "10px 0", borderRadius: 12, background: BLUE_L, border: "none", cursor: "pointer" }}>
          <span style={{ fontSize: 12, fontWeight: 700, color: BLUE, ...TJ }}>شات</span>
        </button>
        <button style={{ flex: 1, padding: "10px 0", borderRadius: 12, background: ROSE_L, border: "none", cursor: "pointer" }}>
          <span style={{ fontSize: 12, fontWeight: 700, color: "#DC2626", ...TJ }}>إلغاء الزيارة</span>
        </button>
      </div>
    </div>
  );
}

// Notification Card — exact style from screens-tenant.tsx / screens-owner.tsx
function NotificationCardReal() {
  return (
    <div style={{ background: WHITE, border: `1px solid ${BDR}`, borderRadius: 18, padding: "14px 16px", width: 280, display: "flex", gap: 12, alignItems: "flex-start", direction: "rtl" }}>
      <div style={{ width: 42, height: 42, borderRadius: 14, background: TEAL_L, display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke={TEAL} strokeWidth="2" strokeLinecap="round"><path d="M18 8A6 6 0 006 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 01-3.46 0"/></svg>
      </div>
      <div style={{ flex: 1 }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 2 }}>
          <span style={{ fontSize: 13, fontWeight: 800, color: NAVY, ...TJ }}>تم قبول طلب الزيارة</span>
          <div style={{ width: 8, height: 8, borderRadius: 4, background: TEAL, flexShrink: 0, marginTop: 4 }} />
        </div>
        <p style={{ fontSize: 11, color: GRAY, margin: 0, ...TJ }}>سيتواصل معك المالك قريباً لتأكيد التفاصيل</p>
        <span style={{ fontSize: 10, color: LGRAY, marginTop: 4, display: "block", ...TJ }}>منذ ٥ دقائق</span>
      </div>
    </div>
  );
}

// Metric Card — exact from OwnerDashboardScreen in screens-owner.tsx
function MetricCardsRow() {
  const cards = [
    { label: "عقارات نشطة",      value: "٣",   color: TEAL,  bg: TEAL_L },
    { label: "زيارات هذا الأسبوع", value: "٧",  color: BLUE,  bg: BLUE_L },
    { label: "طلبات معلقة",      value: "٢",   color: AMBER, bg: AMBER_L },
    { label: "التقييم العام",    value: "٤.٩★", color: "#D97706", bg: "#FEF3C7" },
  ];
  return (
    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10, width: 260 }}>
      {cards.map(c => (
        <div key={c.label} style={{ background: WHITE, border: `1px solid ${BDR}`, borderRadius: 16, padding: 14 }}>
          <div style={{ width: 30, height: 30, borderRadius: 10, background: c.bg, display: "flex", alignItems: "center", justifyContent: "center", marginBottom: 8 }}>
            <div style={{ width: 14, height: 14, borderRadius: 4, background: c.color, opacity: 0.5 }} />
          </div>
          <p style={{ fontSize: 22, fontWeight: 900, color: NAVY, margin: "0 0 2px", ...TJ }}>{c.value}</p>
          <p style={{ fontSize: 10, color: GRAY, margin: 0, ...TJ }}>{c.label}</p>
        </div>
      ))}
    </div>
  );
}

// Accept / Reject request row — from OwnerDashboardScreen
function AcceptRejectCard() {
  return (
    <div style={{ background: WHITE, border: `1px solid ${BDR}`, borderRadius: 16, padding: "14px 16px", width: 280, direction: "rtl" }}>
      <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
        <div style={{ width: 36, height: 36, borderRadius: 18, background: BLUE_L, display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke={BLUE} strokeWidth="2" strokeLinecap="round"><path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
        </div>
        <div style={{ flex: 1 }}>
          <p style={{ fontSize: 13, fontWeight: 900, color: NAVY, margin: 0, ...TJ }}>أحمد خالد</p>
          <p style={{ fontSize: 10, color: GRAY, margin: 0, ...TJ }}>شقة النزهة · الأحد ٧ يوليو</p>
        </div>
        <div style={{ display: "flex", gap: 6 }}>
          <button style={{ padding: "6px 10px", borderRadius: 10, background: GREEN, border: "none", cursor: "pointer" }}>
            <span style={{ fontSize: 11, fontWeight: 800, color: WHITE, ...TJ }}>قبول</span>
          </button>
          <button style={{ padding: "6px 10px", borderRadius: 10, background: ROSE_L, border: "none", cursor: "pointer" }}>
            <span style={{ fontSize: 11, fontWeight: 800, color: "#DC2626", ...TJ }}>رفض</span>
          </button>
        </div>
      </div>
    </div>
  );
}

// ══════════════════════════════════════════════════════════════════════
// C. FORMS & INPUTS — exact from real screens
// ══════════════════════════════════════════════════════════════════════

function SearchBarReal() {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 12, padding: "12px 16px", borderRadius: 16, background: WHITE, border: `2px solid ${TEAL}`, width: 280 }}>
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke={TEAL} strokeWidth="2.5" strokeLinecap="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
      <span style={{ flex: 1, fontSize: 13, color: LGRAY, ...TJ }}>مدينة نصر، القاهرة…</span>
      <button style={{ fontSize: 11, fontWeight: 700, color: TEAL, background: TEAL_L, borderRadius: 10, padding: "4px 10px", border: "none", cursor: "pointer", ...TJ }}>بحث</button>
    </div>
  );
}

function EmailInputReal() {
  return (
    <div style={{ width: 280 }}>
      <div style={{ fontSize: 12, fontWeight: 700, color: NAVY, marginBottom: 6, direction: "rtl", ...TJ }}>البريد الإلكتروني</div>
      <div style={{ display: "flex", alignItems: "center", gap: 12, padding: "0 14px", height: 52, borderRadius: 14, background: WHITE, border: `1.5px solid ${BDR}`, width: "100%", boxSizing: "border-box" }}>
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke={LGRAY} strokeWidth="2" strokeLinecap="round"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/></svg>
        <span style={{ flex: 1, fontSize: 13, color: LGRAY, ...TJ }}>example@email.com</span>
      </div>
    </div>
  );
}

function PasswordInputReal() {
  return (
    <div style={{ width: 280 }}>
      <div style={{ fontSize: 12, fontWeight: 700, color: NAVY, marginBottom: 6, direction: "rtl", ...TJ }}>كلمة المرور</div>
      <div style={{ display: "flex", alignItems: "center", gap: 12, padding: "0 14px", height: 52, borderRadius: 14, background: WHITE, border: `1.5px solid ${BDR}`, width: "100%", boxSizing: "border-box" }}>
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke={LGRAY} strokeWidth="2" strokeLinecap="round"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0110 0v4"/></svg>
        <span style={{ flex: 1, fontSize: 20, color: LGRAY, letterSpacing: 4 }}>••••••••</span>
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke={LGRAY} strokeWidth="2" strokeLinecap="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
      </div>
    </div>
  );
}

function OTPInputReal() {
  return (
    <div style={{ width: 280 }}>
      <div style={{ fontSize: 12, fontWeight: 700, color: NAVY, marginBottom: 12, textAlign: "center", direction: "rtl", ...TJ }}>أدخل الكود المكوّن من ٦ أرقام</div>
      <div style={{ display: "flex", gap: 8, justifyContent: "center" }}>
        {["٣","٧","٢","","",""].map((d, i) => (
          <div key={i} style={{
            width: 42, height: 52, borderRadius: 12,
            border: `1.5px solid ${d ? TEAL : BDR}`,
            background: d ? `${TEAL}06` : WHITE,
            display: "flex", alignItems: "center", justifyContent: "center",
          }}>
            <span style={{ fontSize: 20, fontWeight: 800, color: d ? TEAL : LGRAY, ...TJ }}>{d || "—"}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function NationalIDFieldReal() {
  return (
    <div style={{ width: 280 }}>
      <div style={{ fontSize: 12, fontWeight: 700, color: NAVY, marginBottom: 6, direction: "rtl", ...TJ }}>
        الرقم القومي <span style={{ color: ROSE }}>*</span>
      </div>
      <div style={{ display: "flex", alignItems: "center", padding: "0 14px", height: 52, borderRadius: 14, background: WHITE, border: `1.5px solid ${BDR}`, boxSizing: "border-box", width: "100%" }}>
        <span style={{ flex: 1, fontSize: 14, color: LGRAY, letterSpacing: 3, ...TJ }}>٢٩٠٠١٠١٥٠٠٠٠٠٠٠</span>
      </div>
      <div style={{ display: "flex", justifyContent: "space-between", marginTop: 4 }}>
        <span style={{ fontSize: 10, color: LGRAY, ...TJ }}>٠/١٤ رقم</span>
      </div>
      <div style={{ display: "flex", alignItems: "flex-start", gap: 6, marginTop: 8, padding: "8px 10px", background: "#F0FDF9", borderRadius: 8, border: `1px solid ${TEAL}18` }}>
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke={TEAL} strokeWidth="2" strokeLinecap="round" style={{ flexShrink: 0, marginTop: 1 }}><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
        <span style={{ fontSize: 10, color: TEAL, lineHeight: 1.5, ...TJ }}>الرقم القومي للمراجعة الداخلية فقط ومش هيظهر لأي مستخدم</span>
      </div>
    </div>
  );
}

// ══════════════════════════════════════════════════════════════════════
// D. BADGES & CHIPS — exact from real screens
// ══════════════════════════════════════════════════════════════════════

function BadgesSet() {
  const badges = [
    { l: "موثّق ✓",    c: TEAL,    bg: TEAL_L },
    { l: "قيد المراجعة", c: AMBER,  bg: AMBER_L },
    { l: "مرفوض",     c: "#DC2626", bg: ROSE_L },
    { l: "متاح",      c: GREEN,   bg: GREEN_L },
    { l: "مؤجر",      c: GRAY,    bg: F3 },
    { l: "جديد",      c: BLUE,    bg: BLUE_L },
  ];
  return (
    <div style={{ display: "flex", flexWrap: "wrap", gap: 8, width: 280 }}>
      {badges.map(b => (
        <span key={b.l} style={{ fontSize: 11, fontWeight: 700, color: b.c, background: b.bg, border: `1px solid ${b.c}30`, borderRadius: 12, padding: "4px 12px", ...TJ }}>{b.l}</span>
      ))}
    </div>
  );
}

function FilterChipsReal() {
  const chips = ["الكل", "شقة", "فيلا", "استوديو", "دوبلكس"];
  return (
    <div style={{ display: "flex", flexWrap: "wrap", gap: 8, width: 280 }}>
      {chips.map((c, i) => (
        <button key={c} style={{ fontSize: 12, fontWeight: i === 0 ? 700 : 500, color: i === 0 ? TEAL : NAVY, background: i === 0 ? TEAL_L : WHITE, border: `1.5px solid ${i === 0 ? TEAL : BDR}`, borderRadius: 20, padding: "6px 14px", cursor: "pointer", ...TJ }}>{c}</button>
      ))}
    </div>
  );
}

function AmenityChipsReal() {
  const chips = ["🅿️ مواقف", "❄️ مكيف", "🛜 إنترنت", "🏊 مسبح", "🔐 أمن", "🌿 حديقة"];
  return (
    <div style={{ display: "flex", flexWrap: "wrap", gap: 8, width: 280 }}>
      {chips.map(c => (
        <span key={c} style={{ fontSize: 11, color: GRAY, background: WHITE, border: `1px solid ${BDR}`, borderRadius: 20, padding: "5px 12px", ...TJ }}>{c}</span>
      ))}
    </div>
  );
}

function SuitableForChips() {
  const chips = ["الكل", "ولاد فقط", "بنات فقط", "عائلات", "أفراد", "مشاركة"];
  return (
    <div style={{ display: "flex", flexWrap: "wrap", gap: 8, width: 280 }}>
      {chips.map((c, i) => (
        <button key={c} style={{ fontSize: 12, fontWeight: i === 0 ? 700 : 500, color: i === 0 ? TEAL : NAVY, background: i === 0 ? `${TEAL}12` : WHITE, border: `1.5px solid ${i === 0 ? TEAL : BDR}`, borderRadius: 20, padding: "7px 16px", cursor: "pointer", ...TJ }}>{c}</button>
      ))}
    </div>
  );
}

// ══════════════════════════════════════════════════════════════════════
// E. BANNERS — exact from real screens
// ══════════════════════════════════════════════════════════════════════

function PrivacyBannerReal() {
  return (
    <div style={{ display: "flex", alignItems: "flex-start", gap: 10, padding: "10px 14px", background: `${TEAL}10`, border: `1px solid ${TEAL}25`, borderRadius: 12, width: 280, direction: "rtl" }}>
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke={TEAL} strokeWidth="2" strokeLinecap="round" style={{ flexShrink: 0, marginTop: 2 }}><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
      <span style={{ fontSize: 12, color: TEAL, fontWeight: 600, lineHeight: 1.5, ...TJ }}>الرقم سيظهر بعد تأكيد التوثيق</span>
    </div>
  );
}

function ChatRestrictedBanner() {
  return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 12, padding: 20, width: 280 }}>
      <div style={{ width: 64, height: 64, borderRadius: 20, background: AMBER_L, display: "flex", alignItems: "center", justifyContent: "center" }}>
        <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke={AMBER} strokeWidth="2" strokeLinecap="round"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0110 0v4"/></svg>
      </div>
      <div style={{ textAlign: "center" }}>
        <p style={{ fontSize: 15, fontWeight: 900, color: NAVY, margin: "0 0 6px", ...TJ }}>الشات محدود لحسابات موثّقة</p>
        <p style={{ fontSize: 12, color: GRAY, margin: 0, ...TJ }}>عشان تقدر تتواصل مع الملاك، لازم توثّق هويتك الأول</p>
      </div>
      <div style={{ display: "flex", alignItems: "center", gap: 8, padding: "10px 14px", background: AMBER_L, border: `1px solid ${AMBER}30`, borderRadius: 12, width: "100%", direction: "rtl" }}>
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke={AMBER} strokeWidth="2.5" strokeLinecap="round"><path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
        <span style={{ fontSize: 12, fontWeight: 600, color: "#92400E", flex: 1, ...TJ }}>الشات لمستخدمين موثّقين فقط</span>
        <span style={{ fontSize: 11, fontWeight: 700, color: AMBER, ...TJ }}>وثّق الآن</span>
      </div>
    </div>
  );
}

function WarningBannerReal() {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 10, padding: "10px 14px", background: AMBER_L, border: `1px solid ${AMBER}30`, borderRadius: 12, width: 280, direction: "rtl" }}>
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke={AMBER} strokeWidth="2.5" strokeLinecap="round" style={{ flexShrink: 0 }}><path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
      <span style={{ fontSize: 12, fontWeight: 600, color: "#92400E", flex: 1, ...TJ }}>يرجى إكمال توثيق هويتك أولاً</span>
      <span style={{ fontSize: 11, fontWeight: 700, color: AMBER, ...TJ }}>وثّق الآن</span>
    </div>
  );
}

function VisitorModeBanner() {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 10, padding: "10px 14px", background: `${BLUE}10`, border: `1px solid ${BLUE}25`, borderRadius: 12, width: 280, direction: "rtl" }}>
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke={BLUE} strokeWidth="2" strokeLinecap="round" style={{ flexShrink: 0 }}><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
      <span style={{ fontSize: 12, fontWeight: 600, color: BLUE, flex: 1, ...TJ }}>أنت تتصفح كزائر — سجّل دخولك للوصول الكامل</span>
    </div>
  );
}

// ══════════════════════════════════════════════════════════════════════
// F. CHAT COMPONENTS — exact from screens-tenant.tsx
// ══════════════════════════════════════════════════════════════════════

function ChatBubblesReal() {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 10, width: 280, padding: "4px 0" }}>
      {/* Received */}
      <div style={{ display: "flex", justifyContent: "flex-start" }}>
        <div style={{ background: WHITE, border: `1px solid ${BDR}`, borderRadius: "18px 18px 18px 4px", padding: "10px 14px", maxWidth: "78%" }}>
          <p style={{ fontSize: 13, color: NAVY, margin: 0, ...TJ }}>هل الشقة متاحة للإيجار الآن؟</p>
          <span style={{ fontSize: 9, color: LGRAY, display: "block", textAlign: "left", marginTop: 3 }}>١٠:٤٢ ص</span>
        </div>
      </div>
      {/* Sent */}
      <div style={{ display: "flex", justifyContent: "flex-end" }}>
        <div style={{ background: TEAL, borderRadius: "18px 18px 4px 18px", padding: "10px 14px", maxWidth: "78%" }}>
          <p style={{ fontSize: 13, color: WHITE, margin: 0, ...TJ }}>نعم، متاحة من أول الشهر القادم</p>
          <div style={{ display: "flex", alignItems: "center", gap: 4, justifyContent: "flex-end", marginTop: 3 }}>
            <span style={{ fontSize: 9, color: "rgba(255,255,255,0.65)" }}>١٠:٤٥ ص</span>
            <svg width="14" height="9" viewBox="0 0 24 15" fill="none" stroke="rgba(255,255,255,0.9)" strokeWidth="2.5" strokeLinecap="round"><polyline points="1 7 8 14 23 1"/><polyline points="7 7 14 14" strokeOpacity="0.6"/></svg>
          </div>
        </div>
      </div>
    </div>
  );
}

function ChatInputBarReal() {
  return (
    <div style={{ background: WHITE, borderTop: `1px solid ${BDR}`, padding: "10px 14px", display: "flex", alignItems: "center", gap: 10, width: 280 }}>
      <button style={{ width: 36, height: 36, borderRadius: 12, background: F3, border: "none", cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke={GRAY} strokeWidth="2" strokeLinecap="round"><path d="M21.44 11.05l-9.19 9.19a6 6 0 01-8.49-8.49l9.19-9.19a4 4 0 015.66 5.66l-9.2 9.19a2 2 0 01-2.83-2.83l8.49-8.48"/></svg>
      </button>
      <div style={{ flex: 1, background: BGAPP, borderRadius: 18, padding: "8px 14px", border: `1px solid ${BDR}` }}>
        <span style={{ fontSize: 13, color: LGRAY, ...TJ }}>اكتب رسالتك…</span>
      </div>
      <button style={{ width: 36, height: 36, borderRadius: 12, background: TEAL, border: "none", cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
        <svg width="16" height="16" viewBox="0 0 24 24" fill="white" style={{ transform: "rotate(45deg)" }}><path d="M2 21l21-9L2 3v7l15 2-15 2z"/></svg>
      </button>
    </div>
  );
}

function AttachmentSheet() {
  const opts = [
    { icon: "📷", label: "الكاميرا" },
    { icon: "🖼️", label: "الصور" },
    { icon: "📄", label: "الملفات" },
    { icon: "📍", label: "الموقع" },
  ];
  return (
    <div style={{ background: WHITE, borderRadius: "22px 22px 0 0", padding: "16px 20px 32px", width: 280 }}>
      <div style={{ width: 36, height: 4, borderRadius: 2, background: BDR, margin: "0 auto 18px" }} />
      <div style={{ display: "flex", justifyContent: "space-around" }}>
        {opts.map(o => (
          <div key={o.label} style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 6 }}>
            <div style={{ width: 52, height: 52, borderRadius: 16, background: F3, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 22 }}>{o.icon}</div>
            <span style={{ fontSize: 10, color: GRAY, ...TJ }}>{o.label}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

// ══════════════════════════════════════════════════════════════════════
// G. SHEETS & MODALS — exact from real screens
// ══════════════════════════════════════════════════════════════════════

function ShareSheetReal() {
  return (
    <div style={{ background: WHITE, borderRadius: "24px 24px 0 0", padding: "20px 20px 32px", width: 300 }}>
      <div style={{ width: 40, height: 4, borderRadius: 2, background: BDR, margin: "0 auto 20px" }} />
      <div style={{ fontSize: 16, fontWeight: 700, color: NAVY, marginBottom: 16, direction: "rtl", ...TJ }}>مشاركة العقار</div>
      <div style={{ background: `${TEAL}12`, border: `1px solid ${TEAL}30`, borderRadius: 10, padding: "10px 14px", marginBottom: 12, display: "flex", alignItems: "center", gap: 8 }}>
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke={TEAL} strokeWidth="2.5" strokeLinecap="round"><polyline points="20 6 9 17 4 12"/></svg>
        <span style={{ fontSize: 12, color: TEAL, fontWeight: 600, ...TJ }}>تم نسخ رابط العقار ✓</span>
      </div>
      {["نسخ الرابط", "مشاركة", "إلغاء"].map((label, i) => (
        <button key={label} style={{
          width: "100%", padding: "14px 16px", border: `1px solid ${BDR}`, borderRadius: 14,
          background: WHITE, cursor: "pointer", marginBottom: 8, textAlign: "right", ...TJ,
        }}>
          <span style={{ fontSize: 15, fontWeight: 600, color: i === 0 ? TEAL : i === 1 ? BLUE : ROSE }}>{label}</span>
        </button>
      ))}
    </div>
  );
}

function FilterSheetReal() {
  return (
    <div style={{ background: WHITE, borderRadius: "24px 24px 0 0", padding: "20px 20px 28px", width: 300 }}>
      <div style={{ width: 40, height: 4, borderRadius: 2, background: BDR, margin: "0 auto 16px" }} />
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16, direction: "rtl" }}>
        <span style={{ fontSize: 16, fontWeight: 700, color: NAVY, ...TJ }}>تصفية النتائج</span>
        <span style={{ fontSize: 12, fontWeight: 700, color: TEAL, ...TJ }}>إعادة تعيين</span>
      </div>
      <div style={{ fontSize: 13, fontWeight: 700, color: NAVY, marginBottom: 8, direction: "rtl", ...TJ }}>مناسب لـ</div>
      <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 16 }}>
        {["الكل", "عائلات", "أفراد", "بنات فقط"].map((c, i) => (
          <button key={c} style={{ padding: "6px 14px", borderRadius: 20, border: `1.5px solid ${i === 0 ? TEAL : BDR}`, background: i === 0 ? `${TEAL}12` : WHITE, color: i === 0 ? TEAL : NAVY, fontSize: 12, fontWeight: i === 0 ? 700 : 400, cursor: "pointer", ...TJ }}>{c}</button>
        ))}
      </div>
      <div style={{ fontSize: 13, fontWeight: 700, color: NAVY, marginBottom: 8, direction: "rtl", ...TJ }}>فترة التأجير</div>
      <div style={{ display: "flex", gap: 8 }}>
        {["يوم", "أسبوع", "شهر"].map((p, i) => (
          <button key={p} style={{ flex: 1, padding: "10px 0", borderRadius: 12, border: `1.5px solid ${i === 2 ? TEAL : BDR}`, background: i === 2 ? `${TEAL}12` : WHITE, color: i === 2 ? TEAL : NAVY, fontSize: 13, fontWeight: i === 2 ? 700 : 400, cursor: "pointer", ...TJ }}>{p}</button>
        ))}
      </div>
    </div>
  );
}

function LogoutSheetReal() {
  return (
    <div style={{ background: WHITE, borderRadius: "24px 24px 0 0", padding: "20px 20px 36px", width: 300 }}>
      <div style={{ width: 40, height: 4, borderRadius: 2, background: BDR, margin: "0 auto 20px" }} />
      <div style={{ textAlign: "center", marginBottom: 20 }}>
        <div style={{ width: 56, height: 56, borderRadius: 18, background: ROSE_L, display: "flex", alignItems: "center", justifyContent: "center", margin: "0 auto 12px" }}>
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke={ROSE} strokeWidth="2" strokeLinecap="round"><path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>
        </div>
        <p style={{ fontSize: 15, fontWeight: 900, color: NAVY, margin: "0 0 6px", ...TJ }}>تسجيل الخروج</p>
        <p style={{ fontSize: 12, color: GRAY, margin: 0, ...TJ }}>هل أنت متأكد من تسجيل الخروج؟</p>
      </div>
      <div style={{ display: "flex", gap: 10 }}>
        <button style={{ flex: 1, padding: "13px 0", borderRadius: 14, background: ROSE, border: "none", cursor: "pointer" }}>
          <span style={{ fontSize: 13, fontWeight: 700, color: WHITE, ...TJ }}>تسجيل الخروج</span>
        </button>
        <button style={{ flex: 1, padding: "13px 0", borderRadius: 14, background: F3, border: "none", cursor: "pointer" }}>
          <span style={{ fontSize: 13, fontWeight: 700, color: NAVY, ...TJ }}>إلغاء</span>
        </button>
      </div>
    </div>
  );
}

function DeleteConfirmSheet() {
  return (
    <div style={{ background: WHITE, borderRadius: "24px 24px 0 0", padding: "20px 20px 36px", width: 300 }}>
      <div style={{ width: 40, height: 4, borderRadius: 2, background: BDR, margin: "0 auto 20px" }} />
      <div style={{ textAlign: "center", marginBottom: 20 }}>
        <div style={{ width: 56, height: 56, borderRadius: 18, background: ROSE_L, display: "flex", alignItems: "center", justifyContent: "center", margin: "0 auto 12px" }}>
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke={ROSE} strokeWidth="2" strokeLinecap="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14H6L5 6"/><path d="M10 11v6"/><path d="M14 11v6"/><path d="M9 6V4h6v2"/></svg>
        </div>
        <p style={{ fontSize: 15, fontWeight: 900, color: NAVY, margin: "0 0 6px", ...TJ }}>حذف العقار</p>
        <p style={{ fontSize: 12, color: GRAY, margin: 0, ...TJ }}>هذا الإجراء لا يمكن التراجع عنه</p>
      </div>
      <div style={{ display: "flex", gap: 10 }}>
        <button style={{ flex: 1, padding: "13px 0", borderRadius: 14, background: ROSE, border: "none", cursor: "pointer" }}>
          <span style={{ fontSize: 13, fontWeight: 700, color: WHITE, ...TJ }}>حذف</span>
        </button>
        <button style={{ flex: 1, padding: "13px 0", borderRadius: 14, background: F3, border: "none", cursor: "pointer" }}>
          <span style={{ fontSize: 13, fontWeight: 700, color: NAVY, ...TJ }}>إلغاء</span>
        </button>
      </div>
    </div>
  );
}

function ReportBlockSheet() {
  return (
    <div style={{ background: WHITE, borderRadius: "24px 24px 0 0", padding: "20px 20px 32px", width: 300 }}>
      <div style={{ width: 40, height: 4, borderRadius: 2, background: BDR, margin: "0 auto 16px" }} />
      <div style={{ fontSize: 15, fontWeight: 800, color: NAVY, marginBottom: 16, direction: "rtl", ...TJ }}>إبلاغ أو حظر</div>
      {["إبلاغ عن محتوى مسيء", "إبلاغ عن خداع", "حظر هذا المستخدم"].map((o, i) => (
        <button key={o} style={{
          width: "100%", padding: "14px 16px", border: `1px solid ${BDR}`, borderRadius: 14,
          background: WHITE, cursor: "pointer", marginBottom: 8, textAlign: "right", display: "flex", alignItems: "center", gap: 10, direction: "rtl", ...TJ,
        }}>
          <div style={{ width: 32, height: 32, borderRadius: 10, background: i < 2 ? AMBER_L : ROSE_L, display: "flex", alignItems: "center", justifyContent: "center" }}>
            <span style={{ fontSize: 15 }}>{i < 2 ? "⚠️" : "🚫"}</span>
          </div>
          <span style={{ fontSize: 13, fontWeight: 600, color: i < 2 ? "#92400E" : ROSE }}>{o}</span>
        </button>
      ))}
    </div>
  );
}

// ══════════════════════════════════════════════════════════════════════
// H. STATES — exact from real screens
// ══════════════════════════════════════════════════════════════════════

function EmptyStateReal({ icon = "❤️", title = "لسه معندكش محفوظات", sub = "احفظ العقارات اللي تعجبك عشان تقدر ترجعلها بسهولة", btn = "ابدأ البحث عن سكن" }: { icon?: string; title?: string; sub?: string; btn?: string }) {
  return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 14, padding: "20px 16px", width: 260, direction: "rtl" }}>
      <div style={{ width: 80, height: 80, borderRadius: 24, background: BGAPP, border: `2px dashed ${BDR}`, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 34 }}>
        {icon}
      </div>
      <div style={{ textAlign: "center" }}>
        <p style={{ fontSize: 16, fontWeight: 900, color: NAVY, margin: "0 0 6px", ...TJ }}>{title}</p>
        <p style={{ fontSize: 12, color: GRAY, margin: 0, ...TJ }}>{sub}</p>
      </div>
      <button style={{ width: "100%", padding: "12px 0", borderRadius: 14, background: TEAL, border: "none", cursor: "pointer" }}>
        <span style={{ fontSize: 14, fontWeight: 700, color: WHITE, ...TJ }}>{btn}</span>
      </button>
    </div>
  );
}

function LoadingSkeletonReal() {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 10, width: 260, padding: 4 }}>
      <div style={{ height: 120, borderRadius: 16, background: "#E2E8F0" }} />
      <div style={{ height: 14, borderRadius: 8, background: "#E2E8F0", width: "80%" }} />
      <div style={{ height: 11, borderRadius: 8, background: "#E2E8F0", width: "55%" }} />
      <div style={{ height: 11, borderRadius: 8, background: "#E2E8F0", width: "65%" }} />
      <div style={{ height: 38, borderRadius: 12, background: "#E2E8F0", marginTop: 4 }} />
    </div>
  );
}

function PendingStateReal() {
  return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 12, padding: 24, width: 260, direction: "rtl" }}>
      <div style={{ width: 72, height: 72, borderRadius: 22, background: AMBER_L, display: "flex", alignItems: "center", justifyContent: "center" }}>
        <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke={AMBER} strokeWidth="2" strokeLinecap="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
      </div>
      <p style={{ fontSize: 16, fontWeight: 900, color: NAVY, margin: 0, ...TJ }}>قيد المراجعة</p>
      <p style={{ fontSize: 12, color: GRAY, textAlign: "center", margin: 0, ...TJ }}>طلبك قيد المراجعة من فريق سكون. عادةً خلال ٢٤ ساعة.</p>
    </div>
  );
}

function RejectedStateReal() {
  return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 12, padding: 24, width: 260, direction: "rtl" }}>
      <div style={{ width: 72, height: 72, borderRadius: 22, background: ROSE_L, display: "flex", alignItems: "center", justifyContent: "center" }}>
        <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke={ROSE} strokeWidth="2" strokeLinecap="round"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>
      </div>
      <p style={{ fontSize: 16, fontWeight: 900, color: NAVY, margin: 0, ...TJ }}>تم الرفض</p>
      <p style={{ fontSize: 12, color: GRAY, textAlign: "center", margin: 0, ...TJ }}>للأسف طلبك تم رفضه. يمكنك التواصل مع الدعم لمزيد من التفاصيل.</p>
      <button style={{ padding: "10px 20px", borderRadius: 12, background: F3, border: "none", cursor: "pointer" }}>
        <span style={{ fontSize: 12, fontWeight: 700, color: NAVY, ...TJ }}>التواصل مع الدعم</span>
      </button>
    </div>
  );
}

// ══════════════════════════════════════════════════════════════════════
// AUDIT TABLE
// ══════════════════════════════════════════════════════════════════════
const AUDIT_ROWS = [
  // Navigation
  { name:"COMP-NAV-TENANT-BOTTOM", type:"Navigation", source:"All Tenant Screens", used:"Home, Search, Saved, Chat, Profile", added:true },
  { name:"COMP-NAV-OWNER-BOTTOM",  type:"Navigation", source:"All Owner Screens",  used:"Dashboard, Listings, Requests, Chat, More", added:true },
  { name:"COMP-NAV-HEADER",        type:"Navigation", source:"screens-updates.tsx",used:"All sub-pages (KYC, Settings, Details…)", added:true },
  { name:"COMP-HEADER-PROPERTY",   type:"Navigation", source:"FullPropertyDetailScreen",used:"Property Details (Tenant, Owner, Admin)", added:true },
  // Cards
  { name:"COMP-CARD-PROPERTY",     type:"Card",       source:"SearchResultsScreen",used:"Home, Search, Saved, Nearby, Notifications", added:true },
  { name:"COMP-CARD-VISIT-REQUEST",type:"Card",       source:"OwnerVisitsDashboard",used:"Owner Requests, Visit Dashboard, Admin Visits", added:true },
  { name:"COMP-CARD-NOTIFICATION", type:"Card",       source:"TenantNotifications",used:"Tenant Notifs, Owner Notifs, Admin", added:true },
  { name:"COMP-CARD-METRIC",       type:"Card",       source:"OwnerDashboardScreen",used:"Owner Dashboard, Admin Dashboard", added:true },
  { name:"COMP-CARD-ACCEPT-REJECT",type:"Card",       source:"OwnerDashboardScreen",used:"Owner Requests, Admin Requests", added:true },
  // Inputs
  { name:"COMP-INPUT-SEARCH",      type:"Input",      source:"TenantSearchScreen", used:"Home, Search, Admin Search", added:true },
  { name:"COMP-INPUT-EMAIL",       type:"Input",      source:"LoginEmailScreen",   used:"Tenant Login, Owner Login, Register", added:true },
  { name:"COMP-INPUT-PASSWORD",    type:"Input",      source:"LoginEmailScreen",   used:"Tenant Login, Owner Login, Register", added:true },
  { name:"COMP-INPUT-OTP",         type:"Input",      source:"TenantOTPScreen",    used:"Tenant OTP, Owner OTP", added:true },
  { name:"COMP-INPUT-NATIONAL-ID", type:"Input",      source:"UpdatedTenantKYC02", used:"Tenant KYC, Owner KYC", added:true },
  // Badges & Chips
  { name:"COMP-BADGE-STATUS",      type:"Badge",      source:"PropertyCard, KYCScreens",used:"Property Card, Request Card, KYC, Admin", added:true },
  { name:"COMP-CHIP-FILTER",       type:"Chip",       source:"FilterSheetScreen",  used:"Search, Filter Sheet, Home", added:true },
  { name:"COMP-CHIP-AMENITY",      type:"Chip",       source:"PropertyDetailScreen",used:"Property Details, Add Property", added:true },
  { name:"COMP-CHIP-SUITABLE-FOR", type:"Chip",       source:"FilterSheetScreen",  used:"Filter Sheet, Add Property", added:true },
  // Banners
  { name:"COMP-BANNER-PRIVACY",    type:"Banner",     source:"OwnerVisitsDashboard",used:"Visit Card, Property Details, KYC", added:true },
  { name:"COMP-BANNER-CHAT-RESTRICTED",type:"Banner", source:"TenantChatRestricted",used:"Chat List, Chat Thread", added:true },
  { name:"COMP-BANNER-WARNING",    type:"Banner",     source:"KYC screens",        used:"KYC, Add Property, Profile", added:true },
  { name:"COMP-BANNER-VISITOR",    type:"Banner",     source:"VisitorRestrictedSheet",used:"Home, Search, Property Details", added:true },
  // Chat
  { name:"COMP-CHAT-BUBBLES",      type:"Chat",       source:"TenantChatThreadScreen",used:"Tenant Chat, Owner Chat", added:true },
  { name:"COMP-CHAT-INPUT",        type:"Chat",       source:"TenantChatThreadScreen",used:"Tenant Chat, Owner Chat", added:true },
  { name:"COMP-SHEET-ATTACHMENT",  type:"Sheet",      source:"TenantChatThreadScreen",used:"Tenant Chat, Owner Chat", added:true },
  // Sheets & Modals
  { name:"COMP-SHEET-SHARE",       type:"Sheet",      source:"FullPropertyDetailScreen",used:"Property Details, Listing Cards, Admin", added:true },
  { name:"COMP-SHEET-FILTER",      type:"Sheet",      source:"FullFilterSheetScreen", used:"Search, Home Filters, Admin", added:true },
  { name:"COMP-SHEET-LOGOUT",      type:"Sheet",      source:"TenantProfileScreen", used:"Tenant Profile, Owner Profile, Admin", added:true },
  { name:"COMP-MODAL-DELETE",      type:"Modal",      source:"OwnerMyListingsScreen",used:"My Listings, Requests, Admin", added:true },
  { name:"COMP-SHEET-REPORT",      type:"Sheet",      source:"ReportSheetScreen",   used:"Chat, Property Details, User Profile", added:true },
  // States
  { name:"COMP-STATE-EMPTY",       type:"State",      source:"SavedEmptyStateScreen",used:"Saved, Search, Requests, Notifs, Chat", added:true },
  { name:"COMP-STATE-LOADING",     type:"State",      source:"All list screens",    used:"All screens with async data", added:true },
  { name:"COMP-STATE-PENDING",     type:"State",      source:"KYCPendingScreen",    used:"KYC, Add Property, Admin queue", added:true },
  { name:"COMP-STATE-REJECTED",    type:"State",      source:"PropertyRejectionDetailScreen",used:"Owner Listings, KYC rejected", added:true },
  // Shared Screens
  { name:"SHARED-SCREEN-PROPERTY-DETAILS", type:"Screen", source:"FullPropertyDetailScreen",used:"Home, Search, Saved, Nearby, Notifications", added:true },
  { name:"SHARED-SCREEN-CHAT-DETAIL",      type:"Screen", source:"TenantChatThreadScreen",used:"Chat List (Tenant + Owner), Property CTA, Visit Confirmed", added:true },
  { name:"SHARED-SCREEN-SETTINGS",         type:"Screen", source:"TenantSettingsScreen", used:"Tenant Profile, Owner More", added:true },
  { name:"SHARED-SCREEN-VISIT-REQUEST",    type:"Screen", source:"VisitDetailScreen",    used:"Owner Requests, Tenant Visits, Admin", added:true },
  { name:"SHARED-SCREEN-KYC",              type:"Screen", source:"KYCStartScreen",       used:"Register, Profile Banner, Owner Add Property", added:true },
];

function AuditTable() {
  return (
    <div style={{ background: CARD_B, border: `1px solid ${BDR_B}`, borderRadius: 16, overflow: "hidden" }}>
      <div style={{ padding: "16px 20px", borderBottom: `1px solid ${BDR_B}`, display: "flex", alignItems: "center", gap: 10 }}>
        <span style={{ fontSize: 10, fontWeight: 800, color: GOLD_B, letterSpacing: 3, ...MONO }}>AUDIT</span>
        <span style={{ fontSize: 13, fontWeight: 700, color: "#CBD5E1" }}>Shared Components Audit — Built from real repeated patterns</span>
        <span style={{ fontSize: 9, color: SLATE_B, marginLeft: "auto", ...MONO }}>{AUDIT_ROWS.length} items</span>
      </div>
      <div style={{ overflowX: "auto" }}>
        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 11, ...TJ }}>
          <thead>
            <tr style={{ background: "#081018" }}>
              {["Item Name", "Type", "Source Screen", "Used In Screens", "Added?"].map(h => (
                <th key={h} style={{ padding: "10px 16px", textAlign: "left", color: SLATE_B, fontWeight: 700, borderBottom: `1px solid ${BDR_B}`, whiteSpace: "nowrap", ...MONO, fontSize: 9 }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {AUDIT_ROWS.map((r, i) => (
              <tr key={r.name} style={{ background: i % 2 === 0 ? "transparent" : "#081218", borderBottom: `1px solid ${BDR_B}40` }}>
                <td style={{ padding: "9px 16px", color: TEAL_B, fontWeight: 700, ...MONO, fontSize: 9.5 }}>{r.name}</td>
                <td style={{ padding: "9px 16px", whiteSpace: "nowrap" }}>
                  <span style={{ fontSize: 9.5, fontWeight: 700, color: r.type === "Screen" ? PURP_B : r.type === "Sheet" || r.type === "Modal" ? ROSE_B : TEAL_B, background: `${r.type === "Screen" ? PURP_B : r.type === "Sheet" || r.type === "Modal" ? ROSE_B : TEAL_B}15`, border: `1px solid ${r.type === "Screen" ? PURP_B : r.type === "Sheet" || r.type === "Modal" ? ROSE_B : TEAL_B}30`, borderRadius: 8, padding: "2px 7px" }}>{r.type}</span>
                </td>
                <td style={{ padding: "9px 16px", color: SLATE_B, fontSize: 10 }}>{r.source}</td>
                <td style={{ padding: "9px 16px", color: "#475569", fontSize: 10, maxWidth: 260 }}>{r.used}</td>
                <td style={{ padding: "9px 16px" }}>
                  <span style={{ fontSize: 9.5, fontWeight: 800, color: GREEN_B, background: `${GREEN_B}15`, borderRadius: 8, padding: "2px 10px" }}>✓ Yes</span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ══════════════════════════════════════════════════════════════════════
// SHARED SCREENS PANEL — phone-shell previews
// ══════════════════════════════════════════════════════════════════════
function ScreenRefReal({ id, name, ar, from, preview, color = TEAL_B }: {
  id: string; name: string; ar: string; from: string[]; preview: React.ReactNode; color?: string;
}) {
  return (
    <div style={{ flexShrink: 0, width: 200 }}>
      {/* Phone shell */}
      <div style={{
        width: 200, height: 380, background: "#0A1520", border: `1.5px solid ${BDR_B}`,
        borderRadius: 32, overflow: "hidden", position: "relative",
        boxShadow: "0 12px 48px rgba(0,0,0,0.6)",
      }}>
        {/* Dynamic island */}
        <div style={{ position: "absolute", top: 10, left: "50%", transform: "translateX(-50%)", width: 60, height: 10, background: "#000", borderRadius: 6, zIndex: 10 }} />
        <div style={{ position: "absolute", inset: 0, overflow: "hidden", borderRadius: 32 }}>
          <div style={{ transform: "scale(0.57)", transformOrigin: "top center", width: 352, marginLeft: -76 }}>
            {preview}
          </div>
        </div>
        {/* ID overlay */}
        <div style={{ position: "absolute", bottom: 10, left: 10, right: 10, background: "rgba(0,0,0,0.75)", borderRadius: 10, padding: "4px 10px", textAlign: "center" }}>
          <span style={{ fontSize: 7, fontWeight: 700, color, letterSpacing: 1, ...MONO }}>{id}</span>
        </div>
      </div>
      <div style={{ marginTop: 10 }}>
        <span style={{ fontSize: 12, fontWeight: 700, color: "#E2E8F0", display: "block", ...TJ }}>{name}</span>
        <span style={{ fontSize: 11, color: SLATE_B, display: "block", ...TJ }}>{ar}</span>
        <div style={{ fontSize: 8.5, color: `${SLATE_B}80`, marginTop: 3, marginBottom: 4, ...MONO }}>Opened from:</div>
        <div style={{ display: "flex", flexWrap: "wrap", gap: 4 }}>
          {from.map(f => (
            <span key={f} style={{ fontSize: 8, color: SLATE_B, background: "#0E1E30", border: `1px solid ${BDR_B}`, borderRadius: 8, padding: "1px 7px", ...TJ }}>{f}</span>
          ))}
        </div>
      </div>
    </div>
  );
}

// property detail screen (light)
function PropertyDetailPreview() {
  return (
    <div style={{ background: BGAPP, minHeight: 667, width: 352 }}>
      <div style={{ height: 220, background: "linear-gradient(135deg,#0D6B63,#0F766E)", position: "relative" }}>
        <div style={{ position: "absolute", top: 16, left: 14, right: 14, display: "flex", justifyContent: "space-between" }}>
          <div style={{ width: 36, height: 36, borderRadius: 18, background: "rgba(0,0,0,0.35)", display: "flex", alignItems: "center", justifyContent: "center" }}>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5" strokeLinecap="round"><polyline points="9 18 15 12 9 6"/></svg>
          </div>
          <div style={{ display: "flex", gap: 8 }}>
            <div style={{ width: 36, height: 36, borderRadius: 18, background: "rgba(0,0,0,0.35)" }} />
            <div style={{ width: 36, height: 36, borderRadius: 18, background: "rgba(0,0,0,0.35)" }} />
          </div>
        </div>
        <div style={{ position: "absolute", bottom: 12, left: 14 }}>
          <span style={{ background: TEAL, color: WHITE, fontSize: 11, fontWeight: 700, padding: "4px 10px", borderRadius: 8 }}>موثّق ✓</span>
        </div>
      </div>
      <div style={{ padding: 16 }}>
        <div style={{ fontSize: 20, fontWeight: 900, color: NAVY, marginBottom: 6, direction: "rtl" }}>شقة مفروشة — مدينة نصر</div>
        <div style={{ display: "flex", gap: 8, marginBottom: 12 }}>
          {["٣ غرفة","٢ حمام","١٢٠م²"].map(f => <span key={f} style={{ fontSize: 11, color: GRAY, background: F3, borderRadius: 10, padding: "3px 10px" }}>{f}</span>)}
        </div>
        <div style={{ fontSize: 22, fontWeight: 900, color: TEAL, marginBottom: 12 }}>٣,٥٠٠ ر.س/شهر</div>
        <button style={{ width: "100%", padding: 14, borderRadius: 14, background: TEAL, border: "none" }}>
          <span style={{ fontSize: 15, fontWeight: 700, color: WHITE }}>احجز زيارة</span>
        </button>
      </div>
    </div>
  );
}

function ChatDetailPreview() {
  return (
    <div style={{ background: BGAPP, minHeight: 667, width: 352, display: "flex", flexDirection: "column" }}>
      <div style={{ background: WHITE, borderBottom: `1px solid ${BDR}`, padding: "10px 16px", display: "flex", alignItems: "center", gap: 12 }}>
        <div style={{ width: 36, height: 36, borderRadius: 18, background: F3, display: "flex", alignItems: "center", justifyContent: "center" }}>
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke={NAVY} strokeWidth="2.5" strokeLinecap="round"><polyline points="9 18 15 12 9 6"/></svg>
        </div>
        <div style={{ width: 36, height: 36, borderRadius: 18, background: TEAL_L }} />
        <div>
          <div style={{ fontSize: 14, fontWeight: 800, color: NAVY }}>خالد المالك</div>
          <div style={{ fontSize: 10, color: GREEN }}>متصل الآن</div>
        </div>
      </div>
      <div style={{ flex: 1, padding: 16, display: "flex", flexDirection: "column", gap: 10 }}>
        <div style={{ background: WHITE, border: `1px solid ${BDR}`, borderRadius: "14px 14px 14px 4px", padding: "10px 14px", maxWidth: "75%", alignSelf: "flex-start" }}>
          <div style={{ fontSize: 13, color: NAVY }}>هل الشقة متاحة؟</div>
          <div style={{ fontSize: 9, color: LGRAY, marginTop: 2 }}>١٠:٤٢</div>
        </div>
        <div style={{ background: TEAL, borderRadius: "14px 14px 4px 14px", padding: "10px 14px", maxWidth: "75%", alignSelf: "flex-end" }}>
          <div style={{ fontSize: 13, color: WHITE }}>نعم، متاحة من الشهر القادم</div>
          <div style={{ fontSize: 9, color: "rgba(255,255,255,0.6)", marginTop: 2, textAlign: "right" }}>١٠:٤٥ ✓✓</div>
        </div>
      </div>
      <div style={{ background: WHITE, borderTop: `1px solid ${BDR}`, padding: "10px 14px", display: "flex", gap: 10, alignItems: "center" }}>
        <div style={{ width: 34, height: 34, borderRadius: 10, background: F3 }} />
        <div style={{ flex: 1, height: 36, borderRadius: 18, background: BGAPP, border: `1px solid ${BDR}` }} />
        <div style={{ width: 34, height: 34, borderRadius: 10, background: TEAL }} />
      </div>
    </div>
  );
}

function SettingsPreview() {
  return (
    <div style={{ background: BGAPP, minHeight: 667, width: 352 }}>
      <div style={{ background: WHITE, borderBottom: `1px solid ${BDR}`, padding: "10px 16px", display: "flex", alignItems: "center", gap: 12 }}>
        <div style={{ width: 36, height: 36, borderRadius: 18, background: F3, display: "flex", alignItems: "center", justifyContent: "center" }}>
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke={NAVY} strokeWidth="2.5" strokeLinecap="round"><polyline points="9 18 15 12 9 6"/></svg>
        </div>
        <span style={{ fontSize: 17, fontWeight: 800, color: NAVY }}>الإعدادات</span>
      </div>
      <div style={{ padding: 16, display: "flex", flexDirection: "column", gap: 8 }}>
        {["الإشعارات","الخصوصية والأمان","اللغة","الدعم الفني","الشروط والأحكام","تسجيل الخروج"].map((item, i) => (
          <div key={item} style={{ background: WHITE, border: `1px solid ${BDR}`, borderRadius: 14, padding: "14px 16px", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
            <span style={{ fontSize: 13, fontWeight: 600, color: i === 5 ? ROSE : NAVY }}>⬅ {item}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function KYCPreview() {
  return (
    <div style={{ background: WHITE, minHeight: 667, width: 352 }}>
      <div style={{ background: WHITE, borderBottom: `1px solid ${BDR}`, padding: "10px 16px", display: "flex", alignItems: "center", gap: 12 }}>
        <div style={{ width: 36, height: 36, borderRadius: 18, background: F3 }} />
        <span style={{ fontSize: 17, fontWeight: 800, color: NAVY }}>توثيق الهوية</span>
      </div>
      <div style={{ padding: 20, textAlign: "center" }}>
        <div style={{ width: 72, height: 72, borderRadius: 22, background: `${TEAL}14`, display: "flex", alignItems: "center", justifyContent: "center", margin: "0 auto 14px" }}>
          <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke={TEAL} strokeWidth="2" strokeLinecap="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
        </div>
        <div style={{ fontSize: 18, fontWeight: 900, color: NAVY, marginBottom: 6 }}>وثّق هويتك وابدأ</div>
        <div style={{ fontSize: 12, color: GRAY }}>التوثيق إلزامي للتواصل مع الملاك</div>
      </div>
      <div style={{ padding: "0 20px", display: "flex", flexDirection: "column", gap: 8 }}>
        {["الرقم القومي", "صورة شخصية", "صورة البطاقة"].map(d => (
          <div key={d} style={{ display: "flex", alignItems: "center", gap: 12, padding: 14, background: WHITE, borderRadius: 14, border: `1px solid ${BDR}` }}>
            <div style={{ width: 36, height: 36, borderRadius: 10, background: F3 }} />
            <span style={{ fontSize: 13, fontWeight: 600, color: NAVY }}>{d}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

// ══════════════════════════════════════════════════════════════════════
// SHARED COMPONENTS PANEL
// ══════════════════════════════════════════════════════════════════════
function SharedComponentsPanel() {
  return (
    <div>
      <GroupHeader letter="A" label="Navigation — شريط التنقل" color={BLUE_B} />
      <Row>
        <CompWrapper id="COMP-NAV-TENANT-BOTTOM" name="Tenant Bottom Navigation" ar="شريط تنقل المستأجر" used={["Home","Search","Saved","Chat","Profile"]} w={370}>
          <TenantBottomNavReal active="home" />
        </CompWrapper>
        <CompWrapper id="COMP-NAV-OWNER-BOTTOM" name="Owner Bottom Navigation" ar="شريط تنقل المالك" used={["Dashboard","Listings","Requests","Chat","More"]} w={370}>
          <OwnerBottomNavReal active="home" />
        </CompWrapper>
        <CompWrapper id="COMP-NAV-HEADER" name="Top Header / Back Bar" ar="رأس الصفحة وزر الرجوع" used={["All sub-pages","KYC","Settings","Details"]} w={370}>
          <TopHeaderReal />
        </CompWrapper>
        <CompWrapper id="COMP-HEADER-PROPERTY" name="Property Detail Header" ar="رأس تفاصيل العقار" used={["Property Details (Tenant, Owner, Admin)"]} w={320}>
          <PropertyDetailHeader />
        </CompWrapper>
      </Row>

      <GroupHeader letter="B" label="Cards — البطاقات" color={TEAL_B} />
      <Row>
        <CompWrapper id="COMP-CARD-PROPERTY" name="Property Card" ar="بطاقة العقار" used={["Home","Search Results","Saved","Nearby","Notifications"]}>
          <PropertyCardReal />
        </CompWrapper>
        <CompWrapper id="COMP-CARD-VISIT-REQUEST" name="Visit Request Card" ar="بطاقة طلب الزيارة" used={["Owner Requests","Visit Dashboard","Admin Visits"]}>
          <VisitRequestCardReal />
        </CompWrapper>
        <CompWrapper id="COMP-CARD-NOTIFICATION" name="Notification Card" ar="بطاقة الإشعار" used={["Tenant Notifications","Owner Notifications","Admin"]}>
          <NotificationCardReal />
        </CompWrapper>
        <CompWrapper id="COMP-CARD-METRIC" name="Metric Cards (Grid)" ar="بطاقات الإحصاء" used={["Owner Dashboard","Admin Dashboard"]}>
          <MetricCardsRow />
        </CompWrapper>
        <CompWrapper id="COMP-CARD-ACCEPT-REJECT" name="Accept / Reject Card" ar="بطاقة القبول والرفض" used={["Owner Dashboard Requests","Admin Requests"]}>
          <AcceptRejectCard />
        </CompWrapper>
      </Row>

      <GroupHeader letter="C" label="Forms & Inputs — الحقول والنماذج" color={PURP_B} />
      <Row>
        <CompWrapper id="COMP-INPUT-SEARCH" name="Search Bar" ar="شريط البحث" used={["Tenant Home","Search Screen","Admin Search"]}>
          <SearchBarReal />
        </CompWrapper>
        <CompWrapper id="COMP-INPUT-EMAIL" name="Email Input" ar="حقل البريد الإلكتروني" used={["Tenant Login","Owner Login","Register"]}>
          <EmailInputReal />
        </CompWrapper>
        <CompWrapper id="COMP-INPUT-PASSWORD" name="Password Input" ar="حقل كلمة المرور" used={["Tenant Login","Owner Login","Register"]}>
          <PasswordInputReal />
        </CompWrapper>
        <CompWrapper id="COMP-INPUT-OTP" name="OTP Input (6-digit)" ar="حقل كود التحقق" used={["Tenant OTP","Owner OTP"]} w={320}>
          <OTPInputReal />
        </CompWrapper>
        <CompWrapper id="COMP-INPUT-NATIONAL-ID" name="National ID Field" ar="حقل الرقم القومي" used={["Tenant KYC-02","Owner KYC-02"]} w={320}>
          <NationalIDFieldReal />
        </CompWrapper>
      </Row>

      <GroupHeader letter="D" label="Badges & Chips — الشارات والرقائق" color={GOLD_B} />
      <Row>
        <CompWrapper id="COMP-BADGE-STATUS" name="Status Badges" ar="شارات الحالة" used={["Property Card","Request Card","KYC","Admin Screens"]}>
          <BadgesSet />
        </CompWrapper>
        <CompWrapper id="COMP-CHIP-FILTER" name="Filter / Category Chips" ar="رقائق التصفية والفئات" used={["Search","Filter Sheet","Home Filters"]}>
          <FilterChipsReal />
        </CompWrapper>
        <CompWrapper id="COMP-CHIP-AMENITY" name="Amenity Chips" ar="رقائق المميزات" used={["Property Details","Add Property Step 3"]}>
          <AmenityChipsReal />
        </CompWrapper>
        <CompWrapper id="COMP-CHIP-SUITABLE-FOR" name="Suitable For Chips" ar="رقائق مناسب لـ" used={["Filter Sheet","Add Property"]}>
          <SuitableForChips />
        </CompWrapper>
      </Row>

      <GroupHeader letter="E" label="Banners — اللافتات" color={TEAL_B} />
      <Row>
        <CompWrapper id="COMP-BANNER-PRIVACY" name="Privacy Banner" ar="لافتة الخصوصية" used={["Visit Request Card","Property Details","KYC screens"]}>
          <PrivacyBannerReal />
        </CompWrapper>
        <CompWrapper id="COMP-BANNER-CHAT-RESTRICTED" name="Chat Restricted Banner" ar="لافتة تقييد الشات" used={["Tenant Chat Restricted Screen"]}>
          <ChatRestrictedBanner />
        </CompWrapper>
        <CompWrapper id="COMP-BANNER-WARNING" name="Warning Banner" ar="لافتة التحذير" used={["KYC screens","Add Property","Profile incomplete"]}>
          <WarningBannerReal />
        </CompWrapper>
        <CompWrapper id="COMP-BANNER-VISITOR" name="Visitor Mode Banner" ar="لافتة وضع الزائر" used={["Home (Visitor)","Search","Property Details (Visitor)"]}>
          <VisitorModeBanner />
        </CompWrapper>
      </Row>

      <GroupHeader letter="F" label="Chat Components — مكونات المحادثة" color={BLUE_B} />
      <Row>
        <CompWrapper id="COMP-CHAT-BUBBLES" name="Chat Bubbles (Sent + Received)" ar="فقاعات الرسائل" used={["Tenant Chat Thread","Owner Chat Thread"]}>
          <ChatBubblesReal />
        </CompWrapper>
        <CompWrapper id="COMP-CHAT-INPUT" name="Chat Input Bar" ar="شريط إدخال الرسائل" used={["Tenant Chat Thread","Owner Chat Thread"]}>
          <ChatInputBarReal />
        </CompWrapper>
        <CompWrapper id="COMP-SHEET-ATTACHMENT" name="Attachment Action Sheet" ar="ورقة المرفقات" used={["Tenant Chat Thread","Owner Chat Thread"]}>
          <AttachmentSheet />
        </CompWrapper>
      </Row>

      <GroupHeader letter="G" label="Sheets & Modals — الأوراق والنوافذ" color={ROSE_B} />
      <Row>
        <CompWrapper id="COMP-SHEET-SHARE" name="Share Bottom Sheet" ar="ورقة المشاركة" used={["Property Details","Owner Listing","Admin Listings"]}>
          <ShareSheetReal />
        </CompWrapper>
        <CompWrapper id="COMP-SHEET-FILTER" name="Filter Bottom Sheet" ar="ورقة التصفية" used={["Search Screen","Home Filters","Admin Listings"]}>
          <FilterSheetReal />
        </CompWrapper>
        <CompWrapper id="COMP-SHEET-LOGOUT" name="Logout Bottom Sheet" ar="ورقة تسجيل الخروج" used={["Tenant Profile","Owner More / Profile","Admin"]}>
          <LogoutSheetReal />
        </CompWrapper>
        <CompWrapper id="COMP-MODAL-DELETE" name="Delete Confirmation Sheet" ar="نافذة تأكيد الحذف" used={["Owner My Listings","Admin Listings","Admin Reports"]}>
          <DeleteConfirmSheet />
        </CompWrapper>
        <CompWrapper id="COMP-SHEET-REPORT" name="Report / Block Sheet" ar="ورقة الإبلاغ والحظر" used={["Tenant Chat","Property Details","Admin"]}>
          <ReportBlockSheet />
        </CompWrapper>
      </Row>

      <GroupHeader letter="H" label="States — الحالات" color={SLATE_B} />
      <Row>
        <CompWrapper id="COMP-STATE-EMPTY" name="Empty State" ar="حالة فارغة" used={["Saved","Search","Requests","Notifications","Chat List"]}>
          <EmptyStateReal />
        </CompWrapper>
        <CompWrapper id="COMP-STATE-EMPTY-SEARCH" name="Empty State (Search)" ar="حالة بحث بدون نتائج" used={["Search Results","Admin Search"]}>
          <EmptyStateReal icon="🔍" title="لا توجد نتائج" sub="جرّب تغيير كلمة البحث أو التصفية" btn="تعديل البحث" />
        </CompWrapper>
        <CompWrapper id="COMP-STATE-LOADING" name="Loading Skeleton" ar="هيكل التحميل" used={["All list screens","Dashboard","Search Results"]}>
          <LoadingSkeletonReal />
        </CompWrapper>
        <CompWrapper id="COMP-STATE-PENDING" name="Pending Review State" ar="حالة قيد المراجعة" used={["KYC Pending","Add Property Pending","Admin Queue"]}>
          <PendingStateReal />
        </CompWrapper>
        <CompWrapper id="COMP-STATE-REJECTED" name="Rejected State" ar="حالة الرفض" used={["Owner Listing Rejected","KYC Rejected","Admin"]}>
          <RejectedStateReal />
        </CompWrapper>
      </Row>
    </div>
  );
}

// ══════════════════════════════════════════════════════════════════════
// SHARED SCREENS PANEL
// ══════════════════════════════════════════════════════════════════════
function SharedScreensPanel() {
  return (
    <div>
      <GroupHeader letter="A" label="Property Shared Screens — شاشات العقارات" color={TEAL_B} />
      <Row>
        <ScreenRefReal id="SHARED-SCREEN-PROPERTY-DETAILS" name="Property Details" ar="تفاصيل العقار" color={TEAL_B}
          from={["Home","Search Results","Saved","Nearby","Notifications","Owner Listings"]}
          preview={<PropertyDetailPreview />} />
      </Row>

      <GroupHeader letter="B" label="Communication Shared Screens — التواصل" color={BLUE_B} />
      <Row>
        <ScreenRefReal id="SHARED-SCREEN-CHAT-DETAIL" name="Chat Detail" ar="تفاصيل المحادثة" color={BLUE_B}
          from={["Tenant Chat List","Owner Chat List","Property Details CTA","Visit Confirmed"]}
          preview={<ChatDetailPreview />} />
      </Row>

      <GroupHeader letter="C" label="Account Shared Screens — الحساب" color={GOLD_B} />
      <Row>
        <ScreenRefReal id="SHARED-SCREEN-SETTINGS" name="Settings" ar="الإعدادات" color={GOLD_B}
          from={["Tenant Profile → More","Owner More Screen"]}
          preview={<SettingsPreview />} />
      </Row>

      <GroupHeader letter="D" label="Auth & KYC Shared Screens — التوثيق" color={PURP_B} />
      <Row>
        <ScreenRefReal id="SHARED-SCREEN-KYC" name="KYC Start / Verification" ar="بدء التوثيق" color={PURP_B}
          from={["Register flow","Profile banner CTA","Add Property (unverified owner)","Admin manual trigger"]}
          preview={<KYCPreview />} />
      </Row>

      {/* Reference-only list for remaining shared screens */}
      <GroupHeader letter="E" label="Additional Shared Screens (Reference)" color={SLATE_B} />
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(300px, 1fr))", gap: 12 }}>
        {[
          { id:"SHARED-SCREEN-VISIT-REQUEST-DETAIL", name:"Visit Request Detail",    ar:"تفاصيل طلب الزيارة",    from:"Owner Requests · Tenant Visits · Admin" },
          { id:"SHARED-SCREEN-HELP-CENTER",          name:"Help Center",             ar:"مركز المساعدة",          from:"Settings · Profile · Support" },
          { id:"SHARED-SCREEN-TERMS",                name:"Terms of Service",        ar:"الشروط والأحكام",        from:"Settings · Register · KYC" },
          { id:"SHARED-SCREEN-ABOUT",                name:"About Sokoon",            ar:"عن سكون",                from:"Settings · Onboarding" },
          { id:"SHARED-SCREEN-VERIFY-STATUS",        name:"Verification Status",     ar:"حالة التوثيق",          from:"Profile · KYC Pending · Admin" },
          { id:"SHARED-SCREEN-ADMIN-USER-PROFILE",   name:"Admin User Profile",      ar:"ملف المستخدم (أدمن)",    from:"Users List · Reports · KYC Queue" },
          { id:"SHARED-SCREEN-ADMIN-LISTING-REVIEW", name:"Admin Listing Review",    ar:"مراجعة العقار (أدمن)",   from:"Listings Queue · Reports" },
          { id:"SHARED-SCREEN-ADMIN-REPORT-DETAIL",  name:"Admin Report Detail",     ar:"تفاصيل البلاغ (أدمن)",  from:"Reports List" },
          { id:"SHARED-SCREEN-ADMIN-TICKET",         name:"Support Ticket Detail",   ar:"تفاصيل التذكرة (أدمن)", from:"Support Queue · Admin Dashboard" },
        ].map(s => (
          <div key={s.id} style={{ background: CARD_B, border: `1px solid ${BDR_B}`, borderRadius: 14, padding: "14px 16px" }}>
            <span style={{ fontSize: 8.5, color: GOLD_B, letterSpacing: 2, display: "block", marginBottom: 4, ...MONO }}>{s.id}</span>
            <span style={{ fontSize: 13, fontWeight: 700, color: "#E2E8F0", display: "block", ...TJ }}>{s.name}</span>
            <span style={{ fontSize: 11, color: SLATE_B, display: "block", marginBottom: 6, ...TJ }}>{s.ar}</span>
            <span style={{ fontSize: 9, color: "#334155", ...TJ }}>Opened from: {s.from}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

// ══════════════════════════════════════════════════════════════════════
// ROOT EXPORT
// ══════════════════════════════════════════════════════════════════════
export function SharedView() {
  const [tab, setTab] = useState<"audit" | "components" | "screens">("audit");

  const tabs = [
    { id: "audit"      as const, label: "Audit Checklist",       count: `${AUDIT_ROWS.length}`, color: GOLD_B  },
    { id: "components" as const, label: "Shared Components",     count: "30+",                  color: TEAL_B  },
    { id: "screens"    as const, label: "Shared Screens",        count: "13+",                  color: PURP_B  },
  ];

  return (
    <div style={{ minHeight: "100vh", background: BOARD, ...TJ }}>
      {/* Cover */}
      <div style={{
        background: "linear-gradient(135deg,#060F1C 0%,#0A1F18 50%,#0E1430 100%)",
        borderBottom: `1px solid ${BDR_B}`, padding: "64px 56px 48px", position: "relative", overflow: "hidden",
      }}>
        <div style={{ position: "absolute", top: -80, right: -80, width: 400, height: 400, borderRadius: "50%", background: `radial-gradient(circle,${PURP_B}16,transparent 70%)`, pointerEvents: "none" }} />
        <div style={{ position: "absolute", bottom: -60, left: 120, width: 300, height: 300, borderRadius: "50%", background: `radial-gradient(circle,${TEAL_B}14,transparent 70%)`, pointerEvents: "none" }} />
        <div style={{ maxWidth: 860, position: "relative" }}>
          <div style={{ fontSize: 10, fontWeight: 800, color: PURP_B, letterSpacing: 3, marginBottom: 12, textTransform: "uppercase" }}>
            Shared Components — مكونات مشتركة
          </div>
          <h1 style={{ fontSize: 40, fontWeight: 900, color: "#F1F5F9", margin: "0 0 10px", lineHeight: 1.2 }}>
            Design System Library
          </h1>
          <p style={{ color: "#475569", fontSize: 14, margin: "0 0 28px", direction: "rtl", textAlign: "right", lineHeight: 1.8, maxWidth: 600 }}>
            مبني من المصدر الحقيقي — كل مكوّن منسوخ حرفياً من الشاشات الموجودة · لا تصميم جديد · لا اختراع
          </p>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 10 }}>
            {[
              { l: `${AUDIT_ROWS.length} Audited Items`, c: GOLD_B },
              { l: "Copied from Real Screens",   c: TEAL_B },
              { l: "No New Design",              c: GREEN_B },
              { l: "Arabic RTL Preserved",       c: BLUE_B },
              { l: "Sokoon Visual System",       c: PURP_B },
            ].map(b => (
              <span key={b.l} style={{ fontSize: 11, fontWeight: 700, color: b.c, background: `${b.c}18`, border: `1px solid ${b.c}33`, borderRadius: 20, padding: "4px 14px" }}>{b.l}</span>
            ))}
          </div>
        </div>
        <div style={{ position: "absolute", top: 28, right: 48, display: "flex", flexDirection: "column", gap: 6 }}>
          {[
            { l: "Navigation",  s: "4",  c: BLUE_B  },
            { l: "Cards",       s: "5",  c: TEAL_B  },
            { l: "Forms",       s: "5",  c: PURP_B  },
            { l: "Sheets",      s: "5",  c: ROSE_B  },
            { l: "States",      s: "5",  c: SLATE_B },
          ].map(b => (
            <div key={b.l} style={{ display: "flex", alignItems: "center", gap: 8, justifyContent: "flex-end" }}>
              <span style={{ fontSize: 10, fontWeight: 700, color: "#334155" }}>{b.l}</span>
              <span style={{ fontSize: 9, fontWeight: 800, color: b.c, background: `${b.c}18`, borderRadius: 6, padding: "1px 9px" }}>{b.s} items</span>
            </div>
          ))}
        </div>
      </div>

      {/* Sub-tabs */}
      <div style={{ background: PANEL, borderBottom: `1px solid ${BDR_B}`, padding: "0 48px", display: "flex" }}>
        {tabs.map(t => (
          <button key={t.id} onClick={() => setTab(t.id)}
            style={{
              display: "flex", alignItems: "center", gap: 7, padding: "0 20px",
              border: "none", background: "transparent",
              borderBottom: tab === t.id ? `2px solid ${t.color}` : "2px solid transparent",
              color: tab === t.id ? t.color : "#475569",
              cursor: "pointer", fontSize: 12, fontWeight: tab === t.id ? 800 : 600,
              height: 44, ...TJ, flexShrink: 0,
            }}>
            <span>{t.label}</span>
            <span style={{
              fontSize: 9, fontWeight: 800,
              color: tab === t.id ? t.color : "#334155",
              background: tab === t.id ? `${t.color}18` : "#162030",
              borderRadius: 10, padding: "1px 6px",
            }}>{t.count}</span>
          </button>
        ))}
      </div>

      {/* Content */}
      <div style={{ padding: "52px 48px 80px" }}>
        {tab === "audit" && (
          <div>
            <div style={{ marginBottom: 32 }}>
              <div style={{ fontSize: 11, fontWeight: 800, color: GOLD_B, letterSpacing: 1, textTransform: "uppercase", marginBottom: 8 }}>
                Shared Components Audit
              </div>
              <h2 style={{ fontSize: 22, fontWeight: 900, color: "#E2E8F0", margin: "0 0 6px" }}>
                Built from actual repeated patterns
              </h2>
              <p style={{ color: SLATE_B, fontSize: 13, margin: 0 }}>
                Every item below was found in Flow Overview / Interactive Prototype screens, confirmed to appear in 2+ places, and copied exactly. Nothing was invented.
              </p>
            </div>
            <AuditTable />
          </div>
        )}
        {tab === "components" && <SharedComponentsPanel />}
        {tab === "screens"    && <SharedScreensPanel />}
      </div>
    </div>
  );
}
