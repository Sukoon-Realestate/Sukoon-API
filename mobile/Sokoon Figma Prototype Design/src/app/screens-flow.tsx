import React, { useState } from "react";
import {
  Phone, Lock, Eye, EyeOff, User, Mail, ArrowLeft, ChevronRight,
  Bell, CheckCircle, Home, Building2, Key, Shield, Camera,
  Globe, Moon, Trash2, LogOut, Edit2, AlertCircle, Info,
  ToggleLeft, ToggleRight, FileText, HelpCircle, MessageCircle,
} from "lucide-react";
import {
  C, TJ as tj, PrimaryBtn, OutlineBtn, Card, StatusBar,
  TenantNav, OwnerNav, TextInput, Badge,
} from "./design-system";

const W = 390, H = 844;
const base: React.CSSProperties = {
  width: W, height: H, background: C.bg, ...tj, direction: "rtl",
  overflow: "hidden", position: "relative", fontFamily: "Tajawal, sans-serif",
};

// ── Splash Screen ────────────────────────────────────────────────────
export function SplashScreen() {
  return (
    <div style={{ ...base, background: `linear-gradient(160deg, ${C.teal} 0%, #065F57 100%)`, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center" }}>
      {/* Logo mark */}
      <div style={{ width: 96, height: 96, borderRadius: 28, background: "rgba(255,255,255,0.18)", display: "flex", alignItems: "center", justifyContent: "center", marginBottom: 28, backdropFilter: "blur(4px)" }}>
        <svg width="52" height="52" viewBox="0 0 52 52" fill="none">
          <path d="M26,5 L44,22 L40,22 L40,46 L12,46 L12,22 L8,22 Z" fill="white"/>
          <rect x="16" y="28" width="7" height="6" rx="2" fill={C.teal}/>
          <rect x="29" y="28" width="7" height="6" rx="2" fill={C.teal}/>
          <path d="M21,46 L21,38 Q26,32 31,38 L31,46 Z" fill={C.teal}/>
        </svg>
      </div>
      <h1 style={{ color: "white", fontSize: 44, fontWeight: 900, margin: "0 0 6px", letterSpacing: -1 }}>سكون</h1>
      <p style={{ color: "rgba(255,255,255,0.75)", fontSize: 18, margin: "0 0 6px", letterSpacing: 3, fontWeight: 400 }}>Sokoon</p>
      <p style={{ color: "rgba(255,255,255,0.5)", fontSize: 14, margin: 0 }}>ابحث عن مسكنك بأمان وراحة</p>
      {/* Loading dots */}
      <div style={{ display: "flex", gap: 6, marginTop: 64 }}>
        {[1, 2, 3].map(i => (
          <div key={i} style={{ width: 7, height: 7, borderRadius: "50%", background: i === 1 ? "white" : "rgba(255,255,255,0.35)" }} />
        ))}
      </div>
    </div>
  );
}

// ── Role Select Screen ───────────────────────────────────────────────
export function RoleSelectScreen() {
  const [selected, setSelected] = useState<string | null>(null);
  return (
    <div style={base}>
      <StatusBar />
      <div style={{ padding: "48px 24px 24px" }}>
        <div style={{ width: 52, height: 52, borderRadius: 16, background: C.tealLight, display: "flex", alignItems: "center", justifyContent: "center", marginBottom: 28 }}>
          <Home size={24} color={C.teal} />
        </div>
        <h1 style={{ fontSize: 28, fontWeight: 900, color: C.navy, margin: "0 0 8px" }}>أنت...</h1>
        <p style={{ fontSize: 15, color: C.gray, margin: "0 0 36px" }}>اختر نوع حسابك للمتابعة</p>

        <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
          {/* Tenant */}
          <button onClick={() => setSelected("tenant")} style={{
            background: "white", borderRadius: 20, padding: "24px 20px",
            border: `2px solid ${selected === "tenant" ? C.teal : C.border}`,
            cursor: "pointer", textAlign: "right", direction: "rtl",
            boxShadow: selected === "tenant" ? `0 0 0 4px ${C.tealLight}` : "0 2px 8px rgba(0,0,0,0.06)",
            transition: "all 0.18s",
          }}>
            <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
              <div style={{ width: 56, height: 56, borderRadius: 16, background: C.tealLight, display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
                <Home size={26} color={C.teal} />
              </div>
              <div style={{ flex: 1 }}>
                <p style={{ fontSize: 18, fontWeight: 900, color: C.navy, margin: "0 0 4px" }}>مستأجر</p>
                <p style={{ fontSize: 13, color: C.gray, margin: 0 }}>أبحث عن شقة أو وحدة للإيجار</p>
              </div>
              {selected === "tenant" && <CheckCircle size={22} color={C.teal} />}
            </div>
          </button>

          {/* Owner */}
          <button onClick={() => setSelected("owner")} style={{
            background: "white", borderRadius: 20, padding: "24px 20px",
            border: `2px solid ${selected === "owner" ? C.gold : C.border}`,
            cursor: "pointer", textAlign: "right", direction: "rtl",
            boxShadow: selected === "owner" ? `0 0 0 4px ${C.goldLight}` : "0 2px 8px rgba(0,0,0,0.06)",
            transition: "all 0.18s",
          }}>
            <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
              <div style={{ width: 56, height: 56, borderRadius: 16, background: C.goldLight, display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
                <Key size={26} color={C.gold} />
              </div>
              <div style={{ flex: 1 }}>
                <p style={{ fontSize: 18, fontWeight: 900, color: C.navy, margin: "0 0 4px" }}>مالك عقار</p>
                <p style={{ fontSize: 13, color: C.gray, margin: 0 }}>أعرض وحداتي للإيجار وأدير طلباتي</p>
              </div>
              {selected === "owner" && <CheckCircle size={22} color={C.gold} />}
            </div>
          </button>
        </div>

        <div style={{ marginTop: 32 }}>
          <PrimaryBtn text="متابعة" />
        </div>
      </div>
    </div>
  );
}

// ── Tenant Login Screen ──────────────────────────────────────────────
export function TenantLoginScreen() {
  const [show, setShow] = useState(false);
  return (
    <div style={base}>
      <StatusBar />
      <div style={{ padding: "36px 24px" }}>
        {/* Mini logo */}
        <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 36 }}>
          <div style={{ width: 40, height: 40, borderRadius: 12, background: C.teal, display: "flex", alignItems: "center", justifyContent: "center" }}>
            <Home size={20} color="white" />
          </div>
          <span style={{ fontSize: 20, fontWeight: 900, color: C.navy }}>سكون</span>
        </div>

        <h2 style={{ fontSize: 26, fontWeight: 900, color: C.navy, margin: "0 0 6px" }}>تسجيل الدخول</h2>
        <p style={{ fontSize: 14, color: C.gray, margin: "0 0 32px" }}>أهلاً بعودتك! سجّل دخولك للمتابعة</p>

        <div style={{ display: "flex", flexDirection: "column", gap: 16, marginBottom: 24 }}>
          <TextInput label="رقم الهاتف" placeholder="01xxxxxxxxx" />
          <div style={{ position: "relative" }}>
            <TextInput label="كلمة المرور" placeholder="••••••••" type={show ? "text" : "password"} />
            <button onClick={() => setShow(!show)} style={{ position: "absolute", left: 14, top: 38, background: "none", border: "none", cursor: "pointer", color: C.gray }}>
              {show ? <EyeOff size={18} /> : <Eye size={18} />}
            </button>
          </div>
        </div>

        <p style={{ fontSize: 13, color: C.teal, textAlign: "left", margin: "0 0 24px", cursor: "pointer" }}>نسيت كلمة المرور؟</p>

        <PrimaryBtn text="تسجيل الدخول" />

        <div style={{ display: "flex", alignItems: "center", gap: 12, margin: "20px 0" }}>
          <div style={{ flex: 1, height: 1, background: C.border }} />
          <span style={{ fontSize: 12, color: C.gray }}>أو</span>
          <div style={{ flex: 1, height: 1, background: C.border }} />
        </div>

        <OutlineBtn text="إنشاء حساب جديد" />

        <p style={{ fontSize: 12, color: C.gray, textAlign: "center", marginTop: 24, lineHeight: 1.6 }}>
          بتسجيل دخولك، أنت توافق على
          {" "}<span style={{ color: C.teal }}>الشروط والأحكام</span>{" "}
          و<span style={{ color: C.teal }}>سياسة الخصوصية</span>
        </p>
      </div>
    </div>
  );
}

// ── Tenant Register Screen ───────────────────────────────────────────
export function TenantRegisterScreen() {
  return (
    <div style={base}>
      <StatusBar />
      <div style={{ padding: "28px 24px" }}>
        <button style={{ background: "none", border: "none", cursor: "pointer", marginBottom: 20, padding: 0 }}>
          <ArrowLeft size={22} color={C.navy} style={{ transform: "scaleX(-1)" }} />
        </button>

        <h2 style={{ fontSize: 24, fontWeight: 900, color: C.navy, margin: "0 0 6px" }}>إنشاء حساب</h2>
        <p style={{ fontSize: 14, color: C.gray, margin: "0 0 28px" }}>بضع خطوات وتبدأ رحلة البحث عن مسكنك</p>

        <div style={{ display: "flex", flexDirection: "column", gap: 14, marginBottom: 24 }}>
          <TextInput label="الاسم الكامل" placeholder="محمد أحمد" />
          <TextInput label="رقم الهاتف" placeholder="01xxxxxxxxx" />
          <TextInput label="البريد الإلكتروني" placeholder="example@email.com" />
          <TextInput label="كلمة المرور" placeholder="••••••••" type="password" />
          <TextInput label="تأكيد كلمة المرور" placeholder="••••••••" type="password" />
        </div>

        <PrimaryBtn text="إنشاء الحساب" />

        <p style={{ fontSize: 12, color: C.gray, textAlign: "center", marginTop: 20, lineHeight: 1.6 }}>
          لديك حساب بالفعل؟{" "}
          <span style={{ color: C.teal, fontWeight: 700 }}>تسجيل الدخول</span>
        </p>
      </div>
    </div>
  );
}

// ── Owner Login Screen ───────────────────────────────────────────────
export function OwnerLoginScreen() {
  return (
    <div style={base}>
      <StatusBar />
      <div style={{ padding: "36px 24px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 36 }}>
          <div style={{ width: 40, height: 40, borderRadius: 12, background: C.gold, display: "flex", alignItems: "center", justifyContent: "center" }}>
            <Key size={20} color="white" />
          </div>
          <span style={{ fontSize: 20, fontWeight: 900, color: C.navy }}>سكون — مالك</span>
        </div>

        <h2 style={{ fontSize: 26, fontWeight: 900, color: C.navy, margin: "0 0 6px" }}>دخول المالك</h2>
        <p style={{ fontSize: 14, color: C.gray, margin: "0 0 32px" }}>سجّل دخولك لإدارة عقاراتك وطلباتك</p>

        <div style={{ display: "flex", flexDirection: "column", gap: 16, marginBottom: 24 }}>
          <TextInput label="رقم الهاتف" placeholder="01xxxxxxxxx" />
          <TextInput label="كلمة المرور" placeholder="••••••••" type="password" />
        </div>

        <p style={{ fontSize: 13, color: C.gold, textAlign: "left", margin: "0 0 24px", cursor: "pointer" }}>نسيت كلمة المرور؟</p>

        <button style={{ width: "100%", height: 52, borderRadius: 14, background: C.gold, border: "none", color: "white", fontSize: 16, fontWeight: 800, cursor: "pointer", ...tj }}>
          تسجيل الدخول
        </button>

        <div style={{ display: "flex", alignItems: "center", gap: 12, margin: "20px 0" }}>
          <div style={{ flex: 1, height: 1, background: C.border }} />
          <span style={{ fontSize: 12, color: C.gray }}>أو</span>
          <div style={{ flex: 1, height: 1, background: C.border }} />
        </div>

        <button style={{ width: "100%", height: 52, borderRadius: 14, background: "white", border: `1.5px solid ${C.gold}`, color: C.gold, fontSize: 16, fontWeight: 800, cursor: "pointer", ...tj }}>
          إنشاء حساب مالك
        </button>
      </div>
    </div>
  );
}

// ── Owner Register Screen ────────────────────────────────────────────
export function OwnerRegisterScreen() {
  return (
    <div style={base}>
      <StatusBar />
      <div style={{ padding: "28px 24px" }}>
        <button style={{ background: "none", border: "none", cursor: "pointer", marginBottom: 20, padding: 0 }}>
          <ArrowLeft size={22} color={C.navy} style={{ transform: "scaleX(-1)" }} />
        </button>

        <h2 style={{ fontSize: 24, fontWeight: 900, color: C.navy, margin: "0 0 6px" }}>تسجيل مالك جديد</h2>
        <p style={{ fontSize: 14, color: C.gray, margin: "0 0 28px" }}>أنشئ حسابك لبدء عرض عقاراتك</p>

        <div style={{ display: "flex", flexDirection: "column", gap: 14, marginBottom: 24 }}>
          <TextInput label="الاسم الكامل" placeholder="محمد أحمد" />
          <TextInput label="رقم الهاتف" placeholder="01xxxxxxxxx" />
          <TextInput label="البريد الإلكتروني" placeholder="example@email.com" />
          <TextInput label="كلمة المرور" placeholder="••••••••" type="password" />
          {/* National ID */}
          <div>
            <p style={{ fontSize: 13, fontWeight: 700, color: C.navy, margin: "0 0 8px" }}>الرقم القومي (اختياري)</p>
            <div style={{ background: "white", borderRadius: 12, padding: "14px 16px", border: `1px solid ${C.border}`, display: "flex", alignItems: "center", gap: 10 }}>
              <Shield size={16} color={C.gray} />
              <input placeholder="يُستخدم لاحقاً في التوثيق" style={{ flex: 1, border: "none", background: "none", fontSize: 14, color: C.navy, outline: "none", textAlign: "right", fontFamily: "Tajawal, sans-serif" }} />
            </div>
          </div>
        </div>

        <button style={{ width: "100%", height: 52, borderRadius: 14, background: C.gold, border: "none", color: "white", fontSize: 16, fontWeight: 800, cursor: "pointer", ...tj }}>
          إنشاء الحساب
        </button>
      </div>
    </div>
  );
}

// ── Notification Detail Screen ───────────────────────────────────────
export function NotifDetailScreen() {
  return (
    <div style={base}>
      <StatusBar />
      <div style={{ padding: "16px 20px", display: "flex", alignItems: "center", gap: 12, borderBottom: `1px solid ${C.border}` }}>
        <button style={{ background: "none", border: "none", cursor: "pointer" }}><ArrowLeft size={22} color={C.navy} style={{ transform: "scaleX(-1)" }} /></button>
        <h3 style={{ fontSize: 17, fontWeight: 800, color: C.navy, margin: 0, flex: 1, textAlign: "center" }}>تفاصيل الإشعار</h3>
        <div style={{ width: 22 }} />
      </div>
      <div style={{ padding: "28px 20px" }}>
        <div style={{ background: "white", borderRadius: 20, padding: 24, boxShadow: "0 2px 12px rgba(0,0,0,0.06)" }}>
          <div style={{ width: 56, height: 56, borderRadius: 16, background: C.greenLight, display: "flex", alignItems: "center", justifyContent: "center", marginBottom: 20 }}>
            <CheckCircle size={28} color={C.green} />
          </div>
          <p style={{ fontSize: 11, fontWeight: 700, color: C.gray, margin: "0 0 8px", textTransform: "uppercase", letterSpacing: 1 }}>حجز زيارة</p>
          <h2 style={{ fontSize: 20, fontWeight: 900, color: C.navy, margin: "0 0 12px" }}>تم قبول طلب زيارتك</h2>
          <p style={{ fontSize: 14, color: C.gray, lineHeight: 1.7, margin: "0 0 20px" }}>
            وافق المالك أحمد محمد على موعد الزيارة. يُرجى الحضور في الوقت المحدد للاطلاع على الشقة.
          </p>
          <div style={{ background: C.tealLight, borderRadius: 12, padding: "14px 16px", marginBottom: 20 }}>
            <p style={{ fontSize: 13, fontWeight: 800, color: C.teal, margin: "0 0 4px" }}>تفاصيل الموعد</p>
            <p style={{ fontSize: 13, color: C.navy, margin: 0 }}>الثلاثاء 14 يناير · 3:00 م</p>
            <p style={{ fontSize: 12, color: C.gray, margin: "4px 0 0" }}>مدينة نصر — شارع عباس العقاد</p>
          </div>
          <p style={{ fontSize: 11, color: C.gray, margin: 0 }}>منذ 5 دقائق · 2:55 م</p>
        </div>
        <div style={{ marginTop: 20, display: "flex", gap: 12 }}>
          <div style={{ flex: 1 }}><PrimaryBtn text="عرض الزيارة" /></div>
          <div style={{ flex: 1 }}><OutlineBtn text="تجاهل" /></div>
        </div>
      </div>
    </div>
  );
}

// ── Notifications Empty Screen ───────────────────────────────────────
export function NotifEmptyScreen() {
  return (
    <div style={base}>
      <StatusBar />
      <div style={{ padding: "16px 20px", borderBottom: `1px solid ${C.border}` }}>
        <h3 style={{ fontSize: 18, fontWeight: 900, color: C.navy, margin: 0 }}>الإشعارات</h3>
      </div>
      <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", padding: "80px 40px", textAlign: "center" }}>
        <div style={{ width: 88, height: 88, borderRadius: 28, background: C.border, display: "flex", alignItems: "center", justifyContent: "center", marginBottom: 24 }}>
          <Bell size={40} color={C.gray} />
        </div>
        <h3 style={{ fontSize: 20, fontWeight: 900, color: C.navy, margin: "0 0 10px" }}>لا إشعارات حالياً</h3>
        <p style={{ fontSize: 14, color: C.gray, margin: "0 0 32px", lineHeight: 1.7 }}>
          ستظهر هنا إشعاراتك عند وجود تحديثات على طلباتك أو عقاراتك
        </p>
        <OutlineBtn text="استكشف العقارات" />
      </div>
    </div>
  );
}

// ── Tenant Edit Profile Screen ───────────────────────────────────────
export function TenantEditProfileScreen() {
  return (
    <div style={base}>
      <StatusBar />
      <div style={{ padding: "16px 20px", display: "flex", alignItems: "center", gap: 12, borderBottom: `1px solid ${C.border}` }}>
        <button style={{ background: "none", border: "none", cursor: "pointer" }}><ArrowLeft size={22} color={C.navy} style={{ transform: "scaleX(-1)" }} /></button>
        <h3 style={{ fontSize: 17, fontWeight: 800, color: C.navy, margin: 0, flex: 1, textAlign: "center" }}>تعديل الملف</h3>
        <button style={{ fontSize: 14, fontWeight: 700, color: C.teal, background: "none", border: "none", cursor: "pointer" }}>حفظ</button>
      </div>
      <div style={{ overflowY: "auto", padding: "24px 20px" }}>
        {/* Avatar */}
        <div style={{ display: "flex", flexDirection: "column", alignItems: "center", marginBottom: 28 }}>
          <div style={{ position: "relative" }}>
            <div style={{ width: 88, height: 88, borderRadius: "50%", background: C.teal, display: "flex", alignItems: "center", justifyContent: "center" }}>
              <span style={{ color: "white", fontSize: 32, fontWeight: 900 }}>م</span>
            </div>
            <div style={{ position: "absolute", bottom: 0, left: 0, width: 28, height: 28, borderRadius: "50%", background: C.teal, border: "2px solid white", display: "flex", alignItems: "center", justifyContent: "center" }}>
              <Camera size={13} color="white" />
            </div>
          </div>
          <p style={{ fontSize: 13, color: C.teal, fontWeight: 700, marginTop: 10, cursor: "pointer" }}>تغيير الصورة</p>
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
          <TextInput label="الاسم الكامل" placeholder="محمد أحمد" />
          <TextInput label="رقم الهاتف" placeholder="010****432" />
          <TextInput label="البريد الإلكتروني" placeholder="m.ahmed@email.com" />
          <div>
            <p style={{ fontSize: 13, fontWeight: 700, color: C.navy, margin: "0 0 8px" }}>تاريخ الميلاد</p>
            <div style={{ background: "white", borderRadius: 12, padding: "14px 16px", border: `1px solid ${C.border}`, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <span style={{ fontSize: 14, color: C.navy }}>15 مارس 1995</span>
              <ChevronRight size={16} color={C.gray} style={{ transform: "scaleX(-1)" }} />
            </div>
          </div>
          <div>
            <p style={{ fontSize: 13, fontWeight: 700, color: C.navy, margin: "0 0 8px" }}>الجنس</p>
            <div style={{ background: "white", borderRadius: 12, padding: "14px 16px", border: `1px solid ${C.border}`, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <span style={{ fontSize: 14, color: C.navy }}>ذكر</span>
              <ChevronRight size={16} color={C.gray} style={{ transform: "scaleX(-1)" }} />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// ── Owner Edit Profile Screen ────────────────────────────────────────
export function OwnerEditProfileScreen() {
  return (
    <div style={base}>
      <StatusBar />
      <div style={{ padding: "16px 20px", display: "flex", alignItems: "center", gap: 12, borderBottom: `1px solid ${C.border}` }}>
        <button style={{ background: "none", border: "none", cursor: "pointer" }}><ArrowLeft size={22} color={C.navy} style={{ transform: "scaleX(-1)" }} /></button>
        <h3 style={{ fontSize: 17, fontWeight: 800, color: C.navy, margin: 0, flex: 1, textAlign: "center" }}>تعديل ملف المالك</h3>
        <button style={{ fontSize: 14, fontWeight: 700, color: C.gold, background: "none", border: "none", cursor: "pointer" }}>حفظ</button>
      </div>
      <div style={{ overflowY: "auto", padding: "24px 20px" }}>
        {/* Avatar */}
        <div style={{ display: "flex", flexDirection: "column", alignItems: "center", marginBottom: 28 }}>
          <div style={{ position: "relative" }}>
            <div style={{ width: 88, height: 88, borderRadius: "50%", background: C.gold, display: "flex", alignItems: "center", justifyContent: "center" }}>
              <span style={{ color: "white", fontSize: 32, fontWeight: 900 }}>أ</span>
            </div>
            <div style={{ position: "absolute", bottom: 0, left: 0, width: 28, height: 28, borderRadius: "50%", background: C.gold, border: "2px solid white", display: "flex", alignItems: "center", justifyContent: "center" }}>
              <Camera size={13} color="white" />
            </div>
          </div>
          <p style={{ fontSize: 13, color: C.gold, fontWeight: 700, marginTop: 10, cursor: "pointer" }}>تغيير الصورة</p>
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
          <TextInput label="الاسم الكامل" placeholder="أحمد محمد" />
          <TextInput label="رقم الهاتف" placeholder="011****876" />
          <TextInput label="البريد الإلكتروني" placeholder="a.mohamed@email.com" />
          <div>
            <p style={{ fontSize: 13, fontWeight: 700, color: C.navy, margin: "0 0 8px" }}>المدينة</p>
            <div style={{ background: "white", borderRadius: 12, padding: "14px 16px", border: `1px solid ${C.border}`, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <span style={{ fontSize: 14, color: C.navy }}>القاهرة</span>
              <ChevronRight size={16} color={C.gray} style={{ transform: "scaleX(-1)" }} />
            </div>
          </div>
          {/* Verified badge */}
          <div style={{ background: C.greenLight, borderRadius: 14, padding: "14px 16px", display: "flex", alignItems: "center", gap: 10 }}>
            <CheckCircle size={20} color={C.green} />
            <div>
              <p style={{ fontSize: 13, fontWeight: 800, color: C.green, margin: 0 }}>حساب موثّق</p>
              <p style={{ fontSize: 11, color: C.gray, margin: "2px 0 0" }}>تم التحقق من هويتك بنجاح</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// ── Settings Privacy Screen ──────────────────────────────────────────
export function SettingsPrivacyScreen() {
  const [notifs, setNotifs] = useState(true);
  const [loc, setLoc] = useState(false);
  const [dark, setDark] = useState(false);
  const Toggle = ({ on, onToggle }: { on: boolean; onToggle: () => void }) => (
    <button onClick={onToggle} style={{ background: "none", border: "none", cursor: "pointer", padding: 0 }}>
      {on
        ? <ToggleRight size={28} color={C.teal} />
        : <ToggleLeft size={28} color={C.gray} />}
    </button>
  );
  const Row = ({ icon: I, label, sub, toggle, onToggle, arrow }: { icon: React.ComponentType<{ size?: number; color?: string }>; label: string; sub?: string; toggle?: boolean; onToggle?: () => void; arrow?: boolean }) => (
    <div style={{ background: "white", padding: "16px 16px", display: "flex", alignItems: "center", gap: 14, borderBottom: `1px solid ${C.border}` }}>
      <div style={{ width: 38, height: 38, borderRadius: 10, background: C.tealLight, display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
        <I size={18} color={C.teal} />
      </div>
      <div style={{ flex: 1 }}>
        <p style={{ fontSize: 14, fontWeight: 700, color: C.navy, margin: 0 }}>{label}</p>
        {sub && <p style={{ fontSize: 11, color: C.gray, margin: "2px 0 0" }}>{sub}</p>}
      </div>
      {toggle !== undefined && <Toggle on={toggle} onToggle={onToggle!} />}
      {arrow && <ChevronRight size={18} color={C.gray} style={{ transform: "scaleX(-1)" }} />}
    </div>
  );
  return (
    <div style={base}>
      <StatusBar />
      <div style={{ padding: "16px 20px", display: "flex", alignItems: "center", gap: 12, borderBottom: `1px solid ${C.border}` }}>
        <button style={{ background: "none", border: "none", cursor: "pointer" }}><ArrowLeft size={22} color={C.navy} style={{ transform: "scaleX(-1)" }} /></button>
        <h3 style={{ fontSize: 17, fontWeight: 800, color: C.navy, margin: 0 }}>الخصوصية والأمان</h3>
      </div>
      <div style={{ overflowY: "auto" }}>
        <p style={{ fontSize: 11, fontWeight: 800, color: C.gray, padding: "16px 20px 8px", letterSpacing: 0.8, textTransform: "uppercase" }}>الإشعارات</p>
        <Row icon={Bell} label="الإشعارات" sub="تلقّي تنبيهات الطلبات والرسائل" toggle={notifs} onToggle={() => setNotifs(!notifs)} />
        <Row icon={Globe} label="الموقع الجغرافي" sub="يُستخدم لعرض العقارات القريبة" toggle={loc} onToggle={() => setLoc(!loc)} />

        <p style={{ fontSize: 11, fontWeight: 800, color: C.gray, padding: "16px 20px 8px", letterSpacing: 0.8, textTransform: "uppercase" }}>المظهر</p>
        <Row icon={Moon} label="الوضع الداكن" sub="تجربة أكثر راحة في الإضاءة المنخفضة" toggle={dark} onToggle={() => setDark(!dark)} />

        <p style={{ fontSize: 11, fontWeight: 800, color: C.gray, padding: "16px 20px 8px", letterSpacing: 0.8, textTransform: "uppercase" }}>الحساب</p>
        <Row icon={Lock} label="تغيير كلمة المرور" arrow />
        <Row icon={Shield} label="التحقق بخطوتين" sub="حماية إضافية لحسابك" arrow />
        <Row icon={FileText} label="الشروط والأحكام" arrow />
        <Row icon={Info} label="سياسة الخصوصية" arrow />

        <p style={{ fontSize: 11, fontWeight: 800, color: "#EF4444", padding: "16px 20px 8px", letterSpacing: 0.8, textTransform: "uppercase" }}>خطر</p>
        <div style={{ background: "white", padding: "16px 16px", display: "flex", alignItems: "center", gap: 14 }}>
          <div style={{ width: 38, height: 38, borderRadius: 10, background: "#FFF1F1", display: "flex", alignItems: "center", justifyContent: "center" }}>
            <Trash2 size={18} color="#EF4444" />
          </div>
          <p style={{ fontSize: 14, fontWeight: 700, color: "#EF4444", margin: 0, flex: 1 }}>حذف الحساب</p>
          <ChevronRight size={18} color="#EF4444" style={{ transform: "scaleX(-1)" }} />
        </div>
      </div>
    </div>
  );
}

// ── Owner Settings Screen ────────────────────────────────────────────
export function OwnerSettingsScreen() {
  const [notifs, setNotifs] = useState(true);
  const Row = ({ label, sub, accent = C.teal, arrow = true }: { label: string; sub?: string; accent?: string; arrow?: boolean }) => (
    <div style={{ background: "white", padding: "16px 16px", display: "flex", alignItems: "center", gap: 14, borderBottom: `1px solid ${C.border}` }}>
      <div style={{ flex: 1 }}>
        <p style={{ fontSize: 14, fontWeight: 700, color: accent === "#EF4444" ? "#EF4444" : C.navy, margin: 0 }}>{label}</p>
        {sub && <p style={{ fontSize: 11, color: C.gray, margin: "2px 0 0" }}>{sub}</p>}
      </div>
      {arrow && <ChevronRight size={18} color={C.gray} style={{ transform: "scaleX(-1)" }} />}
    </div>
  );
  return (
    <div style={base}>
      <StatusBar />
      <div style={{ padding: "16px 20px", display: "flex", alignItems: "center", gap: 12, borderBottom: `1px solid ${C.border}` }}>
        <button style={{ background: "none", border: "none", cursor: "pointer" }}><ArrowLeft size={22} color={C.navy} style={{ transform: "scaleX(-1)" }} /></button>
        <h3 style={{ fontSize: 17, fontWeight: 800, color: C.navy, margin: 0, flex: 1, textAlign: "center" }}>الإعدادات</h3>
        <div style={{ width: 22 }} />
      </div>
      <div style={{ overflowY: "auto" }}>
        <p style={{ fontSize: 11, fontWeight: 800, color: C.gray, padding: "16px 20px 8px", textTransform: "uppercase", letterSpacing: 0.8 }}>الحساب</p>
        <Row label="تعديل الملف الشخصي" sub="اسمك ورقمك وصورتك" />
        <Row label="تغيير كلمة المرور" />
        <Row label="التحقق بخطوتين" sub="حماية إضافية" />

        <p style={{ fontSize: 11, fontWeight: 800, color: C.gray, padding: "16px 20px 8px", textTransform: "uppercase", letterSpacing: 0.8 }}>الإشعارات</p>
        <div style={{ background: "white", padding: "16px 16px", display: "flex", alignItems: "center", gap: 14, borderBottom: `1px solid ${C.border}` }}>
          <div style={{ flex: 1 }}>
            <p style={{ fontSize: 14, fontWeight: 700, color: C.navy, margin: 0 }}>الإشعارات</p>
            <p style={{ fontSize: 11, color: C.gray, margin: "2px 0 0" }}>طلبات الزيارة والرسائل</p>
          </div>
          <button onClick={() => setNotifs(!notifs)} style={{ background: "none", border: "none", cursor: "pointer", padding: 0 }}>
            {notifs ? <ToggleRight size={28} color={C.gold} /> : <ToggleLeft size={28} color={C.gray} />}
          </button>
        </div>

        <p style={{ fontSize: 11, fontWeight: 800, color: C.gray, padding: "16px 20px 8px", textTransform: "uppercase", letterSpacing: 0.8 }}>قانوني</p>
        <Row label="الشروط والأحكام" />
        <Row label="سياسة الخصوصية" />
        <Row label="عن سكون" />

        <p style={{ fontSize: 11, fontWeight: 800, color: "#EF4444", padding: "16px 20px 8px", textTransform: "uppercase", letterSpacing: 0.8 }}>خطر</p>
        <Row label="حذف الحساب" sub="سيتم حذف بياناتك نهائياً" accent="#EF4444" />
      </div>
    </div>
  );
}
