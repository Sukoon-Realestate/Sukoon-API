import React, { useState } from "react";

// ── Design tokens (mirrors App.tsx / design-system.tsx) ─────────────────
const TEAL = "#0F766E";
const GOLD = "#D6A84F";
const ROSE = "#E11D48";
const GREEN = "#16A34A";
const SLATE = "#475569";
const TJ: React.CSSProperties = { fontFamily: "Tajawal, sans-serif" };

const C = {
  bg: "#FAFAF8",
  card: "#FFFFFF",
  border: "#E5E7EB",
  text: "#111827",
  sub: "#6B7280",
  teal: TEAL,
  gold: GOLD,
};

// ── Shared micro-components ──────────────────────────────────────────────
function StatusBar() {
  return (
    <div style={{ height: 44, background: "transparent", display: "flex", alignItems: "center", justifyContent: "space-between", padding: "0 20px", ...TJ }}>
      <span style={{ fontSize: 14, fontWeight: 700, color: C.text }}>9:41</span>
      <div style={{ display: "flex", gap: 5, alignItems: "center" }}>
        <svg width="16" height="12" viewBox="0 0 16 12" fill={C.text}><rect x="0" y="4" width="3" height="8" rx="1"/><rect x="4" y="2" width="3" height="10" rx="1"/><rect x="8" y="0" width="3" height="12" rx="1"/><rect x="12" y="0" width="3" height="12" rx="1" opacity="0.3"/></svg>
        <svg width="14" height="12" viewBox="0 0 14 12" fill={C.text}><path d="M7 2C9.5 2 11.7 3.1 13.2 4.8L14 4C12.2 2 9.7 1 7 1 4.3 1 1.8 2 0 4l.8.8C2.3 3.1 4.5 2 7 2z"/><path d="M7 5c1.4 0 2.6.6 3.5 1.5l.8-.8C10.1 4.5 8.6 4 7 4S3.9 4.5 2.7 5.7l.8.8C4.4 5.6 5.6 5 7 5z"/><circle cx="7" cy="9" r="1.5"/></svg>
        <svg width="24" height="12" viewBox="0 0 24 12" fill="none"><rect x="0.5" y="0.5" width="21" height="11" rx="2.5" stroke={C.text} strokeOpacity="0.35"/><rect x="2" y="2" width="15" height="8" rx="1.5" fill={C.text}/><path d="M23 4.5v3a1.5 1.5 0 000-3z" fill={C.text} fillOpacity="0.4"/></svg>
      </div>
    </div>
  );
}

function NavBar({ title, onBack, right }: { title: string; onBack?: () => void; right?: React.ReactNode }) {
  return (
    <div style={{ height: 52, display: "flex", alignItems: "center", justifyContent: "space-between", padding: "0 16px", borderBottom: `1px solid ${C.border}`, background: C.card, direction: "rtl" }}>
      {onBack ? (
        <button onClick={onBack} style={{ width: 36, height: 36, borderRadius: 18, border: "none", background: "#F3F4F6", cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center" }}>
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke={C.text} strokeWidth="2.5" strokeLinecap="round"><polyline points="9 18 15 12 9 6"/></svg>
        </button>
      ) : <div style={{ width: 36 }} />}
      <span style={{ fontSize: 16, fontWeight: 700, color: C.text, ...TJ }}>{title}</span>
      {right || <div style={{ width: 36 }} />}
    </div>
  );
}

function PrimaryBtn({ label, onClick, disabled }: { label: string; onClick?: () => void; disabled?: boolean }) {
  return (
    <button onClick={onClick} disabled={disabled} style={{ width: "100%", height: 52, background: disabled ? "#9CA3AF" : TEAL, border: "none", borderRadius: 14, color: "white", fontSize: 16, fontWeight: 700, cursor: disabled ? "not-allowed" : "pointer", ...TJ }}>
      {label}
    </button>
  );
}

function PrivacyCard({ icon, text, sub }: { icon: React.ReactNode; text: string; sub: string }) {
  return (
    <div style={{ background: "#F0FDF9", border: `1px solid ${TEAL}22`, borderRadius: 14, padding: "14px 16px", display: "flex", gap: 12, alignItems: "flex-start", direction: "rtl" }}>
      <div style={{ width: 36, height: 36, borderRadius: 10, background: TEAL + "18", display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>{icon}</div>
      <div>
        <div style={{ fontSize: 13, fontWeight: 700, color: C.text, ...TJ }}>{text}</div>
        <div style={{ fontSize: 11, color: C.sub, marginTop: 3, lineHeight: 1.5, ...TJ }}>{sub}</div>
      </div>
    </div>
  );
}

// ════════════════════════════════════════════════════════════════════════
// 1. AUTH SCREENS — EMAIL-BASED LOGIN
// ════════════════════════════════════════════════════════════════════════

function SocialBtn({ icon, label, color }: { icon: React.ReactNode; label: string; color?: string }) {
  return (
    <button style={{ width: "100%", height: 48, background: "white", border: `1.5px solid ${C.border}`, borderRadius: 12, display: "flex", alignItems: "center", justifyContent: "center", gap: 10, cursor: "pointer", marginBottom: 10, ...TJ, direction: "rtl" }}>
      <span style={{ fontSize: 14, fontWeight: 600, color: color || C.text }}>{label}</span>
      {icon}
    </button>
  );
}

const GoogleIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24"><path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/><path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/><path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/><path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/></svg>
);
const FbIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="#1877F2"><path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/></svg>
);
const AppleIcon = ({ color = "#111827" }: { color?: string }) => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill={color}><path d="M18.71 19.5c-.83 1.24-1.71 2.45-3.05 2.47-1.34.03-1.77-.79-3.29-.79-1.53 0-2 .77-3.27.82-1.31.05-2.3-1.32-3.14-2.53C4.25 17 2.94 12.45 4.7 9.39c.87-1.52 2.43-2.48 4.12-2.51 1.28-.02 2.5.87 3.29.87.78 0 2.26-1.07 3.8-.91.65.03 2.47.26 3.64 1.98-.09.06-2.17 1.28-2.15 3.81.03 3.02 2.65 4.03 2.68 4.04-.03.07-.42 1.44-1.38 2.83M13 3.5c.73-.83 1.94-1.46 2.94-1.5.13 1.17-.34 2.35-1.04 3.19-.69.85-1.83 1.51-2.95 1.42-.15-1.15.41-2.35 1.05-3.11z"/></svg>
);
const EyeIcon = ({ open }: { open: boolean }) => open ? (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke={SLATE} strokeWidth="2" strokeLinecap="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
) : (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke={SLATE} strokeWidth="2" strokeLinecap="round"><path d="M17.94 17.94A10.07 10.07 0 0112 20c-7 0-11-8-11-8a18.45 18.45 0 015.06-5.94M9.9 4.24A9.12 9.12 0 0112 4c7 0 11 8 11 8a18.5 18.5 0 01-2.16 3.19m-6.72-1.07a3 3 0 11-4.24-4.24"/><line x1="1" y1="1" x2="23" y2="23"/></svg>
);

export function TenantLoginEmailScreen() {
  const [email, setEmail] = useState("ahmed@gmail.com");
  const [pass, setPass] = useState("");
  const [showPass, setShowPass] = useState(false);
  const [passError, setPassError] = useState(false);
  return (
    <div style={{ width: 390, height: 844, background: C.bg, display: "flex", flexDirection: "column", ...TJ, direction: "rtl" }}>
      <StatusBar />
      <div style={{ flex: 1, padding: "0 24px", overflowY: "auto" }}>
        {/* Logo area */}
        <div style={{ display: "flex", flexDirection: "column", alignItems: "center", paddingTop: 28, paddingBottom: 20 }}>
          <div style={{ width: 60, height: 60, borderRadius: 16, background: TEAL, display: "flex", alignItems: "center", justifyContent: "center", marginBottom: 14 }}>
            <svg width="34" height="34" viewBox="0 0 18 18" fill="none"><path d="M9,2 L16,8 L14,8 L14,16 L4,16 L4,8 L2,8 Z" fill="white"/><rect x="5.5" y="10" width="2.5" height="2" rx="0.7" fill={TEAL}/><rect x="10" y="10" width="2.5" height="2" rx="0.7" fill={TEAL}/><path d="M7,16 L7,13 Q9,11.5 11,13 L11,16 Z" fill={TEAL}/></svg>
          </div>
          <div style={{ fontSize: 22, fontWeight: 900, color: C.text, marginBottom: 4 }}>تسجيل الدخول</div>
          <div style={{ fontSize: 12, color: C.sub, textAlign: "center", lineHeight: 1.6 }}>مرحباً بك مجدداً في سكون</div>
        </div>

        {/* Email field */}
        <div style={{ marginBottom: 12 }}>
          <div style={{ fontSize: 13, fontWeight: 600, color: C.text, marginBottom: 6 }}>البريد الإلكتروني</div>
          <input value={email} onChange={e => setEmail(e.target.value)} placeholder="example@email.com"
            style={{ width: "100%", height: 52, borderRadius: 12, border: `1.5px solid ${email ? TEAL : C.border}`, padding: "0 16px", fontSize: 15, color: C.text, background: "white", boxSizing: "border-box", textAlign: "right", direction: "ltr", ...TJ, outline: "none" }} />
        </div>

        {/* Password field */}
        <div style={{ marginBottom: 6 }}>
          <div style={{ fontSize: 13, fontWeight: 600, color: C.text, marginBottom: 6 }}>كلمة المرور</div>
          <div style={{ position: "relative" }}>
            <input value={pass} onChange={e => { setPass(e.target.value); setPassError(false); }} type={showPass ? "text" : "password"} placeholder="••••••••"
              style={{ width: "100%", height: 52, borderRadius: 12, border: `1.5px solid ${passError ? ROSE : (pass ? TEAL : C.border)}`, padding: "0 48px 0 16px", fontSize: 15, color: C.text, background: "white", boxSizing: "border-box", direction: "ltr", textAlign: "left", ...TJ, outline: "none" }} />
            <button onClick={() => setShowPass(!showPass)} style={{ position: "absolute", left: 14, top: "50%", transform: "translateY(-50%)", background: "none", border: "none", cursor: "pointer", padding: 0 }}>
              <EyeIcon open={showPass} />
            </button>
          </div>
          {passError && <div style={{ fontSize: 12, color: ROSE, marginTop: 4, fontWeight: 600 }}>كلمة المرور مطلوبة</div>}
        </div>

        {/* Forgot password */}
        <div style={{ textAlign: "left", marginBottom: 20 }}>
          <button style={{ background: "none", border: "none", color: TEAL, fontSize: 12, cursor: "pointer", fontWeight: 600, ...TJ }}>نسيت كلمة المرور؟</button>
        </div>

        <button onClick={() => { if (!pass) setPassError(true); }} style={{ width: "100%", height: 52, background: TEAL, border: "none", borderRadius: 14, color: "white", fontSize: 16, fontWeight: 700, cursor: "pointer", ...TJ }}>تسجيل الدخول</button>

        {/* Divider */}
        <div style={{ display: "flex", alignItems: "center", gap: 12, margin: "18px 0" }}>
          <div style={{ flex: 1, height: 1, background: C.border }} />
          <span style={{ fontSize: 12, color: C.sub }}>أو</span>
          <div style={{ flex: 1, height: 1, background: C.border }} />
        </div>

        <SocialBtn label="المتابعة باستخدام Google" icon={<GoogleIcon />} />
        <SocialBtn label="المتابعة باستخدام Facebook" icon={<FbIcon />} color="#1877F2" />
        <SocialBtn label="المتابعة باستخدام Apple" icon={<AppleIcon />} />

        <div style={{ textAlign: "center", marginTop: 8, paddingBottom: 24 }}>
          <button style={{ background: "none", border: "none", color: C.sub, fontSize: 13, cursor: "pointer", ...TJ, textDecoration: "underline" }}>الدخول كزائر</button>
        </div>
      </div>
    </div>
  );
}

export function TenantOTPScreen() {
  const [otp, setOtp] = useState(["1", "2", "3", "", "", ""]);
  const [error, setError] = useState(false);
  const filled = otp.filter(Boolean).length;
  return (
    <div style={{ width: 390, height: 844, background: C.bg, display: "flex", flexDirection: "column", ...TJ, direction: "rtl" }}>
      <StatusBar />
      <NavBar title="كود التحقق" onBack={() => {}} />
      <div style={{ flex: 1, padding: "32px 24px", overflowY: "auto" }}>
        {/* Header */}
        <div style={{ textAlign: "center", marginBottom: 32 }}>
          <div style={{ width: 64, height: 64, borderRadius: 18, background: TEAL + "15", display: "flex", alignItems: "center", justifyContent: "center", margin: "0 auto 16px" }}>
            <svg width="30" height="30" viewBox="0 0 24 24" fill="none" stroke={TEAL} strokeWidth="2" strokeLinecap="round"><rect x="2" y="4" width="20" height="16" rx="2"/><polyline points="22,4 12,13 2,4"/></svg>
          </div>
          <div style={{ fontSize: 18, fontWeight: 700, color: C.text, marginBottom: 8 }}>بعتنالك كود على البريد الإلكتروني</div>
          <div style={{ fontSize: 14, color: TEAL, fontWeight: 600 }}>ah****@gmail.com</div>
          <button onClick={() => {}} style={{ background: "none", border: "none", color: C.sub, fontSize: 12, cursor: "pointer", marginTop: 6, ...TJ, textDecoration: "underline" }}>تغيير البريد الإلكتروني</button>
        </div>

        {/* OTP inputs */}
        <div style={{ display: "flex", gap: 10, justifyContent: "center", marginBottom: 20, direction: "ltr" }}>
          {otp.map((v, i) => (
            <div key={i} style={{ width: 48, height: 58, borderRadius: 12, border: `2px solid ${v ? TEAL : (error ? ROSE : C.border)}`, background: v ? TEAL + "0A" : "white", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 22, fontWeight: 800, color: C.text, cursor: "pointer" }}>
              {v || ""}
            </div>
          ))}
        </div>

        {/* Error state */}
        {error && (
          <div style={{ textAlign: "center", color: ROSE, fontSize: 13, fontWeight: 600, marginBottom: 12 }}>الكود غير صحيح، حاول تاني</div>
        )}

        {/* Timer */}
        <div style={{ textAlign: "center", marginBottom: 24 }}>
          <span style={{ fontSize: 13, color: C.sub }}>إعادة الإرسال بعد </span>
          <span style={{ fontSize: 13, fontWeight: 700, color: TEAL }}>45 ثانية</span>
        </div>

        <PrimaryBtn label="تأكيد الدخول" disabled={filled < 6} />

        <div style={{ textAlign: "center", marginTop: 16 }}>
          <button onClick={() => setError(!error)} style={{ background: "none", border: "none", color: TEAL, fontSize: 13, cursor: "pointer", fontWeight: 600, ...TJ }}>إعادة إرسال الكود</button>
        </div>
      </div>
    </div>
  );
}

export function OwnerLoginEmailScreen() {
  const [email, setEmail] = useState("");
  const [pass, setPass] = useState("");
  const [showPass, setShowPass] = useState(false);
  const [passError, setPassError] = useState(false);
  return (
    <div style={{ width: 390, height: 844, background: C.bg, display: "flex", flexDirection: "column", ...TJ, direction: "rtl" }}>
      <StatusBar />
      <div style={{ flex: 1, padding: "0 24px", overflowY: "auto" }}>
        <div style={{ display: "flex", flexDirection: "column", alignItems: "center", paddingTop: 28, paddingBottom: 20 }}>
          <div style={{ width: 60, height: 60, borderRadius: 16, background: GOLD, display: "flex", alignItems: "center", justifyContent: "center", marginBottom: 14 }}>
            <svg width="34" height="34" viewBox="0 0 18 18" fill="none"><path d="M9,2 L16,8 L14,8 L14,16 L4,16 L4,8 L2,8 Z" fill="white"/><rect x="5.5" y="10" width="2.5" height="2" rx="0.7" fill={GOLD}/><rect x="10" y="10" width="2.5" height="2" rx="0.7" fill={GOLD}/><path d="M7,16 L7,13 Q9,11.5 11,13 L11,16 Z" fill={GOLD}/></svg>
          </div>
          <div style={{ fontSize: 22, fontWeight: 900, color: C.text, marginBottom: 4 }}>تسجيل الدخول — مالك</div>
          <div style={{ fontSize: 12, color: C.sub, textAlign: "center", lineHeight: 1.6 }}>مرحباً بك مجدداً في سكون</div>
        </div>

        {/* Email */}
        <div style={{ marginBottom: 12 }}>
          <div style={{ fontSize: 13, fontWeight: 600, color: C.text, marginBottom: 6 }}>البريد الإلكتروني</div>
          <input value={email} onChange={e => setEmail(e.target.value)} placeholder="example@email.com"
            style={{ width: "100%", height: 52, borderRadius: 12, border: `1.5px solid ${email ? GOLD : C.border}`, padding: "0 16px", fontSize: 15, color: C.text, background: "white", boxSizing: "border-box", textAlign: "right", direction: "ltr", ...TJ, outline: "none" }} />
        </div>

        {/* Password */}
        <div style={{ marginBottom: 6 }}>
          <div style={{ fontSize: 13, fontWeight: 600, color: C.text, marginBottom: 6 }}>كلمة المرور</div>
          <div style={{ position: "relative" }}>
            <input value={pass} onChange={e => { setPass(e.target.value); setPassError(false); }} type={showPass ? "text" : "password"} placeholder="••••••••"
              style={{ width: "100%", height: 52, borderRadius: 12, border: `1.5px solid ${passError ? ROSE : (pass ? GOLD : C.border)}`, padding: "0 48px 0 16px", fontSize: 15, color: C.text, background: "white", boxSizing: "border-box", direction: "ltr", textAlign: "left", ...TJ, outline: "none" }} />
            <button onClick={() => setShowPass(!showPass)} style={{ position: "absolute", left: 14, top: "50%", transform: "translateY(-50%)", background: "none", border: "none", cursor: "pointer", padding: 0 }}>
              <EyeIcon open={showPass} />
            </button>
          </div>
          {passError && <div style={{ fontSize: 12, color: ROSE, marginTop: 4, fontWeight: 600 }}>كلمة المرور مطلوبة</div>}
        </div>

        <div style={{ textAlign: "left", marginBottom: 20 }}>
          <button style={{ background: "none", border: "none", color: GOLD, fontSize: 12, cursor: "pointer", fontWeight: 600, ...TJ }}>نسيت كلمة المرور؟</button>
        </div>

        <button onClick={() => { if (!pass) setPassError(true); }} style={{ width: "100%", height: 52, background: GOLD, border: "none", borderRadius: 14, color: "white", fontSize: 16, fontWeight: 700, cursor: "pointer", ...TJ }}>تسجيل الدخول</button>

        <div style={{ display: "flex", alignItems: "center", gap: 12, margin: "18px 0" }}>
          <div style={{ flex: 1, height: 1, background: C.border }} />
          <span style={{ fontSize: 12, color: C.sub }}>أو</span>
          <div style={{ flex: 1, height: 1, background: C.border }} />
        </div>
        <SocialBtn label="المتابعة باستخدام Google" icon={<GoogleIcon />} />
        <SocialBtn label="المتابعة باستخدام Apple" icon={<AppleIcon />} />
        <div style={{ paddingBottom: 24 }} />
      </div>
    </div>
  );
}

export function OwnerOTPScreen() {
  return (
    <div style={{ width: 390, height: 844, background: C.bg, display: "flex", flexDirection: "column", ...TJ, direction: "rtl" }}>
      <StatusBar />
      <NavBar title="كود التحقق" onBack={() => {}} />
      <div style={{ flex: 1, padding: "32px 24px", overflowY: "auto" }}>
        <div style={{ textAlign: "center", marginBottom: 32 }}>
          <div style={{ width: 64, height: 64, borderRadius: 18, background: GOLD + "15", display: "flex", alignItems: "center", justifyContent: "center", margin: "0 auto 16px" }}>
            <svg width="30" height="30" viewBox="0 0 24 24" fill="none" stroke={GOLD} strokeWidth="2" strokeLinecap="round"><rect x="2" y="4" width="20" height="16" rx="2"/><polyline points="22,4 12,13 2,4"/></svg>
          </div>
          <div style={{ fontSize: 18, fontWeight: 700, color: C.text, marginBottom: 8 }}>بعتنالك كود على البريد الإلكتروني</div>
          <div style={{ fontSize: 14, color: GOLD, fontWeight: 600 }}>ow****@gmail.com</div>
          <button style={{ background: "none", border: "none", color: C.sub, fontSize: 12, cursor: "pointer", marginTop: 6, ...TJ, textDecoration: "underline" }}>تغيير البريد الإلكتروني</button>
        </div>
        <div style={{ display: "flex", gap: 10, justifyContent: "center", marginBottom: 20, direction: "ltr" }}>
          {["5", "8", "2", "1", "", ""].map((v, i) => (
            <div key={i} style={{ width: 48, height: 58, borderRadius: 12, border: `2px solid ${v ? GOLD : C.border}`, background: v ? GOLD + "0A" : "white", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 22, fontWeight: 800, color: C.text }}>{v}</div>
          ))}
        </div>
        <div style={{ textAlign: "center", marginBottom: 24 }}>
          <span style={{ fontSize: 13, color: C.sub }}>إعادة الإرسال بعد </span>
          <span style={{ fontSize: 13, fontWeight: 700, color: GOLD }}>38 ثانية</span>
        </div>
        <button style={{ width: "100%", height: 52, background: GOLD, border: "none", borderRadius: 14, color: "white", fontSize: 16, fontWeight: 700, cursor: "pointer", ...TJ }}>تأكيد الدخول</button>
        <div style={{ textAlign: "center", marginTop: 16 }}>
          <button style={{ background: "none", border: "none", color: GOLD, fontSize: 13, cursor: "pointer", fontWeight: 600, ...TJ }}>إعادة إرسال الكود</button>
        </div>
      </div>
    </div>
  );
}

export function VisitorRestrictedSheet() {
  return (
    <div style={{ width: 390, height: 844, background: "rgba(0,0,0,0.5)", display: "flex", flexDirection: "column", justifyContent: "flex-end", ...TJ, direction: "rtl" }}>
      <div style={{ background: "white", borderRadius: "24px 24px 0 0", padding: "24px 24px 40px" }}>
        <div style={{ width: 40, height: 4, borderRadius: 2, background: "#E5E7EB", margin: "0 auto 24px" }} />
        <div style={{ display: "flex", flexDirection: "column", alignItems: "center", textAlign: "center", marginBottom: 28 }}>
          <div style={{ width: 64, height: 64, borderRadius: 20, background: TEAL + "12", display: "flex", alignItems: "center", justifyContent: "center", marginBottom: 16 }}>
            <svg width="30" height="30" viewBox="0 0 24 24" fill="none" stroke={TEAL} strokeWidth="2" strokeLinecap="round"><rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0110 0v4"/></svg>
          </div>
          <div style={{ fontSize: 18, fontWeight: 800, color: C.text, marginBottom: 8 }}>سجّل دخولك عشان تكمل</div>
          <div style={{ fontSize: 13, color: C.sub, lineHeight: 1.6, maxWidth: 280 }}>الميزة دي محتاجة حساب عشان نحافظ على الأمان والثقة</div>
        </div>
        <PrimaryBtn label="تسجيل الدخول" />
        <button style={{ width: "100%", height: 48, background: "none", border: `1.5px solid ${C.border}`, borderRadius: 12, color: C.text, fontSize: 15, fontWeight: 600, cursor: "pointer", marginTop: 10, ...TJ }}>إنشاء حساب</button>
      </div>
    </div>
  );
}

// ════════════════════════════════════════════════════════════════════════
// 2. UPDATED KYC UPLOAD (with privacy hint)
// ════════════════════════════════════════════════════════════════════════

export function UpdatedKYCUploadScreen() {
  return (
    <div style={{ width: 390, height: 844, background: C.bg, display: "flex", flexDirection: "column", ...TJ, direction: "rtl" }}>
      <StatusBar />
      <NavBar title="رفع البطاقة الشخصية" onBack={() => {}} />
      {/* Step bar */}
      <div style={{ padding: "12px 24px", background: "white", borderBottom: `1px solid ${C.border}` }}>
        <div style={{ display: "flex", gap: 6 }}>
          {[1,2,3].map(s => <div key={s} style={{ flex: 1, height: 4, borderRadius: 2, background: s === 1 ? TEAL : "#E5E7EB" }} />)}
        </div>
        <div style={{ fontSize: 11, color: C.sub, marginTop: 6 }}>الخطوة 2 من 3</div>
      </div>
      <div style={{ flex: 1, padding: "20px 20px", overflowY: "auto" }}>
        <div style={{ fontSize: 16, fontWeight: 700, color: C.text, marginBottom: 4 }}>صورة الوجه الأمامي للبطاقة</div>
        <div style={{ fontSize: 12, color: C.sub, marginBottom: 16 }}>تأكد أن الصورة واضحة وكل البيانات مقروءة</div>

        {/* Upload box */}
        <div style={{ border: `2px dashed ${C.border}`, borderRadius: 16, padding: "32px 20px", display: "flex", flexDirection: "column", alignItems: "center", marginBottom: 16, background: "white" }}>
          <div style={{ width: 56, height: 56, borderRadius: 14, background: "#F3F4F6", display: "flex", alignItems: "center", justifyContent: "center", marginBottom: 12 }}>
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke={SLATE} strokeWidth="2" strokeLinecap="round"><rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/></svg>
          </div>
          <div style={{ fontSize: 14, fontWeight: 600, color: C.text, marginBottom: 4 }}>اضغط لرفع الصورة</div>
          <div style={{ fontSize: 11, color: C.sub }}>JPG · PNG · حد أقصى 10 MB</div>
        </div>

        {/* Privacy hint — main card */}
        <PrivacyCard
          icon={<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke={TEAL} strokeWidth="2" strokeLinecap="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>}
          text="صورة البطاقة لا تظهر لأي مستخدم نهائياً"
          sub="المستندات دي للمراجعة الداخلية فقط، ومش بتتعرض للمالك أو المستأجرين"
        />

        <div style={{ height: 20 }} />
        <div style={{ fontSize: 16, fontWeight: 700, color: C.text, marginBottom: 4 }}>صورة الوجه الخلفي للبطاقة</div>
        <div style={{ fontSize: 12, color: C.sub, marginBottom: 16 }}>تأكد من رؤية كل التفاصيل والأرقام</div>
        <div style={{ border: `2px dashed ${C.border}`, borderRadius: 16, padding: "32px 20px", display: "flex", flexDirection: "column", alignItems: "center", marginBottom: 16, background: "white" }}>
          <div style={{ width: 56, height: 56, borderRadius: 14, background: "#F3F4F6", display: "flex", alignItems: "center", justifyContent: "center", marginBottom: 12 }}>
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke={SLATE} strokeWidth="2" strokeLinecap="round"><rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/></svg>
          </div>
          <div style={{ fontSize: 14, fontWeight: 600, color: C.text, marginBottom: 4 }}>اضغط لرفع الصورة</div>
          <div style={{ fontSize: 11, color: C.sub }}>JPG · PNG · حد أقصى 10 MB</div>
        </div>
        <PrivacyCard
          icon={<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke={TEAL} strokeWidth="2" strokeLinecap="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>}
          text="صورة البطاقة لا تظهر لأي مستخدم نهائياً"
          sub="المستندات دي للمراجعة الداخلية فقط، ومش بتتعرض للمالك أو المستأجرين"
        />
        <div style={{ height: 100 }} />
      </div>
      <div style={{ padding: "16px 20px 32px", background: "white", borderTop: `1px solid ${C.border}` }}>
        <PrimaryBtn label="التالي" />
      </div>
    </div>
  );
}

// ════════════════════════════════════════════════════════════════════════
// 3. OWNER DASHBOARD — with Visit Requests icon + badge
// ════════════════════════════════════════════════════════════════════════

export function UpdatedOwnerDashboardScreen() {
  const shortcuts = [
    { icon: "🏠", label: "عقاراتي", count: "4", color: GOLD },
    { icon: "📅", label: "طلبات الزيارة", count: "3", color: TEAL, highlight: true },
    { icon: "💬", label: "الرسائل", count: "2", color: "#2563EB" },
    { icon: "📊", label: "الإيرادات", count: null, color: GREEN },
  ];
  return (
    <div style={{ width: 390, height: 844, background: C.bg, display: "flex", flexDirection: "column", ...TJ, direction: "rtl" }}>
      <StatusBar />
      {/* Header */}
      <div style={{ background: `linear-gradient(135deg,#92400E,${GOLD})`, padding: "16px 20px 24px" }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 16 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <div style={{ width: 40, height: 40, borderRadius: 20, background: "rgba(255,255,255,0.2)", display: "flex", alignItems: "center", justifyContent: "center" }}>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2"><path d="M18 8h1a4 4 0 010 8h-1M2 8h16v9a4 4 0 01-4 4H6a4 4 0 01-4-4V8zM6 1v3M10 1v3M14 1v3"/></svg>
            </div>
            <div>
              <div style={{ fontSize: 11, color: "rgba(255,255,255,0.7)" }}>مرحباً،</div>
              <div style={{ fontSize: 16, fontWeight: 700, color: "white" }}>محمد العمراني</div>
            </div>
          </div>
          <div style={{ position: "relative" }}>
            <div style={{ width: 40, height: 40, borderRadius: 20, background: "rgba(255,255,255,0.15)", display: "flex", alignItems: "center", justifyContent: "center" }}>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2"><path d="M18 8A6 6 0 006 8c0 7-3 9-3 9h18s-3-2-3-9M13.73 21a2 2 0 01-3.46 0"/></svg>
            </div>
            <div style={{ position: "absolute", top: -2, left: -2, width: 16, height: 16, borderRadius: 8, background: ROSE, display: "flex", alignItems: "center", justifyContent: "center" }}>
              <span style={{ fontSize: 9, fontWeight: 800, color: "white" }}>5</span>
            </div>
          </div>
        </div>
        {/* Stats row */}
        <div style={{ display: "flex", gap: 10 }}>
          {[{label:"الإيرادات",val:"12,400 ر.س"},{label:"نسبة الإشغال",val:"75%"}].map(s => (
            <div key={s.label} style={{ flex: 1, background: "rgba(255,255,255,0.15)", borderRadius: 12, padding: "12px 14px" }}>
              <div style={{ fontSize: 11, color: "rgba(255,255,255,0.7)", marginBottom: 4 }}>{s.label}</div>
              <div style={{ fontSize: 18, fontWeight: 800, color: "white" }}>{s.val}</div>
            </div>
          ))}
        </div>
      </div>
      {/* Shortcut grid */}
      <div style={{ padding: "16px 16px 0" }}>
        <div style={{ fontSize: 14, fontWeight: 700, color: C.text, marginBottom: 12 }}>الاختصارات</div>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
          {shortcuts.map(sh => (
            <button key={sh.label} style={{ background: sh.highlight ? TEAL + "0F" : "white", border: sh.highlight ? `2px solid ${TEAL}30` : `1px solid ${C.border}`, borderRadius: 16, padding: "16px 14px", display: "flex", flexDirection: "column", alignItems: "flex-start", gap: 8, cursor: "pointer", position: "relative", textAlign: "right" }}>
              <div style={{ position: "relative" }}>
                <div style={{ width: 40, height: 40, borderRadius: 12, background: sh.color + "18", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 20 }}>{sh.icon}</div>
                {sh.count && (
                  <div style={{ position: "absolute", top: -4, right: -4, width: 18, height: 18, borderRadius: 9, background: sh.highlight ? TEAL : ROSE, display: "flex", alignItems: "center", justifyContent: "center" }}>
                    <span style={{ fontSize: 9, fontWeight: 800, color: "white" }}>{sh.count}</span>
                  </div>
                )}
              </div>
              <div style={{ fontSize: 13, fontWeight: 700, color: sh.highlight ? TEAL : C.text, ...TJ }}>{sh.label}</div>
            </button>
          ))}
        </div>
      </div>
      {/* Platform fees note */}
      <div style={{ margin: "14px 16px 0" }}>
        <div style={{ background: "#FFFBEB", border: `1px solid ${GOLD}30`, borderRadius: 12, padding: "10px 14px", display: "flex", alignItems: "center", gap: 10, direction: "rtl" }}>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke={GOLD} strokeWidth="2" strokeLinecap="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
          <span style={{ fontSize: 12, color: "#92400E", ...TJ }}>رسوم المنصة يتم خصمها من أرباح المالك</span>
        </div>
      </div>
      {/* Recent properties */}
      <div style={{ padding: "14px 16px", flex: 1, overflowY: "auto" }}>
        <div style={{ fontSize: 14, fontWeight: 700, color: C.text, marginBottom: 10 }}>آخر العقارات</div>
        {[
          {name:"شقة في الرياض",status:"مقبول",statusColor:GREEN},
          {name:"استوديو في جدة",status:"قيد المراجعة",statusColor:GOLD},
        ].map(p => (
          <div key={p.name} style={{ background: "white", borderRadius: 14, padding: "14px", border: `1px solid ${C.border}`, marginBottom: 10, display: "flex", alignItems: "center", gap: 12 }}>
            <div style={{ width: 48, height: 48, borderRadius: 12, background: "#F3F4F6" }} />
            <div style={{ flex: 1 }}>
              <div style={{ fontSize: 14, fontWeight: 600, color: C.text }}>{p.name}</div>
              <div style={{ fontSize: 11, color: p.statusColor, fontWeight: 600, marginTop: 3 }}>{p.status}</div>
            </div>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke={C.sub} strokeWidth="2"><polyline points="9 18 15 12 9 6"/></svg>
          </div>
        ))}
      </div>
    </div>
  );
}

// ════════════════════════════════════════════════════════════════════════
// 4 + 7 + 9. ADD PROPERTY — Smoking + Suitable For + Proof of Ownership
// ════════════════════════════════════════════════════════════════════════

export function UpdatedAddPropertyStep3Screen() {
  const [smoking, setSmoking] = useState("ممنوع");
  const [suitable, setSuitable] = useState("عائلات");
  const [uploadState, setUploadState] = useState<"empty"|"uploading"|"uploaded"|"failed">("empty");

  const smokingOpts = ["مسموح", "ممنوع", "حسب الاتفاق"];
  const suitableOpts = ["الكل", "ولاد فقط", "بنات فقط", "عائلات", "أفراد", "مشاركة"];

  return (
    <div style={{ width: 390, height: 844, background: C.bg, display: "flex", flexDirection: "column", ...TJ, direction: "rtl" }}>
      <StatusBar />
      <NavBar title="تفاصيل العقار" onBack={() => {}} />
      <div style={{ flex: 1, padding: "16px 16px 0", overflowY: "auto" }}>

        {/* Smoking field */}
        <div style={{ background: "white", borderRadius: 16, padding: "16px", border: `1px solid ${C.border}`, marginBottom: 12 }}>
          <div style={{ fontSize: 14, fontWeight: 700, color: C.text, marginBottom: 14 }}>التدخين مسموح؟</div>
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            {smokingOpts.map(opt => (
              <button key={opt} onClick={() => setSmoking(opt)} style={{ padding: "8px 18px", borderRadius: 20, border: `1.5px solid ${smoking === opt ? TEAL : C.border}`, background: smoking === opt ? TEAL + "12" : "white", color: smoking === opt ? TEAL : C.text, fontSize: 13, fontWeight: 600, cursor: "pointer", ...TJ, display: "flex", alignItems: "center", gap: 5 }}>
                {smoking === opt && <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke={TEAL} strokeWidth="3" strokeLinecap="round"><polyline points="20 6 9 17 4 12"/></svg>}
                {opt}
              </button>
            ))}
          </div>
        </div>

        {/* Suitable for */}
        <div style={{ background: "white", borderRadius: 16, padding: "16px", border: `1px solid ${C.border}`, marginBottom: 12 }}>
          <div style={{ fontSize: 14, fontWeight: 700, color: C.text, marginBottom: 14 }}>العقار مناسب لـ</div>
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            {suitableOpts.map(opt => (
              <button key={opt} onClick={() => setSuitable(opt)} style={{ padding: "8px 16px", borderRadius: 20, border: `1.5px solid ${suitable === opt ? TEAL : C.border}`, background: suitable === opt ? TEAL + "12" : "white", color: suitable === opt ? TEAL : C.text, fontSize: 13, fontWeight: 600, cursor: "pointer", ...TJ, display: "flex", alignItems: "center", gap: 5 }}>
                {suitable === opt && <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke={TEAL} strokeWidth="3" strokeLinecap="round"><polyline points="20 6 9 17 4 12"/></svg>}
                {opt}
              </button>
            ))}
          </div>
        </div>

        {/* Proof of ownership */}
        <div style={{ background: "white", borderRadius: 16, padding: "16px", border: `1px solid ${C.border}`, marginBottom: 12 }}>
          <div style={{ fontSize: 14, fontWeight: 700, color: C.text, marginBottom: 4 }}>إثبات ملكية العقار</div>
          <div style={{ fontSize: 11, color: C.sub, marginBottom: 14 }}>ممكن ترفع وصل كهربا، وصل مياه، أو عقد الملكية</div>

          {uploadState === "empty" && (
            <button onClick={() => setUploadState("uploading")} style={{ width: "100%", border: `2px dashed ${C.border}`, borderRadius: 12, padding: "24px 16px", background: "#F9FAFB", cursor: "pointer", display: "flex", flexDirection: "column", alignItems: "center", gap: 8 }}>
              <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke={SLATE} strokeWidth="2" strokeLinecap="round"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
              <span style={{ fontSize: 13, fontWeight: 600, color: C.text, ...TJ }}>ارفع إثبات الملكية</span>
              <span style={{ fontSize: 11, color: C.sub, ...TJ }}>PDF · JPG · PNG</span>
            </button>
          )}

          {uploadState === "uploading" && (
            <div style={{ border: `1px solid ${C.border}`, borderRadius: 12, padding: "16px", background: "#F9FAFB" }}>
              <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 10 }}>
                <div style={{ width: 36, height: 36, borderRadius: 8, background: TEAL + "15", display: "flex", alignItems: "center", justifyContent: "center" }}>
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke={TEAL} strokeWidth="2"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
                </div>
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: 12, fontWeight: 600, color: C.text }}>عقد_الملكية.pdf</div>
                  <div style={{ fontSize: 11, color: C.sub }}>جاري الرفع...</div>
                </div>
              </div>
              <div style={{ height: 4, borderRadius: 2, background: "#E5E7EB" }}>
                <div style={{ width: "60%", height: "100%", borderRadius: 2, background: TEAL }} />
              </div>
            </div>
          )}

          {uploadState === "uploaded" && (
            <div style={{ border: `1.5px solid ${GREEN}30`, borderRadius: 12, padding: "14px 16px", background: "#F0FDF4", display: "flex", alignItems: "center", gap: 10 }}>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke={GREEN} strokeWidth="2.5" strokeLinecap="round"><polyline points="20 6 9 17 4 12"/></svg>
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: 12, fontWeight: 600, color: C.text }}>عقد_الملكية.pdf</div>
                <div style={{ fontSize: 11, color: GREEN, fontWeight: 600 }}>تم الرفع بنجاح</div>
              </div>
              <button onClick={() => setUploadState("empty")} style={{ background: "none", border: "none", cursor: "pointer", color: ROSE }}>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke={ROSE} strokeWidth="2.5" strokeLinecap="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
              </button>
            </div>
          )}

          {uploadState === "failed" && (
            <div style={{ border: `1.5px solid ${ROSE}30`, borderRadius: 12, padding: "14px 16px", background: "#FFF5F5", display: "flex", alignItems: "center", gap: 10 }}>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke={ROSE} strokeWidth="2.5" strokeLinecap="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: 12, fontWeight: 600, color: ROSE }}>فشل الرفع، حاول تاني</div>
              </div>
              <button onClick={() => setUploadState("uploading")} style={{ background: "none", border: "none", cursor: "pointer", color: TEAL, fontSize: 12, fontWeight: 600, ...TJ }}>إعادة</button>
            </div>
          )}

          <div style={{ marginTop: 10 }}>
            <PrivacyCard
              icon={<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke={TEAL} strokeWidth="2" strokeLinecap="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>}
              text="المستند ده للمراجعة الداخلية فقط"
              sub="ومش هيظهر للمستخدمين أو المستأجرين"
            />
          </div>

          {/* Upload state switcher for demo */}
          <div style={{ display: "flex", gap: 6, marginTop: 10, flexWrap: "wrap" }}>
            {(["empty","uploading","uploaded","failed"] as const).map(s => (
              <button key={s} onClick={() => setUploadState(s)} style={{ padding: "4px 10px", borderRadius: 8, border: `1px solid ${uploadState===s ? TEAL : C.border}`, background: uploadState===s ? TEAL+"10" : "white", fontSize: 10, color: uploadState===s ? TEAL : C.sub, cursor: "pointer", ...TJ }}>
                {s === "empty" ? "فارغ" : s === "uploading" ? "يرفع" : s === "uploaded" ? "مرفوع" : "خطأ"}
              </button>
            ))}
          </div>
        </div>

        <div style={{ height: 100 }} />
      </div>
      <div style={{ padding: "16px 16px 32px", background: "white", borderTop: `1px solid ${C.border}` }}>
        <PrimaryBtn label="التالي" />
      </div>
    </div>
  );
}

// ════════════════════════════════════════════════════════════════════════
// 5. SHARE PROPERTY SHEET
// ════════════════════════════════════════════════════════════════════════

export function SharePropertySheet() {
  const [copied, setCopied] = useState(false);
  return (
    <div style={{ width: 390, height: 844, background: "rgba(0,0,0,0.5)", display: "flex", flexDirection: "column", justifyContent: "flex-end", ...TJ, direction: "rtl" }}>
      <div style={{ background: "white", borderRadius: "24px 24px 0 0", padding: "20px 20px 40px" }}>
        <div style={{ width: 40, height: 4, borderRadius: 2, background: "#E5E7EB", margin: "0 auto 20px" }} />
        <div style={{ fontSize: 16, fontWeight: 700, color: C.text, marginBottom: 20 }}>مشاركة العقار</div>

        {copied && (
          <div style={{ background: TEAL + "12", border: `1px solid ${TEAL}30`, borderRadius: 10, padding: "10px 14px", marginBottom: 12, display: "flex", alignItems: "center", gap: 8 }}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke={TEAL} strokeWidth="2.5" strokeLinecap="round"><polyline points="20 6 9 17 4 12"/></svg>
            <span style={{ fontSize: 13, color: TEAL, fontWeight: 600 }}>تم نسخ رابط العقار</span>
          </div>
        )}

        {[
          { label: "نسخ الرابط", icon: <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke={TEAL} strokeWidth="2" strokeLinecap="round"><path d="M10 13a5 5 0 007.54.54l3-3a5 5 0 00-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 00-7.54-.54l-3 3a5 5 0 007.07 7.07l1.71-1.71"/></svg>, color: TEAL, action: () => setCopied(true) },
          { label: "مشاركة", icon: <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#2563EB" strokeWidth="2" strokeLinecap="round"><circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><line x1="8.59" y1="13.51" x2="15.42" y2="17.49"/><line x1="15.41" y1="6.51" x2="8.59" y2="10.49"/></svg>, color: "#2563EB", action: () => {} },
          { label: "إلغاء", icon: <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke={ROSE} strokeWidth="2" strokeLinecap="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>, color: ROSE, action: () => {} },
        ].map(item => (
          <button key={item.label} onClick={item.action} style={{ width: "100%", padding: "16px 16px", border: `1px solid ${C.border}`, borderRadius: 14, background: "white", display: "flex", alignItems: "center", gap: 14, cursor: "pointer", marginBottom: 10 }}>
            <div style={{ width: 40, height: 40, borderRadius: 12, background: "#F3F4F6", display: "flex", alignItems: "center", justifyContent: "center" }}>{item.icon}</div>
            <span style={{ fontSize: 15, fontWeight: 600, color: item.color, ...TJ }}>{item.label}</span>
          </button>
        ))}
      </div>
    </div>
  );
}

// ════════════════════════════════════════════════════════════════════════
// 6. TENANT FILTER — with Suitable For + Rental Period combo
// ════════════════════════════════════════════════════════════════════════

export function UpdatedFilterSheetScreen() {
  const [suitable, setSuitable] = useState("الكل");
  const [period, setPeriod] = useState("شهر");
  const [count, setCount] = useState("3");

  const suitableOpts = ["الكل", "ولاد فقط", "بنات فقط", "عائلات", "أفراد", "مشاركة"];
  const periodOpts = ["يوم", "أسبوع", "شهر"];

  return (
    <div style={{ width: 390, height: 844, background: C.bg, display: "flex", flexDirection: "column", ...TJ, direction: "rtl" }}>
      <StatusBar />
      <NavBar title="الفلاتر" onBack={() => {}} right={
        <button style={{ background: "none", border: "none", color: TEAL, fontSize: 13, fontWeight: 600, cursor: "pointer", ...TJ }}>إعادة تعيين</button>
      } />
      <div style={{ flex: 1, padding: "16px 16px 0", overflowY: "auto" }}>

        {/* Property type */}
        <div style={{ background: "white", borderRadius: 16, padding: "16px", border: `1px solid ${C.border}`, marginBottom: 12 }}>
          <div style={{ fontSize: 14, fontWeight: 700, color: C.text, marginBottom: 12 }}>نوع العقار</div>
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            {["الكل", "شقة", "غرفة", "استوديو", "فيلا"].map((o, i) => (
              <button key={o} style={{ padding: "7px 16px", borderRadius: 20, border: `1.5px solid ${i===0 ? TEAL : C.border}`, background: i===0 ? TEAL+"12" : "white", color: i===0 ? TEAL : C.text, fontSize: 13, fontWeight: 600, cursor: "pointer", ...TJ }}>{o}</button>
            ))}
          </div>
        </div>

        {/* Suitable for */}
        <div style={{ background: "white", borderRadius: 16, padding: "16px", border: `1px solid ${C.border}`, marginBottom: 12 }}>
          <div style={{ fontSize: 14, fontWeight: 700, color: C.text, marginBottom: 12 }}>مناسب لـ</div>
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            {suitableOpts.map(opt => (
              <button key={opt} onClick={() => setSuitable(opt)} style={{ padding: "7px 16px", borderRadius: 20, border: `1.5px solid ${suitable===opt ? TEAL : C.border}`, background: suitable===opt ? TEAL+"12" : "white", color: suitable===opt ? TEAL : C.text, fontSize: 13, fontWeight: 600, cursor: "pointer", ...TJ }}>
                {opt}
              </button>
            ))}
          </div>
        </div>

        {/* Rental period — dropdown + number */}
        <div style={{ background: "white", borderRadius: 16, padding: "16px", border: `1px solid ${C.border}`, marginBottom: 12 }}>
          <div style={{ fontSize: 14, fontWeight: 700, color: C.text, marginBottom: 12 }}>فترة التأجير</div>
          <div style={{ display: "flex", gap: 10, alignItems: "flex-start" }}>
            {/* Number field (left in RTL) */}
            <div style={{ flex: 1 }}>
              <div style={{ fontSize: 12, color: C.sub, marginBottom: 6 }}>العدد</div>
              <input
                value={count}
                onChange={e => setCount(e.target.value)}
                placeholder="اكتب العدد"
                type="number"
                style={{ width: "100%", height: 48, borderRadius: 12, border: `1.5px solid ${C.border}`, padding: "0 14px", fontSize: 16, fontWeight: 700, color: C.text, background: "white", boxSizing: "border-box", textAlign: "center", outline: "none", ...TJ }}
              />
            </div>
            {/* Dropdown (right in RTL) */}
            <div style={{ flex: 1 }}>
              <div style={{ fontSize: 12, color: C.sub, marginBottom: 6 }}>الوحدة</div>
              <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                {periodOpts.map(opt => (
                  <button key={opt} onClick={() => setPeriod(opt)} style={{ height: 48, borderRadius: 12, border: `1.5px solid ${period===opt ? TEAL : C.border}`, background: period===opt ? TEAL+"12" : "white", color: period===opt ? TEAL : C.text, fontSize: 14, fontWeight: 700, cursor: "pointer", ...TJ }}>
                    {opt}
                  </button>
                ))}
              </div>
            </div>
          </div>
          {count && period && (
            <div style={{ marginTop: 10, padding: "8px 12px", background: TEAL+"08", borderRadius: 8, fontSize: 12, color: TEAL, fontWeight: 600 }}>
              مدة التأجير: {count} {period}{parseInt(count) > 1 ? "ات" : ""}
            </div>
          )}
        </div>

        {/* Price range */}
        <div style={{ background: "white", borderRadius: 16, padding: "16px", border: `1px solid ${C.border}`, marginBottom: 12 }}>
          <div style={{ fontSize: 14, fontWeight: 700, color: C.text, marginBottom: 12 }}>نطاق السعر (ر.س)</div>
          <div style={{ display: "flex", gap: 10 }}>
            <div style={{ flex: 1, height: 48, borderRadius: 12, border: `1.5px solid ${C.border}`, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 14, color: C.text, background: "white" }}>500</div>
            <div style={{ height: 48, display: "flex", alignItems: "center", color: C.sub, fontSize: 13 }}>—</div>
            <div style={{ flex: 1, height: 48, borderRadius: 12, border: `1.5px solid ${C.border}`, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 14, color: C.text, background: "white" }}>5,000</div>
          </div>
        </div>

        <div style={{ height: 100 }} />
      </div>
      <div style={{ padding: "16px 16px 32px", background: "white", borderTop: `1px solid ${C.border}` }}>
        <PrimaryBtn label="عرض النتائج" />
      </div>
    </div>
  );
}

// ════════════════════════════════════════════════════════════════════════
// 11. OWNER REQUESTS — chat icon instead of "شات"
// ════════════════════════════════════════════════════════════════════════

export function UpdatedOwnerRequestsListScreen() {
  const [activeStatus, setActiveStatus] = useState("الكل");
  const statusTabs = [
    { label: "الكل", count: 6 },
    { label: "جديد", count: 3 },
    { label: "مقبول", count: 2 },
    { label: "مرفوض", count: 1 },
    { label: "مكتمل", count: 0 },
  ];
  const requests = [
    { name: "أحمد السيد", verified: true, property: "شقة 3 غرف — الرياض", date: "غداً 10:00 ص", status: "pending" },
    { name: "سارة محمد", verified: true, property: "استوديو — جدة", date: "الأحد 2:00 م", status: "accepted" },
    { name: "خالد عبدالله", verified: false, property: "غرفة — الدمام", date: "الإثنين 11:00 ص", status: "pending" },
  ];

  return (
    <div style={{ width: 390, height: 844, background: C.bg, display: "flex", flexDirection: "column", ...TJ, direction: "rtl" }}>
      <StatusBar />
      <NavBar title="طلبات الزيارة" onBack={() => {}} />

      {/* Status filter section — copied from O-REQ-01 style */}
      <div style={{ background: "white", borderBottom: `1px solid ${C.border}`, padding: "12px 16px" }}>
        {/* Summary cards */}
        <div style={{ display: "flex", gap: 8, marginBottom: 12 }}>
          {[{label:"إجمالي الطلبات",val:"6",color:TEAL},{label:"بانتظار الرد",val:"3",color:GOLD}].map(s => (
            <div key={s.label} style={{ flex: 1, background: s.color+"0E", border: `1px solid ${s.color}20`, borderRadius: 12, padding: "10px 12px" }}>
              <div style={{ fontSize: 11, color: C.sub }}>{s.label}</div>
              <div style={{ fontSize: 20, fontWeight: 800, color: s.color, marginTop: 2 }}>{s.val}</div>
            </div>
          ))}
        </div>
        {/* Status chips */}
        <div style={{ display: "flex", gap: 8, overflowX: "auto" }}>
          {statusTabs.map(tab => (
            <button key={tab.label} onClick={() => setActiveStatus(tab.label)}
              style={{ flexShrink: 0, display: "flex", alignItems: "center", gap: 5, padding: "7px 14px", borderRadius: 20, border: `1.5px solid ${activeStatus === tab.label ? TEAL : C.border}`, background: activeStatus === tab.label ? TEAL : "white", color: activeStatus === tab.label ? "white" : C.text, fontSize: 13, fontWeight: 600, cursor: "pointer", ...TJ }}>
              <span>{tab.label}</span>
              {tab.count > 0 && (
                <span style={{ fontSize: 11, fontWeight: 700, background: activeStatus === tab.label ? "rgba(255,255,255,0.25)" : C.border, color: activeStatus === tab.label ? "white" : C.sub, borderRadius: 10, padding: "0 6px", lineHeight: "18px" }}>{tab.count}</span>
              )}
            </button>
          ))}
        </div>
      </div>

      <div style={{ flex: 1, padding: "12px 16px", overflowY: "auto" }}>
        {requests.map((req, i) => (
          <div key={i} style={{ background: "white", borderRadius: 16, border: `1px solid ${C.border}`, padding: "14px 14px", marginBottom: 12 }}>
            {/* Tenant info row */}
            <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 12 }}>
              <div style={{ width: 40, height: 40, borderRadius: 20, background: TEAL + "20", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 16, fontWeight: 700, color: TEAL }}>
                {req.name[0]}
              </div>
              <div style={{ flex: 1 }}>
                <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                  <span style={{ fontSize: 14, fontWeight: 700, color: C.text }}>{req.name}</span>
                  {req.verified && (
                    <span style={{ background: TEAL + "12", color: TEAL, fontSize: 10, fontWeight: 700, padding: "2px 8px", borderRadius: 10 }}>موثّق</span>
                  )}
                  {/* Chat icon — replaces "شات" text */}
                  <button title="فتح الشات" style={{ marginRight: "auto", width: 32, height: 32, borderRadius: 10, border: `1.5px solid ${C.border}`, background: "white", display: "flex", alignItems: "center", justifyContent: "center", cursor: "pointer" }}>
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke={TEAL} strokeWidth="2" strokeLinecap="round"><path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z"/></svg>
                  </button>
                </div>
                <div style={{ fontSize: 11, color: C.sub, marginTop: 2 }}>{req.property}</div>
              </div>
            </div>
            {/* Visit time */}
            <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 12, padding: "8px 10px", background: "#F9FAFB", borderRadius: 10 }}>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke={SLATE} strokeWidth="2" strokeLinecap="round"><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>
              <span style={{ fontSize: 12, color: C.sub }}>{req.date}</span>
            </div>
            {/* Actions */}
            <div style={{ display: "flex", gap: 8 }}>
              {req.status === "pending" ? (
                <>
                  <button style={{ flex: 1, height: 40, borderRadius: 10, background: TEAL, border: "none", color: "white", fontSize: 14, fontWeight: 700, cursor: "pointer", ...TJ }}>قبول</button>
                  <button style={{ flex: 1, height: 40, borderRadius: 10, background: "white", border: `1.5px solid ${ROSE}`, color: ROSE, fontSize: 14, fontWeight: 700, cursor: "pointer", ...TJ }}>رفض</button>
                </>
              ) : (
                <div style={{ flex: 1, height: 40, borderRadius: 10, background: GREEN + "12", border: `1px solid ${GREEN}30`, display: "flex", alignItems: "center", justifyContent: "center" }}>
                  <span style={{ fontSize: 13, color: GREEN, fontWeight: 600 }}>تم القبول</span>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ════════════════════════════════════════════════════════════════════════
// O-ADD-01 UPDATED — with map location field
// ════════════════════════════════════════════════════════════════════════

export function UpdatedAddPropertyStep1Screen() {
  const [locSet, setLocSet] = useState(false);
  return (
    <div style={{ width: 390, height: 844, background: C.bg, display: "flex", flexDirection: "column", ...TJ, direction: "rtl" }}>
      <StatusBar />
      <NavBar title="إضافة عقار" onBack={() => {}} />
      <div style={{ padding: "12px 20px", background: "white", borderBottom: `1px solid ${C.border}` }}>
        <div style={{ display: "flex", gap: 6 }}>
          {[1,2,3].map(s => <div key={s} style={{ flex: 1, height: 4, borderRadius: 2, background: s === 1 ? TEAL : "#E5E7EB" }} />)}
        </div>
        <div style={{ fontSize: 11, color: C.sub, marginTop: 6 }}>الخطوة 1 من 3 — معلومات العقار</div>
      </div>
      <div style={{ flex: 1, padding: "16px", overflowY: "auto" }}>
        <div style={{ background: "white", borderRadius: 16, padding: "16px", border: `1px solid ${C.border}`, marginBottom: 12 }}>
          <div style={{ fontSize: 14, fontWeight: 700, color: C.text, marginBottom: 14 }}>نوع العقار</div>
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            {["شقة","غرفة","استوديو","فيلا","دور"].map((o, i) => (
              <button key={o} style={{ padding: "8px 16px", borderRadius: 20, border: `1.5px solid ${i===0 ? TEAL : C.border}`, background: i===0 ? TEAL+"12" : "white", color: i===0 ? TEAL : C.text, fontSize: 13, fontWeight: 600, cursor: "pointer", ...TJ }}>
                {o}
              </button>
            ))}
          </div>
        </div>

        {/* Map location field */}
        <div style={{ background: "white", borderRadius: 16, padding: "16px", border: `1px solid ${C.border}`, marginBottom: 12 }}>
          <div style={{ fontSize: 14, fontWeight: 700, color: C.text, marginBottom: 4 }}>موقع العقار على الخريطة</div>
          <div style={{ fontSize: 11, color: C.sub, marginBottom: 14 }}>حدد موقع العقار بدقة عشان نراجع الإعلان بشكل أسرع</div>
          <div style={{ display: "flex", alignItems: "center", height: 44, borderRadius: 10, border: `1.5px solid ${C.border}`, background: "#F9FAFB", marginBottom: 12, padding: "0 12px", gap: 8 }}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke={SLATE} strokeWidth="2" strokeLinecap="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
            <input placeholder="ابحث عن الموقع..." style={{ flex: 1, border: "none", background: "transparent", fontSize: 13, color: C.text, outline: "none", direction: "rtl", ...TJ }} />
          </div>
          <div style={{ borderRadius: 12, overflow: "hidden", position: "relative", marginBottom: 12, height: 150, background: "#E8F4F0" }}>
            <svg width="100%" height="100%" style={{ position: "absolute", inset: 0 }}>
              {[20,40,60,80,100,120,140].map(y => <line key={y} x1="0" y1={y} x2="400" y2={y} stroke="#CBD5E1" strokeWidth="1"/>)}
              {[30,70,110,150,190,230,270,310,350].map(x => <line key={x} x1={x} y1="0" x2={x} y2="150" stroke="#CBD5E1" strokeWidth="1"/>)}
              <rect x="0" y="68" width="400" height="12" fill="#D1FAE5" rx="2"/>
              <rect x="135" y="0" width="12" height="150" fill="#D1FAE5" rx="2"/>
            </svg>
            <div style={{ position: "absolute", left: "50%", top: "50%", transform: "translate(-50%,-100%)" }}>
              <svg width="28" height="36" viewBox="0 0 32 40"><path d="M16 0C7.16 0 0 7.16 0 16c0 12 16 24 16 24S32 28 32 16C32 7.16 24.84 0 16 0z" fill={TEAL}/><circle cx="16" cy="16" r="7" fill="white"/></svg>
            </div>
            {locSet && (
              <div style={{ position: "absolute", top: 8, right: 8, background: TEAL, borderRadius: 8, padding: "4px 10px", display: "flex", alignItems: "center", gap: 5 }}>
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="3" strokeLinecap="round"><polyline points="20 6 9 17 4 12"/></svg>
                <span style={{ fontSize: 11, fontWeight: 700, color: "white", ...TJ }}>تم تحديد الموقع</span>
              </div>
            )}
          </div>
          <button onClick={() => setLocSet(true)} style={{ width: "100%", height: 44, borderRadius: 12, background: locSet ? GREEN : TEAL, border: "none", color: "white", fontSize: 14, fontWeight: 700, cursor: "pointer", ...TJ, display: "flex", alignItems: "center", justifyContent: "center", gap: 8 }}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5" strokeLinecap="round"><circle cx="12" cy="12" r="3"/><path d="M12 2v3m0 14v3M2 12h3m14 0h3"/></svg>
            {locSet ? "تم تحديد الموقع ✓" : "تحديد الموقع"}
          </button>
          <div style={{ marginTop: 10 }}>
            <PrivacyCard
              icon={<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke={TEAL} strokeWidth="2" strokeLinecap="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>}
              text="قد يظهر الموقع للمستأجرين بشكل تقريبي لحماية الخصوصية"
              sub=""
            />
          </div>
        </div>
        <div style={{ height: 80 }} />
      </div>
      <div style={{ padding: "16px 16px 32px", background: "white", borderTop: `1px solid ${C.border}` }}>
        <PrimaryBtn label="التالي" />
      </div>
    </div>
  );
}

// ════════════════════════════════════════════════════════════════════════
// O-ADD-03 UPDATED — Rental period: dropdown يوم/شهر/سنة + number field
// ════════════════════════════════════════════════════════════════════════

export function UpdatedAddPropertyStep3PricingScreen() {
  const [period, setPeriod] = useState("شهر");
  const [count, setCount] = useState("6");
  const [countErr, setCountErr] = useState("");
  const [showPicker, setShowPicker] = useState(false);
  const periodOpts = ["يوم", "شهر", "سنة"];

  const validate = () => {
    if (!count) { setCountErr("اكتب مدة التأجير"); return; }
    if (isNaN(Number(count)) || Number(count) <= 0) { setCountErr("اكتب رقم صحيح"); return; }
    setCountErr("");
  };

  return (
    <div style={{ width: 390, height: 844, background: C.bg, display: "flex", flexDirection: "column", ...TJ, direction: "rtl" }}>
      <StatusBar />
      <NavBar title="التسعير والتفاصيل" onBack={() => {}} />
      <div style={{ padding: "12px 20px", background: "white", borderBottom: `1px solid ${C.border}` }}>
        <div style={{ display: "flex", gap: 6 }}>
          {[1,2,3].map(s => <div key={s} style={{ flex: 1, height: 4, borderRadius: 2, background: TEAL }} />)}
        </div>
        <div style={{ fontSize: 11, color: C.sub, marginTop: 6 }}>الخطوة 3 من 3 — السعر والتفاصيل</div>
      </div>
      <div style={{ flex: 1, padding: "16px", overflowY: "auto" }}>
        <div style={{ background: "white", borderRadius: 16, padding: "16px", border: `1px solid ${C.border}`, marginBottom: 12 }}>
          <div style={{ fontSize: 14, fontWeight: 700, color: C.text, marginBottom: 12 }}>السعر</div>
          <div style={{ position: "relative" }}>
            <input defaultValue="2500" style={{ width: "100%", height: 52, borderRadius: 12, border: `1.5px solid ${TEAL}`, padding: "0 60px 0 16px", fontSize: 18, fontWeight: 700, color: C.text, background: "white", boxSizing: "border-box", textAlign: "right", outline: "none", ...TJ }} />
            <span style={{ position: "absolute", left: 16, top: "50%", transform: "translateY(-50%)", fontSize: 14, fontWeight: 600, color: C.sub }}>ر.س</span>
          </div>
        </div>

        {/* Rental period */}
        <div style={{ background: "white", borderRadius: 16, padding: "16px", border: `1px solid ${C.border}`, marginBottom: 12, position: "relative" }}>
          <div style={{ fontSize: 14, fontWeight: 700, color: C.text, marginBottom: 12 }}>فترة التأجير</div>
          <div style={{ display: "flex", gap: 10, alignItems: "flex-start" }}>
            {/* Number field — left */}
            <div style={{ flex: 1 }}>
              <div style={{ fontSize: 12, color: C.sub, marginBottom: 6 }}>العدد</div>
              <input value={count} onChange={e => { setCount(e.target.value); setCountErr(""); }} onBlur={validate} type="number" placeholder="اكتب العدد"
                style={{ width: "100%", height: 52, borderRadius: 12, border: `1.5px solid ${countErr ? ROSE : (count ? TEAL : C.border)}`, padding: "0 14px", fontSize: 18, fontWeight: 700, color: C.text, background: "white", boxSizing: "border-box", textAlign: "center", outline: "none", ...TJ }} />
              {countErr && <div style={{ fontSize: 11, color: ROSE, marginTop: 4, fontWeight: 600 }}>{countErr}</div>}
            </div>
            {/* Dropdown — right */}
            <div style={{ flex: 1 }}>
              <div style={{ fontSize: 12, color: C.sub, marginBottom: 6 }}>الوحدة</div>
              <button onClick={() => setShowPicker(!showPicker)} style={{ width: "100%", height: 52, borderRadius: 12, border: `1.5px solid ${TEAL}`, background: TEAL+"08", display: "flex", alignItems: "center", justifyContent: "space-between", padding: "0 14px", cursor: "pointer", ...TJ }}>
                <span style={{ fontSize: 16, fontWeight: 700, color: TEAL }}>{period}</span>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke={TEAL} strokeWidth="2.5"><polyline points="6 9 12 15 18 9"/></svg>
              </button>
              {showPicker && (
                <div style={{ position: "absolute", left: 16, zIndex: 10, background: "white", borderRadius: 12, border: `1.5px solid ${C.border}`, boxShadow: "0 8px 24px rgba(0,0,0,0.1)", overflow: "hidden", marginTop: 4, width: 120 }}>
                  {periodOpts.map(opt => (
                    <button key={opt} onClick={() => { setPeriod(opt); setShowPicker(false); }} style={{ width: "100%", padding: "13px 16px", border: "none", background: opt === period ? TEAL+"10" : "white", color: opt === period ? TEAL : C.text, fontSize: 15, fontWeight: opt === period ? 700 : 500, cursor: "pointer", textAlign: "right", ...TJ, display: "block", borderBottom: `1px solid ${C.border}` }}>{opt}</button>
                  ))}
                </div>
              )}
            </div>
          </div>
          {count && !countErr && (
            <div style={{ marginTop: 12, padding: "8px 12px", background: TEAL+"08", borderRadius: 8, fontSize: 12, color: TEAL, fontWeight: 600 }}>
              فترة التأجير: {count} {period}
            </div>
          )}
        </div>

        <div style={{ background: "#FFFBEB", border: `1px solid ${GOLD}25`, borderRadius: 12, padding: "12px 14px", display: "flex", alignItems: "flex-start", gap: 10, marginBottom: 12 }}>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke={GOLD} strokeWidth="2" strokeLinecap="round" style={{ flexShrink: 0, marginTop: 1 }}><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
          <span style={{ fontSize: 12, color: "#92400E", lineHeight: 1.5, ...TJ }}>رسوم المنصة يتم خصمها من أرباح المالك حسب سياسة سكون</span>
        </div>
        <div style={{ height: 80 }} />
      </div>
      <div style={{ padding: "16px 16px 32px", background: "white", borderTop: `1px solid ${C.border}` }}>
        <PrimaryBtn label="إرسال للمراجعة" />
      </div>
    </div>
  );
}

// ════════════════════════════════════════════════════════════════════════
// T-PROP-01 UPDATED — with Share button in header
// ════════════════════════════════════════════════════════════════════════

export function UpdatedPropertyDetailScreen() {
  const [saved, setSaved] = useState(false);
  const [showShare, setShowShare] = useState(false);
  const [copied, setCopied] = useState(false);

  return (
    <div style={{ width: 390, height: 844, background: C.bg, display: "flex", flexDirection: "column", ...TJ, direction: "rtl", position: "relative" }}>
      <StatusBar />
      <div style={{ position: "relative", height: 220, background: "linear-gradient(135deg,#0D6B63,#0F766E)", flexShrink: 0 }}>
        <div style={{ position: "absolute", top: 0, left: 0, right: 0, display: "flex", alignItems: "center", justifyContent: "space-between", padding: "10px 14px", zIndex: 2 }}>
          <button style={{ width: 36, height: 36, borderRadius: 18, background: "rgba(0,0,0,0.35)", border: "none", cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center" }}>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5" strokeLinecap="round"><polyline points="9 18 15 12 9 6"/></svg>
          </button>
          <div style={{ display: "flex", gap: 8 }}>
            <button onClick={() => { setShowShare(true); setCopied(false); }} style={{ width: 36, height: 36, borderRadius: 18, background: "rgba(0,0,0,0.35)", border: "none", cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center" }}>
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2" strokeLinecap="round"><circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><line x1="8.59" y1="13.51" x2="15.42" y2="17.49"/><line x1="15.41" y1="6.51" x2="8.59" y2="10.49"/></svg>
            </button>
            <button onClick={() => setSaved(!saved)} style={{ width: 36, height: 36, borderRadius: 18, background: "rgba(0,0,0,0.35)", border: "none", cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center" }}>
              <svg width="18" height="18" viewBox="0 0 24 24" fill={saved ? ROSE : "none"} stroke={saved ? ROSE : "white"} strokeWidth="2" strokeLinecap="round"><path d="M20.84 4.61a5.5 5.5 0 00-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 00-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 000-7.78z"/></svg>
            </button>
          </div>
        </div>
        <div style={{ position: "absolute", bottom: 12, left: 14 }}>
          <span style={{ background: TEAL, color: "white", fontSize: 11, fontWeight: 700, padding: "4px 10px", borderRadius: 8, ...TJ }}>موثّق ✓</span>
        </div>
      </div>
      <div style={{ flex: 1, overflowY: "auto" }}>
        <div style={{ padding: "18px 18px 0" }}>
          <div style={{ fontSize: 20, fontWeight: 800, color: C.text, marginBottom: 4 }}>شقة 3 غرف في الرياض</div>
          <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 12 }}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke={C.sub} strokeWidth="2" strokeLinecap="round"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0118 0z"/><circle cx="12" cy="10" r="3"/></svg>
            <span style={{ fontSize: 13, color: C.sub }}>حي الملك فهد، الرياض</span>
          </div>
          <span style={{ fontSize: 22, fontWeight: 900, color: TEAL }}>2,500 <span style={{ fontSize: 14, fontWeight: 600 }}>ر.س / شهر</span></span>
          <div style={{ display: "flex", gap: 16, margin: "14px 0", padding: "12px", background: "#F9FAFB", borderRadius: 12 }}>
            {[{icon:"🛏",val:"3",label:"غرف"},{icon:"🚿",val:"2",label:"حمام"},{icon:"📐",val:"120",label:"م²"}].map(s => (
              <div key={s.label} style={{ flex: 1, textAlign: "center" }}>
                <div style={{ fontSize: 18 }}>{s.icon}</div>
                <div style={{ fontSize: 14, fontWeight: 700, color: C.text }}>{s.val}</div>
                <div style={{ fontSize: 11, color: C.sub }}>{s.label}</div>
              </div>
            ))}
          </div>
          <div style={{ background: "white", borderRadius: 14, border: `1px solid ${C.border}`, padding: "14px", marginBottom: 14 }}>
            <div style={{ fontSize: 13, fontWeight: 700, color: C.text, marginBottom: 10 }}>قواعد السكن</div>
            {[{label:"التدخين",val:"ممنوع"},{label:"مناسب لـ",val:"عائلات"},{label:"فترة التأجير",val:"6 شهور"}].map(r => (
              <div key={r.label} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", paddingBottom: 8, borderBottom: `1px solid ${C.border}`, marginBottom: 8 }}>
                <span style={{ fontSize: 13, fontWeight: 600, color: C.sub }}>{r.label}</span>
                <span style={{ fontSize: 13, fontWeight: 600, color: C.text }}>{r.val}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
      <div style={{ padding: "12px 16px 28px", background: "white", borderTop: `1px solid ${C.border}`, display: "flex", gap: 10 }}>
        <button style={{ flex: 1, height: 50, borderRadius: 14, background: TEAL, border: "none", color: "white", fontSize: 15, fontWeight: 700, cursor: "pointer", ...TJ }}>احجز زيارة</button>
        <button style={{ width: 50, height: 50, borderRadius: 14, background: "#F3F4F6", border: "none", cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center" }}>
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke={TEAL} strokeWidth="2" strokeLinecap="round"><path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z"/></svg>
        </button>
      </div>
      {showShare && (
        <div style={{ position: "absolute", inset: 0, background: "rgba(0,0,0,0.5)", display: "flex", flexDirection: "column", justifyContent: "flex-end", zIndex: 20 }} onClick={() => setShowShare(false)}>
          <div style={{ background: "white", borderRadius: "24px 24px 0 0", padding: "20px 20px 40px" }} onClick={e => e.stopPropagation()}>
            <div style={{ width: 40, height: 4, borderRadius: 2, background: "#E5E7EB", margin: "0 auto 20px" }} />
            <div style={{ fontSize: 16, fontWeight: 700, color: C.text, marginBottom: 16 }}>مشاركة العقار</div>
            {copied && (
              <div style={{ background: TEAL+"12", border: `1px solid ${TEAL}30`, borderRadius: 10, padding: "10px 14px", marginBottom: 12, display: "flex", alignItems: "center", gap: 8 }}>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke={TEAL} strokeWidth="2.5" strokeLinecap="round"><polyline points="20 6 9 17 4 12"/></svg>
                <span style={{ fontSize: 13, color: TEAL, fontWeight: 600, ...TJ }}>تم نسخ رابط العقار</span>
              </div>
            )}
            {[{label:"نسخ الرابط",color:TEAL,action:()=>setCopied(true)},{label:"مشاركة",color:"#2563EB",action:()=>{}},{label:"إلغاء",color:ROSE,action:()=>setShowShare(false)}].map(item => (
              <button key={item.label} onClick={item.action} style={{ width: "100%", padding: "15px 16px", border: `1px solid ${C.border}`, borderRadius: 14, background: "white", cursor: "pointer", marginBottom: 10, textAlign: "right", ...TJ }}>
                <span style={{ fontSize: 15, fontWeight: 600, color: item.color }}>{item.label}</span>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// ════════════════════════════════════════════════════════════════════════
// KYC SHARED — National ID field component
// ════════════════════════════════════════════════════════════════════════

function NationalIDField({ value, onChange, error }: { value: string; onChange: (v: string) => void; error: string }) {
  return (
    <div style={{ marginBottom: 16 }}>
      <div style={{ fontSize: 13, fontWeight: 700, color: C.text, marginBottom: 6 }}>
        الرقم القومي <span style={{ color: ROSE }}>*</span>
      </div>
      <input
        value={value}
        onChange={e => { const v = e.target.value.replace(/\D/g, "").slice(0, 14); onChange(v); }}
        type="tel"
        maxLength={14}
        placeholder="اكتب الرقم القومي المكوّن من 14 رقم"
        style={{ width: "100%", height: 52, borderRadius: 12, border: `1.5px solid ${error ? ROSE : (value.length === 14 ? TEAL : C.border)}`, padding: "0 14px", fontSize: 15, color: C.text, background: "white", boxSizing: "border-box", textAlign: "right", direction: "ltr", letterSpacing: 2, outline: "none", ...TJ }}
      />
      {error ? (
        <div style={{ fontSize: 12, color: ROSE, marginTop: 4, fontWeight: 600 }}>{error}</div>
      ) : (
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: 4 }}>
          <span style={{ fontSize: 11, color: C.sub }}>{value.length}/14 رقم</span>
          {value.length === 14 && <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke={TEAL} strokeWidth="3" strokeLinecap="round"><polyline points="20 6 9 17 4 12"/></svg>}
        </div>
      )}
      <div style={{ display: "flex", alignItems: "flex-start", gap: 6, marginTop: 8, padding: "8px 10px", background: "#F0FDF9", borderRadius: 8, border: `1px solid ${TEAL}18` }}>
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke={TEAL} strokeWidth="2" strokeLinecap="round" style={{ flexShrink: 0, marginTop: 1 }}><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
        <span style={{ fontSize: 11, color: TEAL, lineHeight: 1.5, ...TJ }}>الرقم القومي للمراجعة الداخلية فقط ومش هيظهر لأي مستخدم</span>
      </div>
    </div>
  );
}

// ════════════════════════════════════════════════════════════════════════
// T-KYC-01 — Tenant KYC Start (matches updated O-KYC-01 structure, no ownership doc)
// ════════════════════════════════════════════════════════════════════════

export function UpdatedTenantKYC01Screen() {
  const docs = [
    { label: "بطاقة الرقم القومي (وجه وظهر)", done: true },
    { label: "صورة سيلفي واضحة", done: false },
  ];
  return (
    <div style={{ width: 390, height: 844, background: C.bg, display: "flex", flexDirection: "column", ...TJ, direction: "rtl" }}>
      <StatusBar />
      <div style={{ display: "flex", alignItems: "center", gap: 12, padding: "8px 16px 10px", background: "white", borderBottom: `1px solid ${C.border}` }}>
        <button style={{ width: 36, height: 36, borderRadius: 18, border: "none", background: "#F3F4F6", cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center" }}>
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke={C.text} strokeWidth="2.5" strokeLinecap="round"><polyline points="9 18 15 12 9 6"/></svg>
        </button>
        <span style={{ fontSize: 18, fontWeight: 800, color: C.text, flex: 1 }}>توثيق الهوية</span>
      </div>
      <div style={{ flex: 1, overflowY: "auto", padding: "16px" }}>
        {/* Step progress */}
        <div style={{ display: "flex", gap: 6, marginBottom: 20 }}>
          {[1,2,3].map(s => <div key={s} style={{ flex: 1, height: 4, borderRadius: 2, background: s === 1 ? TEAL : "#E5E7EB" }} />)}
        </div>
        {/* Icon + heading */}
        <div style={{ textAlign: "center", padding: "16px 0 20px" }}>
          <div style={{ width: 72, height: 72, borderRadius: 22, background: TEAL+"14", display: "flex", alignItems: "center", justifyContent: "center", margin: "0 auto 14px" }}>
            <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke={TEAL} strokeWidth="2" strokeLinecap="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
          </div>
          <div style={{ fontSize: 20, fontWeight: 900, color: C.text, marginBottom: 6 }}>وثّق هويتك وابدأ</div>
          <div style={{ fontSize: 13, color: C.sub, lineHeight: 1.6 }}>التوثيق إلزامي للتواصل مع الملاك وحجز الزيارات</div>
        </div>
        {/* Document checklist */}
        <div style={{ marginBottom: 14 }}>
          <div style={{ fontSize: 13, fontWeight: 700, color: C.text, marginBottom: 10 }}>المستندات المطلوبة</div>
          {docs.map((doc, i) => (
            <div key={i} style={{ display: "flex", alignItems: "center", gap: 12, padding: "14px", background: "white", borderRadius: 14, border: `1px solid ${doc.done ? TEAL+"30" : C.border}`, marginBottom: 8 }}>
              <div style={{ width: 36, height: 36, borderRadius: 10, background: doc.done ? TEAL+"14" : "#F3F4F6", display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke={doc.done ? TEAL : SLATE} strokeWidth="2" strokeLinecap="round"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
              </div>
              <span style={{ flex: 1, fontSize: 14, fontWeight: 600, color: C.text }}>{doc.label}</span>
              {doc.done && <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke={GREEN} strokeWidth="2.5" strokeLinecap="round"><polyline points="20 6 9 17 4 12"/></svg>}
            </div>
          ))}
        </div>
        {/* Privacy hint */}
        <PrivacyCard
          icon={<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke={TEAL} strokeWidth="2" strokeLinecap="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>}
          text="مستنداتك مشفّرة ولن تُشارك مع الملاك أو المستأجرين"
          sub="للمراجعة الداخلية فقط"
        />
        <div style={{ height: 80 }} />
      </div>
      <div style={{ padding: "16px 16px 32px", background: "white", borderTop: `1px solid ${C.border}` }}>
        <PrimaryBtn label="رفع المستندات" />
      </div>
    </div>
  );
}

// ════════════════════════════════════════════════════════════════════════
// O-KYC-01 UPDATED — Owner KYC Start (without "مستند ملكية العقار أو عقد إيجار")
// ════════════════════════════════════════════════════════════════════════

export function UpdatedOwnerKYC01Screen() {
  const docs = [
    { label: "بطاقة الرقم القومي (وجه وظهر)", done: true },
    { label: "صورة سيلفي واضحة", done: false },
  ];
  return (
    <div style={{ width: 390, height: 844, background: C.bg, display: "flex", flexDirection: "column", ...TJ, direction: "rtl" }}>
      <StatusBar />
      <div style={{ display: "flex", alignItems: "center", gap: 12, padding: "8px 16px 10px", background: "white", borderBottom: `1px solid ${C.border}` }}>
        <button style={{ width: 36, height: 36, borderRadius: 18, border: "none", background: "#F3F4F6", cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center" }}>
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke={C.text} strokeWidth="2.5" strokeLinecap="round"><polyline points="9 18 15 12 9 6"/></svg>
        </button>
        <span style={{ fontSize: 18, fontWeight: 800, color: C.text, flex: 1 }}>توثيق هوية المالك</span>
      </div>
      <div style={{ flex: 1, overflowY: "auto", padding: "16px" }}>
        <div style={{ display: "flex", gap: 6, marginBottom: 20 }}>
          {[1,2,3].map(s => <div key={s} style={{ flex: 1, height: 4, borderRadius: 2, background: s === 1 ? GOLD : "#E5E7EB" }} />)}
        </div>
        <div style={{ textAlign: "center", padding: "16px 0 20px" }}>
          <div style={{ width: 72, height: 72, borderRadius: 22, background: GOLD+"18", display: "flex", alignItems: "center", justifyContent: "center", margin: "0 auto 14px" }}>
            <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke={GOLD} strokeWidth="2" strokeLinecap="round"><rect x="2" y="7" width="20" height="14" rx="2"/><path d="M16 21V5a2 2 0 00-2-2h-4a2 2 0 00-2 2v16"/></svg>
          </div>
          <div style={{ fontSize: 20, fontWeight: 900, color: C.text, marginBottom: 6 }}>وثّق هويتك كمالك</div>
          <div style={{ fontSize: 13, color: C.sub, lineHeight: 1.6 }}>التوثيق إلزامي لعرض عقاراتك والتواصل مع المستأجرين</div>
        </div>
        <div style={{ marginBottom: 14 }}>
          <div style={{ fontSize: 13, fontWeight: 700, color: C.text, marginBottom: 10 }}>المستندات المطلوبة</div>
          {docs.map((doc, i) => (
            <div key={i} style={{ display: "flex", alignItems: "center", gap: 12, padding: "14px", background: "white", borderRadius: 14, border: `1px solid ${doc.done ? GOLD+"40" : C.border}`, marginBottom: 8 }}>
              <div style={{ width: 36, height: 36, borderRadius: 10, background: doc.done ? GOLD+"18" : "#F3F4F6", display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke={doc.done ? GOLD : SLATE} strokeWidth="2" strokeLinecap="round"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
              </div>
              <span style={{ flex: 1, fontSize: 14, fontWeight: 600, color: C.text }}>{doc.label}</span>
              {doc.done && <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke={GREEN} strokeWidth="2.5" strokeLinecap="round"><polyline points="20 6 9 17 4 12"/></svg>}
            </div>
          ))}
        </div>
        <PrivacyCard
          icon={<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke={TEAL} strokeWidth="2" strokeLinecap="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>}
          text="مستنداتك مشفّرة ولن تُشارك مع المستأجرين"
          sub="للمراجعة الداخلية فقط"
        />
        <div style={{ height: 80 }} />
      </div>
      <div style={{ padding: "16px 16px 32px", background: "white", borderTop: `1px solid ${C.border}` }}>
        <button style={{ width: "100%", height: 52, background: GOLD, border: "none", borderRadius: 14, color: "white", fontSize: 16, fontWeight: 700, cursor: "pointer", ...TJ }}>رفع المستندات</button>
      </div>
    </div>
  );
}

// ════════════════════════════════════════════════════════════════════════
// T-KYC-02 UPDATED — Tenant KYC Upload + National ID field
// ════════════════════════════════════════════════════════════════════════

export function UpdatedTenantKYC02Screen() {
  const [nid, setNid] = useState("");
  const [nidErr, setNidErr] = useState("");
  const [frontUploaded, setFrontUploaded] = useState(true);
  const [backUploaded, setBackUploaded] = useState(false);

  const valid = nid.length === 14 && frontUploaded && backUploaded;

  const validate = () => {
    if (!nid) { setNidErr("الرقم القومي مطلوب"); return; }
    if (nid.length !== 14) { setNidErr("اكتب رقم قومي صحيح من 14 رقم"); return; }
    setNidErr("");
  };

  return (
    <div style={{ width: 390, height: 844, background: C.bg, display: "flex", flexDirection: "column", ...TJ, direction: "rtl" }}>
      <StatusBar />
      <div style={{ display: "flex", alignItems: "center", gap: 12, padding: "8px 16px 10px", background: "white", borderBottom: `1px solid ${C.border}` }}>
        <button style={{ width: 36, height: 36, borderRadius: 18, border: "none", background: "#F3F4F6", cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center" }}>
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke={C.text} strokeWidth="2.5" strokeLinecap="round"><polyline points="9 18 15 12 9 6"/></svg>
        </button>
        <span style={{ fontSize: 18, fontWeight: 800, color: C.text, flex: 1 }}>رفع المستندات</span>
      </div>
      <div style={{ flex: 1, overflowY: "auto", padding: "16px" }}>
        <div style={{ display: "flex", gap: 6, marginBottom: 16 }}>
          {[1,2,3].map(s => <div key={s} style={{ flex: 1, height: 4, borderRadius: 2, background: s <= 2 ? TEAL : "#E5E7EB" }} />)}
        </div>
        <div style={{ fontSize: 12, color: C.sub, marginBottom: 16 }}>ارفع صورة واضحة للبطاقة الشخصية</div>

        {/* National ID number field */}
        <NationalIDField value={nid} onChange={v => { setNid(v); setNidErr(""); }} error={nidErr} />

        {/* Front upload */}
        <div style={{ marginBottom: 12 }}>
          <div style={{ fontSize: 13, fontWeight: 700, color: C.text, marginBottom: 8 }}>وجه البطاقة (أمامية)</div>
          <div onClick={() => setFrontUploaded(!frontUploaded)}
            style={{ height: 120, borderRadius: 16, border: `2px dashed ${frontUploaded ? TEAL : C.border}`, background: frontUploaded ? TEAL+"08" : "white", display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: 6, cursor: "pointer" }}>
            {frontUploaded ? (
              <>
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke={TEAL} strokeWidth="2" strokeLinecap="round"><polyline points="20 6 9 17 4 12"/></svg>
                <span style={{ fontSize: 12, fontWeight: 700, color: TEAL, ...TJ }}>تم الرفع ✓</span>
                <span style={{ fontSize: 10, color: TEAL, ...TJ }}>national_id_front.jpg</span>
              </>
            ) : (
              <>
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke={SLATE} strokeWidth="2" strokeLinecap="round"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
                <span style={{ fontSize: 12, fontWeight: 700, color: C.sub, ...TJ }}>اضغط للرفع</span>
                <span style={{ fontSize: 10, color: "#9CA3AF", ...TJ }}>JPG أو PNG حتى 5MB</span>
              </>
            )}
          </div>
        </div>

        {/* Back upload */}
        <div style={{ marginBottom: 12 }}>
          <div style={{ fontSize: 13, fontWeight: 700, color: C.text, marginBottom: 8 }}>ظهر البطاقة (خلفية)</div>
          <div onClick={() => setBackUploaded(!backUploaded)}
            style={{ height: 120, borderRadius: 16, border: `2px dashed ${backUploaded ? TEAL : C.border}`, background: backUploaded ? TEAL+"08" : "white", display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: 6, cursor: "pointer" }}>
            {backUploaded ? (
              <>
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke={TEAL} strokeWidth="2" strokeLinecap="round"><polyline points="20 6 9 17 4 12"/></svg>
                <span style={{ fontSize: 12, fontWeight: 700, color: TEAL, ...TJ }}>تم الرفع ✓</span>
                <span style={{ fontSize: 10, color: TEAL, ...TJ }}>national_id_back.jpg</span>
              </>
            ) : (
              <>
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke={SLATE} strokeWidth="2" strokeLinecap="round"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
                <span style={{ fontSize: 12, fontWeight: 700, color: C.sub, ...TJ }}>اضغط للرفع</span>
                <span style={{ fontSize: 10, color: "#9CA3AF", ...TJ }}>JPG أو PNG حتى 5MB</span>
              </>
            )}
          </div>
        </div>

        {/* Selfie */}
        <div style={{ background: "white", borderRadius: 16, padding: "14px", border: `1px solid ${C.border}`, marginBottom: 12 }}>
          <div style={{ fontSize: 13, fontWeight: 700, color: C.text, marginBottom: 8 }}>صورة سيلفي</div>
          <div style={{ height: 100, borderRadius: 12, border: `2px dashed ${C.border}`, background: C.bg, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: 5 }}>
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke={SLATE} strokeWidth="2" strokeLinecap="round"><path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
            <span style={{ fontSize: 12, fontWeight: 700, color: C.sub, ...TJ }}>التقط صورة</span>
          </div>
        </div>

        <PrivacyCard
          icon={<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke={TEAL} strokeWidth="2" strokeLinecap="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>}
          text="مستنداتك مشفّرة ولن تُشارك إلا مع فريق المراجعة"
          sub="صورة البطاقة لا تظهر لأي مستخدم نهائياً"
        />

        <div style={{ height: 80 }} />
      </div>
      <div style={{ padding: "16px 16px 32px", background: "white", borderTop: `1px solid ${C.border}` }}>
        {!valid && (
          <div style={{ fontSize: 12, color: C.sub, textAlign: "center", marginBottom: 8 }}>
            {!nid ? "أدخل الرقم القومي للمتابعة" : nid.length < 14 ? `الرقم القومي ${nid.length}/14` : !frontUploaded || !backUploaded ? "ارفع صور البطاقة للمتابعة" : ""}
          </div>
        )}
        <button onClick={validate}
          style={{ width: "100%", height: 52, background: valid ? TEAL : "#9CA3AF", border: "none", borderRadius: 14, color: "white", fontSize: 16, fontWeight: 700, cursor: valid ? "pointer" : "not-allowed", ...TJ }}>
          التالي — مراجعة البيانات
        </button>
      </div>
    </div>
  );
}

// ════════════════════════════════════════════════════════════════════════
// O-KYC-02 — Owner KYC Upload (mirrors T-KYC-02, adapted for owner, gold theme)
// ════════════════════════════════════════════════════════════════════════

export function OwnerKYC02Screen() {
  const [nid, setNid] = useState("");
  const [nidErr, setNidErr] = useState("");
  const [frontUploaded, setFrontUploaded] = useState(false);
  const [backUploaded, setBackUploaded] = useState(false);

  const valid = nid.length === 14 && frontUploaded && backUploaded;

  const validate = () => {
    if (!nid) { setNidErr("الرقم القومي مطلوب"); return; }
    if (nid.length !== 14) { setNidErr("اكتب رقم قومي صحيح من 14 رقم"); return; }
    setNidErr("");
  };

  const UploadBox = ({ label, uploaded, onToggle, filename }: { label: string; uploaded: boolean; onToggle: () => void; filename: string }) => (
    <div style={{ marginBottom: 12 }}>
      <div style={{ fontSize: 13, fontWeight: 700, color: C.text, marginBottom: 8 }}>{label}</div>
      <div onClick={onToggle} style={{ height: 120, borderRadius: 16, border: `2px dashed ${uploaded ? GOLD : C.border}`, background: uploaded ? GOLD+"08" : "white", display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: 6, cursor: "pointer" }}>
        {uploaded ? (
          <>
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke={GOLD} strokeWidth="2" strokeLinecap="round"><polyline points="20 6 9 17 4 12"/></svg>
            <span style={{ fontSize: 12, fontWeight: 700, color: GOLD, ...TJ }}>تم الرفع ✓</span>
            <span style={{ fontSize: 10, color: GOLD, ...TJ }}>{filename}</span>
          </>
        ) : (
          <>
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke={SLATE} strokeWidth="2" strokeLinecap="round"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
            <span style={{ fontSize: 12, fontWeight: 700, color: C.sub, ...TJ }}>اضغط للرفع</span>
            <span style={{ fontSize: 10, color: "#9CA3AF", ...TJ }}>JPG أو PNG حتى 5MB</span>
          </>
        )}
      </div>
    </div>
  );

  return (
    <div style={{ width: 390, height: 844, background: C.bg, display: "flex", flexDirection: "column", ...TJ, direction: "rtl" }}>
      <StatusBar />
      <div style={{ display: "flex", alignItems: "center", gap: 12, padding: "8px 16px 10px", background: "white", borderBottom: `1px solid ${C.border}` }}>
        <button style={{ width: 36, height: 36, borderRadius: 18, border: "none", background: "#F3F4F6", cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center" }}>
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke={C.text} strokeWidth="2.5" strokeLinecap="round"><polyline points="9 18 15 12 9 6"/></svg>
        </button>
        <span style={{ fontSize: 18, fontWeight: 800, color: C.text, flex: 1 }}>رفع مستندات المالك</span>
      </div>
      <div style={{ flex: 1, overflowY: "auto", padding: "16px" }}>
        <div style={{ display: "flex", gap: 6, marginBottom: 16 }}>
          {[1,2,3].map(s => <div key={s} style={{ flex: 1, height: 4, borderRadius: 2, background: s <= 2 ? GOLD : "#E5E7EB" }} />)}
        </div>
        <div style={{ fontSize: 12, color: C.sub, marginBottom: 16 }}>ارفع صورة واضحة للبطاقة الشخصية</div>

        <NationalIDField value={nid} onChange={v => { setNid(v); setNidErr(""); }} error={nidErr} />

        <UploadBox label="وجه البطاقة (أمامية)" uploaded={frontUploaded} onToggle={() => setFrontUploaded(!frontUploaded)} filename="owner_id_front.jpg" />
        <UploadBox label="ظهر البطاقة (خلفية)" uploaded={backUploaded} onToggle={() => setBackUploaded(!backUploaded)} filename="owner_id_back.jpg" />

        <div style={{ background: "white", borderRadius: 16, padding: "14px", border: `1px solid ${C.border}`, marginBottom: 12 }}>
          <div style={{ fontSize: 13, fontWeight: 700, color: C.text, marginBottom: 8 }}>صورة سيلفي</div>
          <div style={{ height: 100, borderRadius: 12, border: `2px dashed ${C.border}`, background: C.bg, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: 5 }}>
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke={SLATE} strokeWidth="2" strokeLinecap="round"><path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
            <span style={{ fontSize: 12, fontWeight: 700, color: C.sub, ...TJ }}>التقط صورة</span>
          </div>
        </div>

        <PrivacyCard
          icon={<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke={TEAL} strokeWidth="2" strokeLinecap="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>}
          text="مستنداتك مشفّرة ولن تُشارك مع المستأجرين"
          sub="صورة البطاقة للمراجعة الداخلية فقط ولا تظهر لأي مستخدم"
        />

        <div style={{ height: 80 }} />
      </div>
      <div style={{ padding: "16px 16px 32px", background: "white", borderTop: `1px solid ${C.border}` }}>
        {!valid && (
          <div style={{ fontSize: 12, color: C.sub, textAlign: "center", marginBottom: 8 }}>
            {!nid ? "أدخل الرقم القومي للمتابعة" : nid.length < 14 ? `الرقم القومي ${nid.length}/14` : "ارفع صور البطاقة للمتابعة"}
          </div>
        )}
        <button onClick={validate}
          style={{ width: "100%", height: 52, background: valid ? GOLD : "#9CA3AF", border: "none", borderRadius: 14, color: "white", fontSize: 16, fontWeight: 700, cursor: valid ? "pointer" : "not-allowed", ...TJ }}>
          التالي — مراجعة البيانات
        </button>
      </div>
    </div>
  );
}

// ════════════════════════════════════════════════════════════════════════
// O-ADD-01 MERGED — property info + area + specs + map location
// ════════════════════════════════════════════════════════════════════════

export function MergedAddPropertyStep1Screen() {
  const [locSet, setLocSet] = useState(false);
  const [typeIdx, setTypeIdx] = useState(0);
  return (
    <div style={{ width: 390, height: 844, background: C.bg, display: "flex", flexDirection: "column", ...TJ, direction: "rtl" }}>
      <StatusBar />
      <NavBar title="إضافة عقار جديد" onBack={() => {}} />
      <div style={{ padding: "12px 20px", background: "white", borderBottom: `1px solid ${C.border}` }}>
        <div style={{ display: "flex", gap: 6 }}>
          {[1,2,3].map(s => <div key={s} style={{ flex: 1, height: 4, borderRadius: 2, background: s === 1 ? TEAL : "#E5E7EB" }} />)}
        </div>
        <div style={{ fontSize: 11, color: C.sub, marginTop: 6 }}>الخطوة 1 من 3 — معلومات العقار</div>
      </div>
      <div style={{ flex: 1, padding: "16px", overflowY: "auto" }}>

        {/* Property type */}
        <div style={{ background: "white", borderRadius: 16, padding: "16px", border: `1px solid ${C.border}`, marginBottom: 12 }}>
          <div style={{ fontSize: 14, fontWeight: 700, color: C.text, marginBottom: 12 }}>نوع العقار</div>
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            {["شقة","غرفة","استوديو","فيلا","دور","روف"].map((o, i) => (
              <button key={o} onClick={() => setTypeIdx(i)} style={{ padding: "8px 16px", borderRadius: 20, border: `1.5px solid ${i===typeIdx ? TEAL : C.border}`, background: i===typeIdx ? TEAL+"12" : "white", color: i===typeIdx ? TEAL : C.text, fontSize: 13, fontWeight: 600, cursor: "pointer", ...TJ }}>{o}</button>
            ))}
          </div>
        </div>

        {/* Area and address */}
        <div style={{ background: "white", borderRadius: 16, padding: "16px", border: `1px solid ${C.border}`, marginBottom: 12 }}>
          <div style={{ fontSize: 14, fontWeight: 700, color: C.text, marginBottom: 12 }}>المنطقة والعنوان</div>
          {[{label:"المحافظة",ph:"القاهرة"},{label:"المنطقة",ph:"مدينة نصر"},{label:"الشارع",ph:"شارع النصر"}].map(f => (
            <div key={f.label} style={{ marginBottom: 10 }}>
              <div style={{ fontSize: 12, fontWeight: 600, color: C.sub, marginBottom: 5 }}>{f.label}</div>
              <input placeholder={f.ph} style={{ width: "100%", height: 46, borderRadius: 12, border: `1.5px solid ${C.border}`, padding: "0 14px", fontSize: 14, color: C.text, background: "#F9FAFB", boxSizing: "border-box", outline: "none", direction: "rtl", ...TJ }} />
            </div>
          ))}
        </div>

        {/* Property specs */}
        <div style={{ background: "white", borderRadius: 16, padding: "16px", border: `1px solid ${C.border}`, marginBottom: 12 }}>
          <div style={{ fontSize: 14, fontWeight: 700, color: C.text, marginBottom: 12 }}>تفاصيل العقار</div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
            {[{label:"عدد الغرف",ph:"3"},{label:"المساحة (م²)",ph:"90"},{label:"الدور",ph:"3"},{label:"سنة البناء",ph:"2020"}].map(f => (
              <div key={f.label}>
                <div style={{ fontSize: 12, fontWeight: 600, color: C.sub, marginBottom: 5 }}>{f.label}</div>
                <input placeholder={f.ph} type="number" style={{ width: "100%", height: 46, borderRadius: 12, border: `1.5px solid ${C.border}`, padding: "0 14px", fontSize: 14, color: C.text, background: "#F9FAFB", boxSizing: "border-box", outline: "none", textAlign: "center", ...TJ }} />
              </div>
            ))}
          </div>
        </div>

        {/* Map location */}
        <div style={{ background: "white", borderRadius: 16, padding: "16px", border: `1px solid ${C.border}`, marginBottom: 12 }}>
          <div style={{ fontSize: 14, fontWeight: 700, color: C.text, marginBottom: 4 }}>موقع العقار على الخريطة</div>
          <div style={{ fontSize: 11, color: C.sub, marginBottom: 12 }}>حدد موقع العقار بدقة عشان نراجع الإعلان بشكل أسرع</div>
          <div style={{ display: "flex", alignItems: "center", height: 44, borderRadius: 10, border: `1.5px solid ${C.border}`, background: "#F9FAFB", marginBottom: 12, padding: "0 12px", gap: 8 }}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke={SLATE} strokeWidth="2" strokeLinecap="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
            <input placeholder="ابحث عن الموقع..." style={{ flex: 1, border: "none", background: "transparent", fontSize: 13, color: C.text, outline: "none", direction: "rtl", ...TJ }} />
          </div>
          <div style={{ borderRadius: 12, overflow: "hidden", position: "relative", marginBottom: 12, height: 140, background: "#E8F4F0" }}>
            <svg width="100%" height="100%" style={{ position: "absolute", inset: 0 }}>
              {[20,40,60,80,100,120,140].map(y => <line key={y} x1="0" y1={y} x2="400" y2={y} stroke="#CBD5E1" strokeWidth="1"/>)}
              {[30,70,110,150,190,230,270,310,350].map(x => <line key={x} x1={x} y1="0" x2={x} y2="140" stroke="#CBD5E1" strokeWidth="1"/>)}
              <rect x="0" y="65" width="400" height="10" fill="#D1FAE5" rx="2"/>
              <rect x="135" y="0" width="10" height="140" fill="#D1FAE5" rx="2"/>
            </svg>
            <div style={{ position: "absolute", left: "50%", top: "50%", transform: "translate(-50%,-100%)" }}>
              <svg width="28" height="36" viewBox="0 0 32 40"><path d="M16 0C7.16 0 0 7.16 0 16c0 12 16 24 16 24S32 28 32 16C32 7.16 24.84 0 16 0z" fill={TEAL}/><circle cx="16" cy="16" r="7" fill="white"/></svg>
            </div>
            {locSet && (
              <div style={{ position: "absolute", top: 8, right: 8, background: TEAL, borderRadius: 8, padding: "4px 10px", display: "flex", alignItems: "center", gap: 5 }}>
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="3" strokeLinecap="round"><polyline points="20 6 9 17 4 12"/></svg>
                <span style={{ fontSize: 11, fontWeight: 700, color: "white", ...TJ }}>تم تحديد الموقع</span>
              </div>
            )}
          </div>
          <button onClick={() => setLocSet(true)} style={{ width: "100%", height: 44, borderRadius: 12, background: locSet ? GREEN : TEAL, border: "none", color: "white", fontSize: 14, fontWeight: 700, cursor: "pointer", ...TJ, display: "flex", alignItems: "center", justifyContent: "center", gap: 8 }}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5" strokeLinecap="round"><circle cx="12" cy="12" r="3"/><path d="M12 2v3m0 14v3M2 12h3m14 0h3"/></svg>
            {locSet ? "تم تحديد الموقع ✓" : "تحديد الموقع"}
          </button>
          <div style={{ marginTop: 10 }}>
            <PrivacyCard
              icon={<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke={TEAL} strokeWidth="2" strokeLinecap="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>}
              text="قد يظهر الموقع للمستأجرين بشكل تقريبي لحماية الخصوصية" sub=""
            />
          </div>
        </div>
        <div style={{ height: 80 }} />
      </div>
      <div style={{ padding: "16px 16px 32px", background: "white", borderTop: `1px solid ${C.border}` }}>
        <PrimaryBtn label="التالي — الصور" />
      </div>
    </div>
  );
}

// ════════════════════════════════════════════════════════════════════════
// O-ADD-03 MERGED — price + rental period (dropdown+number) + amenities
// ════════════════════════════════════════════════════════════════════════

export function MergedAddPropertyStep3Screen() {
  const [period, setPeriod] = useState("شهر");
  const [count, setCount] = useState("6");
  const [countErr, setCountErr] = useState("");
  const [showPicker, setShowPicker] = useState(false);
  const [amenities, setAmenities] = useState<string[]>(["واي فاي","مكيف","غسالة","ثلاجة","مفروش"]);
  const periodOpts = ["يوم", "شهر", "سنة"];

  const allAmenities = ["واي فاي","مكيف","غسالة","ثلاجة","مفروش","بوتوجاز","جراج","أسانسير","حارس","بلكونة","تكييف","غاز طبيعي","عداد كهرباء","عداد مياه","قريب من المترو"];

  const toggleAmenity = (a: string) => setAmenities(prev => prev.includes(a) ? prev.filter(x => x !== a) : [...prev, a]);

  const validate = () => {
    if (!count) { setCountErr("اكتب مدة التأجير"); return; }
    if (isNaN(Number(count)) || Number(count) <= 0) { setCountErr("اكتب رقم صحيح"); return; }
    setCountErr("");
  };

  return (
    <div style={{ width: 390, height: 844, background: C.bg, display: "flex", flexDirection: "column", ...TJ, direction: "rtl" }}>
      <StatusBar />
      <NavBar title="التسعير والتفاصيل" onBack={() => {}} />
      <div style={{ padding: "12px 20px", background: "white", borderBottom: `1px solid ${C.border}` }}>
        <div style={{ display: "flex", gap: 6 }}>
          {[1,2,3].map(s => <div key={s} style={{ flex: 1, height: 4, borderRadius: 2, background: TEAL }} />)}
        </div>
        <div style={{ fontSize: 11, color: C.sub, marginTop: 6 }}>الخطوة 3 من 3 — السعر والتفاصيل</div>
      </div>
      <div style={{ flex: 1, padding: "16px", overflowY: "auto" }}>

        {/* Price */}
        <div style={{ background: "white", borderRadius: 16, padding: "16px", border: `1px solid ${C.border}`, marginBottom: 12 }}>
          <div style={{ fontSize: 14, fontWeight: 700, color: C.text, marginBottom: 12 }}>السعر</div>
          <div style={{ position: "relative" }}>
            <input defaultValue="2500" style={{ width: "100%", height: 52, borderRadius: 12, border: `1.5px solid ${TEAL}`, padding: "0 60px 0 16px", fontSize: 18, fontWeight: 700, color: C.text, background: "white", boxSizing: "border-box", textAlign: "right", outline: "none", ...TJ }} />
            <span style={{ position: "absolute", left: 16, top: "50%", transform: "translateY(-50%)", fontSize: 14, fontWeight: 600, color: C.sub }}>ر.س</span>
          </div>
          <div style={{ marginTop: 10 }}>
            <div style={{ fontSize: 12, fontWeight: 600, color: C.sub, marginBottom: 5 }}>تأمين الشقة</div>
            <input placeholder="شهر واحد" style={{ width: "100%", height: 46, borderRadius: 12, border: `1.5px solid ${C.border}`, padding: "0 14px", fontSize: 14, color: C.text, background: "#F9FAFB", boxSizing: "border-box", outline: "none", direction: "rtl", ...TJ }} />
          </div>
        </div>

        {/* Rental period */}
        <div style={{ background: "white", borderRadius: 16, padding: "16px", border: `1px solid ${C.border}`, marginBottom: 12, position: "relative" }}>
          <div style={{ fontSize: 14, fontWeight: 700, color: C.text, marginBottom: 12 }}>فترة التأجير</div>
          <div style={{ display: "flex", gap: 10, alignItems: "flex-start" }}>
            <div style={{ flex: 1 }}>
              <div style={{ fontSize: 12, color: C.sub, marginBottom: 6 }}>العدد</div>
              <input value={count} onChange={e => { setCount(e.target.value); setCountErr(""); }} onBlur={validate} type="number" placeholder="اكتب العدد"
                style={{ width: "100%", height: 52, borderRadius: 12, border: `1.5px solid ${countErr ? ROSE : (count ? TEAL : C.border)}`, padding: "0 14px", fontSize: 18, fontWeight: 700, color: C.text, background: "white", boxSizing: "border-box", textAlign: "center", outline: "none", ...TJ }} />
              {countErr && <div style={{ fontSize: 11, color: ROSE, marginTop: 4, fontWeight: 600 }}>{countErr}</div>}
            </div>
            <div style={{ flex: 1 }}>
              <div style={{ fontSize: 12, color: C.sub, marginBottom: 6 }}>الوحدة</div>
              <button onClick={() => setShowPicker(!showPicker)} style={{ width: "100%", height: 52, borderRadius: 12, border: `1.5px solid ${TEAL}`, background: TEAL+"08", display: "flex", alignItems: "center", justifyContent: "space-between", padding: "0 14px", cursor: "pointer", ...TJ }}>
                <span style={{ fontSize: 16, fontWeight: 700, color: TEAL }}>{period}</span>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke={TEAL} strokeWidth="2.5"><polyline points="6 9 12 15 18 9"/></svg>
              </button>
              {showPicker && (
                <div style={{ position: "absolute", left: 16, zIndex: 10, background: "white", borderRadius: 12, border: `1.5px solid ${C.border}`, boxShadow: "0 8px 24px rgba(0,0,0,0.1)", overflow: "hidden", marginTop: 4, width: 120 }}>
                  {periodOpts.map(opt => (
                    <button key={opt} onClick={() => { setPeriod(opt); setShowPicker(false); }} style={{ width: "100%", padding: "13px 16px", border: "none", background: opt === period ? TEAL+"10" : "white", color: opt === period ? TEAL : C.text, fontSize: 15, fontWeight: opt === period ? 700 : 500, cursor: "pointer", textAlign: "right", ...TJ, display: "block", borderBottom: `1px solid ${C.border}` }}>{opt}</button>
                  ))}
                </div>
              )}
            </div>
          </div>
          {count && !countErr && (
            <div style={{ marginTop: 12, padding: "8px 12px", background: TEAL+"08", borderRadius: 8, fontSize: 12, color: TEAL, fontWeight: 600 }}>
              فترة التأجير: {count} {period}
            </div>
          )}
        </div>

        {/* Amenities */}
        <div style={{ background: "white", borderRadius: 16, padding: "16px", border: `1px solid ${C.border}`, marginBottom: 12 }}>
          <div style={{ fontSize: 14, fontWeight: 700, color: C.text, marginBottom: 12 }}>المرافق والخدمات</div>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
            {allAmenities.map(a => {
              const on = amenities.includes(a);
              return (
                <button key={a} onClick={() => toggleAmenity(a)} style={{ padding: "7px 14px", borderRadius: 20, border: `1.5px solid ${on ? TEAL : C.border}`, background: on ? TEAL+"12" : "white", color: on ? TEAL : C.text, fontSize: 12, fontWeight: 600, cursor: "pointer", ...TJ }}>{a}</button>
              );
            })}
          </div>
        </div>

        {/* Description */}
        <div style={{ background: "white", borderRadius: 16, padding: "16px", border: `1px solid ${C.border}`, marginBottom: 12 }}>
          <div style={{ fontSize: 14, fontWeight: 700, color: C.text, marginBottom: 12 }}>وصف العقار</div>
          <textarea placeholder="اكتب وصفاً جذاباً للعقار…" style={{ width: "100%", borderRadius: 12, border: `1.5px solid ${C.border}`, padding: "12px 14px", fontSize: 13, color: C.text, background: "#F9FAFB", boxSizing: "border-box", outline: "none", resize: "none", height: 80, direction: "rtl", lineHeight: 1.6, ...TJ }} />
        </div>

        <div style={{ background: "#FFFBEB", border: `1px solid ${GOLD}25`, borderRadius: 12, padding: "12px 14px", display: "flex", alignItems: "flex-start", gap: 10, marginBottom: 12 }}>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke={GOLD} strokeWidth="2" strokeLinecap="round" style={{ flexShrink: 0, marginTop: 1 }}><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
          <span style={{ fontSize: 12, color: "#92400E", lineHeight: 1.5, ...TJ }}>رسوم المنصة يتم خصمها من أرباح المالك حسب سياسة سكون</span>
        </div>
        <div style={{ height: 80 }} />
      </div>
      <div style={{ padding: "16px 16px 32px", background: "white", borderTop: `1px solid ${C.border}` }}>
        <PrimaryBtn label="التالي — التفاصيل الإضافية" />
      </div>
    </div>
  );
}

// ════════════════════════════════════════════════════════════════════════
// T-PROP-01 FULL — all owner-added details + share button
// ════════════════════════════════════════════════════════════════════════

export function FullPropertyDetailScreen() {
  const [saved, setSaved] = useState(false);
  const [showShare, setShowShare] = useState(false);
  const [copied, setCopied] = useState(false);

  const amenities = ["واي فاي","أسانسير","جراج","أمن","بلكونة","تكييف","مفروش","قريب من المترو","غاز طبيعي","عداد كهرباء","عداد مياه"];

  return (
    <div style={{ width: 390, height: 844, background: C.bg, display: "flex", flexDirection: "column", ...TJ, direction: "rtl", position: "relative" }}>
      <StatusBar />

      {/* Hero image */}
      <div style={{ position: "relative", height: 210, background: "linear-gradient(135deg,#0D6B63,#0F766E)", flexShrink: 0 }}>
        <div style={{ position: "absolute", top: 0, left: 0, right: 0, display: "flex", alignItems: "center", justifyContent: "space-between", padding: "10px 14px", zIndex: 2 }}>
          <button style={{ width: 36, height: 36, borderRadius: 18, background: "rgba(0,0,0,0.35)", border: "none", cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center" }}>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5" strokeLinecap="round"><polyline points="9 18 15 12 9 6"/></svg>
          </button>
          <div style={{ display: "flex", gap: 8 }}>
            <button onClick={() => { setShowShare(true); setCopied(false); }} style={{ width: 36, height: 36, borderRadius: 18, background: "rgba(0,0,0,0.35)", border: "none", cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center" }}>
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2" strokeLinecap="round"><circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><line x1="8.59" y1="13.51" x2="15.42" y2="17.49"/><line x1="15.41" y1="6.51" x2="8.59" y2="10.49"/></svg>
            </button>
            <button onClick={() => setSaved(!saved)} style={{ width: 36, height: 36, borderRadius: 18, background: "rgba(0,0,0,0.35)", border: "none", cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center" }}>
              <svg width="18" height="18" viewBox="0 0 24 24" fill={saved ? ROSE : "none"} stroke={saved ? ROSE : "white"} strokeWidth="2" strokeLinecap="round"><path d="M20.84 4.61a5.5 5.5 0 00-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 00-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 000-7.78z"/></svg>
            </button>
          </div>
        </div>
        <div style={{ position: "absolute", bottom: 10, left: 14, display: "flex", gap: 6 }}>
          <span style={{ background: TEAL, color: "white", fontSize: 11, fontWeight: 700, padding: "4px 10px", borderRadius: 8 }}>موثّق ✓</span>
          <span style={{ background: "rgba(0,0,0,0.45)", color: "white", fontSize: 11, fontWeight: 600, padding: "4px 10px", borderRadius: 8 }}>12 صورة</span>
        </div>
      </div>

      {/* Image thumbnail strip */}
      <div style={{ display: "flex", gap: 6, padding: "10px 14px", background: "#111827", overflowX: "auto", flexShrink: 0 }}>
        {[TEAL+"CC","#0D4A45","#1A5F59","#0F766E","#0A3D38"].map((bg, i) => (
          <div key={i} style={{ width: 60, height: 44, borderRadius: 8, background: bg, flexShrink: 0, border: i===0 ? `2px solid white` : "2px solid transparent", display: "flex", alignItems: "center", justifyContent: "center" }}>
            {i===0 && <div style={{ width: 6, height: 6, borderRadius: 3, background: "white" }} />}
          </div>
        ))}
        <div style={{ width: 60, height: 44, borderRadius: 8, background: "rgba(255,255,255,0.1)", flexShrink: 0, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: 1 }}>
          <span style={{ fontSize: 13, fontWeight: 800, color: "white" }}>+7</span>
          <span style={{ fontSize: 9, color: "rgba(255,255,255,0.6)", ...TJ }}>صور</span>
        </div>
      </div>

      <div style={{ flex: 1, overflowY: "auto" }}>
        <div style={{ padding: "14px 18px 0" }}>

          {/* Property type badge + title */}
          <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 6 }}>
            <span style={{ background: TEAL+"18", color: TEAL, fontSize: 11, fontWeight: 700, padding: "3px 10px", borderRadius: 8, border: `1px solid ${TEAL}30` }}>شقة</span>
            <span style={{ background: "#F3F4F6", color: C.sub, fontSize: 11, fontWeight: 600, padding: "3px 10px", borderRadius: 8 }}>مفروشة</span>
            <span style={{ background: GREEN+"18", color: GREEN, fontSize: 11, fontWeight: 700, padding: "3px 10px", borderRadius: 8 }}>موثّق ✓</span>
          </div>
          <div style={{ fontSize: 20, fontWeight: 800, color: C.text, marginBottom: 4 }}>شقة مفروشة 3 غرف — مدينة نصر</div>
          <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 8 }}>
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke={C.sub} strokeWidth="2" strokeLinecap="round"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0118 0z"/><circle cx="12" cy="10" r="3"/></svg>
            <span style={{ fontSize: 12, color: C.sub }}>منطقة تقريبية · مدينة نصر، القاهرة</span>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 14 }}>
            <span style={{ fontSize: 24, fontWeight: 900, color: TEAL }}>6,500</span>
            <span style={{ fontSize: 13, color: C.sub, fontWeight: 600 }}>ج / شهر</span>
            <div style={{ flex: 1 }} />
            <div style={{ display: "flex", alignItems: "center", gap: 4 }}>
              <span style={{ fontSize: 14 }}>⭐</span>
              <span style={{ fontSize: 13, fontWeight: 700, color: C.text }}>4.8</span>
              <span style={{ fontSize: 12, color: C.sub }}>(24)</span>
            </div>
          </div>

          {/* Stats row */}
          <div style={{ display: "flex", gap: 10, marginBottom: 14 }}>
            {[{icon:"🛏",val:"3",label:"غرف"},{icon:"🚿",val:"2",label:"حمام"},{icon:"📐",val:"90",label:"م²"},{icon:"🏢",val:"3",label:"دور"}].map(s => (
              <div key={s.label} style={{ flex: 1, background: "white", borderRadius: 12, padding: "10px 4px", textAlign: "center", border: `1px solid ${C.border}` }}>
                <div style={{ fontSize: 16, marginBottom: 2 }}>{s.icon}</div>
                <div style={{ fontSize: 13, fontWeight: 700, color: C.text }}>{s.val}</div>
                <div style={{ fontSize: 10, color: C.sub }}>{s.label}</div>
              </div>
            ))}
          </div>

          {/* Description */}
          <div style={{ background: "white", borderRadius: 14, border: `1px solid ${C.border}`, padding: "14px", marginBottom: 12 }}>
            <div style={{ fontSize: 13, fontWeight: 700, color: C.text, marginBottom: 8 }}>الوصف</div>
            <div style={{ fontSize: 12, color: C.sub, lineHeight: 1.7 }}>شقة مفروشة بالكامل في قلب مدينة نصر، قريبة من مترو الأنفاق والخدمات. مجددة حديثاً وتحتوي على كل الأجهزة الكهربائية.</div>
          </div>

          {/* Map preview */}
          <div style={{ background: "white", borderRadius: 14, border: `1px solid ${C.border}`, padding: "14px", marginBottom: 12 }}>
            <div style={{ fontSize: 13, fontWeight: 700, color: C.text, marginBottom: 10 }}>الموقع</div>
            <div style={{ borderRadius: 10, overflow: "hidden", height: 110, background: "#E8F4F0", position: "relative", marginBottom: 8 }}>
              <svg width="100%" height="100%" style={{ position: "absolute", inset: 0 }}>
                {[22,44,66,88,110].map(y => <line key={y} x1="0" y1={y} x2="400" y2={y} stroke="#CBD5E1" strokeWidth="1"/>)}
                {[40,90,140,190,240,290,340].map(x => <line key={x} x1={x} y1="0" x2={x} y2="110" stroke="#CBD5E1" strokeWidth="1"/>)}
                <rect x="0" y="50" width="400" height="10" fill="#D1FAE5" rx="2"/>
                <circle cx="195" cy="55" r="18" fill={TEAL} opacity="0.2"/>
                <circle cx="195" cy="55" r="8" fill={TEAL} opacity="0.4"/>
              </svg>
              <div style={{ position: "absolute", left: "50%", top: "50%", transform: "translate(-50%,-100%)" }}>
                <svg width="24" height="30" viewBox="0 0 32 40"><path d="M16 0C7.16 0 0 7.16 0 16c0 12 16 24 16 24S32 28 32 16C32 7.16 24.84 0 16 0z" fill={TEAL}/><circle cx="16" cy="16" r="7" fill="white"/></svg>
              </div>
            </div>
            <div style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 11, color: C.sub }}>
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke={TEAL} strokeWidth="2" strokeLinecap="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
              الموقع قد يظهر بشكل تقريبي لحماية الخصوصية
            </div>
          </div>

          {/* Rules & rental */}
          <div style={{ background: "white", borderRadius: 14, border: `1px solid ${C.border}`, padding: "14px", marginBottom: 12 }}>
            <div style={{ fontSize: 13, fontWeight: 700, color: C.text, marginBottom: 10 }}>تفاصيل التأجير وقواعد السكن</div>
            {[
              { label: "فترة التأجير", val: "6 شهور" },
              { label: "مناسب لـ", val: "عائلات" },
              { label: "التدخين", val: "ممنوع" },
            ].map((r, i, arr) => (
              <div key={r.label} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", paddingBottom: i < arr.length-1 ? 8 : 0, borderBottom: i < arr.length-1 ? `1px solid ${C.border}` : "none", marginBottom: i < arr.length-1 ? 8 : 0 }}>
                <span style={{ fontSize: 13, color: C.sub }}>{r.label}</span>
                <span style={{ fontSize: 13, fontWeight: 700, color: C.text }}>{r.val}</span>
              </div>
            ))}
          </div>

          {/* Amenities */}
          <div style={{ background: "white", borderRadius: 14, border: `1px solid ${C.border}`, padding: "14px", marginBottom: 12 }}>
            <div style={{ fontSize: 13, fontWeight: 700, color: C.text, marginBottom: 10 }}>المرافق والخدمات</div>
            <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
              {amenities.map(a => (
                <span key={a} style={{ padding: "5px 12px", borderRadius: 20, background: TEAL+"12", color: TEAL, fontSize: 12, fontWeight: 600 }}>{a}</span>
              ))}
            </div>
          </div>

          {/* Ownership verification */}
          <div style={{ background: GREEN+"10", border: `1px solid ${GREEN}30`, borderRadius: 14, padding: "12px 14px", marginBottom: 12, display: "flex", alignItems: "center", gap: 10 }}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke={GREEN} strokeWidth="2.5" strokeLinecap="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><polyline points="9 12 11 14 15 10"/></svg>
            <span style={{ fontSize: 13, fontWeight: 700, color: GREEN }}>تم التحقق من إثبات الملكية</span>
          </div>

          {/* Platform fee note */}
          <div style={{ background: "#FFFBEB", border: `1px solid ${GOLD}25`, borderRadius: 12, padding: "10px 14px", marginBottom: 12, display: "flex", alignItems: "flex-start", gap: 8 }}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke={GOLD} strokeWidth="2" strokeLinecap="round" style={{ flexShrink: 0, marginTop: 1 }}><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
            <span style={{ fontSize: 11, color: "#92400E", lineHeight: 1.5 }}>رسوم المنصة يتم خصمها من أرباح المالك — السعر المعروض هو ما ستدفعه فعلاً</span>
          </div>

          {/* Owner box */}
          <div style={{ background: "white", borderRadius: 14, border: `1px solid ${C.border}`, padding: "14px", marginBottom: 12 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
              <div style={{ width: 44, height: 44, borderRadius: 22, background: TEAL+"20", display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke={TEAL} strokeWidth="2" strokeLinecap="round"><path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
              </div>
              <div style={{ flex: 1 }}>
                <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 2 }}>
                  <span style={{ fontSize: 14, fontWeight: 700, color: C.text }}>أحمد محمد إبراهيم</span>
                  <span style={{ background: TEAL, color: "white", fontSize: 10, fontWeight: 700, padding: "2px 7px", borderRadius: 6 }}>موثّق</span>
                </div>
                <span style={{ fontSize: 12, color: C.sub }}>مالك موثّق · 3 عقارات · 4.9 ★</span>
              </div>
            </div>
            <div style={{ marginTop: 10, background: "#F9FAFB", borderRadius: 10, padding: "8px 12px", display: "flex", alignItems: "center", gap: 8 }}>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke={C.sub} strokeWidth="2" strokeLinecap="round"><rect x="5" y="2" width="14" height="20" rx="2" ry="2"/><line x1="12" y1="18" x2="12.01" y2="18"/></svg>
              <span style={{ fontSize: 11, color: C.sub }}>رقم الموبايل مخفي ومش هيظهر غير بموافقة واضحة</span>
            </div>
          </div>

          <div style={{ height: 80 }} />
        </div>
      </div>

      {/* Action bar */}
      <div style={{ padding: "12px 16px 28px", background: "white", borderTop: `1px solid ${C.border}`, display: "flex", gap: 10 }}>
        <button style={{ flex: 1, height: 50, borderRadius: 14, background: TEAL, border: "none", color: "white", fontSize: 15, fontWeight: 700, cursor: "pointer", ...TJ }}>احجز زيارة</button>
        <button style={{ width: 50, height: 50, borderRadius: 14, background: "#F3F4F6", border: "none", cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center" }}>
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke={TEAL} strokeWidth="2" strokeLinecap="round"><path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z"/></svg>
        </button>
      </div>

      {/* Share sheet */}
      {showShare && (
        <div style={{ position: "absolute", inset: 0, background: "rgba(0,0,0,0.5)", display: "flex", flexDirection: "column", justifyContent: "flex-end", zIndex: 20 }} onClick={() => setShowShare(false)}>
          <div style={{ background: "white", borderRadius: "24px 24px 0 0", padding: "20px 20px 40px" }} onClick={e => e.stopPropagation()}>
            <div style={{ width: 40, height: 4, borderRadius: 2, background: "#E5E7EB", margin: "0 auto 20px" }} />
            <div style={{ fontSize: 16, fontWeight: 700, color: C.text, marginBottom: 16 }}>مشاركة العقار</div>
            {copied && (
              <div style={{ background: TEAL+"12", border: `1px solid ${TEAL}30`, borderRadius: 10, padding: "10px 14px", marginBottom: 12, display: "flex", alignItems: "center", gap: 8 }}>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke={TEAL} strokeWidth="2.5" strokeLinecap="round"><polyline points="20 6 9 17 4 12"/></svg>
                <span style={{ fontSize: 13, color: TEAL, fontWeight: 600 }}>تم نسخ رابط العقار</span>
              </div>
            )}
            {([
              { label: "نسخ الرابط", color: TEAL, action: () => setCopied(true) },
              { label: "مشاركة", color: "#2563EB", action: () => {} },
              { label: "إلغاء", color: ROSE, action: () => setShowShare(false) },
            ] as { label: string; color: string; action: () => void }[]).map(item => (
              <button key={item.label} onClick={item.action} style={{ width: "100%", padding: "15px 16px", border: `1px solid ${C.border}`, borderRadius: 14, background: "white", cursor: "pointer", marginBottom: 10, textAlign: "right", fontSize: 15, fontWeight: 600, color: item.color, ...TJ }}>{item.label}</button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// ════════════════════════════════════════════════════════════════════════
// FULL FILTER SHEET — all 13 owner-add-property fields
// ════════════════════════════════════════════════════════════════════════

export function FullFilterSheetScreen() {
  const [propType, setPropType] = useState<string[]>([]);
  const [suitable, setSuitable] = useState("الكل");
  const [smoking, setSmoking] = useState("الكل");
  const [period, setPeriod] = useState("شهر");
  const [periodCount, setPeriodCount] = useState("6");
  const [showPeriodPicker, setShowPeriodPicker] = useState(false);
  const [amenities, setAmenities] = useState<string[]>([]);
  const [verifiedOnly, setVerifiedOnly] = useState(false);
  const [verifiedOwnership, setVerifiedOwnership] = useState(false);
  const [rooms, setRooms] = useState("");
  const [baths, setBaths] = useState("");
  const [floor, setFloor] = useState("");

  const togglePropType = (t: string) => setPropType(prev => prev.includes(t) ? prev.filter(x=>x!==t) : [...prev,t]);
  const toggleAmenity = (a: string) => setAmenities(prev => prev.includes(a) ? prev.filter(x=>x!==a) : [...prev,a]);

  const sectionTitle = (t: string) => (
    <div style={{ fontSize: 14, fontWeight: 700, color: C.text, marginBottom: 12 }}>{t}</div>
  );

  const ChipRow = ({ opts, active, onToggle }: { opts: string[]; active: string; onToggle: (v:string)=>void }) => (
    <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
      {opts.map(o => (
        <button key={o} onClick={() => onToggle(o)} style={{ padding: "7px 16px", borderRadius: 20, border: `1.5px solid ${active===o ? TEAL : C.border}`, background: active===o ? TEAL+"12" : "white", color: active===o ? TEAL : C.text, fontSize: 13, fontWeight: 600, cursor: "pointer", ...TJ }}>{o}</button>
      ))}
    </div>
  );

  const MultiChipRow = ({ opts, active, onToggle }: { opts: string[]; active: string[]; onToggle: (v:string)=>void }) => (
    <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
      {opts.map(o => {
        const on = active.includes(o);
        return <button key={o} onClick={() => onToggle(o)} style={{ padding: "7px 14px", borderRadius: 20, border: `1.5px solid ${on ? TEAL : C.border}`, background: on ? TEAL+"12" : "white", color: on ? TEAL : C.text, fontSize: 12, fontWeight: 600, cursor: "pointer", ...TJ }}>{o}</button>;
      })}
    </div>
  );

  const NumChipRow = ({ opts, active, onSet }: { opts: string[]; active: string; onSet: (v:string)=>void }) => (
    <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
      {opts.map(o => (
        <button key={o} onClick={() => onSet(active===o ? "" : o)} style={{ width: 52, height: 44, borderRadius: 12, border: `1.5px solid ${active===o ? TEAL : C.border}`, background: active===o ? TEAL+"12" : "white", color: active===o ? TEAL : C.text, fontSize: 14, fontWeight: 700, cursor: "pointer", ...TJ }}>{o}</button>
      ))}
    </div>
  );

  const Card = ({ children }: { children: React.ReactNode }) => (
    <div style={{ background: "white", borderRadius: 16, padding: "16px", border: `1px solid ${C.border}`, marginBottom: 12 }}>{children}</div>
  );

  const activeCount = [
    propType.length > 0, suitable !== "الكل", smoking !== "الكل",
    periodCount !== "", amenities.length > 0, verifiedOnly, verifiedOwnership,
    rooms !== "", baths !== "", floor !== ""
  ].filter(Boolean).length;

  return (
    <div style={{ width: 390, height: 844, background: C.bg, display: "flex", flexDirection: "column", ...TJ, direction: "rtl" }}>
      <StatusBar />
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "14px 18px", background: "white", borderBottom: `1px solid ${C.border}` }}>
        <div style={{ fontSize: 17, fontWeight: 800, color: C.text }}>
          فلتر البحث
          {activeCount > 0 && <span style={{ marginRight: 8, fontSize: 12, fontWeight: 700, background: TEAL, color: "white", borderRadius: 12, padding: "2px 8px" }}>{activeCount}</span>}
        </div>
        <button style={{ background: "none", border: "none", color: TEAL, fontSize: 13, fontWeight: 700, cursor: "pointer", ...TJ }}
          onClick={() => { setPropType([]); setSuitable("الكل"); setSmoking("الكل"); setAmenities([]); setVerifiedOnly(false); setVerifiedOwnership(false); setRooms(""); setBaths(""); setFloor(""); setPeriodCount(""); }}>
          إعادة تعيين
        </button>
      </div>

      <div style={{ flex: 1, padding: "12px 16px 0", overflowY: "auto" }}>

        {/* 1. Property type */}
        <Card>
          {sectionTitle("نوع العقار")}
          <MultiChipRow opts={["شقة","ستوديو","غرفة","دوبلكس","فيلا","روف"]} active={propType} onToggle={togglePropType} />
        </Card>

        {/* 2-3. City & Area */}
        <Card>
          {sectionTitle("المدينة والمنطقة")}
          <div style={{ marginBottom: 10 }}>
            <div style={{ fontSize: 12, color: C.sub, marginBottom: 5 }}>المدينة</div>
            <input placeholder="مثال: القاهرة، الرياض…" style={{ width: "100%", height: 46, borderRadius: 12, border: `1.5px solid ${C.border}`, padding: "0 14px", fontSize: 14, color: C.text, background: "#F9FAFB", boxSizing: "border-box", outline: "none", direction: "rtl", ...TJ }} />
          </div>
          <div>
            <div style={{ fontSize: 12, color: C.sub, marginBottom: 5 }}>المنطقة / الحي</div>
            <input placeholder="مثال: مدينة نصر، التجمع…" style={{ width: "100%", height: 46, borderRadius: 12, border: `1.5px solid ${C.border}`, padding: "0 14px", fontSize: 14, color: C.text, background: "#F9FAFB", boxSizing: "border-box", outline: "none", direction: "rtl", ...TJ }} />
          </div>
        </Card>

        {/* 4. Price range */}
        <Card>
          {sectionTitle("نطاق السعر (ر.س / ج)")}
          <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
            <input type="number" placeholder="من" style={{ flex: 1, height: 46, borderRadius: 12, border: `1.5px solid ${C.border}`, padding: "0 14px", fontSize: 14, color: C.text, background: "#F9FAFB", boxSizing: "border-box", outline: "none", textAlign: "center", ...TJ }} />
            <span style={{ fontSize: 16, color: C.sub, fontWeight: 600 }}>—</span>
            <input type="number" placeholder="إلى" style={{ flex: 1, height: 46, borderRadius: 12, border: `1.5px solid ${C.border}`, padding: "0 14px", fontSize: 14, color: C.text, background: "#F9FAFB", boxSizing: "border-box", outline: "none", textAlign: "center", ...TJ }} />
          </div>
        </Card>

        {/* 5-7. Rooms, baths, area */}
        <Card>
          {sectionTitle("تفاصيل العقار")}
          <div style={{ marginBottom: 12 }}>
            <div style={{ fontSize: 12, color: C.sub, marginBottom: 8 }}>عدد الغرف</div>
            <NumChipRow opts={["1","2","3","4","5+"]} active={rooms} onSet={setRooms} />
          </div>
          <div style={{ marginBottom: 12 }}>
            <div style={{ fontSize: 12, color: C.sub, marginBottom: 8 }}>عدد الحمامات</div>
            <NumChipRow opts={["1","2","3+"]} active={baths} onSet={setBaths} />
          </div>
          <div>
            <div style={{ fontSize: 12, color: C.sub, marginBottom: 5 }}>المساحة (م²)</div>
            <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
              <input type="number" placeholder="من" style={{ flex: 1, height: 46, borderRadius: 12, border: `1.5px solid ${C.border}`, padding: "0 14px", fontSize: 14, color: C.text, background: "#F9FAFB", boxSizing: "border-box", outline: "none", textAlign: "center", ...TJ }} />
              <span style={{ fontSize: 16, color: C.sub }}>—</span>
              <input type="number" placeholder="إلى" style={{ flex: 1, height: 46, borderRadius: 12, border: `1.5px solid ${C.border}`, padding: "0 14px", fontSize: 14, color: C.text, background: "#F9FAFB", boxSizing: "border-box", outline: "none", textAlign: "center", ...TJ }} />
            </div>
          </div>
        </Card>

        {/* 8. Floor */}
        <Card>
          {sectionTitle("الدور")}
          <NumChipRow opts={["أرضي","1","2","3","4","5+"]} active={floor} onSet={setFloor} />
        </Card>

        {/* 9. Rental period */}
        <Card>
          {sectionTitle("فترة التأجير")}
          <div style={{ display: "flex", gap: 10, alignItems: "flex-start", position: "relative" }}>
            <div style={{ flex: 1 }}>
              <div style={{ fontSize: 12, color: C.sub, marginBottom: 6 }}>العدد</div>
              <input value={periodCount} onChange={e => setPeriodCount(e.target.value)} type="number" placeholder="اكتب العدد"
                style={{ width: "100%", height: 48, borderRadius: 12, border: `1.5px solid ${periodCount ? TEAL : C.border}`, padding: "0 14px", fontSize: 16, fontWeight: 700, color: C.text, background: "white", boxSizing: "border-box", textAlign: "center", outline: "none", ...TJ }} />
            </div>
            <div style={{ flex: 1 }}>
              <div style={{ fontSize: 12, color: C.sub, marginBottom: 6 }}>الوحدة</div>
              <button onClick={() => setShowPeriodPicker(!showPeriodPicker)} style={{ width: "100%", height: 48, borderRadius: 12, border: `1.5px solid ${TEAL}`, background: TEAL+"08", display: "flex", alignItems: "center", justifyContent: "space-between", padding: "0 14px", cursor: "pointer", ...TJ }}>
                <span style={{ fontSize: 15, fontWeight: 700, color: TEAL }}>{period}</span>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke={TEAL} strokeWidth="2.5"><polyline points="6 9 12 15 18 9"/></svg>
              </button>
              {showPeriodPicker && (
                <div style={{ position: "absolute", left: 0, zIndex: 10, background: "white", borderRadius: 12, border: `1.5px solid ${C.border}`, boxShadow: "0 8px 24px rgba(0,0,0,0.1)", overflow: "hidden", marginTop: 4, width: 110 }}>
                  {["يوم","شهر","سنة"].map(opt => (
                    <button key={opt} onClick={() => { setPeriod(opt); setShowPeriodPicker(false); }} style={{ width: "100%", padding: "12px 14px", border: "none", background: opt===period ? TEAL+"10" : "white", color: opt===period ? TEAL : C.text, fontSize: 14, fontWeight: opt===period ? 700 : 500, cursor: "pointer", textAlign: "right", ...TJ, display: "block", borderBottom: `1px solid ${C.border}` }}>{opt}</button>
                  ))}
                </div>
              )}
            </div>
          </div>
          {periodCount && (
            <div style={{ marginTop: 10, padding: "7px 12px", background: TEAL+"08", borderRadius: 8, fontSize: 12, color: TEAL, fontWeight: 600 }}>
              فترة التأجير: {periodCount} {period}
            </div>
          )}
        </Card>

        {/* 10. Suitable for */}
        <Card>
          {sectionTitle("مناسب لـ")}
          <ChipRow opts={["الكل","ولاد فقط","بنات فقط","عائلات","أفراد","مشاركة"]} active={suitable} onToggle={setSuitable} />
        </Card>

        {/* 11. Smoking */}
        <Card>
          {sectionTitle("التدخين")}
          <ChipRow opts={["الكل","مسموح","ممنوع","حسب الاتفاق"]} active={smoking} onToggle={setSmoking} />
        </Card>

        {/* 12. Amenities */}
        <Card>
          {sectionTitle("المرافق والخدمات")}
          <MultiChipRow opts={["واي فاي","أسانسير","جراج","أمن","بلكونة","تكييف","مفروش","قريب من المترو","غاز طبيعي","عداد كهرباء","عداد مياه"]} active={amenities} onToggle={toggleAmenity} />
        </Card>

        {/* 13. Verification */}
        <Card>
          {sectionTitle("التوثيق")}
          {[
            { label: "عقارات موثقة فقط", sub: "عقارات مراجعة ومعتمدة من سكون", val: verifiedOnly, set: setVerifiedOnly },
            { label: "إثبات ملكية تم التحقق منه", sub: "المالك أثبت ملكية العقار", val: verifiedOwnership, set: setVerifiedOwnership },
          ].map(item => (
            <div key={item.label} style={{ display: "flex", alignItems: "center", justifyContent: "space-between", paddingBottom: 12, marginBottom: 12, borderBottom: `1px solid ${C.border}` }}>
              <div>
                <div style={{ fontSize: 13, fontWeight: 700, color: C.text }}>{item.label}</div>
                <div style={{ fontSize: 11, color: C.sub, marginTop: 2 }}>{item.sub}</div>
              </div>
              <button onClick={() => item.set(!item.val)} style={{ width: 46, height: 26, borderRadius: 13, background: item.val ? TEAL : "#D1D5DB", border: "none", cursor: "pointer", position: "relative", flexShrink: 0, transition: "background 0.2s" }}>
                <div style={{ position: "absolute", top: 3, left: item.val ? 23 : 3, width: 20, height: 20, borderRadius: 10, background: "white", boxShadow: "0 1px 3px rgba(0,0,0,0.2)", transition: "left 0.2s" }} />
              </button>
            </div>
          ))}
          <div style={{ display: "flex", alignItems: "center", gap: 8, padding: "8px 10px", background: "#FEF3C7", borderRadius: 10 }}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke={GOLD} strokeWidth="2" strokeLinecap="round" style={{ flexShrink: 0 }}><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
            <span style={{ fontSize: 11, color: "#92400E", ...TJ }}>المستندات الخاصة لا تظهر للمستخدمين — فقط حالة التحقق</span>
          </div>
        </Card>

        <div style={{ height: 100 }} />
      </div>

      <div style={{ padding: "14px 16px 32px", background: "white", borderTop: `1px solid ${C.border}` }}>
        <PrimaryBtn label={`عرض النتائج${activeCount > 0 ? ` (${activeCount} فلاتر نشطة)` : ""}`} />
      </div>
    </div>
  );
}

// ════════════════════════════════════════════════════════════════════════
// SEARCH RESULTS — active filter chips + property cards with mini chips
// ════════════════════════════════════════════════════════════════════════

export function FullSearchResultsScreen() {
  const [activeChips, setActiveChips] = useState(["شقة","مدينة نصر","6 شهور","عائلات","ممنوع التدخين","أسانسير"]);
  const removeChip = (c: string) => setActiveChips(prev => prev.filter(x => x !== c));

  const props = [
    { title: "شقة مفروشة 3 غرف", area: "مدينة نصر، القاهرة", price: "6,500", unit: "ج/شهر", rooms: 3, baths: 2, m2: 90, chips: ["موثّق","عائلات","ممنوع التدخين","أسانسير"], color: TEAL },
    { title: "استوديو حديث", area: "التجمع الخامس، القاهرة", price: "3,200", unit: "ج/شهر", rooms: 1, baths: 1, m2: 45, chips: ["موثّق","أفراد","مسموح التدخين","واي فاي"], color: "#2563EB" },
    { title: "غرفة مفروشة", area: "مصر الجديدة، القاهرة", price: "1,800", unit: "ج/شهر", rooms: 1, baths: 1, m2: 30, chips: ["بنات فقط","ممنوع التدخين"], color: ROSE },
    { title: "شقة 4 غرف فيلا", area: "الشيخ زايد، الجيزة", price: "12,000", unit: "ج/شهر", rooms: 4, baths: 3, m2: 200, chips: ["موثّق","عائلات","جراج","أسانسير"], color: GOLD },
  ];

  return (
    <div style={{ width: 390, height: 844, background: C.bg, display: "flex", flexDirection: "column", ...TJ, direction: "rtl" }}>
      <StatusBar />

      {/* Search bar row */}
      <div style={{ padding: "10px 14px", background: "white", borderBottom: `1px solid ${C.border}`, display: "flex", alignItems: "center", gap: 10 }}>
        <div style={{ flex: 1, height: 44, borderRadius: 22, background: "#F3F4F6", display: "flex", alignItems: "center", padding: "0 14px", gap: 8 }}>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke={C.sub} strokeWidth="2" strokeLinecap="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
          <span style={{ fontSize: 14, color: C.sub }}>شقة مفروشة مدينة نصر…</span>
        </div>
        <button style={{ width: 44, height: 44, borderRadius: 22, background: TEAL+"12", border: `1.5px solid ${TEAL}30`, display: "flex", alignItems: "center", justifyContent: "center", cursor: "pointer", flexShrink: 0 }}>
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke={TEAL} strokeWidth="2.5" strokeLinecap="round"><line x1="4" y1="6" x2="20" y2="6"/><line x1="8" y1="12" x2="16" y2="12"/><line x1="12" y1="18" x2="12" y2="18"/></svg>
        </button>
      </div>

      {/* Active filter chips */}
      {activeChips.length > 0 && (
        <div style={{ display: "flex", gap: 8, padding: "10px 14px", overflowX: "auto", background: "white", borderBottom: `1px solid ${C.border}`, flexShrink: 0 }}>
          {activeChips.map(chip => (
            <div key={chip} style={{ display: "flex", alignItems: "center", gap: 5, padding: "5px 10px", borderRadius: 20, background: TEAL+"12", border: `1px solid ${TEAL}30`, flexShrink: 0 }}>
              <span style={{ fontSize: 12, fontWeight: 600, color: TEAL }}>{chip}</span>
              <button onClick={() => removeChip(chip)} style={{ background: "none", border: "none", cursor: "pointer", display: "flex", alignItems: "center", padding: 0 }}>
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke={TEAL} strokeWidth="3" strokeLinecap="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
              </button>
            </div>
          ))}
          <button onClick={() => setActiveChips([])} style={{ padding: "5px 10px", borderRadius: 20, background: ROSE+"12", border: `1px solid ${ROSE}30`, color: ROSE, fontSize: 12, fontWeight: 600, cursor: "pointer", flexShrink: 0, ...TJ }}>مسح الكل</button>
        </div>
      )}

      {/* Results count */}
      <div style={{ padding: "10px 18px", fontSize: 12, color: C.sub, fontWeight: 600 }}>
        {props.length} نتيجة
      </div>

      {/* Property cards */}
      <div style={{ flex: 1, overflowY: "auto", padding: "0 14px 16px" }}>
        {props.map((p, idx) => (
          <div key={idx} style={{ background: "white", borderRadius: 16, border: `1px solid ${C.border}`, marginBottom: 12, overflow: "hidden" }}>
            {/* Image placeholder */}
            <div style={{ height: 140, background: `linear-gradient(135deg,${p.color}CC,${p.color}66)`, position: "relative", display: "flex", alignItems: "center", justifyContent: "center" }}>
              <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="rgba(255,255,255,0.5)" strokeWidth="1.5" strokeLinecap="round"><rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/></svg>
              <div style={{ position: "absolute", top: 10, right: 10, display: "flex", gap: 5 }}>
                {p.chips.includes("موثّق") && <span style={{ background: TEAL, color: "white", fontSize: 10, fontWeight: 700, padding: "3px 8px", borderRadius: 6 }}>موثّق ✓</span>}
              </div>
              <div style={{ position: "absolute", bottom: 8, left: 10 }}>
                <span style={{ background: "rgba(0,0,0,0.45)", color: "white", fontSize: 10, fontWeight: 600, padding: "3px 8px", borderRadius: 6 }}>8 صور</span>
              </div>
            </div>

            {/* Card body */}
            <div style={{ padding: "12px 14px" }}>
              <div style={{ fontSize: 15, fontWeight: 800, color: C.text, marginBottom: 4 }}>{p.title}</div>
              <div style={{ display: "flex", alignItems: "center", gap: 4, marginBottom: 8 }}>
                <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke={C.sub} strokeWidth="2" strokeLinecap="round"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0118 0z"/><circle cx="12" cy="10" r="3"/></svg>
                <span style={{ fontSize: 11, color: C.sub }}>{p.area}</span>
              </div>

              {/* Stats row */}
              <div style={{ display: "flex", gap: 12, marginBottom: 10 }}>
                <span style={{ fontSize: 12, color: C.sub }}>🛏 {p.rooms} غرف</span>
                <span style={{ fontSize: 12, color: C.sub }}>🚿 {p.baths} حمام</span>
                <span style={{ fontSize: 12, color: C.sub }}>📐 {p.m2}م²</span>
              </div>

              {/* Mini chips */}
              <div style={{ display: "flex", gap: 6, flexWrap: "wrap", marginBottom: 10 }}>
                {p.chips.filter(c => c !== "موثّق").map(chip => (
                  <span key={chip} style={{ padding: "3px 10px", borderRadius: 16, background: "#F3F4F6", color: C.sub, fontSize: 11, fontWeight: 600 }}>{chip}</span>
                ))}
              </div>

              {/* Price row */}
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                <div>
                  <span style={{ fontSize: 18, fontWeight: 900, color: TEAL }}>{p.price}</span>
                  <span style={{ fontSize: 12, color: C.sub, marginRight: 4 }}>{p.unit}</span>
                </div>
                <button style={{ height: 36, padding: "0 16px", borderRadius: 10, background: TEAL, border: "none", color: "white", fontSize: 13, fontWeight: 700, cursor: "pointer", ...TJ }}>تفاصيل</button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ════════════════════════════════════════════════════════════════════════
// O-ADD-02 UPDATED — PROPERTY PHOTOS WITH NAME & DESCRIPTION
// ════════════════════════════════════════════════════════════════════════

type PhotoSlot = {
  filled: boolean;
  uploading: boolean;
  failed: boolean;
  name: string;
  desc: string;
  nameErr: string;
  descErr: string;
};

function photoDefault(filled = false): PhotoSlot {
  return { filled, uploading: false, failed: false, name: "", desc: "", nameErr: "", descErr: "" };
}

const PHOTO_NAME_HINTS = ["غرفة النوم","الريسبشن","المطبخ","الحمام","البلكونة","واجهة العقار"];
const PHOTO_SLOT_COLORS = ["#CBD5E1","#BAC8D3","#C5D5C5","#D5CEC5","#C5C8D5","#D5C8BD"];

function AddPhotoStepBar({ current }: { current: number }) {
  const steps = ["الأساسيات","الصور","فيديو","التسعير"];
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 4, marginBottom: 14 }}>
      {steps.map((s, i) => (
        <React.Fragment key={s}>
          <div style={{ display: "flex", flex: 1, flexDirection: "column", alignItems: "center", gap: 3 }}>
            <div style={{ width: "100%", height: 4, borderRadius: 2, background: i <= current ? TEAL : "#E5E7EB" }} />
            <span style={{ fontSize: 8.5, color: i === current ? TEAL : i < current ? TEAL : C.sub, fontWeight: i === current ? 800 : 500 }}>{s}</span>
          </div>
          {i < steps.length - 1 && <div style={{ width: 4, height: 4, borderRadius: 2, background: "#E5E7EB", flexShrink: 0 }} />}
        </React.Fragment>
      ))}
    </div>
  );
}

export function UpdatedAddPropertyStep2Screen() {
  const REQUIRED = 10;
  const [slots, setSlots] = React.useState<PhotoSlot[]>([
    { ...photoDefault(true), name: "غرفة النوم", desc: "غرفة نوم واسعة بإضاءة طبيعية" },
    { ...photoDefault(true), name: "الريسبشن",   desc: "صالة استقبال مريحة" },
    { ...photoDefault(true), name: "المطبخ",      desc: "مطبخ مجهز بالكامل" },
    { ...photoDefault(true), name: "الحمام",       desc: "" },
    photoDefault(false), photoDefault(false), photoDefault(false),
    photoDefault(false), photoDefault(false), photoDefault(false),
  ]);
  const [showTips, setShowTips] = React.useState(false);

  const uploaded = slots.filter(s => s.filled && !s.failed).length;
  const canNext = uploaded >= REQUIRED && slots.filter(s => s.filled).every(s => s.name.trim() && s.desc.trim());

  function upd(i: number, patch: Partial<PhotoSlot>) {
    setSlots(prev => prev.map((s, idx) => idx === i ? { ...s, ...patch } : s));
  }
  function startUpload(i: number) {
    upd(i, { uploading: true, filled: false, failed: false });
    setTimeout(() => upd(i, { uploading: false, filled: true, name: PHOTO_NAME_HINTS[i % PHOTO_NAME_HINTS.length], desc: "" }), 1200);
  }
  function blur(i: number) {
    const s = slots[i];
    if (!s.filled) return;
    upd(i, { nameErr: s.name.trim() ? "" : "اسم الصورة مطلوب", descErr: s.desc.trim() ? "" : "وصف الصورة مطلوب" });
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100%", background: C.bg, fontFamily: "Tajawal, sans-serif" }}>
      <StatusBar />
      <NavBar title="صور العقار" onBack={() => {}} />
      <div style={{ flex: 1, overflowY: "auto", padding: "16px 16px 100px", direction: "rtl" }}>
        <AddPhotoStepBar current={1} />

        {/* Progress */}
        <div style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 14, padding: "12px 16px", marginBottom: 14 }}>
          <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 8 }}>
            <span style={{ fontSize: 13, fontWeight: 700, color: C.text }}>الصور المرفوعة</span>
            <span style={{ fontSize: 13, fontWeight: 800, color: uploaded >= REQUIRED ? TEAL : ROSE }}>{uploaded} / {REQUIRED}</span>
          </div>
          <div style={{ height: 6, background: "#E5E7EB", borderRadius: 3, overflow: "hidden" }}>
            <div style={{ height: "100%", width: `${Math.min((uploaded / REQUIRED) * 100, 100)}%`, background: uploaded >= REQUIRED ? TEAL : ROSE, borderRadius: 3 }} />
          </div>
          {uploaded === 0 && <p style={{ fontSize: 11, color: ROSE, marginTop: 6 }}>ارفع صور العقار · الحد الأدنى {REQUIRED} صور</p>}
        </div>

        {/* Warning */}
        <div style={{ display: "flex", alignItems: "flex-start", gap: 10, padding: "10px 14px", background: "#FFFBEB", border: "1px solid #FDE68A", borderRadius: 12, marginBottom: 16 }}>
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#D97706" strokeWidth="2.5" strokeLinecap="round" style={{ flexShrink: 0, marginTop: 1 }}><path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
          <span style={{ fontSize: 12, color: "#92400E", lineHeight: 1.5 }}>10 صور على الأقل — تأكد إن الصور واضحة وبدون أرقام هواتف</span>
        </div>

        {/* Slots */}
        <div style={{ display: "flex", flexDirection: "column", gap: 14, marginBottom: 16 }}>
          {slots.map((slot, i) => (
            <div key={i} style={{ background: C.card, border: `1px solid ${slot.nameErr || slot.descErr ? ROSE + "55" : C.border}`, borderRadius: 18, overflow: "hidden" }}>
              <div style={{ display: "flex", gap: 12, padding: "12px 14px", alignItems: "flex-start" }}>
                {/* Thumb */}
                <div style={{ width: 76, height: 76, borderRadius: 12, flexShrink: 0, position: "relative", overflow: "hidden", background: slot.filled ? PHOTO_SLOT_COLORS[i % 6] : "#F3F4F6", border: slot.filled ? "none" : `1.5px dashed ${C.border}`, display: "flex", alignItems: "center", justifyContent: "center" }}>
                  {slot.uploading ? (
                    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 4 }}>
                      <div style={{ width: 20, height: 20, borderRadius: 10, border: `2.5px solid ${TEAL}`, borderTopColor: "transparent" }} />
                      <span style={{ fontSize: 8, color: TEAL }}>جاري الرفع</span>
                    </div>
                  ) : slot.filled ? (
                    <>
                      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="rgba(255,255,255,0.7)" strokeWidth="1.5" strokeLinecap="round"><rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/></svg>
                      <button onClick={() => upd(i, photoDefault(false))} style={{ position: "absolute", top: 4, left: 4, width: 20, height: 20, borderRadius: 10, background: ROSE, border: "none", cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center" }}>
                        <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="3" strokeLinecap="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
                      </button>
                    </>
                  ) : slot.failed ? (
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke={ROSE} strokeWidth="2" strokeLinecap="round"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>
                  ) : (
                    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 3 }}>
                      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#9CA3AF" strokeWidth="1.5" strokeLinecap="round"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
                      <span style={{ fontSize: 8, color: "#9CA3AF" }}>إضافة</span>
                    </div>
                  )}
                </div>

                {/* Right */}
                <div style={{ flex: 1 }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
                    <span style={{ fontSize: 10, fontWeight: 700, color: C.sub }}>صورة {i + 1}</span>
                    {slot.filled ? (
                      <div style={{ display: "flex", gap: 6 }}>
                        <button onClick={() => startUpload(i)} style={{ fontSize: 10, fontWeight: 600, color: TEAL, background: TEAL + "12", border: `1px solid ${TEAL}25`, borderRadius: 8, padding: "3px 10px", cursor: "pointer" }}>تغيير</button>
                        <button onClick={() => upd(i, photoDefault(false))} style={{ fontSize: 10, fontWeight: 600, color: ROSE, background: ROSE + "12", border: `1px solid ${ROSE}25`, borderRadius: 8, padding: "3px 10px", cursor: "pointer" }}>حذف</button>
                      </div>
                    ) : (
                      <button onClick={() => startUpload(i)} style={{ fontSize: 10, fontWeight: 600, color: TEAL, background: TEAL + "12", border: `1px solid ${TEAL}25`, borderRadius: 8, padding: "4px 12px", cursor: "pointer" }}>+ إضافة</button>
                    )}
                  </div>
                  {/* Name */}
                  <label style={{ fontSize: 11, fontWeight: 700, color: C.text, display: "block", marginBottom: 4 }}>اسم الصورة {slot.filled && <span style={{ color: ROSE }}>*</span>}</label>
                  <input value={slot.name} onChange={e => upd(i, { name: e.target.value, nameErr: "" })} onBlur={() => blur(i)} placeholder={PHOTO_NAME_HINTS[i % PHOTO_NAME_HINTS.length]} disabled={!slot.filled}
                    style={{ width: "100%", height: 36, borderRadius: 10, border: `1.5px solid ${slot.nameErr ? ROSE : slot.filled && slot.name ? TEAL : C.border}`, padding: "0 10px", fontSize: 12, color: C.text, background: slot.filled ? "white" : "#F9FAFB", outline: "none", boxSizing: "border-box", direction: "rtl", marginBottom: slot.nameErr ? 2 : 8, fontFamily: "Tajawal, sans-serif" }} />
                  {slot.nameErr && <span style={{ fontSize: 10, color: ROSE, display: "block", marginBottom: 8 }}>{slot.nameErr}</span>}
                  {/* Desc */}
                  <label style={{ fontSize: 11, fontWeight: 700, color: C.text, display: "block", marginBottom: 4 }}>وصف الصورة {slot.filled && <span style={{ color: ROSE }}>*</span>}</label>
                  <input value={slot.desc} onChange={e => upd(i, { desc: e.target.value, descErr: "" })} onBlur={() => blur(i)} placeholder="اكتب وصف بسيط للصورة" disabled={!slot.filled}
                    style={{ width: "100%", height: 36, borderRadius: 10, border: `1.5px solid ${slot.descErr ? ROSE : slot.filled && slot.desc ? TEAL : C.border}`, padding: "0 10px", fontSize: 12, color: C.text, background: slot.filled ? "white" : "#F9FAFB", outline: "none", boxSizing: "border-box", direction: "rtl", fontFamily: "Tajawal, sans-serif" }} />
                  {slot.descErr && <span style={{ fontSize: 10, color: ROSE, display: "block", marginTop: 2 }}>{slot.descErr}</span>}
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Tips */}
        <div style={{ background: TEAL + "08", border: `1px solid ${TEAL}25`, borderRadius: 16, marginBottom: 20, overflow: "hidden" }}>
          <button onClick={() => setShowTips(v => !v)} style={{ width: "100%", padding: "12px 16px", background: "transparent", border: "none", cursor: "pointer", display: "flex", justifyContent: "space-between", alignItems: "center", direction: "rtl" }}>
            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke={TEAL} strokeWidth="2" strokeLinecap="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
              <span style={{ fontSize: 13, fontWeight: 700, color: TEAL }}>نصائح لصور أفضل</span>
            </div>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke={TEAL} strokeWidth="2.5" strokeLinecap="round"><polyline points="6 9 12 15 18 9"/></svg>
          </button>
          {showTips && (
            <div style={{ padding: "0 16px 14px", direction: "rtl" }}>
              {["صوّر كل غرفة بوضوح","استخدم إضاءة كويسة","اكتب اسم ووصف لكل صورة","متصورش أي مستندات أو أرقام شخصية"].map((tip, i, arr) => (
                <div key={i} style={{ display: "flex", alignItems: "flex-start", gap: 8, padding: "8px 0", borderBottom: i < arr.length - 1 ? `1px solid ${TEAL}18` : "none" }}>
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke={TEAL} strokeWidth="2.5" strokeLinecap="round" style={{ flexShrink: 0, marginTop: 2 }}><polyline points="20 6 9 17 4 12"/></svg>
                  <span style={{ fontSize: 12, color: TEAL, lineHeight: 1.5 }}>{tip}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* CTA */}
      <div style={{ padding: "12px 16px 24px", background: C.card, borderTop: `1px solid ${C.border}`, flexShrink: 0 }}>
        {!canNext && uploaded > 0 && (
          <p style={{ fontSize: 11, color: ROSE, textAlign: "center", marginBottom: 8 }}>
            {uploaded < REQUIRED ? `ارفع ${REQUIRED - uploaded} صور إضافية` : "أكمل اسم ووصف كل صورة"}
          </p>
        )}
        <PrimaryBtn label="التالي — فيديو العقار" disabled={!canNext} />
      </div>
    </div>
  );
}

// ════════════════════════════════════════════════════════════════════════
// O-ADD-02V — PROPERTY VIDEO UPLOAD
// ════════════════════════════════════════════════════════════════════════

type VideoUploadState = "empty" | "uploading" | "uploaded" | "failed" | "tooLong";

export function AddPropertyVideoScreen() {
  const [vState, setVState] = React.useState<VideoUploadState>("empty");

  function doUpload(over = false) {
    setVState("uploading");
    setTimeout(() => setVState(over ? "tooLong" : "uploaded"), 1400);
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100%", background: C.bg, fontFamily: "Tajawal, sans-serif" }}>
      <StatusBar />
      <NavBar title="فيديو العقار" onBack={() => {}} />

      <div style={{ flex: 1, overflowY: "auto", padding: "16px 16px 100px", direction: "rtl" }}>
        <AddPhotoStepBar current={2} />

        <h2 style={{ fontSize: 20, fontWeight: 900, color: C.text, margin: "0 0 6px" }}>فيديو العقار</h2>
        <p style={{ fontSize: 13, color: C.sub, margin: "0 0 16px" }}>صوّر فيديو قصير يوضح العقار للمستأجرين</p>

        {/* Requirements card */}
        <div style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 16, padding: "14px 16px", marginBottom: 16 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 12 }}>
            <div style={{ width: 30, height: 30, borderRadius: 10, background: TEAL + "14", display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke={TEAL} strokeWidth="2" strokeLinecap="round"><polygon points="23 7 16 12 23 17 23 7"/><rect x="1" y="5" width="15" height="14" rx="2" ry="2"/></svg>
            </div>
            <span style={{ fontSize: 13, fontWeight: 800, color: C.text }}>متطلبات الفيديو</span>
          </div>
          {["مدة الفيديو لا تزيد عن دقيقة واحدة (60 ثانية)","صوّر مدخل العقار والغرف الأساسية","خلي الفيديو واضح وثابت","متظهرش أرقام تليفونات أو مستندات شخصية في الفيديو"].map((req, i, arr) => (
            <div key={i} style={{ display: "flex", alignItems: "flex-start", gap: 10, padding: "9px 0", borderBottom: i < arr.length - 1 ? `1px solid ${C.border}` : "none" }}>
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke={TEAL} strokeWidth="2.5" strokeLinecap="round" style={{ flexShrink: 0, marginTop: 2 }}><polyline points="20 6 9 17 4 12"/></svg>
              <span style={{ fontSize: 12, color: C.sub, lineHeight: 1.5 }}>{req}</span>
            </div>
          ))}
          <div style={{ marginTop: 10, padding: "8px 12px", background: "#FEF3C7", border: "1px solid #FDE68A", borderRadius: 10, display: "flex", alignItems: "center", gap: 8 }}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#D97706" strokeWidth="2.5" strokeLinecap="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
            <span style={{ fontSize: 12, fontWeight: 700, color: "#92400E" }}>الحد الأقصى: 60 ثانية</span>
          </div>
        </div>

        {/* Empty */}
        {vState === "empty" && (
          <div style={{ background: C.card, border: `2px dashed ${C.border}`, borderRadius: 20, padding: "36px 20px", marginBottom: 16, textAlign: "center" }}>
            <div style={{ width: 64, height: 64, borderRadius: 20, background: "#F3F4F6", display: "flex", alignItems: "center", justifyContent: "center", margin: "0 auto 16px" }}>
              <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#9CA3AF" strokeWidth="1.5" strokeLinecap="round"><polygon points="23 7 16 12 23 17 23 7"/><rect x="1" y="5" width="15" height="14" rx="2" ry="2"/></svg>
            </div>
            <p style={{ fontSize: 15, fontWeight: 700, color: C.text, margin: "0 0 6px" }}>ارفع أو صوّر فيديو للعقار</p>
            <p style={{ fontSize: 12, color: C.sub, margin: "0 0 20px" }}>الحد الأقصى: 60 ثانية</p>
            <div style={{ display: "flex", gap: 10, justifyContent: "center" }}>
              <button onClick={() => doUpload(false)} style={{ display: "flex", alignItems: "center", gap: 8, height: 44, padding: "0 18px", background: TEAL, border: "none", borderRadius: 12, cursor: "pointer" }}>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2" strokeLinecap="round"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="3" fill="white"/></svg>
                <span style={{ fontSize: 13, fontWeight: 700, color: "white" }}>تصوير فيديو</span>
              </button>
              <button onClick={() => doUpload(false)} style={{ display: "flex", alignItems: "center", gap: 8, height: 44, padding: "0 18px", background: "white", border: `1.5px solid ${C.border}`, borderRadius: 12, cursor: "pointer" }}>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke={C.text} strokeWidth="2" strokeLinecap="round"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
                <span style={{ fontSize: 13, fontWeight: 700, color: C.text }}>رفع فيديو</span>
              </button>
            </div>
            <button onClick={() => doUpload(true)} style={{ marginTop: 12, fontSize: 11, color: C.sub, background: "none", border: "none", cursor: "pointer", textDecoration: "underline" }}>اختبار: رفع فيديو طويل</button>
          </div>
        )}

        {/* Uploading */}
        {vState === "uploading" && (
          <div style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 20, padding: 24, marginBottom: 16, textAlign: "center" }}>
            <div style={{ width: 56, height: 56, borderRadius: 18, background: TEAL + "14", display: "flex", alignItems: "center", justifyContent: "center", margin: "0 auto 14px" }}>
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke={TEAL} strokeWidth="2" strokeLinecap="round"><polygon points="23 7 16 12 23 17 23 7"/><rect x="1" y="5" width="15" height="14" rx="2" ry="2"/></svg>
            </div>
            <p style={{ fontSize: 14, fontWeight: 700, color: C.text, margin: "0 0 10px" }}>جاري رفع الفيديو…</p>
            <div style={{ height: 6, background: "#E5E7EB", borderRadius: 3, overflow: "hidden" }}>
              <div style={{ height: "100%", width: "65%", background: TEAL, borderRadius: 3 }} />
            </div>
            <p style={{ fontSize: 11, color: C.sub, marginTop: 6 }}>65%</p>
          </div>
        )}

        {/* Uploaded */}
        {vState === "uploaded" && (
          <div style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 20, overflow: "hidden", marginBottom: 16 }}>
            <div style={{ height: 160, background: "linear-gradient(135deg,#0D1B2A,#1A3A4A)", position: "relative", display: "flex", alignItems: "center", justifyContent: "center" }}>
              <div style={{ width: 52, height: 52, borderRadius: 26, background: "rgba(255,255,255,0.2)", display: "flex", alignItems: "center", justifyContent: "center" }}>
                <svg width="22" height="22" viewBox="0 0 24 24" fill="white"><polygon points="5 3 19 12 5 21 5 3"/></svg>
              </div>
              <div style={{ position: "absolute", bottom: 10, right: 12, background: "rgba(0,0,0,0.65)", borderRadius: 8, padding: "3px 10px" }}>
                <span style={{ fontSize: 12, fontWeight: 800, color: "white", letterSpacing: 1 }}>00:45</span>
              </div>
              <div style={{ position: "absolute", top: 10, right: 12, background: "#16A34A", borderRadius: 8, padding: "3px 10px", display: "flex", alignItems: "center", gap: 4 }}>
                <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="3" strokeLinecap="round"><polyline points="20 6 9 17 4 12"/></svg>
                <span style={{ fontSize: 10, fontWeight: 700, color: "white" }}>تم الرفع</span>
              </div>
            </div>
            <div style={{ padding: "12px 16px", display: "flex", justifyContent: "space-between", alignItems: "center", direction: "rtl" }}>
              <div>
                <p style={{ fontSize: 13, fontWeight: 700, color: C.text, margin: "0 0 3px" }}>فيديو العقار</p>
                <p style={{ fontSize: 11, color: C.sub, margin: 0 }}>المدة: 00:45 · MP4</p>
              </div>
              <div style={{ display: "flex", gap: 8 }}>
                <button onClick={() => setVState("empty")} style={{ fontSize: 11, fontWeight: 600, color: TEAL, background: TEAL + "12", border: `1px solid ${TEAL}25`, borderRadius: 10, padding: "6px 12px", cursor: "pointer" }}>تغيير الفيديو</button>
                <button onClick={() => setVState("empty")} style={{ fontSize: 11, fontWeight: 600, color: ROSE, background: ROSE + "12", border: `1px solid ${ROSE}25`, borderRadius: 10, padding: "6px 12px", cursor: "pointer" }}>حذف الفيديو</button>
              </div>
            </div>
          </div>
        )}

        {/* Too long */}
        {vState === "tooLong" && (
          <div style={{ background: ROSE + "08", border: `1px solid ${ROSE}30`, borderRadius: 16, padding: 16, marginBottom: 16, direction: "rtl" }}>
            <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 8 }}>
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke={ROSE} strokeWidth="2" strokeLinecap="round"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>
              <span style={{ fontSize: 13, fontWeight: 700, color: ROSE }}>الفيديو لازم يكون أقل من دقيقة</span>
            </div>
            <p style={{ fontSize: 12, color: ROSE, margin: "0 0 12px", opacity: 0.8 }}>الفيديو اللي رفعته طوله أكتر من 60 ثانية. اختار فيديو أقصر.</p>
            <button onClick={() => setVState("empty")} style={{ height: 40, padding: "0 16px", background: ROSE, border: "none", borderRadius: 10, cursor: "pointer" }}>
              <span style={{ fontSize: 12, fontWeight: 700, color: "white" }}>رفع فيديو تاني</span>
            </button>
          </div>
        )}

        {/* Privacy hint */}
        <div style={{ display: "flex", alignItems: "flex-start", gap: 10, padding: "12px 14px", background: "#F0FDF9", border: `1px solid ${TEAL}22`, borderRadius: 14 }}>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke={TEAL} strokeWidth="2" strokeLinecap="round" style={{ flexShrink: 0, marginTop: 2 }}><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
          <span style={{ fontSize: 12, color: TEAL, lineHeight: 1.5 }}>الفيديو هيظهر للمستأجرين بعد مراجعة سكون، فمتظهرش فيه أي بيانات شخصية</span>
        </div>
      </div>

      {/* CTAs */}
      <div style={{ padding: "12px 16px 24px", background: C.card, borderTop: `1px solid ${C.border}`, flexShrink: 0, display: "flex", flexDirection: "column", gap: 10 }}>
        <PrimaryBtn label="التالي — التسعير" disabled={vState !== "uploaded"} />
        <button style={{ width: "100%", height: 44, background: "transparent", border: `1.5px solid ${C.border}`, borderRadius: 14, cursor: "pointer" }}>
          <span style={{ fontSize: 14, fontWeight: 600, color: C.sub }}>تخطي الفيديو</span>
        </button>
      </div>
    </div>
  );
}

// ════════════════════════════════════════════════════════════════════════
// FORGOT PASSWORD SCREENS
// ════════════════════════════════════════════════════════════════════════

type ForgotStep = "email" | "sent" | "newpass";

function ForgotPasswordBase({ accentColor, logoFill }: { accentColor: string; logoFill: string }) {
  const [step, setStep] = React.useState<ForgotStep>("email");
  const [email, setEmail] = React.useState("");
  const [emailErr, setEmailErr] = React.useState("");
  const [newPass, setNewPass] = React.useState("");
  const [confirmPass, setConfirmPass] = React.useState("");
  const [showNew, setShowNew] = React.useState(false);
  const [showConfirm, setShowConfirm] = React.useState(false);
  const [passErr, setPassErr] = React.useState("");
  const [sending, setSending] = React.useState(false);
  const [resendTimer, setResendTimer] = React.useState(45);

  function isValidEmail(v: string) { return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v); }

  function handleSend() {
    if (!email.trim()) { setEmailErr("البريد الإلكتروني مطلوب"); return; }
    if (!isValidEmail(email)) { setEmailErr("البريد الإلكتروني غير صحيح"); return; }
    setSending(true);
    setTimeout(() => { setSending(false); setStep("sent"); }, 1200);
  }

  function handleReset() {
    if (newPass.length < 8) { setPassErr("كلمة المرور لازم تكون 8 أحرف على الأقل"); return; }
    if (newPass !== confirmPass) { setPassErr("كلمة المرور مش متطابقة"); return; }
    setStep("email"); // simulate done
  }

  const maskedEmail = email ? email.replace(/(.{2})[^@]+(@.+)/, "$1****$2") : "ah****@gmail.com";

  return (
    <div style={{ width: 390, height: 844, background: C.bg, display: "flex", flexDirection: "column", ...TJ, direction: "rtl", overflow: "hidden" }}>
      <StatusBar />

      {/* Step: Enter Email */}
      {step === "email" && (
        <>
          <NavBar title="استعادة كلمة المرور" onBack={() => {}} />
          <div style={{ flex: 1, padding: "32px 24px", overflowY: "auto" }}>
            {/* Illustration */}
            <div style={{ display: "flex", flexDirection: "column", alignItems: "center", marginBottom: 32 }}>
              <div style={{ width: 80, height: 80, borderRadius: 24, background: accentColor + "15", display: "flex", alignItems: "center", justifyContent: "center", marginBottom: 16 }}>
                <svg width="38" height="38" viewBox="0 0 24 24" fill="none" stroke={accentColor} strokeWidth="1.8" strokeLinecap="round">
                  <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
                  <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
                  <circle cx="12" cy="16" r="1.5" fill={accentColor}/>
                </svg>
              </div>
              <div style={{ fontSize: 20, fontWeight: 900, color: C.text, marginBottom: 8 }}>نسيت كلمة المرور؟</div>
              <div style={{ fontSize: 13, color: C.sub, textAlign: "center", lineHeight: 1.7, maxWidth: 280 }}>مش مشكلة، هنبعتلك رابط على بريدك الإلكتروني عشان تعيد تعيين كلمة المرور</div>
            </div>

            {/* Email field */}
            <div style={{ marginBottom: 8 }}>
              <div style={{ fontSize: 13, fontWeight: 700, color: C.text, marginBottom: 8 }}>البريد الإلكتروني</div>
              <div style={{ position: "relative" }}>
                <input
                  value={email}
                  onChange={e => { setEmail(e.target.value); setEmailErr(""); }}
                  onBlur={() => { if (email && !isValidEmail(email)) setEmailErr("البريد الإلكتروني غير صحيح"); }}
                  placeholder="example@email.com"
                  type="email"
                  style={{
                    width: "100%", height: 52, borderRadius: 12,
                    border: `1.5px solid ${emailErr ? ROSE : (email && isValidEmail(email) ? accentColor : C.border)}`,
                    padding: "0 46px 0 16px", fontSize: 15, color: C.text, background: "white",
                    boxSizing: "border-box", textAlign: "right", direction: "ltr", ...TJ, outline: "none",
                  }}
                />
                {/* Email icon */}
                <div style={{ position: "absolute", right: 14, top: "50%", transform: "translateY(-50%)", pointerEvents: "none" }}>
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke={emailErr ? ROSE : (email && isValidEmail(email) ? accentColor : "#9CA3AF")} strokeWidth="2" strokeLinecap="round">
                    <rect x="2" y="4" width="20" height="16" rx="2"/>
                    <polyline points="22,4 12,13 2,4"/>
                  </svg>
                </div>
                {/* Checkmark on valid */}
                {email && isValidEmail(email) && !emailErr && (
                  <div style={{ position: "absolute", left: 14, top: "50%", transform: "translateY(-50%)", pointerEvents: "none" }}>
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke={accentColor} strokeWidth="2.5" strokeLinecap="round"><polyline points="20 6 9 17 4 12"/></svg>
                  </div>
                )}
              </div>
              {emailErr && <div style={{ fontSize: 12, color: ROSE, marginTop: 6, fontWeight: 600 }}>{emailErr}</div>}
              {!emailErr && <div style={{ fontSize: 11, color: C.sub, marginTop: 6 }}>هنبعت رابط إعادة تعيين على بريدك</div>}
            </div>

            {/* CTA */}
            <div style={{ marginTop: 28 }}>
              <button
                onClick={handleSend}
                disabled={sending}
                style={{ width: "100%", height: 52, background: sending ? accentColor + "99" : accentColor, border: "none", borderRadius: 14, color: "white", fontSize: 16, fontWeight: 700, cursor: sending ? "not-allowed" : "pointer", display: "flex", alignItems: "center", justifyContent: "center", gap: 10, ...TJ }}>
                {sending ? (
                  <>
                    <div style={{ width: 18, height: 18, borderRadius: 9, border: "2.5px solid rgba(255,255,255,0.4)", borderTopColor: "white" }} />
                    <span>جاري الإرسال…</span>
                  </>
                ) : (
                  <>
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2" strokeLinecap="round"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>
                    <span>إرسال رابط الاستعادة</span>
                  </>
                )}
              </button>
            </div>

            {/* Back to login */}
            <div style={{ textAlign: "center", marginTop: 20 }}>
              <button style={{ background: "none", border: "none", color: C.sub, fontSize: 13, cursor: "pointer", ...TJ }}>
                <span>تذكرت كلمة المرور؟ </span>
                <span style={{ color: accentColor, fontWeight: 700, textDecoration: "underline" }}>تسجيل الدخول</span>
              </button>
            </div>

            {/* Security hint */}
            <div style={{ marginTop: 28, padding: "14px 16px", background: accentColor + "08", border: `1px solid ${accentColor}22`, borderRadius: 14, display: "flex", gap: 12, alignItems: "flex-start" }}>
              <div style={{ width: 34, height: 34, borderRadius: 10, background: accentColor + "18", display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke={accentColor} strokeWidth="2" strokeLinecap="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
              </div>
              <div>
                <div style={{ fontSize: 12, fontWeight: 700, color: C.text, marginBottom: 3 }}>الرابط صالح لمدة 15 دقيقة</div>
                <div style={{ fontSize: 11, color: C.sub, lineHeight: 1.5 }}>لو ماوصلكش الإيميل، اتأكد من مجلد السبام أو جرب تاني</div>
              </div>
            </div>
          </div>
        </>
      )}

      {/* Step: Email Sent */}
      {step === "sent" && (
        <>
          <NavBar title="تحقق من بريدك" onBack={() => setStep("email")} />
          <div style={{ flex: 1, padding: "32px 24px", overflowY: "auto" }}>
            <div style={{ display: "flex", flexDirection: "column", alignItems: "center", marginBottom: 36 }}>
              {/* Success animation card */}
              <div style={{ width: 96, height: 96, borderRadius: 28, background: "linear-gradient(135deg," + accentColor + "20," + accentColor + "10)", display: "flex", alignItems: "center", justifyContent: "center", marginBottom: 20, border: `2px solid ${accentColor}25` }}>
                <svg width="44" height="44" viewBox="0 0 24 24" fill="none" stroke={accentColor} strokeWidth="1.5" strokeLinecap="round">
                  <rect x="2" y="4" width="20" height="16" rx="2"/>
                  <polyline points="22,4 12,13 2,4"/>
                  <polyline points="8 14 10.5 16.5 16 11" stroke={GREEN} strokeWidth="2.5"/>
                </svg>
              </div>
              <div style={{ fontSize: 22, fontWeight: 900, color: C.text, marginBottom: 10 }}>تم إرسال الرابط!</div>
              <div style={{ fontSize: 13, color: C.sub, textAlign: "center", lineHeight: 1.7 }}>بعتنالك رابط إعادة تعيين كلمة المرور على</div>
              <div style={{ fontSize: 15, fontWeight: 800, color: accentColor, marginTop: 6 }}>{maskedEmail}</div>
            </div>

            {/* Steps guide */}
            {[
              { n: "1", text: "افتح بريدك الإلكتروني", sub: "ابحث عن إيميل من سكون" },
              { n: "2", text: "اضغط على الرابط", sub: "الرابط صالح لمدة 15 دقيقة" },
              { n: "3", text: "أنشئ كلمة مرور جديدة", sub: "8 أحرف على الأقل" },
            ].map((item, i, arr) => (
              <div key={i} style={{ display: "flex", alignItems: "flex-start", gap: 14, marginBottom: i < arr.length - 1 ? 0 : 0, position: "relative" }}>
                <div style={{ display: "flex", flexDirection: "column", alignItems: "center" }}>
                  <div style={{ width: 34, height: 34, borderRadius: 17, background: accentColor, display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
                    <span style={{ fontSize: 14, fontWeight: 800, color: "white" }}>{item.n}</span>
                  </div>
                  {i < arr.length - 1 && <div style={{ width: 2, height: 32, background: accentColor + "30", margin: "4px 0" }} />}
                </div>
                <div style={{ paddingTop: 6, paddingBottom: i < arr.length - 1 ? 0 : 0 }}>
                  <div style={{ fontSize: 14, fontWeight: 700, color: C.text }}>{item.text}</div>
                  <div style={{ fontSize: 12, color: C.sub, marginTop: 2 }}>{item.sub}</div>
                  {i < arr.length - 1 && <div style={{ height: 24 }} />}
                </div>
              </div>
            ))}

            <div style={{ height: 28 }} />

            {/* Resend */}
            <div style={{ padding: "14px 16px", background: "#F9FAFB", border: `1px solid ${C.border}`, borderRadius: 14, display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
              <div>
                <div style={{ fontSize: 13, fontWeight: 700, color: C.text }}>ماوصلكش الإيميل؟</div>
                <div style={{ fontSize: 11, color: C.sub, marginTop: 2 }}>تأكد من مجلد السبام أولاً</div>
              </div>
              <button onClick={() => setResendTimer(45)} style={{ height: 36, padding: "0 14px", background: accentColor + "12", border: `1px solid ${accentColor}30`, borderRadius: 10, cursor: "pointer" }}>
                <span style={{ fontSize: 12, fontWeight: 700, color: accentColor }}>
                  {resendTimer > 0 ? `${resendTimer}ث` : "إعادة الإرسال"}
                </span>
              </button>
            </div>

            <button onClick={() => setStep("email")} style={{ width: "100%", height: 52, background: "white", border: `1.5px solid ${C.border}`, borderRadius: 14, color: C.text, fontSize: 15, fontWeight: 700, cursor: "pointer", ...TJ }}>
              تغيير البريد الإلكتروني
            </button>

            {/* Demo: go to reset step */}
            <div style={{ textAlign: "center", marginTop: 12 }}>
              <button onClick={() => setStep("newpass")} style={{ background: "none", border: "none", color: C.sub, fontSize: 12, cursor: "pointer", ...TJ, textDecoration: "underline" }}>
                معاينة: تعيين كلمة مرور جديدة
              </button>
            </div>
          </div>
        </>
      )}

      {/* Step: New Password */}
      {step === "newpass" && (
        <>
          <NavBar title="كلمة مرور جديدة" onBack={() => setStep("sent")} />
          <div style={{ flex: 1, padding: "32px 24px", overflowY: "auto" }}>
            <div style={{ display: "flex", flexDirection: "column", alignItems: "center", marginBottom: 28 }}>
              <div style={{ width: 72, height: 72, borderRadius: 20, background: accentColor + "15", display: "flex", alignItems: "center", justifyContent: "center", marginBottom: 14 }}>
                <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke={accentColor} strokeWidth="1.8" strokeLinecap="round">
                  <rect x="3" y="11" width="18" height="11" rx="2"/>
                  <path d="M7 11V7a5 5 0 0 1 9.9-1"/>
                  <circle cx="12" cy="16" r="1.5" fill={accentColor}/>
                </svg>
              </div>
              <div style={{ fontSize: 20, fontWeight: 900, color: C.text, marginBottom: 6 }}>أنشئ كلمة مرور جديدة</div>
              <div style={{ fontSize: 13, color: C.sub, textAlign: "center" }}>اختار كلمة مرور قوية ومختلفة عن القديمة</div>
            </div>

            {/* New password */}
            <div style={{ marginBottom: 14 }}>
              <div style={{ fontSize: 13, fontWeight: 700, color: C.text, marginBottom: 8 }}>كلمة المرور الجديدة</div>
              <div style={{ position: "relative" }}>
                <input
                  value={newPass}
                  onChange={e => { setNewPass(e.target.value); setPassErr(""); }}
                  type={showNew ? "text" : "password"}
                  placeholder="••••••••"
                  style={{ width: "100%", height: 52, borderRadius: 12, border: `1.5px solid ${passErr ? ROSE : (newPass.length >= 8 ? accentColor : C.border)}`, padding: "0 48px 0 16px", fontSize: 15, color: C.text, background: "white", boxSizing: "border-box", direction: "ltr", textAlign: "left", ...TJ, outline: "none" }}
                />
                <button onClick={() => setShowNew(!showNew)} style={{ position: "absolute", left: 14, top: "50%", transform: "translateY(-50%)", background: "none", border: "none", cursor: "pointer", padding: 0 }}>
                  <EyeIcon open={showNew} />
                </button>
              </div>
              {/* Strength bar */}
              {newPass.length > 0 && (
                <div style={{ marginTop: 8 }}>
                  <div style={{ display: "flex", gap: 4, marginBottom: 4 }}>
                    {[...Array(4)].map((_, i) => {
                      const strength = newPass.length < 4 ? 1 : newPass.length < 8 ? 2 : /[A-Z]/.test(newPass) && /[0-9]/.test(newPass) ? 4 : 3;
                      return <div key={i} style={{ flex: 1, height: 4, borderRadius: 2, background: i < strength ? (strength <= 1 ? ROSE : strength <= 2 ? "#F59E0B" : strength <= 3 ? accentColor : GREEN) : C.border }} />;
                    })}
                  </div>
                  <span style={{ fontSize: 11, color: newPass.length < 4 ? ROSE : newPass.length < 8 ? "#D97706" : accentColor }}>
                    {newPass.length < 4 ? "ضعيفة" : newPass.length < 8 ? "متوسطة" : /[A-Z]/.test(newPass) && /[0-9]/.test(newPass) ? "ممتازة" : "قوية"}
                  </span>
                </div>
              )}
            </div>

            {/* Confirm password */}
            <div style={{ marginBottom: 8 }}>
              <div style={{ fontSize: 13, fontWeight: 700, color: C.text, marginBottom: 8 }}>تأكيد كلمة المرور</div>
              <div style={{ position: "relative" }}>
                <input
                  value={confirmPass}
                  onChange={e => { setConfirmPass(e.target.value); setPassErr(""); }}
                  type={showConfirm ? "text" : "password"}
                  placeholder="••••••••"
                  style={{ width: "100%", height: 52, borderRadius: 12, border: `1.5px solid ${passErr ? ROSE : (confirmPass && confirmPass === newPass ? accentColor : C.border)}`, padding: "0 48px 0 16px", fontSize: 15, color: C.text, background: "white", boxSizing: "border-box", direction: "ltr", textAlign: "left", ...TJ, outline: "none" }}
                />
                <button onClick={() => setShowConfirm(!showConfirm)} style={{ position: "absolute", left: 14, top: "50%", transform: "translateY(-50%)", background: "none", border: "none", cursor: "pointer", padding: 0 }}>
                  <EyeIcon open={showConfirm} />
                </button>
                {confirmPass && confirmPass === newPass && (
                  <div style={{ position: "absolute", right: 14, top: "50%", transform: "translateY(-50%)", pointerEvents: "none" }}>
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke={accentColor} strokeWidth="2.5" strokeLinecap="round"><polyline points="20 6 9 17 4 12"/></svg>
                  </div>
                )}
              </div>
              {passErr && <div style={{ fontSize: 12, color: ROSE, marginTop: 6, fontWeight: 600 }}>{passErr}</div>}
            </div>

            {/* Rules */}
            <div style={{ padding: "12px 14px", background: "#F9FAFB", border: `1px solid ${C.border}`, borderRadius: 12, marginBottom: 28, marginTop: 4 }}>
              {[
                { ok: newPass.length >= 8, text: "8 أحرف على الأقل" },
                { ok: /[A-Z]/.test(newPass), text: "حرف كبير واحد على الأقل" },
                { ok: /[0-9]/.test(newPass), text: "رقم واحد على الأقل" },
              ].map((rule, i) => (
                <div key={i} style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: i < 2 ? 8 : 0 }}>
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke={rule.ok ? GREEN : "#9CA3AF"} strokeWidth="2.5" strokeLinecap="round">
                    {rule.ok ? <polyline points="20 6 9 17 4 12"/> : <circle cx="12" cy="12" r="10"/>}
                  </svg>
                  <span style={{ fontSize: 12, color: rule.ok ? GREEN : C.sub, fontWeight: rule.ok ? 600 : 400 }}>{rule.text}</span>
                </div>
              ))}
            </div>

            <button
              onClick={handleReset}
              style={{ width: "100%", height: 52, background: accentColor, border: "none", borderRadius: 14, color: "white", fontSize: 16, fontWeight: 700, cursor: "pointer", ...TJ }}>
              تغيير كلمة المرور
            </button>
          </div>
        </>
      )}
    </div>
  );
}

export function TenantForgotPasswordScreen() {
  return <ForgotPasswordBase accentColor={TEAL} logoFill={TEAL} />;
}

export function OwnerForgotPasswordScreen() {
  return <ForgotPasswordBase accentColor={GOLD} logoFill={GOLD} />;
}
