import React, { useState } from "react";
import {
  Home, Search, Heart, MessageCircle, Bell, User, Shield, Lock,
  Camera, Upload, CheckCircle, AlertCircle, Clock, Eye, EyeOff,
  Key, Building2, MapPin, Star, Filter, ChevronDown, X, Plus, Minus,
  Check, AlertTriangle, FileText, Settings, Users, BarChart2,
  LogOut, Calendar, Send, Mic, Image as ImageIcon, Edit2, Trash2,
  RefreshCw, Wifi, ArrowLeft, Map, ZoomIn,
  RotateCw, Award, Info, Menu, Share2,
  ChevronRight, ChevronLeft, Phone
} from "lucide-react";

// ─────────────────────────────────────────────
//  BRAND TOKENS
// ─────────────────────────────────────────────
const C = {
  teal: "#0F766E", tealLight: "#E0F2F1",
  bg: "#FAFAF8", border: "#EEF0F3",
  green: "#22C55E", greenLight: "#EAFBF1",
  amber: "#F59E0B", amberLight: "#FFF7E6",
  red: "#EF4444", redLight: "#FFF1F1",
  blue: "#2563EB", blueLight: "#EEF5FF",
  gold: "#D6A84F", goldLight: "#FFF8E7",
  navy: "#111827", gray: "#6B7280",
  white: "#FFFFFF",
  dark: "#0F172A", darkCard: "#1E293B", darkBorder: "#334155", darkMuted: "#94A3B8",
};
const TJ: React.CSSProperties = { fontFamily: "Tajawal, sans-serif" };

// ─────────────────────────────────────────────
//  SHARED MICRO-COMPONENTS
// ─────────────────────────────────────────────
type BadgeType = "verified" | "pending" | "rejected" | "approved" | "hidden" | "rented";

function Badge({ type, text }: { type: BadgeType; text?: string }) {
  const cfg: Record<BadgeType, { bg: string; color: string; Icon: React.ElementType; label: string }> = {
    verified: { bg: C.goldLight, color: C.gold, Icon: CheckCircle, label: "موثّق" },
    pending:  { bg: C.amberLight, color: C.amber, Icon: Clock, label: "قيد المراجعة" },
    rejected: { bg: C.redLight,  color: C.red,  Icon: AlertCircle, label: "مرفوض" },
    approved: { bg: C.greenLight, color: C.green, Icon: CheckCircle, label: "مقبول" },
    hidden:   { bg: "#F3F4F6", color: C.gray, Icon: EyeOff, label: "مخفي" },
    rented:   { bg: C.blueLight, color: C.blue, Icon: Key, label: "تم تأجيره" },
  };
  const { bg, color, Icon, label } = cfg[type];
  return (
    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold"
      style={{ backgroundColor: bg, color }}>
      <Icon size={10} />{text ?? label}
    </span>
  );
}

function PrimaryBtn({ text, onClick, disabled, danger }: { text: string; onClick?: () => void; disabled?: boolean; danger?: boolean }) {
  return (
    <button onClick={onClick} disabled={disabled}
      className="w-full flex items-center justify-center py-4 rounded-2xl font-bold text-base transition-all"
      style={{ ...TJ, backgroundColor: disabled ? "#D1D5DB" : danger ? C.red : C.teal, color: C.white }}>
      {text}
    </button>
  );
}

function OutlineBtn({ text, onClick }: { text: string; onClick?: () => void }) {
  return (
    <button onClick={onClick}
      className="w-full flex items-center justify-center py-4 rounded-2xl font-bold text-base"
      style={{ ...TJ, backgroundColor: C.white, color: C.navy, border: `1px solid ${C.border}` }}>
      {text}
    </button>
  );
}

function TextInput({ label, placeholder, type = "text", error }: { label: string; placeholder: string; type?: string; error?: string }) {
  return (
    <div className="flex flex-col gap-1.5">
      {label && <label className="text-sm font-bold" style={{ ...TJ, color: C.navy }}>{label}</label>}
      <input type={type} placeholder={placeholder} dir="rtl" readOnly
        className="w-full px-4 py-3.5 rounded-2xl border text-sm outline-none"
        style={{ borderColor: error ? C.red : C.border, backgroundColor: C.white, ...TJ, color: C.navy }} />
      {error && <p className="text-xs" style={{ ...TJ, color: C.red }}>{error}</p>}
    </div>
  );
}

function Card({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  return (
    <div className={`rounded-3xl p-4 ${className}`}
      style={{ backgroundColor: C.white, border: `1px solid ${C.border}`, boxShadow: "0 2px 8px rgba(0,0,0,0.04)" }}>
      {children}
    </div>
  );
}

function SectionHead({ title, action }: { title: string; action?: string }) {
  return (
    <div className="flex items-center justify-between mb-3" dir="rtl">
      <h2 className="font-bold" style={{ ...TJ, color: C.navy, fontSize: 17 }}>{title}</h2>
      {action && <span className="text-sm font-bold" style={{ ...TJ, color: C.teal }}>{action}</span>}
    </div>
  );
}

function PrivacyBanner({ text }: { text: string }) {
  return (
    <div className="flex items-center gap-2 px-4 py-3 rounded-2xl" style={{ backgroundColor: C.blueLight }}>
      <Lock size={13} style={{ color: C.blue, flexShrink: 0 }} />
      <p className="text-xs font-medium flex-1" style={{ ...TJ, color: C.blue }}>{text}</p>
    </div>
  );
}

function WarnBanner({ text, action }: { text: string; action?: string }) {
  return (
    <div className="flex items-center gap-2 px-4 py-3 rounded-2xl" style={{ backgroundColor: C.amberLight }}>
      <AlertTriangle size={13} style={{ color: C.amber, flexShrink: 0 }} />
      <p className="text-xs font-medium flex-1" style={{ ...TJ, color: "#92400E" }}>{text}</p>
      {action && <button className="text-xs font-bold flex-shrink-0" style={{ ...TJ, color: C.teal }}>{action}</button>}
    </div>
  );
}

function StatusBar({ dark: isDark = false }: { dark?: boolean }) {
  return (
    <div className="h-11 flex items-center justify-between px-6 flex-shrink-0">
      <span className="text-sm font-black" style={{ color: isDark ? C.white : C.navy }}>9:41</span>
      <div className="w-24 h-5 rounded-full" style={{ backgroundColor: isDark ? "#334155" : "#1a1a1a" }} />
      <span className="text-xs font-black" style={{ color: isDark ? C.white : C.navy }}>●●●</span>
    </div>
  );
}

function StepProgress({ step, total }: { step: number; total: number }) {
  return (
    <div className="flex items-center gap-1.5 mb-5">
      {Array.from({ length: total }).map((_, i) => (
        <div key={i} className="flex-1 h-1.5 rounded-full" style={{ backgroundColor: i < step ? C.teal : C.border }} />
      ))}
      <span className="text-xs font-bold ml-1" style={{ ...TJ, color: C.gray }}>{step}/{total}</span>
    </div>
  );
}

function TenantNav({ active = "home" }: { active?: string }) {
  return (
    <div className="flex items-center justify-around px-2 py-2 flex-shrink-0"
      style={{ backgroundColor: C.white, borderTop: `1px solid ${C.border}` }}>
      {[{ id: "home", l: "الرئيسية", I: Home }, { id: "saved", l: "المحفوظات", I: Heart },
        { id: "chat", l: "الشات", I: MessageCircle }, { id: "notif", l: "الإشعارات", I: Bell }, { id: "profile", l: "الحساب", I: User }].map(({ id, l, I }) => (
        <button key={id} className="flex flex-col items-center gap-0.5 py-1 px-2">
          <I size={22} style={{ color: id === active ? C.teal : "#9CA3AF" }} strokeWidth={id === active ? 2.5 : 1.5} />
          <span className="font-semibold" style={{ ...TJ, color: id === active ? C.teal : "#9CA3AF", fontSize: 10 }}>{l}</span>
        </button>
      ))}
    </div>
  );
}

function OwnerNav({ active = "home" }: { active?: string }) {
  return (
    <div className="flex items-center justify-around px-2 py-2 flex-shrink-0"
      style={{ backgroundColor: C.white, borderTop: `1px solid ${C.border}` }}>
      {[{ id: "home", l: "الرئيسية", I: Home }, { id: "props", l: "عقاراتي", I: Building2 },
        { id: "requests", l: "الطلبات", I: Calendar }, { id: "chat", l: "الشات", I: MessageCircle }, { id: "more", l: "المزيد", I: Menu }].map(({ id, l, I }) => (
        <button key={id} className="flex flex-col items-center gap-0.5 py-1 px-2">
          <I size={22} style={{ color: id === active ? C.teal : "#9CA3AF" }} strokeWidth={id === active ? 2.5 : 1.5} />
          <span className="font-semibold" style={{ ...TJ, color: id === active ? C.teal : "#9CA3AF", fontSize: 10 }}>{l}</span>
        </button>
      ))}
    </div>
  );
}

function PropCard({ verified = true, saved = false, badge }: { verified?: boolean; saved?: boolean; badge?: BadgeType }) {
  return (
    <div className="rounded-3xl overflow-hidden" style={{ backgroundColor: C.white, border: `1px solid ${C.border}`, boxShadow: "0 2px 8px rgba(0,0,0,0.04)" }}>
      <div className="relative flex items-center justify-center" style={{ height: 170, backgroundColor: "#E2E8F0" }}>
        <Building2 size={40} style={{ color: "#94A3B8" }} />
        <button className="absolute top-3 left-3 w-8 h-8 rounded-full flex items-center justify-center" style={{ backgroundColor: "rgba(255,255,255,0.9)" }}>
          <Heart size={14} style={{ color: saved ? C.red : "#9CA3AF", fill: saved ? C.red : "none" }} />
        </button>
        <div className="absolute top-3 right-3">
          {badge ? <Badge type={badge} /> : verified ? <Badge type="verified" /> : null}
        </div>
        <span className="absolute bottom-3 right-3 px-2 py-0.5 rounded-lg text-xs font-bold text-white" style={{ backgroundColor: "rgba(0,0,0,0.55)" }}>1/8</span>
      </div>
      <div className="p-4" dir="rtl">
        <div className="flex items-start justify-between mb-1">
          <p className="font-black text-lg" style={{ ...TJ, color: C.teal }}>12,000 ج.م/شهر</p>
          <div className="flex items-center gap-1"><Star size={13} fill={C.amber} style={{ color: C.amber }} /><span className="text-sm font-bold" style={{ ...TJ, color: C.navy }}>4.8</span></div>
        </div>
        <p className="text-sm mb-1" style={{ ...TJ, color: C.navy }}>شقة مفروشة قريبة من عباس العقاد</p>
        <div className="flex items-center gap-1 mb-3"><MapPin size={11} style={{ color: C.gray }} /><span className="text-xs" style={{ ...TJ, color: C.gray }}>مدينة نصر، القاهرة</span></div>
        <div className="flex gap-2">
          {["3 غرف", "2 حمام", "120م²"].map((t, i) => (
            <span key={i} className="text-xs font-semibold px-2 py-1 rounded-lg" style={{ backgroundColor: C.bg, ...TJ, color: C.navy }}>{t}</span>
          ))}
        </div>
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════
//  AUTH SCREENS  (19 screens)
// ═══════════════════════════════════════════════

function SplashScreen() {
  return (
    <div className="flex flex-col h-full" style={{ backgroundColor: C.bg }}>
      <StatusBar />
      <div className="flex-1 flex flex-col items-center justify-center px-6 gap-8">
        <div className="flex flex-col items-center gap-5">
          <div className="w-24 h-24 rounded-3xl flex items-center justify-center" style={{ backgroundColor: C.tealLight }}>
            <div className="relative">
              <Home size={36} style={{ color: C.teal }} />
              <Shield size={16} style={{ color: C.teal, position: "absolute", bottom: -5, right: -10 }} />
            </div>
          </div>
          <div className="text-center">
            <h1 className="font-black mb-1" style={{ ...TJ, color: C.teal, fontSize: 56 }}>سكون</h1>
            <p className="text-xl font-bold mb-1" style={{ ...TJ, color: C.navy }}>سكن آمن، موثّق، ومن غير دوشة</p>
            <p className="text-sm" style={{ ...TJ, color: C.gray }}>دور على سكن أو اعرض عقارك بثقة</p>
          </div>
        </div>
        <div className="w-full flex flex-col gap-3">
          <PrimaryBtn text="ابدأ الآن" />
          <OutlineBtn text="لدي حساب بالفعل" />
        </div>
      </div>
      <div className="px-6 pb-8 flex items-center justify-center gap-2">
        <Lock size={11} style={{ color: C.gray }} />
        <p className="text-xs" style={{ ...TJ, color: C.gray }}>بياناتك محمية، ورقمك مخفي لحد ما توافق</p>
      </div>
    </div>
  );
}

function OnboardingScreen() {
  return (
    <div className="flex flex-col h-full" style={{ backgroundColor: C.bg }}>
      <StatusBar />
      <div className="flex-1 overflow-y-auto px-6 py-3">
        <div className="flex items-center justify-center py-5">
          <div className="w-28 h-28 rounded-full flex items-center justify-center" style={{ backgroundColor: C.tealLight }}>
            <Shield size={52} style={{ color: C.teal }} />
          </div>
        </div>
        <div className="text-center mb-6" dir="rtl">
          <h1 className="text-2xl font-black mb-1" style={{ ...TJ, color: C.navy }}>الثقة هي أساس سكون</h1>
          <p className="text-sm" style={{ ...TJ, color: C.gray }}>بنيناه عشان التعاملات تكون أأمن وأسهل</p>
        </div>
        <div className="flex flex-col gap-3 mb-6" dir="rtl">
          {[{ I: CheckCircle, c: C.teal, bg: C.tealLight, t: "حسابات موثقة", d: "نتحقق من الهوية لتقليل الاحتيال" },
            { I: EyeOff, c: C.blue, bg: C.blueLight, t: "أرقام مخفية", d: "رقمك مش بيظهر لأي طرف غير بموافقتك" },
            { I: MessageCircle, c: C.green, bg: C.greenLight, t: "شات آمن", d: "المحادثات محمية ومقيدة للحسابات غير الموثقة" }]
            .map(({ I, c, bg, t, d }, i) => (
              <Card key={i}>
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 rounded-2xl flex items-center justify-center flex-shrink-0" style={{ backgroundColor: bg }}>
                    <I size={22} style={{ color: c }} />
                  </div>
                  <div><p className="font-bold text-base" style={{ ...TJ, color: C.navy }}>{t}</p><p className="text-sm" style={{ ...TJ, color: C.gray }}>{d}</p></div>
                </div>
              </Card>
            ))}
        </div>
        <div className="flex flex-col gap-3">
          <PrimaryBtn text="كمّل" />
          <button className="text-center text-sm font-medium" style={{ ...TJ, color: C.gray }}>تخطّي مؤقتاً</button>
        </div>
      </div>
    </div>
  );
}

function RoleSelectionScreen() {
  const [sel, setSel] = useState<string>("tenant");
  return (
    <div className="flex flex-col h-full" style={{ backgroundColor: C.bg }}>
      <StatusBar />
      <div className="flex-1 px-6 py-4" dir="rtl">
        <div className="mb-7">
          <h1 className="text-2xl font-black mb-1" style={{ ...TJ, color: C.navy }}>إنت داخل سكون كـ؟</h1>
          <p className="text-sm" style={{ ...TJ, color: C.gray }}>اختار نوع حسابك عشان نجهزلك التجربة المناسبة</p>
        </div>
        <div className="flex flex-col gap-4 mb-7">
          {[{ id: "tenant", t: "مستأجر", s: "بدور على شقة، ستوديو، أو غرفة", b: "أتصفح وأحجز زيارة", I: User, bg: C.blueLight, c: C.blue },
            { id: "owner", t: "مالك", s: "عندي عقار وعايز أعرضه", b: "أضيف عقارات وأدير الطلبات", I: Key, bg: C.goldLight, c: C.gold }]
            .map(({ id, t, s, b, I, bg, c }) => (
              <button key={id} onClick={() => setSel(id)}
                className="text-right p-5 rounded-3xl transition-all"
                style={{ backgroundColor: C.white, border: `2px solid ${sel === id ? C.teal : C.border}`, boxShadow: sel === id ? `0 0 0 1px ${C.teal}` : "0 2px 8px rgba(0,0,0,0.04)" }}>
                <div className="flex items-center gap-4">
                  <div className="w-14 h-14 rounded-2xl flex items-center justify-center" style={{ backgroundColor: bg }}>
                    <I size={26} style={{ color: c }} />
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center justify-between">
                      <h3 className="text-lg font-black" style={{ ...TJ, color: C.navy }}>{t}</h3>
                      {sel === id && <Check size={20} style={{ color: C.teal }} />}
                    </div>
                    <p className="text-sm" style={{ ...TJ, color: C.gray }}>{s}</p>
                    <span className="inline-block mt-2 text-xs px-2 py-0.5 rounded-full font-bold" style={{ backgroundColor: C.tealLight, color: C.teal, ...TJ }}>{b}</span>
                  </div>
                </div>
              </button>
            ))}
        </div>
        <PrimaryBtn text="متابعة" disabled={!sel} />
      </div>
    </div>
  );
}

function LoginScreen() {
  return (
    <div className="flex flex-col h-full" style={{ backgroundColor: C.bg }}>
      <StatusBar />
      <div className="flex-1 overflow-y-auto px-6 py-4" dir="rtl">
        <div className="mb-7">
          <h1 className="text-2xl font-black mb-1" style={{ ...TJ, color: C.navy }}>👋 أهلاً برجوعك</h1>
          <p className="text-sm" style={{ ...TJ, color: C.gray }}>ادخل لحسابك وكمّل بحثك</p>
        </div>
        <Card className="mb-4">
          <div className="flex flex-col gap-4">
            <TextInput label="البريد الإلكتروني أو رقم الموبايل" placeholder="اكتب هنا" />
            <TextInput label="كلمة المرور" placeholder="كلمة المرور" type="password" />
            <div className="flex justify-between items-center">
              <button className="text-xs font-bold" style={{ ...TJ, color: C.teal }}>نسيت كلمة المرور؟</button>
              <div className="flex items-center gap-2"><span className="text-xs" style={{ ...TJ, color: C.gray }}>تذكرني</span><div className="w-5 h-5 rounded border" style={{ borderColor: C.border }} /></div>
            </div>
          </div>
        </Card>
        <PrivacyBanner text="جلسة دخول آمنة، ورقمك مش بيظهر لأي مستخدم" />
        <div className="flex flex-col gap-3 mt-5">
          <PrimaryBtn text="تسجيل الدخول" />
          <button className="text-center text-sm" style={{ ...TJ, color: C.gray }}>لسه معندكش حساب؟ <span style={{ color: C.teal }}>إنشاء حساب</span></button>
        </div>
      </div>
    </div>
  );
}

function RegisterScreen() {
  return (
    <div className="flex flex-col h-full" style={{ backgroundColor: C.bg }}>
      <StatusBar />
      <div className="flex-1 overflow-y-auto px-6 py-4" dir="rtl">
        <StepProgress step={1} total={4} />
        <div className="flex items-center gap-3 mb-5">
          <div className="w-10 h-10 rounded-2xl flex items-center justify-center" style={{ backgroundColor: C.tealLight }}>
            <Shield size={20} style={{ color: C.teal }} />
          </div>
          <div><h1 className="text-xl font-black" style={{ ...TJ, color: C.navy }}>إنشاء حساب جديد</h1><p className="text-xs" style={{ ...TJ, color: C.gray }}>التوثيق بعد كده</p></div>
        </div>
        <div className="flex flex-col gap-4 mb-4">
          <TextInput label="الاسم بالكامل" placeholder="أحمد محمد علي" />
          <TextInput label="البريد الإلكتروني" placeholder="example@email.com" type="email" />
          <TextInput label="رقم الموبايل" placeholder="010XXXXXXXX" type="tel" />
          <TextInput label="كلمة المرور" placeholder="8 أحرف على الأقل" type="password" />
          <TextInput label="تأكيد كلمة المرور" placeholder="أعد كلمة المرور" type="password" />
        </div>
        <div className="flex items-center gap-3 px-4 py-3 rounded-2xl mb-5" style={{ backgroundColor: C.white, border: `1px solid ${C.border}` }}>
          <div className="w-5 h-5 rounded border-2 flex items-center justify-center flex-shrink-0" style={{ borderColor: C.teal, backgroundColor: C.teal }}>
            <Check size={12} style={{ color: C.white }} />
          </div>
          <p className="text-xs flex-1" style={{ ...TJ, color: C.gray }}>أوافق على شروط الاستخدام وسياسة الخصوصية</p>
        </div>
        <PrimaryBtn text="إنشاء الحساب" />
        <button className="w-full text-center mt-3 text-sm" style={{ ...TJ, color: C.gray }}>عندي حساب بالفعل</button>
      </div>
    </div>
  );
}

function AccountCreatedScreen() {
  return (
    <div className="flex flex-col h-full" style={{ backgroundColor: C.bg }}>
      <StatusBar />
      <div className="flex-1 overflow-y-auto px-6 py-4" dir="rtl">
        <div className="text-center py-5 mb-4">
          <div className="w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-3" style={{ backgroundColor: C.greenLight }}>
            <CheckCircle size={32} style={{ color: C.green }} />
          </div>
          <h1 className="text-2xl font-black mb-1" style={{ ...TJ, color: C.navy }}>حسابك اتعمل بنجاح 🎉</h1>
          <p className="text-sm mb-2" style={{ ...TJ, color: C.gray }}>وثّق هويتك عشان تستخدم سكون بثقة كاملة</p>
          <Badge type="pending" />
        </div>
        <Card className="mb-3">
          <h3 className="font-bold text-base mb-3" style={{ ...TJ, color: C.navy }}>ليه أوثق حسابي؟</h3>
          {["تحصل على علامة موثّق", "تقدر تستخدم الشات بدون قيود", "تزيد ثقة الطرف التاني", "تساعدنا نقلل الحسابات الوهمية"].map((t, i) => (
            <div key={i} className="flex items-center gap-3 mb-2">
              <Check size={15} style={{ color: C.green }} />
              <p className="text-sm" style={{ ...TJ, color: C.gray }}>{t}</p>
            </div>
          ))}
        </Card>
        <WarnBanner text="لو كملت من غير توثيق، الشات المباشر ممكن يكون محدود" />
        <div className="flex flex-col gap-3 mt-4">
          <PrimaryBtn text="وثّق حسابي دلوقتي" />
          <OutlineBtn text="لاحقاً أكمل" />
        </div>
      </div>
    </div>
  );
}

function KYCIntroScreen() {
  return (
    <div className="flex flex-col h-full" style={{ backgroundColor: C.bg }}>
      <StatusBar />
      <div className="flex-1 overflow-y-auto px-6 py-4" dir="rtl">
        <StepProgress step={2} total={4} />
        <h1 className="text-2xl font-black mb-1" style={{ ...TJ, color: C.navy }}>توثيق الهوية</h1>
        <p className="text-sm mb-5" style={{ ...TJ, color: C.gray }}>هنحتاج كام مستند بسيط عشان نراجع حسابك</p>
        <div className="flex flex-col gap-3 mb-5">
          {[{ I: FileText, c: C.blue, bg: C.blueLight, t: "بطاقة الرقم القومي", req: true },
            { I: Camera, c: C.teal, bg: C.tealLight, t: "سيلفي واضح للمطابقة", req: true },
            { I: Upload, c: C.amber, bg: C.amberLight, t: "عقد إيجار سابق (مستأجرين)", req: false }]
            .map(({ I, c, bg, t, req }, i) => (
              <Card key={i}>
                <div className="flex items-center gap-4">
                  <div className="w-11 h-11 rounded-2xl flex items-center justify-center flex-shrink-0" style={{ backgroundColor: bg }}>
                    <I size={20} style={{ color: c }} />
                  </div>
                  <p className="font-semibold text-sm flex-1" style={{ ...TJ, color: C.navy }}>{t}</p>
                  <span className="text-xs font-bold" style={{ color: req ? C.red : C.gray, ...TJ }}>{req ? "مطلوب" : "اختياري"}</span>
                </div>
              </Card>
            ))}
        </div>
        <PrivacyBanner text="مستنداتك مش هتظهر للمستخدمين، تستخدم للمراجعة فقط" />
        <div className="flex flex-col gap-3 mt-5">
          <PrimaryBtn text="ابدأ التوثيق" />
          <button className="text-center text-sm font-bold" style={{ ...TJ, color: C.teal }}>اعرف أكتر عن الخصوصية</button>
        </div>
      </div>
    </div>
  );
}

function NationalIDScreen() {
  return (
    <div className="flex flex-col h-full" style={{ backgroundColor: C.bg }}>
      <StatusBar />
      <div className="flex-1 overflow-y-auto px-6 py-4" dir="rtl">
        <StepProgress step={2} total={4} />
        <h1 className="text-xl font-black mb-1" style={{ ...TJ, color: C.navy }}>ارفع بطاقة الرقم القومي</h1>
        <p className="text-sm mb-5" style={{ ...TJ, color: C.gray }}>اتأكد إن الصورة واضحة وكل البيانات مقروءة</p>
        <div className="flex flex-col gap-4 mb-4">
          <div>
            <p className="font-bold text-sm mb-2" style={{ ...TJ, color: C.navy }}>الوجه الأمامي</p>
            <div className="rounded-2xl p-4 flex items-center gap-3" style={{ backgroundColor: C.greenLight, border: `1px solid ${C.green}` }}>
              <CheckCircle size={20} style={{ color: C.green }} />
              <div className="flex-1"><p className="text-sm font-bold" style={{ ...TJ, color: C.navy }}>id_front.jpg</p><p className="text-xs" style={{ ...TJ, color: C.green }}>تم الرفع بنجاح</p></div>
              <button className="text-xs font-bold" style={{ ...TJ, color: C.teal }}>تغيير</button>
            </div>
          </div>
          <div>
            <p className="font-bold text-sm mb-2" style={{ ...TJ, color: C.navy }}>الوجه الخلفي</p>
            <button className="w-full rounded-2xl p-8 flex flex-col items-center gap-3 border-2 border-dashed" style={{ borderColor: C.border, backgroundColor: C.white }}>
              <Upload size={28} style={{ color: C.gray }} />
              <p className="text-sm font-medium" style={{ ...TJ, color: C.gray }}>اضغط للرفع أو التصوير</p>
              <p className="text-xs" style={{ ...TJ, color: "#D1D5DB" }}>JPG, PNG — بحد أقصى 10MB</p>
            </button>
          </div>
        </div>
        <Card className="mb-4">
          <p className="font-bold text-sm mb-2" style={{ ...TJ, color: C.navy }}>إرشادات</p>
          {["إضاءة كويسة", "البطاقة كلها جوه الإطار", "ممنوع صور مقصوصة أو ضبابية"].map((t, i) => (
            <div key={i} className="flex items-center gap-2 mb-1"><Check size={13} style={{ color: C.teal }} /><p className="text-xs" style={{ ...TJ, color: C.gray }}>{t}</p></div>
          ))}
        </Card>
        <PrivacyBanner text="بيانات البطاقة محمية ومش بتظهر لأي مستخدم" />
        <div className="mt-4"><PrimaryBtn text="التالي" /></div>
      </div>
    </div>
  );
}

function SelfieScreen() {
  return (
    <div className="flex flex-col h-full" style={{ backgroundColor: C.bg }}>
      <StatusBar />
      <div className="flex-1 overflow-y-auto px-6 py-4" dir="rtl">
        <StepProgress step={3} total={4} />
        <h1 className="text-xl font-black mb-1" style={{ ...TJ, color: C.navy }}>سيلفي للتأكيد</h1>
        <p className="text-sm mb-5" style={{ ...TJ, color: C.gray }}>هنطابق صورتك مع البطاقة أثناء المراجعة</p>
        <div className="flex justify-center mb-5">
          <div className="relative" style={{ width: 240, height: 240 }}>
            <div className="w-full h-full rounded-full flex items-center justify-center" style={{ backgroundColor: "#1a1a2e", border: `4px solid ${C.teal}` }}>
              <div className="w-44 h-44 rounded-full flex items-center justify-center" style={{ border: `2px dashed ${C.teal}50` }}>
                <User size={64} style={{ color: `${C.teal}60` }} />
              </div>
            </div>
          </div>
        </div>
        <Card className="mb-3">
          <p className="font-bold text-sm mb-2" style={{ ...TJ, color: C.navy }}>نصايح</p>
          {["وشك يكون واضح", "بلاش نضارة شمس", "مكان منور كويس"].map((t, i) => (
            <div key={i} className="flex items-center gap-2 mb-1"><Check size={13} style={{ color: C.teal }} /><p className="text-xs" style={{ ...TJ, color: C.gray }}>{t}</p></div>
          ))}
        </Card>
        <PrivacyBanner text="الصورة للمراجعة فقط ومش هتظهر على البروفايل" />
        <div className="flex flex-col gap-3 mt-4">
          <button className="w-full py-4 rounded-2xl font-bold text-white flex items-center justify-center gap-2" style={{ backgroundColor: C.teal, ...TJ }}>
            <Camera size={18} />التقاط صورة
          </button>
          <OutlineBtn text="إعادة التصوير" />
        </div>
      </div>
    </div>
  );
}

function TenantHistoryScreen() {
  return (
    <div className="flex flex-col h-full" style={{ backgroundColor: C.bg }}>
      <StatusBar />
      <div className="flex-1 overflow-y-auto px-6 py-4" dir="rtl">
        <StepProgress step={4} total={4} />
        <h1 className="text-xl font-black mb-1" style={{ ...TJ, color: C.navy }}>إثبات حالة مستأجر</h1>
        <p className="text-sm mb-4" style={{ ...TJ, color: C.gray }}>ارفع عقد إيجار سابق أو مستند يثبت تعاملك الإيجاري</p>
        <div className="px-4 py-3 rounded-2xl mb-4 flex items-center gap-3" style={{ backgroundColor: C.greenLight }}>
          <Award size={20} style={{ color: C.green, flexShrink: 0 }} />
          <p className="text-sm" style={{ ...TJ, color: "#166534" }}>أسرع Verified Badge — هذه الخطوة تساعدنا نديك</p>
        </div>
        <button className="w-full rounded-2xl p-8 flex flex-col items-center gap-3 border-2 border-dashed mb-4" style={{ borderColor: C.border, backgroundColor: C.white }}>
          <div className="w-14 h-14 rounded-2xl flex items-center justify-center" style={{ backgroundColor: C.blueLight }}>
            <Upload size={24} style={{ color: C.blue }} />
          </div>
          <p className="text-sm font-bold" style={{ ...TJ, color: C.navy }}>عقد إيجار سابق</p>
          <p className="text-xs" style={{ ...TJ, color: C.gray }}>PDF, JPG, PNG</p>
        </button>
        <Card className="mb-5">
          <div className="flex items-start gap-2">
            <Info size={13} style={{ color: C.gray, flexShrink: 0, marginTop: 1 }} />
            <p className="text-xs" style={{ ...TJ, color: C.gray }}>ممكن تكمل من غير مستند، لكن المراجعة قد تستغرق وقتاً أطول</p>
          </div>
        </Card>
        <div className="flex flex-col gap-3">
          <PrimaryBtn text="مراجعة وإرسال" />
          <OutlineBtn text="تخطي المستند الإضافي" />
        </div>
      </div>
    </div>
  );
}

function OwnerVerificationNoteScreen() {
  return (
    <div className="flex flex-col h-full" style={{ backgroundColor: C.bg }}>
      <StatusBar />
      <div className="flex-1 overflow-y-auto px-6 py-4" dir="rtl">
        <StepProgress step={4} total={4} />
        <div className="text-center py-4 mb-4">
          <div className="w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-3" style={{ backgroundColor: C.goldLight }}>
            <Key size={28} style={{ color: C.gold }} />
          </div>
          <h1 className="text-xl font-black mb-1" style={{ ...TJ, color: C.navy }}>توثيق حساب المالك</h1>
          <p className="text-sm" style={{ ...TJ, color: C.gray }}>تم استلام هويتك — إثباتات العقار بتتضاف مع العقار</p>
        </div>
        <div className="flex flex-col gap-3 mb-6">
          {["بعد الموافقة تقدر تضيف عقارك مباشرة", "كل عقار بيمر بمراجعة صور وموقع وبيانات"].map((t, i) => (
            <Card key={i}>
              <div className="flex items-start gap-3">
                <div className="w-8 h-8 rounded-xl flex items-center justify-center flex-shrink-0" style={{ backgroundColor: C.tealLight }}>
                  <Check size={16} style={{ color: C.teal }} />
                </div>
                <p className="text-sm" style={{ ...TJ, color: C.gray }}>{t}</p>
              </div>
            </Card>
          ))}
        </div>
        <div className="flex flex-col gap-3">
          <PrimaryBtn text="مراجعة وإرسال" />
          <OutlineBtn text="رجوع" />
        </div>
      </div>
    </div>
  );
}

function KYCReviewScreen() {
  return (
    <div className="flex flex-col h-full" style={{ backgroundColor: C.bg }}>
      <StatusBar />
      <div className="flex-1 overflow-y-auto px-6 py-4" dir="rtl">
        <h1 className="text-xl font-black mb-4" style={{ ...TJ, color: C.navy }}>راجع بيانات التوثيق</h1>
        <Card className="mb-3">
          <p className="font-bold text-base mb-3" style={{ ...TJ, color: C.navy }}>البيانات الأساسية</p>
          {[["الاسم", "أحمد محمد علي"], ["نوع الحساب", "مستأجر"], ["البريد", "ahmed@example.com"], ["الموبايل", "010****432"]].map(([l, v], i) => (
            <div key={i} className="flex justify-between items-center py-2" style={{ borderBottom: i < 3 ? `1px solid ${C.border}` : "none" }}>
              <span className="text-sm font-bold" style={{ ...TJ, color: C.navy }}>{v}</span>
              <span className="text-xs" style={{ ...TJ, color: C.gray }}>{l}</span>
            </div>
          ))}
        </Card>
        <Card className="mb-3">
          <p className="font-bold text-base mb-3" style={{ ...TJ, color: C.navy }}>المستندات</p>
          {[["بطاقة الرقم — الأمام", true], ["بطاقة الرقم — الخلف", true], ["سيلفي", true], ["عقد إيجار سابق", false]].map(([l, ok], i) => (
            <div key={i} className="flex items-center justify-between py-2" style={{ borderBottom: i < 3 ? `1px solid ${C.border}` : "none" }}>
              <div className="flex items-center gap-2">
                {ok ? <CheckCircle size={15} style={{ color: C.green }} /> : <AlertCircle size={15} style={{ color: C.amber }} />}
                <span className="text-xs" style={{ ...TJ, color: ok ? C.green : C.amber }}>{ok ? "مرفوع" : "تم تخطيه"}</span>
              </div>
              <span className="text-sm" style={{ ...TJ, color: C.navy }}>{l as string}</span>
            </div>
          ))}
        </Card>
        <PrivacyBanner text="أرقامك ومستنداتك مش هتظهر للمستخدمين أبداً" />
        <div className="flex flex-col gap-3 mt-4">
          <PrimaryBtn text="إرسال للمراجعة" />
          <OutlineBtn text="تعديل البيانات" />
        </div>
      </div>
    </div>
  );
}

function PendingVerificationScreen() {
  return (
    <div className="flex flex-col h-full" style={{ backgroundColor: C.bg }}>
      <StatusBar />
      <div className="flex-1 overflow-y-auto px-6 py-4" dir="rtl">
        <div className="text-center py-4 mb-4">
          <div className="w-20 h-20 rounded-full flex items-center justify-center mx-auto mb-3" style={{ backgroundColor: C.amberLight }}>
            <Clock size={36} style={{ color: C.amber }} />
          </div>
          <Badge type="pending" />
          <h1 className="text-xl font-black mt-3" style={{ ...TJ, color: C.navy }}>طلبك قيد المراجعة</h1>
          <p className="text-sm mt-1" style={{ ...TJ, color: C.gray }}>عادةً بتخلص المراجعة في 24-48 ساعة</p>
        </div>
        <Card className="mb-3">
          <p className="font-bold text-sm mb-3" style={{ ...TJ, color: C.navy }}>مراحل التوثيق</p>
          {[{ s: "تم استلام البيانات", done: true }, { s: "مراجعة البطاقة والسيلفي", active: true }, { s: "تحديث حالة الحساب", done: false }]
            .map((item, i) => (
              <div key={i} className="flex items-center gap-3 py-2">
                <div className="w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0"
                  style={{ backgroundColor: item.done ? C.greenLight : item.active ? C.amberLight : C.border }}>
                  {item.done ? <Check size={12} style={{ color: C.green }} /> : item.active ? <Clock size={12} style={{ color: C.amber }} /> : <div className="w-2 h-2 rounded-full" style={{ backgroundColor: C.gray }} />}
                </div>
                <p className="text-sm" style={{ ...TJ, color: item.done ? C.navy : item.active ? C.amber : C.gray, fontWeight: item.active ? 700 : 400 }}>{item.s}</p>
              </div>
            ))}
        </Card>
        <WarnBanner text="لحد ما يتم التوثيق، الشات المباشر ممكن يكون محدود" />
        <div className="mt-3"><PrivacyBanner text="رقمك لسه مخفي ومش هيظهر لأي طرف" /></div>
        <div className="flex flex-col gap-3 mt-4">
          <PrimaryBtn text="متابعة حالة التوثيق" />
          <OutlineBtn text="العودة للتطبيق" />
        </div>
        <p className="text-center text-xs mt-3" style={{ ...TJ, color: C.gray }}>هنبعتلك إشعار أول ما المراجعة تخلص</p>
      </div>
    </div>
  );
}

function VerificationApprovedScreen() {
  return (
    <div className="flex flex-col h-full" style={{ backgroundColor: C.bg }}>
      <StatusBar />
      <div className="flex-1 overflow-y-auto px-6 py-4" dir="rtl">
        <div className="text-center py-5 mb-4">
          <div className="relative mx-auto mb-4" style={{ width: 80, height: 80 }}>
            <div className="w-20 h-20 rounded-full flex items-center justify-center" style={{ backgroundColor: C.greenLight, border: `3px solid ${C.green}` }}>
              <User size={32} style={{ color: C.green }} />
            </div>
            <div className="absolute -bottom-1 -right-1 w-7 h-7 rounded-full flex items-center justify-center" style={{ backgroundColor: C.gold }}>
              <Check size={14} style={{ color: C.white }} />
            </div>
          </div>
          <h1 className="text-2xl font-black mb-2" style={{ ...TJ, color: C.navy }}>تم توثيق حسابك 🎉</h1>
          <Badge type="verified" text="موثّق ✓" />
          <p className="text-sm mt-3" style={{ ...TJ, color: C.gray }}>دلوقتي تقدر تستخدم مميزات سكون بثقة أكبر</p>
        </div>
        <div className="flex flex-col gap-3 mb-6">
          {[{ I: MessageCircle, c: C.teal, bg: C.tealLight, t: "الشات متاح بدون قيود" },
            { I: Award, c: C.gold, bg: C.goldLight, t: "علامة موثّق ظاهرة في البروفايل" },
            { I: Shield, c: C.blue, bg: C.blueLight, t: "ثقة أعلى في كل التعاملات" }].map(({ I, c, bg, t }, i) => (
            <Card key={i}>
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl flex items-center justify-center" style={{ backgroundColor: bg }}><I size={18} style={{ color: c }} /></div>
                <p className="text-sm font-bold" style={{ ...TJ, color: C.navy }}>{t}</p>
              </div>
            </Card>
          ))}
        </div>
        <div className="flex flex-col gap-3">
          <PrimaryBtn text="ابدأ البحث عن سكن" />
          <OutlineBtn text="عرض البروفايل" />
        </div>
      </div>
    </div>
  );
}

function VerificationRejectedScreen() {
  return (
    <div className="flex flex-col h-full" style={{ backgroundColor: C.bg }}>
      <StatusBar />
      <div className="flex-1 overflow-y-auto px-6 py-4" dir="rtl">
        <div className="text-center py-4 mb-4">
          <div className="w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-3" style={{ backgroundColor: C.redLight }}>
            <AlertCircle size={28} style={{ color: C.red }} />
          </div>
          <Badge type="rejected" />
          <h1 className="text-xl font-black mt-2" style={{ ...TJ, color: C.navy }}>محتاجين نراجع بياناتك تاني</h1>
        </div>
        <Card className="mb-4">
          <p className="font-bold text-sm mb-3" style={{ ...TJ, color: C.navy }}>سبب الرفض</p>
          {["صورة البطاقة غير واضحة", "الاسم في المستند غير مطابق"].map((r, i) => (
            <div key={i} className="flex items-center gap-2 py-2" style={{ borderBottom: i === 0 ? `1px solid ${C.border}` : "none" }}>
              <X size={14} style={{ color: C.red }} /><p className="text-sm" style={{ ...TJ, color: C.navy }}>{r}</p>
            </div>
          ))}
        </Card>
        <div className="px-4 py-3 rounded-2xl mb-6 text-center" style={{ backgroundColor: C.amberLight }}>
          <p className="text-sm" style={{ ...TJ, color: "#92400E" }}>ولا يهمك، عدّل البيانات وابعتهالنا تاني</p>
        </div>
        <div className="flex flex-col gap-3">
          <PrimaryBtn text="تعديل وإعادة الإرسال" />
          <OutlineBtn text="تواصل مع الدعم" />
        </div>
      </div>
    </div>
  );
}

function AccountRestrictedScreen() {
  return (
    <div className="flex flex-col h-full" style={{ backgroundColor: C.bg }}>
      <StatusBar />
      <div className="flex-1 overflow-y-auto px-6 py-4" dir="rtl">
        <div className="text-center py-10 mb-4">
          <div className="w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-3" style={{ backgroundColor: C.amberLight }}>
            <AlertTriangle size={28} style={{ color: C.amber }} />
          </div>
          <h1 className="text-xl font-black mb-2" style={{ ...TJ, color: C.navy }}>الحساب موقوف مؤقتاً</h1>
          <p className="text-sm" style={{ ...TJ, color: C.gray }}>تم تقييد المميزات لحين مراجعة فريق الدعم</p>
        </div>
        <Card className="mb-6"><p className="text-sm text-center" style={{ ...TJ, color: C.gray }}>للمساعدة تواصل مع فريق الدعم عبر البريد الإلكتروني أو رقم الخدمة</p></Card>
        <div className="flex flex-col gap-3">
          <PrimaryBtn text="تواصل مع الدعم" />
          <OutlineBtn text="تسجيل الخروج" />
        </div>
      </div>
    </div>
  );
}

function ForgotPasswordScreen() {
  return (
    <div className="flex flex-col h-full" style={{ backgroundColor: C.bg }}>
      <StatusBar />
      <div className="flex-1 px-6 py-4" dir="rtl">
        <div className="mb-7">
          <h1 className="text-2xl font-black mb-1" style={{ ...TJ, color: C.navy }}>نسيت كلمة المرور؟</h1>
          <p className="text-sm" style={{ ...TJ, color: C.gray }}>هنبعتلك كود استرجاع على بريدك أو موبايلك</p>
        </div>
        <Card className="mb-5"><TextInput label="البريد الإلكتروني أو رقم الموبايل" placeholder="اكتب هنا" /></Card>
        <div className="flex flex-col gap-3">
          <PrimaryBtn text="إرسال كود الاسترجاع" />
          <OutlineBtn text="رجوع لتسجيل الدخول" />
        </div>
      </div>
    </div>
  );
}

function ResetPasswordScreen() {
  return (
    <div className="flex flex-col h-full" style={{ backgroundColor: C.bg }}>
      <StatusBar />
      <div className="flex-1 px-6 py-4" dir="rtl">
        <h1 className="text-2xl font-black mb-6" style={{ ...TJ, color: C.navy }}>إنشاء كلمة مرور جديدة</h1>
        <Card className="mb-4">
          <div className="flex flex-col gap-4">
            <TextInput label="كلمة المرور الجديدة" placeholder="8 أحرف على الأقل" type="password" />
            <TextInput label="تأكيد كلمة المرور" placeholder="أعد كلمة المرور" type="password" />
          </div>
        </Card>
        <div className="flex gap-2 mb-2">
          {["ضعيفة", "متوسطة", "قوية"].map((_, i) => (
            <div key={i} className="flex-1 h-1.5 rounded-full" style={{ backgroundColor: i === 0 ? C.red : i === 1 ? C.amber : C.green }} />
          ))}
        </div>
        <p className="text-xs mb-6" style={{ ...TJ, color: C.amber }}>كلمة المرور متوسطة القوة</p>
        <PrimaryBtn text="تحديث كلمة المرور" />
      </div>
    </div>
  );
}

function LogoutScreen() {
  return (
    <div className="flex flex-col h-full" style={{ backgroundColor: "rgba(0,0,0,0.45)" }}>
      <StatusBar />
      <div className="flex-1" />
      <div className="rounded-t-3xl px-6 py-6" style={{ backgroundColor: C.white }}>
        <div className="w-12 h-1.5 rounded-full mx-auto mb-5" style={{ backgroundColor: C.border }} />
        <div className="text-center mb-5" dir="rtl">
          <div className="w-14 h-14 rounded-full flex items-center justify-center mx-auto mb-3" style={{ backgroundColor: C.redLight }}>
            <LogOut size={24} style={{ color: C.red }} />
          </div>
          <h2 className="text-xl font-black mb-1" style={{ ...TJ, color: C.navy }}>تسجيل الخروج؟</h2>
          <p className="text-sm" style={{ ...TJ, color: C.gray }}>هتحتاج تسجل دخولك تاني علشان تستخدم حسابك</p>
        </div>
        <div className="flex flex-col gap-3">
          <PrimaryBtn text="تسجيل الخروج" danger />
          <OutlineBtn text="إلغاء" />
        </div>
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════
//  TENANT SCREENS  (16 screens)
// ═══════════════════════════════════════════════

function TenantHomeMain() {
  return (
    <div className="flex flex-col h-full" style={{ backgroundColor: C.bg }}>
      <StatusBar />
      <div className="flex-1 overflow-y-auto">
        <div className="px-5 pt-1 pb-3" dir="rtl">
          <div className="flex items-center justify-between mb-3">
            <div>
              <h1 className="text-xl font-black" style={{ ...TJ, color: C.navy }}>👋 أهلاً يا أحمد</h1>
              <p className="text-sm" style={{ ...TJ, color: C.gray }}>جاهز تلاقي سكن مناسب؟</p>
            </div>
            <button className="relative w-10 h-10 rounded-full flex items-center justify-center" style={{ backgroundColor: C.white, border: `1px solid ${C.border}` }}>
              <Bell size={18} style={{ color: C.navy }} />
              <div className="absolute top-1 right-1 w-2.5 h-2.5 rounded-full" style={{ backgroundColor: C.red }} />
            </button>
          </div>
          <button className="flex items-center gap-2 px-3 py-1.5 rounded-xl" style={{ backgroundColor: C.tealLight }}>
            <MapPin size={12} style={{ color: C.teal }} /><span className="text-xs font-bold" style={{ ...TJ, color: C.teal }}>القاهرة، مدينة نصر</span><ChevronDown size={12} style={{ color: C.teal }} />
          </button>
        </div>
        <div className="px-5 mb-3" dir="rtl">
          <div className="flex items-center gap-3 px-4 py-3.5 rounded-2xl" style={{ backgroundColor: C.white, border: `1px solid ${C.border}` }}>
            <Search size={17} style={{ color: C.gray }} />
            <span className="flex-1 text-sm" style={{ color: "#9CA3AF", ...TJ }}>ابحث عن سكنك…</span>
            <button className="w-8 h-8 rounded-xl flex items-center justify-center" style={{ backgroundColor: C.teal }}>
              <Filter size={13} style={{ color: C.white }} />
            </button>
          </div>
        </div>
        <div className="px-5 mb-3 flex gap-2 overflow-x-auto pb-1" dir="rtl">
          {["الكل", "شقة", "ستوديو", "غرفة", "دوبلكس"].map((c, i) => (
            <button key={i} className="flex-shrink-0 px-4 py-2 rounded-full text-sm font-bold"
              style={{ backgroundColor: i === 0 ? C.teal : C.white, color: i === 0 ? C.white : C.navy, border: `1px solid ${i === 0 ? C.teal : C.border}`, ...TJ }}>{c}</button>
          ))}
        </div>
        <div className="px-5 mb-4">
          <div className="flex items-center justify-between px-4 py-3 rounded-2xl" style={{ backgroundColor: C.tealLight }}>
            <div className="flex items-center gap-2" dir="rtl">
              <div className="w-8 h-8 rounded-xl flex items-center justify-center" style={{ backgroundColor: C.white }}>
                <MapPin size={14} style={{ color: C.teal }} />
              </div>
              <p className="text-xs font-medium" style={{ ...TJ, color: C.teal }}>نعرضلك أقرب سكن بناءً على موقعك</p>
            </div>
            <button className="text-xs font-bold px-3 py-1.5 rounded-xl text-white" style={{ backgroundColor: C.teal, ...TJ }}>تفعيل</button>
          </div>
        </div>
        <div className="px-5 mb-4">
          <SectionHead title="قريب منك" action="عرض الكل" />
          <div className="flex gap-3 overflow-x-auto pb-1">
            {[{ p: "8,500", d: "1.2" }, { p: "11,000", d: "2.1" }, { p: "6,800", d: "3.4" }].map((item, i) => (
              <div key={i} className="flex-shrink-0 rounded-2xl overflow-hidden" style={{ width: 190, backgroundColor: C.white, border: `1px solid ${C.border}` }}>
                <div className="relative flex items-center justify-center" style={{ height: 110, backgroundColor: "#E2E8F0" }}>
                  <Building2 size={28} style={{ color: "#94A3B8" }} />
                  <div className="absolute top-2 right-2"><Badge type="verified" /></div>
                  <span className="absolute bottom-2 right-2 flex items-center gap-1 px-2 py-0.5 rounded-lg text-xs font-bold text-white" style={{ backgroundColor: "rgba(0,0,0,0.55)" }}>
                    <MapPin size={10} style={{ color: C.white }} />{item.d} كم
                  </span>
                </div>
                <div className="p-3" dir="rtl">
                  <p className="font-black text-sm" style={{ ...TJ, color: C.teal }}>{item.p} ج.م/شهر</p>
                  <p className="text-xs" style={{ ...TJ, color: C.gray }}>شقة، مدينة نصر</p>
                </div>
              </div>
            ))}
          </div>
        </div>
        <div className="px-5 mb-6">
          <SectionHead title="مقترح ليك" />
          <div className="flex flex-col gap-4">
            <PropCard /><PropCard saved />
          </div>
        </div>
      </div>
      <TenantNav active="home" />
    </div>
  );
}

function TenantSearchFocusScreen() {
  return (
    <div className="flex flex-col h-full" style={{ backgroundColor: C.white }}>
      <StatusBar />
      <div className="px-5 pt-1 pb-3">
        <div className="flex items-center gap-3" dir="rtl">
          <button><ArrowLeft size={20} style={{ color: C.navy }} /></button>
          <div className="flex-1 flex items-center gap-2 px-4 py-3 rounded-2xl" style={{ backgroundColor: C.bg, border: `2px solid ${C.teal}` }}>
            <Search size={15} style={{ color: C.teal }} />
            <input placeholder="ابحث عن سكنك…" dir="rtl" readOnly className="flex-1 text-sm outline-none bg-transparent" style={{ ...TJ, color: C.navy }} />
            <X size={15} style={{ color: C.gray }} />
          </div>
        </div>
      </div>
      <div className="flex-1 overflow-y-auto px-5" dir="rtl">
        <p className="text-xs font-black mb-2 mt-1" style={{ ...TJ, color: C.gray }}>اقتراحات</p>
        {["شقة في مدينة نصر", "ستوديو في التجمع الخامس", "غرفة في المعادي", "شقة قريبة من جامعة القاهرة"].map((s, i) => (
          <div key={i} className="flex items-center gap-3 py-3" style={{ borderBottom: `1px solid ${C.border}` }}>
            <Search size={13} style={{ color: C.gray }} />
            <span className="text-sm flex-1" style={{ ...TJ, color: C.navy }}>{s}</span>
            <ChevronLeft size={13} style={{ color: C.gray }} />
          </div>
        ))}
        <p className="text-xs font-black mb-2 mt-4" style={{ ...TJ, color: C.gray }}>عمليات بحث أخيرة</p>
        {["مدينة نصر", "شقة غرفتين", "ستوديو مفروش"].map((s, i) => (
          <div key={i} className="flex items-center gap-3 py-3" style={{ borderBottom: `1px solid ${C.border}` }}>
            <Clock size={13} style={{ color: C.gray }} />
            <span className="text-sm flex-1" style={{ ...TJ, color: C.navy }}>{s}</span>
            <X size={13} style={{ color: C.gray }} />
          </div>
        ))}
        <p className="text-xs font-black mb-2 mt-4" style={{ ...TJ, color: C.gray }}>مناطق شهيرة</p>
        <div className="flex flex-wrap gap-2">
          {["مدينة نصر", "التجمع الخامس", "المعادي", "الشيخ زايد", "أكتوبر", "الهرم", "المهندسين"].map((a, i) => (
            <button key={i} className="px-3 py-1.5 rounded-xl text-sm" style={{ backgroundColor: C.bg, border: `1px solid ${C.border}`, ...TJ, color: C.navy }}>{a}</button>
          ))}
        </div>
      </div>
    </div>
  );
}

function TenantSearchResultsScreen() {
  return (
    <div className="flex flex-col h-full" style={{ backgroundColor: C.bg }}>
      <StatusBar />
      <div className="px-5 pt-1 pb-3" dir="rtl">
        <div className="flex items-center gap-3 mb-3">
          <button><ArrowLeft size={20} style={{ color: C.navy }} /></button>
          <div className="flex-1 flex items-center gap-2 px-3 py-2 rounded-2xl" style={{ backgroundColor: C.white, border: `1px solid ${C.border}` }}>
            <Search size={13} style={{ color: C.gray }} /><span className="text-sm" style={{ ...TJ, color: C.navy }}>شقة في مدينة نصر</span>
          </div>
          <button className="w-10 h-10 rounded-2xl flex items-center justify-center" style={{ backgroundColor: C.white, border: `1px solid ${C.border}` }}>
            <Filter size={15} style={{ color: C.navy }} />
          </button>
        </div>
        <div className="flex items-center gap-2">
          <p className="text-sm font-black" style={{ ...TJ, color: C.navy }}>128 نتيجة</p>
          {["مدينة نصر", "شقة"].map((chip, i) => (
            <span key={i} className="text-xs px-2 py-0.5 rounded-full flex items-center gap-1" style={{ backgroundColor: C.tealLight, ...TJ, color: C.teal }}>{chip}<X size={9} /></span>
          ))}
        </div>
      </div>
      <div className="flex-1 overflow-y-auto px-5 pb-4">
        <div className="flex flex-col gap-4">
          <PropCard /><PropCard verified={false} /><PropCard saved />
        </div>
      </div>
      <TenantNav />
    </div>
  );
}

function TenantFilterSheet() {
  return (
    <div className="flex flex-col h-full" style={{ backgroundColor: "rgba(0,0,0,0.4)" }}>
      <div className="flex-1" />
      <div className="rounded-t-3xl overflow-y-auto" style={{ backgroundColor: C.white, maxHeight: "88%" }}>
        <div className="sticky top-0 px-5 pt-4 pb-3 flex items-center justify-between" style={{ backgroundColor: C.white, borderBottom: `1px solid ${C.border}` }}>
          <div className="w-12 h-1.5 rounded-full absolute top-2 left-1/2 -translate-x-1/2" style={{ backgroundColor: C.border }} />
          <h2 className="font-black text-lg mt-2" style={{ ...TJ, color: C.navy }} dir="rtl">تصفية النتائج</h2>
          <button className="mt-2"><X size={20} style={{ color: C.navy }} /></button>
        </div>
        <div className="px-5 py-4" dir="rtl">
          <div className="mb-5">
            <p className="font-black text-base mb-3" style={{ ...TJ, color: C.navy }}>نوع السكن</p>
            <div className="flex gap-2">
              {["شقة", "ستوديو", "غرفة", "دوبلكس"].map((t, i) => (
                <button key={i} className="flex-1 py-2 rounded-xl text-sm font-bold border" style={{ backgroundColor: i === 0 ? C.teal : C.white, color: i === 0 ? C.white : C.navy, borderColor: i === 0 ? C.teal : C.border, ...TJ }}>{t}</button>
              ))}
            </div>
          </div>
          <div className="mb-5">
            <p className="font-black text-base mb-2" style={{ ...TJ, color: C.navy }}>السعر الشهري</p>
            <div className="flex justify-between text-sm font-bold mb-2" style={{ ...TJ, color: C.navy }}><span>15,000 ج.م</span><span>5,000 ج.م</span></div>
            <div className="h-1.5 rounded-full relative" style={{ backgroundColor: C.border }}>
              <div className="absolute inset-y-0 left-0 w-2/3 rounded-full" style={{ backgroundColor: C.teal }} />
              <div className="absolute top-1/2 -translate-y-1/2 left-2/3 w-4 h-4 rounded-full border-2" style={{ backgroundColor: C.white, borderColor: C.teal }} />
            </div>
          </div>
          <div className="mb-5">
            <p className="font-black text-base mb-3" style={{ ...TJ, color: C.navy }}>عدد الغرف</p>
            <div className="flex gap-2">
              {["1", "2", "3", "4+"].map((r, i) => (
                <button key={i} className="w-12 h-10 rounded-xl text-sm font-black border" style={{ backgroundColor: i === 1 ? C.teal : C.white, color: i === 1 ? C.white : C.navy, borderColor: i === 1 ? C.teal : C.border, ...TJ }}>{r}</button>
              ))}
            </div>
          </div>
          <div className="mb-5">
            <p className="font-black text-base mb-3" style={{ ...TJ, color: C.navy }}>المرافق</p>
            <div className="flex flex-wrap gap-2">
              {["WiFi", "أسانسير", "جراج", "مفروش", "قريب من المترو", "بلكونة"].map((a, i) => (
                <button key={i} className="px-3 py-1.5 rounded-xl text-sm border font-medium"
                  style={{ backgroundColor: i < 2 ? C.tealLight : C.white, color: i < 2 ? C.teal : C.navy, borderColor: i < 2 ? C.teal : C.border, ...TJ }}>{a}</button>
              ))}
            </div>
          </div>
          <div className="flex items-center justify-between p-4 rounded-2xl mb-5" style={{ backgroundColor: C.bg, border: `1px solid ${C.border}` }}>
            <div className="w-12 h-6 rounded-full flex items-center relative" style={{ backgroundColor: C.teal }}>
              <div className="absolute right-1 w-4 h-4 rounded-full" style={{ backgroundColor: C.white }} />
            </div>
            <p className="text-sm font-bold" style={{ ...TJ, color: C.navy }}>اعرض العقارات الموثقة فقط</p>
          </div>
          <div className="flex gap-3">
            <button className="flex-1 py-4 rounded-2xl text-sm font-bold border" style={{ borderColor: C.border, ...TJ, color: C.gray }}>مسح الكل</button>
            <button className="flex-1 py-4 rounded-2xl text-sm font-bold text-white" style={{ backgroundColor: C.teal, ...TJ }}>تطبيق (3 فلاتر)</button>
          </div>
        </div>
      </div>
    </div>
  );
}

function TenantNearbyScreen() {
  return (
    <div className="flex flex-col h-full" style={{ backgroundColor: C.bg }}>
      <StatusBar />
      <div className="px-5 pt-1 pb-3 flex items-center gap-3" dir="rtl">
        <button><ArrowLeft size={20} style={{ color: C.navy }} /></button>
        <h1 className="text-xl font-black flex-1" style={{ ...TJ, color: C.navy }}>قريب منك</h1>
        <button className="flex items-center gap-1 px-3 py-1.5 rounded-xl text-sm font-bold" style={{ backgroundColor: C.tealLight, ...TJ, color: C.teal }}>
          <Map size={13} />خريطة
        </button>
      </div>
      <div className="px-5 mb-2 flex items-center gap-2" dir="rtl">
        <MapPin size={13} style={{ color: C.teal }} />
        <span className="text-xs font-bold" style={{ ...TJ, color: C.teal }}>مدينة نصر، القاهرة</span>
        <span className="text-xs" style={{ ...TJ, color: C.gray }}>· 128 عقار في نطاق 5 كم</span>
      </div>
      <div className="flex-1 overflow-y-auto px-5 pb-4">
        {[{ km: "0.8", price: "8,500" }, { km: "1.2", price: "12,000" }, { km: "2.1", price: "6,500" }, { km: "3.4", price: "9,000" }].map((p, i) => (
          <div key={i} className="rounded-3xl overflow-hidden mb-3" style={{ backgroundColor: C.white, border: `1px solid ${C.border}`, boxShadow: "0 2px 8px rgba(0,0,0,0.04)" }}>
            <div className="flex items-center gap-3 p-4" dir="rtl">
              <div className="flex-shrink-0 rounded-2xl flex items-center justify-center" style={{ width: 90, height: 90, backgroundColor: "#E2E8F0" }}>
                <Building2 size={28} style={{ color: "#94A3B8" }} />
              </div>
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <Badge type="verified" />
                  <span className="text-xs px-2 py-0.5 rounded-full font-bold" style={{ backgroundColor: C.tealLight, ...TJ, color: C.teal }}>{p.km} كم</span>
                </div>
                <p className="font-black" style={{ ...TJ, color: C.teal }}>{p.price} ج.م/شهر</p>
                <p className="text-sm" style={{ ...TJ, color: C.navy }}>شقة مفروشة 3 غرف</p>
                <p className="text-xs" style={{ ...TJ, color: C.gray }}>مدينة نصر</p>
              </div>
            </div>
          </div>
        ))}
      </div>
      <TenantNav />
    </div>
  );
}

function PropCardStatesScreen() {
  return (
    <div className="flex flex-col h-full" style={{ backgroundColor: C.bg }}>
      <StatusBar />
      <div className="flex-1 overflow-y-auto px-5 py-3">
        <h1 className="text-xl font-black mb-1" style={{ ...TJ, color: C.navy }} dir="rtl">حالات بطاقة العقار</h1>
        <p className="text-xs mb-4" style={{ ...TJ, color: C.gray }} dir="rtl">أربع حالات مختلفة للبطاقة</p>
        <div className="flex flex-col gap-4">
          <div><p className="text-xs font-black mb-2" style={{ ...TJ, color: C.green }} dir="rtl">● موثّق — متاح</p><PropCard verified /></div>
          <div><p className="text-xs font-black mb-2" style={{ ...TJ, color: C.gray }} dir="rtl">○ غير موثّق</p><PropCard verified={false} /></div>
          <div><p className="text-xs font-black mb-2" style={{ ...TJ, color: C.blue }} dir="rtl">● مؤجّر</p><PropCard badge="rented" /></div>
          <div><p className="text-xs font-black mb-2" style={{ ...TJ, color: C.gray }} dir="rtl">● مخفي</p><PropCard badge="hidden" /></div>
        </div>
      </div>
      <TenantNav />
    </div>
  );
}

function PropertyDetailsScreen() {
  return (
    <div className="flex flex-col h-full" style={{ backgroundColor: C.bg }}>
      <div className="relative flex-shrink-0 flex items-center justify-center" style={{ height: 230, backgroundColor: "#E2E8F0" }}>
        <Building2 size={52} style={{ color: "#94A3B8" }} />
        <div className="absolute top-4 left-4">
          <button className="w-10 h-10 rounded-full flex items-center justify-center" style={{ backgroundColor: "rgba(255,255,255,0.9)" }}>
            <ArrowLeft size={18} style={{ color: C.navy }} />
          </button>
        </div>
        <div className="absolute top-4 right-4 flex gap-2">
          <button className="w-9 h-9 rounded-full flex items-center justify-center" style={{ backgroundColor: "rgba(255,255,255,0.9)" }}>
            <Heart size={15} style={{ color: "#9CA3AF" }} />
          </button>
          <button className="w-9 h-9 rounded-full flex items-center justify-center" style={{ backgroundColor: "rgba(255,255,255,0.9)" }}>
            <Share2 size={15} style={{ color: C.navy }} />
          </button>
        </div>
        <span className="absolute bottom-3 right-3 px-2 py-0.5 rounded-lg text-xs font-bold text-white" style={{ backgroundColor: "rgba(0,0,0,0.6)" }}>1/10</span>
      </div>
      <div className="flex-1 overflow-y-auto px-5 pt-5 pb-24" style={{ borderRadius: "24px 24px 0 0", marginTop: -24, backgroundColor: C.white }} dir="rtl">
        <div className="flex items-start justify-between mb-2">
          <div>
            <p className="text-2xl font-black" style={{ ...TJ, color: C.teal }}>12,000 ج.م/شهر</p>
            <h2 className="text-base font-black" style={{ ...TJ, color: C.navy }}>شقة مفروشة قريبة من عباس العقاد</h2>
          </div>
          <Badge type="verified" text="عقار موثّق" />
        </div>
        <div className="flex items-center gap-1 mb-4"><MapPin size={13} style={{ color: C.gray }} /><span className="text-sm" style={{ ...TJ, color: C.gray }}>مدينة نصر، القاهرة</span></div>
        <div className="grid grid-cols-4 gap-2 mb-5">
          {[["3", "الغرف"], ["2", "الحمامات"], ["120م²", "المساحة"], ["5", "الدور"]].map(([v, l], i) => (
            <div key={i} className="flex flex-col items-center p-3 rounded-2xl text-center" style={{ backgroundColor: C.bg }}>
              <p className="font-black text-base" style={{ ...TJ, color: C.navy }}>{v}</p>
              <p className="text-xs" style={{ ...TJ, color: C.gray }}>{l}</p>
            </div>
          ))}
        </div>
        <div className="mb-5">
          <h3 className="font-black text-base mb-2" style={{ ...TJ, color: C.navy }}>وصف السكن</h3>
          <p className="text-sm leading-6" style={{ ...TJ, color: C.gray }}>شقة مفروشة بالكامل، قريبة من الخدمات والمواصلات، مناسبة للعائلات. الشقة تتميز بإطلالة هادئة وتهوية ممتازة.</p>
        </div>
        <div className="mb-5">
          <h3 className="font-black text-base mb-3" style={{ ...TJ, color: C.navy }}>المرافق</h3>
          <div className="flex flex-wrap gap-2">
            {["WiFi", "أسانسير", "جراج", "مفروش", "بلكونة", "أمن 24/7"].map((a, i) => (
              <span key={i} className="flex items-center gap-1 px-3 py-1.5 rounded-xl text-sm font-medium" style={{ backgroundColor: C.tealLight, ...TJ, color: C.teal }}>
                <Check size={11} />{a}
              </span>
            ))}
          </div>
        </div>
        <div className="mb-5">
          <h3 className="font-black text-base mb-2" style={{ ...TJ, color: C.navy }}>الموقع</h3>
          <div className="rounded-2xl flex flex-col items-center justify-center gap-2" style={{ height: 130, backgroundColor: "#E5E7EB" }}>
            <Map size={28} style={{ color: C.gray }} />
            <p className="text-xs" style={{ ...TJ, color: C.gray }}>الموقع تقريبي — لحماية خصوصية المالك</p>
          </div>
        </div>
        <Card>
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-full flex items-center justify-center" style={{ backgroundColor: C.tealLight }}>
              <User size={24} style={{ color: C.teal }} />
            </div>
            <div className="flex-1">
              <div className="flex items-center gap-2"><p className="font-black text-base" style={{ ...TJ, color: C.navy }}>أحمد محمد</p><Badge type="verified" text="مالك موثّق" /></div>
              <div className="flex items-center gap-1"><Star size={12} fill={C.amber} style={{ color: C.amber }} /><span className="text-xs" style={{ ...TJ, color: C.gray }}>4.7 (38 تقييم)</span></div>
            </div>
          </div>
          <div className="mt-3 pt-3" style={{ borderTop: `1px solid ${C.border}` }}>
            <PrivacyBanner text="رقم الموبايل مخفي — يظهر فقط بموافقتك" />
          </div>
        </Card>
      </div>
      <div className="absolute bottom-0 left-0 right-0 px-5 py-4 flex gap-3" style={{ backgroundColor: C.white, borderTop: `1px solid ${C.border}` }}>
        <button className="flex-1 py-3.5 rounded-2xl font-black text-white" style={{ backgroundColor: C.teal, ...TJ }}>احجز زيارة</button>
        <button className="w-12 h-12 rounded-2xl flex items-center justify-center flex-shrink-0" style={{ backgroundColor: C.blueLight }}>
          <MessageCircle size={20} style={{ color: C.blue }} />
        </button>
        <button className="w-12 h-12 rounded-2xl flex items-center justify-center flex-shrink-0" style={{ backgroundColor: C.bg, border: `1px solid ${C.border}` }}>
          <Heart size={20} style={{ color: C.gray }} />
        </button>
      </div>
    </div>
  );
}

function MediaGalleryScreen() {
  return (
    <div className="flex flex-col h-full" style={{ backgroundColor: "#000" }}>
      <div className="flex items-center justify-between px-5 pt-12 pb-4">
        <button className="w-10 h-10 rounded-full flex items-center justify-center" style={{ backgroundColor: "rgba(255,255,255,0.15)" }}>
          <X size={20} style={{ color: C.white }} />
        </button>
        <span className="font-bold text-white" style={{ ...TJ }}>3 / 10</span>
        <button className="w-10 h-10 rounded-full flex items-center justify-center" style={{ backgroundColor: "rgba(255,255,255,0.15)" }}>
          <Share2 size={18} style={{ color: C.white }} />
        </button>
      </div>
      <div className="flex-1 flex items-center justify-center px-4">
        <div className="w-full rounded-3xl flex items-center justify-center" style={{ height: 320, backgroundColor: "#1C1C1E" }}>
          <Building2 size={64} style={{ color: "#3A3A3C" }} />
        </div>
      </div>
      <div className="px-5 py-4">
        <p className="text-white font-bold text-center mb-4" style={{ ...TJ }}>المطبخ والصالة</p>
        <div className="flex gap-2 overflow-x-auto pb-2">
          {Array.from({ length: 10 }).map((_, i) => (
            <div key={i} className="flex-shrink-0 rounded-xl flex items-center justify-center"
              style={{ width: 64, height: 64, backgroundColor: i === 2 ? `${C.teal}30` : "#1C1C1E", border: i === 2 ? `2px solid ${C.teal}` : "none" }}>
              <Building2 size={20} style={{ color: i === 2 ? C.teal : "#3A3A3C" }} />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function BookVisitSheet() {
  return (
    <div className="flex flex-col h-full" style={{ backgroundColor: "rgba(0,0,0,0.3)" }}>
      <div className="flex-1" />
      <div className="rounded-t-3xl overflow-y-auto" style={{ backgroundColor: C.white, maxHeight: "88%" }}>
        <div className="px-5 pt-4 pb-2">
          <div className="w-12 h-1.5 rounded-full mx-auto mb-4" style={{ backgroundColor: C.border }} />
          <h2 className="text-xl font-black text-center mb-1" style={{ ...TJ, color: C.navy }}>احجز زيارة</h2>
          <p className="text-sm text-center mb-4" style={{ ...TJ, color: C.gray }}>اختار اليوم والوقت المناسبين ليك</p>
        </div>
        <div className="px-5 pb-5" dir="rtl">
          <div className="flex items-center gap-3 p-3 rounded-2xl mb-4" style={{ backgroundColor: C.bg }}>
            <div className="flex-shrink-0 rounded-2xl flex items-center justify-center" style={{ width: 56, height: 56, backgroundColor: "#E2E8F0" }}>
              <Building2 size={20} style={{ color: "#94A3B8" }} />
            </div>
            <div>
              <p className="font-bold text-sm" style={{ ...TJ, color: C.navy }}>شقة مفروشة، مدينة نصر</p>
              <p className="text-xs" style={{ ...TJ, color: C.gray }}>12,000 ج.م/شهر</p>
            </div>
          </div>
          <p className="font-black text-sm mb-2" style={{ ...TJ, color: C.navy }}>اليوم</p>
          <div className="flex gap-2 mb-4">
            {["النهارده", "بكرة", "الجمعة", "اختار"].map((d, i) => (
              <button key={i} className="flex-1 py-2.5 rounded-xl text-xs font-bold border"
                style={{ backgroundColor: i === 0 ? C.teal : C.white, color: i === 0 ? C.white : C.navy, borderColor: i === 0 ? C.teal : C.border, ...TJ }}>{d}</button>
            ))}
          </div>
          <p className="font-black text-sm mb-2" style={{ ...TJ, color: C.navy }}>الوقت</p>
          <div className="grid grid-cols-3 gap-2 mb-4">
            {["10:00 ص", "12:00 م", "2:00 م", "5:00 م", "7:00 م"].map((t, i) => (
              <button key={i} className="py-2.5 rounded-xl text-sm font-bold border"
                style={{ backgroundColor: i === 1 ? C.teal : C.white, color: i === 1 ? C.white : C.navy, borderColor: i === 1 ? C.teal : C.border, ...TJ }}>{t}</button>
            ))}
          </div>
          <input placeholder="ملاحظة للمالك… (اختياري)" dir="rtl" readOnly className="w-full px-4 py-3 rounded-2xl text-sm border outline-none mb-4" style={{ borderColor: C.border, ...TJ, color: C.navy }} />
          <PrivacyBanner text="رقمك لسه مخفي — المالك هيستلم طلب الزيارة فقط" />
          <div className="mt-4"><PrimaryBtn text="إرسال طلب الزيارة" /></div>
        </div>
      </div>
    </div>
  );
}

function VisitRequestSentScreen() {
  return (
    <div className="flex flex-col h-full" style={{ backgroundColor: C.bg }}>
      <StatusBar />
      <div className="flex-1 flex flex-col items-center justify-center px-6 gap-5" dir="rtl">
        <div className="w-24 h-24 rounded-full flex items-center justify-center" style={{ backgroundColor: C.greenLight, border: `3px solid ${C.green}` }}>
          <CheckCircle size={44} style={{ color: C.green }} />
        </div>
        <div className="text-center">
          <h1 className="text-2xl font-black mb-1" style={{ ...TJ, color: C.navy }}>تم إرسال طلب الزيارة 🎉</h1>
          <p className="text-sm mb-1" style={{ ...TJ, color: C.gray }}>المالك هيراجع طلبك ويرد عليك قريباً</p>
          <p className="text-xs" style={{ ...TJ, color: C.gray }}>رقمك لسه مخفي لحد ما يتم الاتفاق</p>
        </div>
        <Card className="w-full">
          {[["العقار", "شقة مفروشة، مدينة نصر"], ["الموعد المطلوب", "النهارده 2:00 م"], ["المالك", "أحمد محمد"], ["الحالة", "بانتظار الرد"]].map(([l, v], i) => (
            <div key={i} className="flex justify-between items-center py-2" style={{ borderBottom: i < 3 ? `1px solid ${C.border}` : "none" }}>
              <span className="text-sm font-bold" style={{ ...TJ, color: C.navy }}>{v}</span>
              <span className="text-xs" style={{ ...TJ, color: C.gray }}>{l}</span>
            </div>
          ))}
        </Card>
        <div className="px-4 py-3 rounded-2xl w-full" style={{ backgroundColor: C.amberLight }}>
          <div className="flex items-center gap-2"><Bell size={14} style={{ color: C.amber }} /><p className="text-xs" style={{ ...TJ, color: "#92400E" }}>هنبعتلك إشعار لما المالك يرد</p></div>
        </div>
        <div className="w-full flex flex-col gap-3">
          <PrimaryBtn text="تابع طلبات الزيارة" />
          <OutlineBtn text="رجوع للعقار" />
        </div>
      </div>
    </div>
  );
}

function ChatWarningScreen() {
  return (
    <div className="flex flex-col h-full" style={{ backgroundColor: C.bg }}>
      <StatusBar />
      <WarnBanner text="الشات محدود لحد ما توثق حسابك" action="وثّق الآن" />
      <div className="flex-1 flex flex-col items-center justify-center px-6 gap-5" dir="rtl">
        <div className="w-16 h-16 rounded-full flex items-center justify-center" style={{ backgroundColor: C.amberLight }}>
          <MessageCircle size={28} style={{ color: C.amber }} />
        </div>
        <div className="text-center">
          <h2 className="font-black text-xl mb-2" style={{ ...TJ, color: C.navy }}>الشات غير متاح</h2>
          <p className="text-sm" style={{ ...TJ, color: C.gray }}>لازم توثق حسابك عشان تبدأ محادثة كاملة مع المالك</p>
        </div>
        <div className="w-full rounded-2xl p-4 flex items-center gap-3" style={{ backgroundColor: C.bg, border: `2px dashed ${C.border}` }}>
          <Lock size={18} style={{ color: C.gray }} />
          <div><p className="text-sm font-bold" style={{ ...TJ, color: C.gray }}>الرسائل مقفولة</p><p className="text-xs" style={{ ...TJ, color: "#D1D5DB" }}>أرسل توثيقك أولاً</p></div>
        </div>
        <div className="w-full flex flex-col gap-3">
          <PrimaryBtn text="توثيق الحساب" />
          <OutlineBtn text="رجوع للعقار" />
        </div>
      </div>
      <TenantNav active="chat" />
    </div>
  );
}

function TenantChatScreen() {
  return (
    <div className="flex flex-col h-full" style={{ backgroundColor: C.bg }}>
      <StatusBar />
      <div className="px-5 py-3 flex items-center gap-3" style={{ backgroundColor: C.white, borderBottom: `1px solid ${C.border}` }}>
        <button><ArrowLeft size={20} style={{ color: C.navy }} /></button>
        <div className="w-10 h-10 rounded-full flex items-center justify-center" style={{ backgroundColor: C.tealLight }}>
          <User size={20} style={{ color: C.teal }} />
        </div>
        <div className="flex-1" dir="rtl">
          <div className="flex items-center gap-2"><p className="font-black text-base" style={{ ...TJ, color: C.navy }}>أحمد محمد</p><Badge type="verified" text="مالك موثّق" /></div>
          <p className="text-xs" style={{ ...TJ, color: C.gray }}>شقة مفروشة · مدينة نصر</p>
        </div>
        <div className="w-2 h-2 rounded-full" style={{ backgroundColor: C.green }} />
      </div>
      <div className="px-4 py-2"><PrivacyBanner text="رقم الموبايل مخفي داخل المحادثة" /></div>
      <div className="flex-1 overflow-y-auto px-5 py-3 flex flex-col gap-3">
        {[{ mine: false, text: "أهلاً! الشقة لسه متاحة؟" }, { mine: true, text: "أيوه، متاحة. تقدر تعمل حجز زيارة من تفاصيل العقار" },
          { mine: false, text: "تمام. هل فيه أسانسير؟" }, { mine: true, text: "أيوه في أسانسير، والشقة في الدور الخامس" },
          { mine: false, text: "ممتاز، هبعت طلب زيارة النهارده الساعة 2" }].map((m, i) => (
          <div key={i} className={`flex ${m.mine ? "justify-start" : "justify-end"}`}>
            <div className="max-w-xs px-4 py-2.5 text-sm" dir="rtl"
              style={{ backgroundColor: m.mine ? C.teal : C.white, color: m.mine ? C.white : C.navy,
                border: m.mine ? "none" : `1px solid ${C.border}`, ...TJ,
                borderRadius: m.mine ? "16px 4px 16px 16px" : "4px 16px 16px 16px" }}>
              {m.text}
            </div>
          </div>
        ))}
      </div>
      <div className="px-4 py-3 flex items-center gap-2" style={{ backgroundColor: C.white, borderTop: `1px solid ${C.border}` }}>
        <button className="w-9 h-9 rounded-full flex items-center justify-center" style={{ backgroundColor: C.bg }}><Mic size={16} style={{ color: C.gray }} /></button>
        <div className="flex-1 flex items-center px-3 py-2 rounded-2xl gap-2" style={{ backgroundColor: C.bg }}>
          <input placeholder="اكتب رسالة…" dir="rtl" readOnly className="flex-1 text-sm outline-none bg-transparent" style={{ ...TJ }} />
          <ImageIcon size={15} style={{ color: C.gray }} />
        </div>
        <button className="w-9 h-9 rounded-full flex items-center justify-center" style={{ backgroundColor: C.teal }}>
          <Send size={15} style={{ color: C.white }} />
        </button>
      </div>
    </div>
  );
}

function SavedListingsScreen() {
  return (
    <div className="flex flex-col h-full" style={{ backgroundColor: C.bg }}>
      <StatusBar />
      <div className="px-5 pt-1 pb-3" dir="rtl">
        <h1 className="text-xl font-black" style={{ ...TJ, color: C.navy }}>المحفوظات</h1>
        <p className="text-sm" style={{ ...TJ, color: C.gray }}>3 عقارات في قائمتك</p>
      </div>
      <div className="px-5 mb-3 flex gap-2" dir="rtl">
        {["الكل", "شقة", "ستوديو"].map((t, i) => (
          <button key={i} className="px-4 py-1.5 rounded-full text-sm font-bold"
            style={{ backgroundColor: i === 0 ? C.teal : C.white, color: i === 0 ? C.white : C.navy, border: `1px solid ${i === 0 ? C.teal : C.border}`, ...TJ }}>{t}</button>
        ))}
      </div>
      <div className="flex-1 overflow-y-auto px-5 pb-4">
        <div className="flex flex-col gap-4"><PropCard saved /><PropCard verified={false} saved /><PropCard saved /></div>
      </div>
      <TenantNav active="saved" />
    </div>
  );
}

function TenantSkeletonScreen() {
  const Sk = ({ w = "w-full", h = "h-4", r = "rounded-xl" }: { w?: string; h?: string; r?: string }) => (
    <div className={`${w} ${h} ${r} animate-pulse`} style={{ backgroundColor: "#E5E7EB" }} />
  );
  return (
    <div className="flex flex-col h-full" style={{ backgroundColor: C.bg }}>
      <StatusBar />
      <div className="flex-1 overflow-y-auto px-5 py-3">
        <div className="flex items-center justify-between mb-4">
          <div className="flex flex-col gap-2"><Sk w="w-32" h="h-5" /><Sk w="w-24" h="h-3" /></div>
          <Sk w="w-10" h="h-10" r="rounded-full" />
        </div>
        <Sk h="h-12" r="rounded-2xl" />
        <div className="flex gap-2 mt-3 mb-4">{[1, 2, 3, 4].map(i => <Sk key={i} w="w-16" h="h-8" r="rounded-full" />)}</div>
        <div className="flex gap-3 mb-5">
          {[1, 2].map(i => <div key={i} className="flex-1 rounded-2xl overflow-hidden"><Sk h="h-28" r="rounded-none" /><div className="p-3 flex flex-col gap-2" style={{ backgroundColor: "#F3F4F6" }}><Sk h="h-4" /><Sk w="w-20" h="h-3" /></div></div>)}
        </div>
        {[1, 2].map(i => (
          <div key={i} className="rounded-3xl overflow-hidden mb-4">
            <Sk h="h-44" r="rounded-none" />
            <div className="p-4 flex flex-col gap-2" style={{ backgroundColor: "#F3F4F6" }}><Sk h="h-5" w="w-32" /><Sk h="h-4" w="w-48" /><Sk h="h-3" w="w-20" /></div>
          </div>
        ))}
      </div>
      <TenantNav />
    </div>
  );
}

function TenantEmptyScreen() {
  return (
    <div className="flex flex-col h-full" style={{ backgroundColor: C.bg }}>
      <StatusBar />
      <div className="px-5 pt-1 pb-3" dir="rtl">
        <div className="flex items-center gap-2 px-4 py-3 rounded-2xl" style={{ backgroundColor: C.white, border: `1px solid ${C.border}` }}>
          <Search size={15} style={{ color: C.gray }} /><span className="flex-1 text-sm" style={{ color: "#9CA3AF", ...TJ }}>ستوديو في المعادي بجوار المترو</span><X size={15} style={{ color: C.gray }} />
        </div>
      </div>
      <div className="flex-1 flex flex-col items-center justify-center px-8 gap-5" dir="rtl">
        <div className="w-24 h-24 rounded-3xl flex items-center justify-center" style={{ backgroundColor: C.bg, border: `2px dashed ${C.border}` }}>
          <Search size={40} style={{ color: "#D1D5DB" }} />
        </div>
        <div className="text-center">
          <h2 className="font-black text-xl mb-2" style={{ ...TJ, color: C.navy }}>مافيش نتايج</h2>
          <p className="text-sm" style={{ ...TJ, color: C.gray }}>ما لقيناش عقارات مطابقة لبحثك في المنطقة دي</p>
        </div>
        <div className="flex flex-col gap-3 w-full">
          <PrimaryBtn text="وسّع نطاق البحث" />
          <OutlineBtn text="غيّر الفلاتر" />
        </div>
        <div className="text-center">
          <p className="text-sm font-bold mb-2" style={{ ...TJ, color: C.navy }}>ممكن تجرب:</p>
          {["مناطق قريبة زي المقطم أو حلوان", "تقليل الفلاتر المختارة", "رفع السعر الأقصى شوية"].map((t, i) => (
            <p key={i} className="text-xs mb-1" style={{ ...TJ, color: C.gray }}>· {t}</p>
          ))}
        </div>
      </div>
      <TenantNav />
    </div>
  );
}

function TenantErrorScreen() {
  return (
    <div className="flex flex-col h-full" style={{ backgroundColor: C.bg }}>
      <StatusBar />
      <div className="flex-1 flex flex-col items-center justify-center px-8 gap-5" dir="rtl">
        <div className="w-24 h-24 rounded-3xl flex items-center justify-center" style={{ backgroundColor: C.redLight }}>
          <RefreshCw size={40} style={{ color: C.red }} />
        </div>
        <div className="text-center">
          <h2 className="font-black text-xl mb-2" style={{ ...TJ, color: C.navy }}>في مشكلة في الاتصال</h2>
          <p className="text-sm" style={{ ...TJ, color: C.gray }}>تأكد من اتصالك بالإنترنت وحاول تاني</p>
        </div>
        <div className="px-4 py-3 rounded-2xl w-full" style={{ backgroundColor: C.redLight }}>
          <div className="flex items-center gap-2"><AlertCircle size={14} style={{ color: C.red }} /><p className="text-xs" style={{ ...TJ, color: C.red }}>Error: Network request failed (timeout)</p></div>
        </div>
        <div className="flex flex-col gap-3 w-full">
          <PrimaryBtn text="إعادة المحاولة" />
          <OutlineBtn text="الاتصال بالدعم" />
        </div>
      </div>
      <TenantNav />
    </div>
  );
}

// ═══════════════════════════════════════════════
//  OWNER SCREENS  (20 screens)
// ═══════════════════════════════════════════════

function OwnerDashboardMain() {
  return (
    <div className="flex flex-col h-full" style={{ backgroundColor: C.bg }}>
      <StatusBar />
      <div className="flex-1 overflow-y-auto">
        <div className="px-5 pt-1 pb-2" dir="rtl">
          <div className="flex items-center justify-between mb-3">
            <div>
              <h1 className="text-xl font-black" style={{ ...TJ, color: C.navy }}>👋 أهلاً يا أحمد</h1>
              <p className="text-sm" style={{ ...TJ, color: C.gray }}>تابع عقاراتك وطلبات الزيارة</p>
            </div>
            <div className="flex gap-2">
              <button className="relative w-10 h-10 rounded-full flex items-center justify-center" style={{ backgroundColor: C.white, border: `1px solid ${C.border}` }}>
                <Bell size={17} style={{ color: C.navy }} /><div className="absolute top-1 right-1 w-2 h-2 rounded-full" style={{ backgroundColor: C.red }} />
              </button>
              <div className="w-10 h-10 rounded-full flex items-center justify-center" style={{ backgroundColor: C.tealLight }}>
                <User size={17} style={{ color: C.teal }} />
              </div>
            </div>
          </div>
          <div className="flex items-center gap-3 px-4 py-2.5 rounded-2xl mb-3" style={{ backgroundColor: C.greenLight }}>
            <CheckCircle size={16} style={{ color: C.green }} /><p className="text-sm font-bold" style={{ ...TJ, color: "#166534" }}>حسابك موثّق</p><Badge type="verified" />
          </div>
        </div>
        <div className="px-5 mb-4">
          <div className="grid grid-cols-2 gap-3">
            {[{ I: Eye, c: C.blue, bg: C.blueLight, n: "1,245", l: "إجمالي المشاهدات" },
              { I: Calendar, c: C.teal, bg: C.tealLight, n: "18", l: "طلبات الزيارة" },
              { I: MessageCircle, c: C.amber, bg: C.amberLight, n: "5", l: "رسائل غير مقروءة" },
              { I: Building2, c: C.green, bg: C.greenLight, n: "3", l: "عقارات نشطة" }].map(({ I, c, bg, n, l }, i) => (
              <div key={i} className="rounded-2xl p-4" style={{ backgroundColor: C.white, border: `1px solid ${C.border}` }} dir="rtl">
                <div className="w-10 h-10 rounded-xl flex items-center justify-center mb-2" style={{ backgroundColor: bg }}><I size={17} style={{ color: c }} /></div>
                <p className="text-2xl font-black" style={{ ...TJ, color: C.navy }}>{n}</p>
                <p className="text-xs" style={{ ...TJ, color: C.gray }}>{l}</p>
              </div>
            ))}
          </div>
        </div>
        <div className="px-5 mb-3">
          <Card>
            <div className="flex items-center justify-between" dir="rtl">
              <div className="flex-1">
                <p className="font-bold text-sm" style={{ ...TJ, color: C.navy }}>تحديث الظهور اليومي</p>
                <p className="text-xs" style={{ ...TJ, color: C.gray }}>يخلي عقاراتك محدثة في نتايج البحث</p>
              </div>
              <div className="w-12 h-6 rounded-full relative mr-3" style={{ backgroundColor: C.teal }}>
                <div className="absolute right-1 top-1 w-4 h-4 rounded-full" style={{ backgroundColor: C.white }} />
              </div>
            </div>
          </Card>
        </div>
        <div className="px-5 mb-4">
          <SectionHead title="طلبات زيارة جديدة" action="عرض الكل" />
          <div className="flex flex-col gap-3">
            {[{ n: "سارة أحمد", t: "النهارده 3م", isNew: true }, { n: "محمد علي", t: "غداً 12م", isNew: false }].map((r, i) => (
              <Card key={i}>
                <div className="flex items-center gap-3 mb-3" dir="rtl">
                  <div className="w-10 h-10 rounded-full flex items-center justify-center" style={{ backgroundColor: C.tealLight }}><User size={18} style={{ color: C.teal }} /></div>
                  <div className="flex-1">
                    <div className="flex items-center gap-2"><p className="font-black text-sm" style={{ ...TJ, color: C.navy }}>{r.n}</p><Badge type="verified" /></div>
                    <p className="text-xs" style={{ ...TJ, color: C.gray }}>مدينة نصر · {r.t}</p>
                  </div>
                  {r.isNew && <span className="text-xs px-2 py-0.5 rounded-full font-black" style={{ backgroundColor: C.greenLight, ...TJ, color: C.green }}>جديد</span>}
                </div>
                <div className="flex gap-2">
                  <button className="flex-1 py-2 rounded-xl text-xs font-black text-white" style={{ backgroundColor: C.green, ...TJ }}>قبول</button>
                  <button className="flex-1 py-2 rounded-xl text-xs font-black" style={{ backgroundColor: C.redLight, color: C.red, ...TJ }}>رفض</button>
                  <button className="flex-1 py-2 rounded-xl text-xs font-black" style={{ backgroundColor: C.blueLight, color: C.blue, ...TJ }}>شات</button>
                </div>
              </Card>
            ))}
          </div>
        </div>
      </div>
      <OwnerNav active="home" />
      <div className="absolute bottom-20 left-5 w-14 h-14 rounded-2xl flex items-center justify-center shadow-lg" style={{ backgroundColor: C.teal }}>
        <Plus size={24} style={{ color: C.white }} />
      </div>
    </div>
  );
}

function OwnerDashboardEmpty() {
  return (
    <div className="flex flex-col h-full" style={{ backgroundColor: C.bg }}>
      <StatusBar />
      <div className="px-5 pt-1 pb-3" dir="rtl">
        <div className="flex items-center justify-between mb-3">
          <div><h1 className="text-xl font-black" style={{ ...TJ, color: C.navy }}>أهلاً يا أحمد</h1><p className="text-sm" style={{ ...TJ, color: C.gray }}>ابدأ بإضافة أول عقار ليك</p></div>
          <div className="w-10 h-10 rounded-full flex items-center justify-center" style={{ backgroundColor: C.tealLight }}><User size={18} style={{ color: C.teal }} /></div>
        </div>
        <WarnBanner text="حسابك تحت المراجعة — بعد الموافقة تقدر تضيف عقار" />
      </div>
      <div className="flex-1 flex flex-col items-center justify-center px-8 gap-5" dir="rtl">
        <div className="w-28 h-28 rounded-3xl flex items-center justify-center" style={{ backgroundColor: C.tealLight }}>
          <Building2 size={52} style={{ color: C.teal }} />
        </div>
        <div className="text-center">
          <h2 className="font-black text-xl mb-2" style={{ ...TJ, color: C.navy }}>لسه معندكش عقارات</h2>
          <p className="text-sm" style={{ ...TJ, color: C.gray }}>أضف أول عقارك وابدأ تستقبل طلبات الزيارة</p>
        </div>
        <div className="w-full flex flex-col gap-3"><PrimaryBtn text="إضافة عقار جديد" /><OutlineBtn text="عرض دليل الاستخدام" /></div>
      </div>
      <OwnerNav active="home" />
    </div>
  );
}

function OwnerMetricsScreen() {
  return (
    <div className="flex flex-col h-full" style={{ backgroundColor: C.bg }}>
      <StatusBar />
      <div className="px-5 pt-1 pb-3 flex items-center gap-3" dir="rtl">
        <button><ArrowLeft size={20} style={{ color: C.navy }} /></button>
        <h1 className="text-xl font-black flex-1" style={{ ...TJ, color: C.navy }}>تحليلات العقارات</h1>
        <span className="text-xs px-3 py-1 rounded-full font-bold" style={{ backgroundColor: C.tealLight, ...TJ, color: C.teal }}>آخر 30 يوم</span>
      </div>
      <div className="flex-1 overflow-y-auto px-5 pb-4" dir="rtl">
        <div className="grid grid-cols-2 gap-3 mb-4">
          {[{ n: "1,245", l: "مشاهدة", I: Eye, c: C.blue, bg: C.blueLight, t: "+12%" },
            { n: "38", l: "طلب زيارة", I: Calendar, c: C.teal, bg: C.tealLight, t: "+8%" },
            { n: "12", l: "زيارة مقبولة", I: CheckCircle, c: C.green, bg: C.greenLight, t: "+15%" },
            { n: "4.7", l: "متوسط التقييم", I: Star, c: C.amber, bg: C.amberLight, t: "ثابت" }].map(({ n, l, I, c, bg, t }, i) => (
            <div key={i} className="rounded-2xl p-4" style={{ backgroundColor: C.white, border: `1px solid ${C.border}` }}>
              <div className="flex items-center justify-between mb-2">
                <div className="w-8 h-8 rounded-xl flex items-center justify-center" style={{ backgroundColor: bg }}><I size={15} style={{ color: c }} /></div>
                <span className="text-xs font-bold" style={{ ...TJ, color: C.green }}>{t}</span>
              </div>
              <p className="text-2xl font-black" style={{ ...TJ, color: C.navy }}>{n}</p>
              <p className="text-xs" style={{ ...TJ, color: C.gray }}>{l}</p>
            </div>
          ))}
        </div>
        <Card className="mb-4">
          <p className="font-black text-base mb-3" style={{ ...TJ, color: C.navy }}>المشاهدات اليومية</p>
          <div className="flex items-end gap-1 justify-between" style={{ height: 80 }}>
            {[40, 65, 50, 80, 70, 90, 75, 88, 60, 95, 85, 100, 70, 90].map((h, i) => (
              <div key={i} className="flex-1 rounded-t-sm" style={{ height: `${h}%`, backgroundColor: i === 13 ? C.teal : `${C.teal}40` }} />
            ))}
          </div>
          <div className="flex justify-between mt-1">
            <span className="text-xs" style={{ ...TJ, color: C.gray }}>1 يناير</span>
            <span className="text-xs" style={{ ...TJ, color: C.gray }}>14 يناير</span>
          </div>
        </Card>
        <Card>
          <p className="font-black text-base mb-3" style={{ ...TJ, color: C.navy }}>أداء العقارات</p>
          {[{ t: "شقة مدينة نصر", v: "540", vs: "12" }, { t: "ستوديو التجمع", v: "380", vs: "8" }, { t: "شقة المهندسين", v: "325", vs: "6" }].map((p, i) => (
            <div key={i} className="flex items-center gap-3 py-2" style={{ borderBottom: i < 2 ? `1px solid ${C.border}` : "none" }}>
              <div className="w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0" style={{ backgroundColor: C.tealLight }}><Building2 size={15} style={{ color: C.teal }} /></div>
              <div className="flex-1"><p className="text-sm font-bold" style={{ ...TJ, color: C.navy }}>{p.t}</p><p className="text-xs" style={{ ...TJ, color: C.gray }}>{p.v} مشاهدة · {p.vs} زيارة</p></div>
            </div>
          ))}
        </Card>
      </div>
    </div>
  );
}

function BookingRequestsListScreen() {
  return (
    <div className="flex flex-col h-full" style={{ backgroundColor: C.bg }}>
      <StatusBar />
      <div className="px-5 pt-1 pb-3" dir="rtl">
        <h1 className="text-xl font-black mb-1" style={{ ...TJ, color: C.navy }}>طلبات الزيارة</h1>
        <div className="flex gap-2">
          {["الجديدة (3)", "المقبولة", "المرفوضة"].map((t, i) => (
            <button key={i} className="px-3 py-1.5 rounded-full text-xs font-bold"
              style={{ backgroundColor: i === 0 ? C.teal : C.white, color: i === 0 ? C.white : C.navy, border: `1px solid ${i === 0 ? C.teal : C.border}`, ...TJ }}>{t}</button>
          ))}
        </div>
      </div>
      <div className="flex-1 overflow-y-auto px-5 pb-4">
        <div className="flex flex-col gap-3">
          {[{ n: "سارة أحمد", p: "شقة مدينة نصر", t: "النهارده 3م", status: "جديد" },
            { n: "محمد علي", p: "شقة مدينة نصر", t: "غداً 12م", status: "جديد" },
            { n: "نورا كمال", p: "ستوديو التجمع", t: "الثلاثاء 5م", status: "قيد الانتظار" }].map((r, i) => (
            <Card key={i}>
              <div className="flex items-center gap-3 mb-3" dir="rtl">
                <div className="w-11 h-11 rounded-full flex items-center justify-center flex-shrink-0" style={{ backgroundColor: C.tealLight }}><User size={19} style={{ color: C.teal }} /></div>
                <div className="flex-1">
                  <div className="flex items-center gap-2"><p className="font-black text-base" style={{ ...TJ, color: C.navy }}>{r.n}</p><Badge type="verified" /></div>
                  <p className="text-xs" style={{ ...TJ, color: C.gray }}>{r.p} · {r.t}</p>
                </div>
                <span className="text-xs px-2 py-1 rounded-full font-black" style={{ backgroundColor: C.greenLight, ...TJ, color: C.green }}>{r.status}</span>
              </div>
              <div className="flex gap-2">
                <button className="flex-1 py-2 rounded-xl text-xs font-black text-white" style={{ backgroundColor: C.green, ...TJ }}>قبول</button>
                <button className="flex-1 py-2 rounded-xl text-xs font-black" style={{ backgroundColor: C.redLight, color: C.red, ...TJ }}>رفض</button>
                <button className="flex-1 py-2 rounded-xl text-xs font-black" style={{ backgroundColor: C.blueLight, color: C.blue, ...TJ }}>شات</button>
              </div>
            </Card>
          ))}
        </div>
      </div>
      <OwnerNav active="requests" />
    </div>
  );
}

function BookingRequestDetailScreen() {
  return (
    <div className="flex flex-col h-full" style={{ backgroundColor: C.bg }}>
      <StatusBar />
      <div className="px-5 pt-1 pb-3 flex items-center gap-3" dir="rtl">
        <button><ArrowLeft size={20} style={{ color: C.navy }} /></button>
        <h1 className="text-xl font-black flex-1" style={{ ...TJ, color: C.navy }}>تفاصيل طلب الزيارة</h1>
      </div>
      <div className="flex-1 overflow-y-auto px-5 pb-4" dir="rtl">
        <Card className="mb-4">
          <div className="flex items-center gap-4">
            <div className="w-14 h-14 rounded-full flex items-center justify-center" style={{ backgroundColor: C.tealLight }}><User size={26} style={{ color: C.teal }} /></div>
            <div>
              <div className="flex items-center gap-2"><p className="font-black text-lg" style={{ ...TJ, color: C.navy }}>سارة أحمد خالد</p><Badge type="verified" /></div>
              <div className="flex items-center gap-1"><Star size={12} fill={C.amber} style={{ color: C.amber }} /><span className="text-xs" style={{ ...TJ, color: C.gray }}>4.9 (12 تقييم كمستأجر)</span></div>
              <p className="text-xs" style={{ ...TJ, color: C.gray }}>010****432</p>
            </div>
          </div>
        </Card>
        <Card className="mb-4">
          <p className="font-black text-base mb-3" style={{ ...TJ, color: C.navy }}>تفاصيل الزيارة</p>
          {[["العقار", "شقة مدينة نصر"], ["الموعد المطلوب", "النهارده 3:00 م"], ["تاريخ الطلب", "14 يناير 2026"], ["الحالة", "بانتظار موافقتك"]].map(([l, v], i) => (
            <div key={i} className="flex justify-between py-2" style={{ borderBottom: i < 3 ? `1px solid ${C.border}` : "none" }}>
              <span className="text-sm font-bold" style={{ ...TJ, color: C.navy }}>{v}</span>
              <span className="text-xs" style={{ ...TJ, color: C.gray }}>{l}</span>
            </div>
          ))}
        </Card>
        <div className="px-4 py-3 rounded-2xl mb-4" style={{ backgroundColor: C.bg, border: `1px solid ${C.border}` }}>
          <p className="text-xs font-black mb-1" style={{ ...TJ, color: C.navy }}>ملاحظة من المستأجر:</p>
          <p className="text-sm" style={{ ...TJ, color: C.gray }}>أنا مهتم جداً بالشقة، هل ممكن تعرفني على تفاصيل التعاقد؟</p>
        </div>
        <PrivacyBanner text="رقم المستأجر مخفي — يظهر لك بعد القبول فقط" />
        <div className="flex flex-col gap-3 mt-4">
          <button className="w-full py-4 rounded-2xl font-black text-white flex items-center justify-center gap-2" style={{ backgroundColor: C.green, ...TJ }}>
            <Check size={18} />قبول الزيارة
          </button>
          <button className="w-full py-4 rounded-2xl font-black flex items-center justify-center gap-2" style={{ backgroundColor: C.redLight, color: C.red, ...TJ }}>
            <X size={18} />رفض الزيارة
          </button>
          <OutlineBtn text="فتح الشات" />
        </div>
      </div>
    </div>
  );
}

function AcceptVisitScreen() {
  return (
    <div className="flex flex-col h-full" style={{ backgroundColor: "rgba(0,0,0,0.4)" }}>
      <div className="flex-1" />
      <div className="rounded-t-3xl px-6 py-6" style={{ backgroundColor: C.white }}>
        <div className="w-12 h-1.5 rounded-full mx-auto mb-5" style={{ backgroundColor: C.border }} />
        <div className="text-center mb-5" dir="rtl">
          <div className="w-14 h-14 rounded-full flex items-center justify-center mx-auto mb-3" style={{ backgroundColor: C.greenLight }}><CheckCircle size={26} style={{ color: C.green }} /></div>
          <h2 className="text-xl font-black mb-1" style={{ ...TJ, color: C.navy }}>قبول الزيارة</h2>
          <p className="text-sm" style={{ ...TJ, color: C.gray }}>هيتم إخطار سارة أحمد بموافقتك</p>
        </div>
        <Card className="mb-4">
          {[["المستأجر", "سارة أحمد"], ["الموعد", "النهارده 3:00 م"], ["العقار", "شقة مدينة نصر"]].map(([l, v], i) => (
            <div key={i} className="flex justify-between py-2" style={{ borderBottom: i < 2 ? `1px solid ${C.border}` : "none" }} dir="rtl">
              <span className="text-sm font-bold" style={{ ...TJ, color: C.navy }}>{v}</span>
              <span className="text-xs" style={{ ...TJ, color: C.gray }}>{l}</span>
            </div>
          ))}
        </Card>
        <div className="px-4 py-3 rounded-2xl mb-4" style={{ backgroundColor: C.greenLight }}>
          <div className="flex items-center gap-2"><Phone size={13} style={{ color: C.green }} /><p className="text-xs" style={{ ...TJ, color: "#166534" }}>بعد القبول — رقم المستأجر هيظهر ليك</p></div>
        </div>
        <div className="flex gap-3">
          <button className="flex-1 py-4 rounded-2xl font-black text-white" style={{ backgroundColor: C.green, ...TJ }}>تأكيد القبول</button>
          <button className="flex-1 py-4 rounded-2xl font-black border" style={{ borderColor: C.border, ...TJ, color: C.gray }}>إلغاء</button>
        </div>
      </div>
    </div>
  );
}

function RejectVisitScreen() {
  return (
    <div className="flex flex-col h-full" style={{ backgroundColor: "rgba(0,0,0,0.4)" }}>
      <div className="flex-1" />
      <div className="rounded-t-3xl px-6 py-6" style={{ backgroundColor: C.white }}>
        <div className="w-12 h-1.5 rounded-full mx-auto mb-5" style={{ backgroundColor: C.border }} />
        <div className="text-center mb-5" dir="rtl">
          <div className="w-14 h-14 rounded-full flex items-center justify-center mx-auto mb-3" style={{ backgroundColor: C.redLight }}><X size={26} style={{ color: C.red }} /></div>
          <h2 className="text-xl font-black mb-1" style={{ ...TJ, color: C.navy }}>رفض الزيارة</h2>
          <p className="text-sm" style={{ ...TJ, color: C.gray }}>اختار سبب الرفض (اختياري)</p>
        </div>
        <div className="flex flex-col gap-2 mb-4" dir="rtl">
          {["الميعاد المطلوب مش مناسب", "العقار اتأجر", "محتاج معلومات أكتر", "سبب تاني"].map((r, i) => (
            <button key={i} className="flex items-center gap-3 px-4 py-3 rounded-2xl text-right"
              style={{ backgroundColor: i === 0 ? C.redLight : C.bg, border: `1px solid ${i === 0 ? C.red : C.border}` }}>
              <div className="w-5 h-5 rounded-full border-2 flex items-center justify-center" style={{ borderColor: i === 0 ? C.red : C.border }}>
                {i === 0 && <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: C.red }} />}
              </div>
              <span className="text-sm" style={{ ...TJ, color: C.navy }}>{r}</span>
            </button>
          ))}
        </div>
        <div className="flex gap-3">
          <button className="flex-1 py-4 rounded-2xl font-black text-white" style={{ backgroundColor: C.red, ...TJ }}>تأكيد الرفض</button>
          <button className="flex-1 py-4 rounded-2xl font-black border" style={{ borderColor: C.border, ...TJ, color: C.gray }}>إلغاء</button>
        </div>
      </div>
    </div>
  );
}

function OwnerChatScreen() {
  return (
    <div className="flex flex-col h-full" style={{ backgroundColor: C.bg }}>
      <StatusBar />
      <div className="px-5 py-3 flex items-center gap-3" style={{ backgroundColor: C.white, borderBottom: `1px solid ${C.border}` }}>
        <button><ArrowLeft size={20} style={{ color: C.navy }} /></button>
        <div className="w-10 h-10 rounded-full flex items-center justify-center" style={{ backgroundColor: C.blueLight }}><User size={20} style={{ color: C.blue }} /></div>
        <div className="flex-1" dir="rtl">
          <div className="flex items-center gap-2"><p className="font-black text-base" style={{ ...TJ, color: C.navy }}>سارة أحمد</p><Badge type="verified" /></div>
          <p className="text-xs" style={{ ...TJ, color: C.gray }}>طلب زيارة · شقة مدينة نصر</p>
        </div>
        <span className="text-xs px-2 py-1 rounded-full font-bold" style={{ backgroundColor: C.greenLight, ...TJ, color: C.green }}>مقبول</span>
      </div>
      <div className="px-4 py-2"><PrivacyBanner text="رقم المستأجر مرئي بعد القبول: 010****432" /></div>
      <div className="flex-1 overflow-y-auto px-5 py-3 flex flex-col gap-3">
        {[{ mine: true, text: "أهلاً يا سارة! طلب الزيارة اتقبل، موعدك الساعة 3 م النهارده" },
          { mine: false, text: "شكراً جداً! هكون موجودة في الوقت" },
          { mine: true, text: "ممتاز، العنوان: شارع عباس العقاد، مدينة نصر، الدور 5" }].map((m, i) => (
          <div key={i} className={`flex ${m.mine ? "justify-start" : "justify-end"}`}>
            <div className="max-w-xs px-4 py-2.5 text-sm" dir="rtl"
              style={{ backgroundColor: m.mine ? C.teal : C.white, color: m.mine ? C.white : C.navy, border: m.mine ? "none" : `1px solid ${C.border}`, ...TJ,
                borderRadius: m.mine ? "16px 4px 16px 16px" : "4px 16px 16px 16px" }}>
              {m.text}
            </div>
          </div>
        ))}
      </div>
      <div className="px-4 py-3 flex items-center gap-2" style={{ backgroundColor: C.white, borderTop: `1px solid ${C.border}` }}>
        <div className="flex-1 flex items-center px-3 py-2 rounded-2xl gap-2" style={{ backgroundColor: C.bg }}>
          <input placeholder="اكتب رسالة…" dir="rtl" readOnly className="flex-1 text-sm outline-none bg-transparent" style={{ ...TJ }} />
        </div>
        <button className="w-9 h-9 rounded-full flex items-center justify-center" style={{ backgroundColor: C.teal }}><Send size={15} style={{ color: C.white }} /></button>
      </div>
    </div>
  );
}

function AddPropertyIntroScreen() {
  return (
    <div className="flex flex-col h-full" style={{ backgroundColor: C.bg }}>
      <StatusBar />
      <div className="flex-1 overflow-y-auto px-5 py-4" dir="rtl">
        <div className="flex items-center gap-2 mb-4">
          <button><ArrowLeft size={20} style={{ color: C.navy }} /></button>
          <h1 className="text-xl font-black flex-1" style={{ ...TJ, color: C.navy }}>أضف عقار جديد</h1>
        </div>
        <p className="text-sm mb-5" style={{ ...TJ, color: C.gray }}>كمّل البيانات وارفع الصور — العقار هيدخل المراجعة قبل ظهوره</p>
        <div className="flex flex-col gap-3 mb-5">
          {[{ s: 1, t: "صور وفيديوهات", I: ImageIcon, c: C.blue, bg: C.blueLight },
            { s: 2, t: "بيانات العقار", I: FileText, c: C.teal, bg: C.tealLight },
            { s: 3, t: "الموقع", I: MapPin, c: C.green, bg: C.greenLight },
            { s: 4, t: "تفاصيل المساحة والغرف", I: Building2, c: C.amber, bg: C.amberLight },
            { s: 5, t: "المرافق", I: Wifi, c: C.blue, bg: C.blueLight },
            { s: 6, t: "مراجعة وإرسال", I: CheckCircle, c: C.green, bg: C.greenLight }].map(({ s, t, I, c, bg }) => (
            <div key={s} className="flex items-center gap-3 p-4 rounded-2xl" style={{ backgroundColor: C.white, border: `1px solid ${C.border}` }}>
              <div className="w-10 h-10 rounded-xl flex items-center justify-center" style={{ backgroundColor: bg }}><I size={17} style={{ color: c }} /></div>
              <p className="font-bold text-sm flex-1" style={{ ...TJ, color: C.navy }}>{t}</p>
              <div className="w-6 h-6 rounded-full flex items-center justify-center text-xs font-black" style={{ backgroundColor: C.bg, color: C.gray, ...TJ }}>{s}</div>
            </div>
          ))}
        </div>
        <WarnBanner text="العقار مش هيظهر في البحث غير بعد المراجعة" />
        <div className="mt-4"><PrimaryBtn text="ابدأ الإضافة" /></div>
      </div>
    </div>
  );
}

function AddPropertyMediaScreen() {
  return (
    <div className="flex flex-col h-full" style={{ backgroundColor: C.bg }}>
      <StatusBar />
      <div className="flex-1 overflow-y-auto px-5 py-4" dir="rtl">
        <StepProgress step={1} total={6} />
        <h1 className="text-xl font-black mb-1" style={{ ...TJ, color: C.navy }}>صور وفيديوهات العقار</h1>
        <p className="text-xs mb-4" style={{ ...TJ, color: C.gray }}>· ارفع من 9 إلى 10 صور واضحة · يمكن رفع حتى 2 فيديو</p>
        <div className="grid grid-cols-3 gap-2 mb-4">
          {Array.from({ length: 10 }).map((_, i) => (
            <div key={i} className="aspect-square rounded-2xl flex items-center justify-center"
              style={{ backgroundColor: i < 5 ? "#E2E8F0" : C.white, border: i < 5 ? "1px solid #CBD5E1" : `1px dashed ${C.border}` }}>
              {i < 5 ? (
                <div className="relative w-full h-full flex items-center justify-center rounded-2xl">
                  <Building2 size={18} style={{ color: "#94A3B8" }} />
                  <button className="absolute top-1 right-1 w-5 h-5 rounded-full flex items-center justify-center" style={{ backgroundColor: "rgba(0,0,0,0.5)" }}>
                    <X size={10} style={{ color: C.white }} />
                  </button>
                </div>
              ) : <Plus size={16} style={{ color: C.gray }} />}
            </div>
          ))}
        </div>
        <Card className="mb-4">
          <p className="font-black text-sm mb-2" style={{ ...TJ, color: C.navy }}>إرشادات الصور</p>
          {["صوّر كل الغرف", "صوّر الحمام والمطبخ", "صور واضحة بدون فلاتر", "ممنوع صور مستندات أو أرقام"].map((t, i) => (
            <div key={i} className="flex items-center gap-2 mb-1"><Check size={12} style={{ color: C.teal }} /><p className="text-xs" style={{ ...TJ, color: C.gray }}>{t}</p></div>
          ))}
        </Card>
        <PrimaryBtn text="التالي: بيانات العقار" />
      </div>
    </div>
  );
}

function AddPropertyBasicDetailsScreen() {
  return (
    <div className="flex flex-col h-full" style={{ backgroundColor: C.bg }}>
      <StatusBar />
      <div className="flex-1 overflow-y-auto px-5 py-4" dir="rtl">
        <StepProgress step={2} total={6} />
        <h1 className="text-xl font-black mb-1" style={{ ...TJ, color: C.navy }}>بيانات العقار</h1>
        <div className="flex flex-col gap-4 mb-4">
          <TextInput label="عنوان العقار" placeholder="مثال: شقة مفروشة قريبة من عباس العقاد" />
          <div>
            <label className="text-sm font-bold mb-1.5 block" style={{ ...TJ, color: C.navy }}>نوع السكن</label>
            <div className="flex gap-2">
              {["شقة", "ستوديو", "غرفة", "دوبلكس"].map((t, i) => (
                <button key={i} className="flex-1 py-2.5 rounded-xl text-sm font-bold border"
                  style={{ backgroundColor: i === 0 ? C.teal : C.white, color: i === 0 ? C.white : C.navy, borderColor: i === 0 ? C.teal : C.border, ...TJ }}>{t}</button>
              ))}
            </div>
          </div>
          <TextInput label="السعر الشهري (ج.م)" placeholder="مثال: 12000" type="number" />
          <div>
            <label className="text-sm font-bold mb-1.5 block" style={{ ...TJ, color: C.navy }}>الوصف</label>
            <textarea dir="rtl" readOnly placeholder="اكتب وصفاً مفصلاً للشقة…" className="w-full px-4 py-3 rounded-2xl border text-sm outline-none resize-none"
              style={{ borderColor: C.border, ...TJ, color: C.navy, height: 100 }} />
          </div>
          <TextInput label="المنطقة" placeholder="مثال: مدينة نصر، القاهرة" />
        </div>
        <div className="flex gap-3"><OutlineBtn text="رجوع" /><PrimaryBtn text="التالي: الموقع" /></div>
      </div>
    </div>
  );
}

function AddPropertyMapScreen() {
  return (
    <div className="flex flex-col h-full" style={{ backgroundColor: C.bg }}>
      <StatusBar />
      <div className="flex-1 flex flex-col px-5 py-4" dir="rtl">
        <StepProgress step={3} total={6} />
        <h1 className="text-xl font-black mb-1" style={{ ...TJ, color: C.navy }}>تحديد الموقع</h1>
        <p className="text-sm mb-3" style={{ ...TJ, color: C.gray }}>الموقع المعروض للمستأجرين يكون تقريبي — لحماية خصوصيتك</p>
        <div className="rounded-3xl flex items-center justify-center mb-4" style={{ backgroundColor: "#E5E7EB", minHeight: 260 }}>
          <div className="text-center">
            <div className="relative inline-block">
              <Map size={52} style={{ color: "#94A3B8" }} />
              <div className="absolute -top-2 -right-2 w-8 h-8 rounded-full flex items-center justify-center" style={{ backgroundColor: C.teal }}>
                <MapPin size={14} style={{ color: C.white }} />
              </div>
            </div>
            <p className="text-xs mt-2" style={{ ...TJ, color: "#94A3B8" }}>اضغط لتحديد الموقع</p>
          </div>
        </div>
        <TextInput label="العنوان الكامل (للمراجعة الداخلية فقط)" placeholder="شارع، مبنى، دور…" />
        <div className="mt-3 mb-4"><PrivacyBanner text="العنوان الكامل ما بيتعرضش للمستأجر — يظهر موقع تقريبي فقط" /></div>
        <div className="flex gap-3"><OutlineBtn text="رجوع" /><PrimaryBtn text="التالي: تفاصيل المساحة" /></div>
      </div>
    </div>
  );
}

function AddPropertyStructureScreen() {
  return (
    <div className="flex flex-col h-full" style={{ backgroundColor: C.bg }}>
      <StatusBar />
      <div className="flex-1 overflow-y-auto px-5 py-4" dir="rtl">
        <StepProgress step={4} total={6} />
        <h1 className="text-xl font-black mb-4" style={{ ...TJ, color: C.navy }}>تفاصيل المساحة والغرف</h1>
        <div className="flex flex-col gap-5 mb-5">
          {[["الغرف", "3"], ["الحمامات", "2"]].map(([l, v], i) => (
            <div key={i}>
              <label className="text-sm font-black mb-2 block" style={{ ...TJ, color: C.navy }}>{l}</label>
              <div className="flex items-center gap-3">
                <button className="w-10 h-10 rounded-xl flex items-center justify-center" style={{ backgroundColor: C.bg, border: `1px solid ${C.border}` }}><Minus size={16} style={{ color: C.navy }} /></button>
                <span className="text-2xl font-black flex-1 text-center" style={{ ...TJ, color: C.navy }}>{v}</span>
                <button className="w-10 h-10 rounded-xl flex items-center justify-center" style={{ backgroundColor: C.teal }}><Plus size={16} style={{ color: C.white }} /></button>
              </div>
            </div>
          ))}
          <TextInput label="المساحة (م²)" placeholder="120" type="number" />
          <TextInput label="الدور" placeholder="5" type="number" />
        </div>
        <div className="flex gap-3"><OutlineBtn text="رجوع" /><PrimaryBtn text="التالي: المرافق" /></div>
      </div>
    </div>
  );
}

function AddPropertyAmenitiesScreen() {
  const amenities = ["WiFi", "أسانسير", "جراج", "مفروش", "بلكونة", "أمن 24/7", "تكييف", "غاز طبيعي", "أرضية خشب", "غرفة سواق"];
  const [sel, setSel] = useState([0, 1, 3, 4]);
  return (
    <div className="flex flex-col h-full" style={{ backgroundColor: C.bg }}>
      <StatusBar />
      <div className="flex-1 overflow-y-auto px-5 py-4" dir="rtl">
        <StepProgress step={5} total={6} />
        <h1 className="text-xl font-black mb-1" style={{ ...TJ, color: C.navy }}>المرافق والخدمات</h1>
        <p className="text-sm mb-4" style={{ ...TJ, color: C.gray }}>اختار كل المرافق المتاحة في العقار</p>
        <div className="flex flex-wrap gap-2 mb-6">
          {amenities.map((a, i) => {
            const on = sel.includes(i);
            return (
              <button key={i} onClick={() => setSel(p => p.includes(i) ? p.filter(x => x !== i) : [...p, i])}
                className="flex items-center gap-2 px-4 py-2.5 rounded-2xl text-sm font-bold border"
                style={{ backgroundColor: on ? C.tealLight : C.white, color: on ? C.teal : C.gray, borderColor: on ? C.teal : C.border, ...TJ }}>
                {on && <Check size={13} />}{a}
              </button>
            );
          })}
        </div>
        <Card className="mb-4"><p className="text-xs" style={{ ...TJ, color: C.gray }}>المرافق المختارة: <span className="font-black" style={{ color: C.navy }}>{sel.length}</span></p></Card>
        <div className="flex gap-3"><OutlineBtn text="رجوع" /><PrimaryBtn text="التالي: مراجعة" /></div>
      </div>
    </div>
  );
}

function AddPropertyReviewScreen() {
  return (
    <div className="flex flex-col h-full" style={{ backgroundColor: C.bg }}>
      <StatusBar />
      <div className="flex-1 overflow-y-auto px-5 py-4" dir="rtl">
        <StepProgress step={6} total={6} />
        <h1 className="text-xl font-black mb-1" style={{ ...TJ, color: C.navy }}>مراجعة وإرسال</h1>
        <div className="mb-3 rounded-2xl overflow-hidden flex items-center justify-center" style={{ height: 140, backgroundColor: "#E2E8F0", position: "relative" }}>
          <Building2 size={40} style={{ color: "#94A3B8" }} />
          <span className="absolute bottom-3 right-3 px-2 py-0.5 rounded-lg text-xs font-bold text-white" style={{ backgroundColor: "rgba(0,0,0,0.6)" }}>5 صور</span>
        </div>
        <Card className="mb-3">
          {[["العنوان", "شقة مفروشة قريبة من عباس العقاد"], ["النوع", "شقة"], ["السعر", "12,000 ج.م/شهر"],
            ["المنطقة", "مدينة نصر"], ["الغرف", "3"], ["الحمامات", "2"], ["المساحة", "120 م²"],
            ["المرافق", "WiFi، أسانسير، مفروش، بلكونة"]].map(([l, v], i) => (
            <div key={i} className="flex justify-between py-2" style={{ borderBottom: i < 7 ? `1px solid ${C.border}` : "none" }}>
              <span className="text-sm font-bold" style={{ ...TJ, color: C.navy }}>{v}</span>
              <span className="text-xs" style={{ ...TJ, color: C.gray }}>{l}</span>
            </div>
          ))}
        </Card>
        <WarnBanner text="العقار هيمر بمراجعة من الفريق قبل ظهوره في البحث" />
        <div className="flex flex-col gap-3 mt-4"><PrimaryBtn text="إرسال للمراجعة" /><OutlineBtn text="تعديل البيانات" /></div>
      </div>
    </div>
  );
}

function PropertyPendingReviewScreen() {
  return (
    <div className="flex flex-col h-full" style={{ backgroundColor: C.bg }}>
      <StatusBar />
      <div className="flex-1 overflow-y-auto px-5 py-4" dir="rtl">
        <div className="text-center py-5 mb-4">
          <div className="w-20 h-20 rounded-full flex items-center justify-center mx-auto mb-3" style={{ backgroundColor: C.amberLight }}><FileText size={36} style={{ color: C.amber }} /></div>
          <Badge type="pending" />
          <h1 className="text-xl font-black mt-3" style={{ ...TJ, color: C.navy }}>عقارك قيد المراجعة</h1>
          <p className="text-sm mt-1" style={{ ...TJ, color: C.gray }}>هنراجع الصور والبيانات والموقع قبل الظهور في البحث</p>
        </div>
        <Card className="mb-4">
          <p className="font-black text-sm mb-3" style={{ ...TJ, color: C.navy }}>مراحل المراجعة</p>
          {[{ s: "تم استلام البيانات", done: true }, { s: "مراجعة الصور والموقع", active: true }, { s: "تحديث حالة العقار", done: false }].map((item, i) => (
            <div key={i} className="flex items-center gap-3 py-2">
              <div className="w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0"
                style={{ backgroundColor: item.done ? C.greenLight : item.active ? C.amberLight : C.border }}>
                {item.done ? <Check size={12} style={{ color: C.green }} /> : item.active ? <Clock size={12} style={{ color: C.amber }} /> : <div className="w-2 h-2 rounded-full" style={{ backgroundColor: C.gray }} />}
              </div>
              <p className="text-sm" style={{ ...TJ, color: item.done ? C.navy : item.active ? C.amber : C.gray, fontWeight: item.active ? 700 : 400 }}>{item.s}</p>
            </div>
          ))}
        </Card>
        <div className="flex flex-col gap-3"><PrimaryBtn text="عرض عقاراتي" /><OutlineBtn text="إضافة عقار آخر" /></div>
      </div>
    </div>
  );
}

function MyPropertiesScreen() {
  return (
    <div className="flex flex-col h-full" style={{ backgroundColor: C.bg }}>
      <StatusBar />
      <div className="px-5 pt-1 pb-3" dir="rtl">
        <div className="flex items-center justify-between">
          <h1 className="text-xl font-black" style={{ ...TJ, color: C.navy }}>عقاراتي</h1>
          <button className="flex items-center gap-1 px-3 py-2 rounded-xl font-bold text-sm text-white" style={{ backgroundColor: C.teal, ...TJ }}>
            <Plus size={14} />إضافة
          </button>
        </div>
        <div className="flex gap-2 mt-2">
          {["الكل (3)", "نشط", "قيد المراجعة", "مخفي"].map((t, i) => (
            <button key={i} className="px-3 py-1 rounded-full text-xs font-bold"
              style={{ backgroundColor: i === 0 ? C.teal : C.white, color: i === 0 ? C.white : C.navy, border: `1px solid ${i === 0 ? C.teal : C.border}`, ...TJ }}>{t}</button>
          ))}
        </div>
      </div>
      <div className="flex-1 overflow-y-auto px-5 pb-4">
        {[{ t: "شقة مفروشة، مدينة نصر", p: "12,000", bType: "approved" as BadgeType, v: 540, vs: 12 },
          { t: "ستوديو، التجمع الخامس", p: "7,500", bType: "pending" as BadgeType, v: 0, vs: 0 },
          { t: "شقة، المهندسين", p: "9,000", bType: "hidden" as BadgeType, v: 325, vs: 6 }].map((item, i) => (
          <div key={i} className="rounded-3xl overflow-hidden mb-3" style={{ backgroundColor: C.white, border: `1px solid ${C.border}` }}>
            <div className="flex items-center gap-3 p-4" dir="rtl">
              <div className="flex-shrink-0 rounded-2xl flex items-center justify-center" style={{ width: 80, height: 80, backgroundColor: "#E2E8F0" }}>
                <Building2 size={24} style={{ color: "#94A3B8" }} />
              </div>
              <div className="flex-1">
                <div className="mb-1"><Badge type={item.bType} /></div>
                <p className="font-black text-sm" style={{ ...TJ, color: C.navy }}>{item.t}</p>
                <p className="font-bold" style={{ ...TJ, color: C.teal }}>{item.p} ج.م/شهر</p>
                <div className="flex gap-3 mt-1">
                  <span className="text-xs" style={{ ...TJ, color: C.gray }}>{item.v} مشاهدة</span>
                  <span className="text-xs" style={{ ...TJ, color: C.gray }}>{item.vs} زيارة</span>
                </div>
              </div>
              <button><ChevronRight size={18} style={{ color: C.gray }} /></button>
            </div>
          </div>
        ))}
      </div>
      <OwnerNav active="props" />
    </div>
  );
}

function PropertyStatusDetailScreen() {
  return (
    <div className="flex flex-col h-full" style={{ backgroundColor: C.bg }}>
      <StatusBar />
      <div className="px-5 pt-1 pb-3 flex items-center gap-3" dir="rtl">
        <button><ArrowLeft size={20} style={{ color: C.navy }} /></button>
        <h1 className="text-xl font-black flex-1" style={{ ...TJ, color: C.navy }}>حالة العقار</h1>
        <button><Edit2 size={18} style={{ color: C.teal }} /></button>
      </div>
      <div className="flex-1 overflow-y-auto px-5 pb-4" dir="rtl">
        <div className="mb-3 rounded-2xl overflow-hidden flex items-center justify-center" style={{ height: 160, backgroundColor: "#E2E8F0", position: "relative" }}>
          <Building2 size={40} style={{ color: "#94A3B8" }} />
          <div className="absolute top-3 right-3"><Badge type="approved" text="نشط" /></div>
        </div>
        <Card className="mb-3">
          {[["الاسم", "شقة مفروشة، مدينة نصر"], ["السعر", "12,000 ج.م/شهر"], ["الحالة", "نشط"],
            ["المشاهدات", "540"], ["طلبات الزيارة", "12"], ["آخر تحديث", "اليوم 9:30 ص"]].map(([l, v], i) => (
            <div key={i} className="flex justify-between py-2" style={{ borderBottom: i < 5 ? `1px solid ${C.border}` : "none" }}>
              <span className="text-sm font-bold" style={{ ...TJ, color: C.navy }}>{v}</span>
              <span className="text-xs" style={{ ...TJ, color: C.gray }}>{l}</span>
            </div>
          ))}
        </Card>
        <div className="flex gap-2">
          {[["إخفاء", C.gray, C.bg, C.border], ["تأجير", C.blue, C.blueLight, C.border], ["حذف", C.red, C.redLight, C.red]].map(([t, color, bg, border], i) => (
            <button key={i} className="flex-1 py-2.5 rounded-xl text-xs font-bold"
              style={{ backgroundColor: bg as string, color: color as string, border: `1px solid ${border}`, ...TJ }}>{t}</button>
          ))}
        </div>
      </div>
    </div>
  );
}

function EditPropertyScreen() {
  return (
    <div className="flex flex-col h-full" style={{ backgroundColor: C.bg }}>
      <StatusBar />
      <div className="px-5 pt-1 pb-3 flex items-center gap-3" dir="rtl">
        <button><ArrowLeft size={20} style={{ color: C.navy }} /></button>
        <h1 className="text-xl font-black flex-1" style={{ ...TJ, color: C.navy }}>تعديل العقار</h1>
        <button className="text-sm font-black" style={{ ...TJ, color: C.teal }}>حفظ</button>
      </div>
      <div className="flex-1 overflow-y-auto px-5 pb-4" dir="rtl">
        <WarnBanner text="أي تعديل هيعرض العقار للمراجعة تاني" />
        <div className="flex flex-col gap-4 mt-4">
          <TextInput label="عنوان العقار" placeholder="شقة مفروشة قريبة من عباس العقاد" />
          <TextInput label="السعر الشهري (ج.م)" placeholder="12000" type="number" />
          <div>
            <label className="text-sm font-black mb-1.5 block" style={{ ...TJ, color: C.navy }}>الوصف</label>
            <textarea dir="rtl" readOnly placeholder="وصف الشقة…" className="w-full px-4 py-3 rounded-2xl border text-sm outline-none resize-none"
              style={{ borderColor: C.border, ...TJ, color: C.navy, height: 90 }} />
          </div>
          <TextInput label="المنطقة" placeholder="مدينة نصر، القاهرة" />
        </div>
        <div className="mt-5 flex gap-3"><OutlineBtn text="إلغاء" /><PrimaryBtn text="حفظ التعديلات" /></div>
      </div>
    </div>
  );
}

function PropertyActionSheetsScreen() {
  return (
    <div className="flex flex-col h-full" style={{ backgroundColor: C.bg }}>
      <StatusBar />
      <div className="flex-1 overflow-y-auto px-5 py-3" dir="rtl">
        <h1 className="text-xl font-black mb-1" style={{ ...TJ, color: C.navy }}>إجراءات العقار</h1>
        <p className="text-xs mb-4" style={{ ...TJ, color: C.gray }}>ثلاث حالات مختلفة لـ bottom sheet</p>
        <Card className="mb-3">
          <p className="font-black text-sm mb-3" style={{ ...TJ, color: C.gray }}>Sheet 1 — إخفاء مؤقت</p>
          <div className="flex items-center gap-3 mb-3">
            <div className="w-10 h-10 rounded-xl flex items-center justify-center" style={{ backgroundColor: "#F3F4F6" }}><EyeOff size={18} style={{ color: C.gray }} /></div>
            <div><p className="font-bold text-sm" style={{ ...TJ, color: C.navy }}>إخفاء العقار مؤقتاً</p><p className="text-xs" style={{ ...TJ, color: C.gray }}>العقار مش هيظهر في البحث</p></div>
          </div>
          <div className="flex gap-2">
            <button className="flex-1 py-2 rounded-xl text-xs font-bold" style={{ backgroundColor: "#F3F4F6", ...TJ, color: C.gray }}>تأكيد الإخفاء</button>
            <button className="flex-1 py-2 rounded-xl text-xs font-bold border" style={{ borderColor: C.border, ...TJ, color: C.navy }}>إلغاء</button>
          </div>
        </Card>
        <Card className="mb-3">
          <p className="font-black text-sm mb-3" style={{ ...TJ, color: C.blue }}>Sheet 2 — تأجير</p>
          <div className="flex items-center gap-3 mb-3">
            <div className="w-10 h-10 rounded-xl flex items-center justify-center" style={{ backgroundColor: C.blueLight }}><Key size={18} style={{ color: C.blue }} /></div>
            <div><p className="font-bold text-sm" style={{ ...TJ, color: C.navy }}>تحديد كـ "تم تأجيره"</p><p className="text-xs" style={{ ...TJ, color: C.gray }}>العقار هيظهر كمؤجر — مش متاح للحجز</p></div>
          </div>
          <div className="flex gap-2">
            <button className="flex-1 py-2 rounded-xl text-xs font-bold text-white" style={{ backgroundColor: C.blue, ...TJ }}>تأكيد التأجير</button>
            <button className="flex-1 py-2 rounded-xl text-xs font-bold border" style={{ borderColor: C.border, ...TJ, color: C.navy }}>إلغاء</button>
          </div>
        </Card>
        <Card>
          <p className="font-black text-sm mb-3" style={{ ...TJ, color: C.red }}>Sheet 3 — حذف نهائي</p>
          <div className="flex items-center gap-3 mb-3">
            <div className="w-10 h-10 rounded-xl flex items-center justify-center" style={{ backgroundColor: C.redLight }}><Trash2 size={18} style={{ color: C.red }} /></div>
            <div><p className="font-bold text-sm" style={{ ...TJ, color: C.navy }}>حذف العقار نهائياً</p><p className="text-xs" style={{ ...TJ, color: C.red }}>العملية لا يمكن التراجع عنها</p></div>
          </div>
          <div className="flex gap-2">
            <button className="flex-1 py-2 rounded-xl text-xs font-bold text-white" style={{ backgroundColor: C.red, ...TJ }}>حذف نهائي</button>
            <button className="flex-1 py-2 rounded-xl text-xs font-bold border" style={{ borderColor: C.border, ...TJ, color: C.navy }}>إلغاء</button>
          </div>
        </Card>
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════
//  ADMIN SCREENS  (5 desktop screens)
// ═══════════════════════════════════════════════

function AdminSidebar({ active }: { active: string }) {
  const items = [{ id: "dashboard", I: Home }, { id: "users", I: Users }, { id: "kyc", I: CheckCircle }, { id: "properties", I: Building2 }, { id: "analytics", I: BarChart2 }, { id: "settings", I: Settings }];
  return (
    <div className="w-14 flex flex-col items-center py-3 gap-2 flex-shrink-0" style={{ backgroundColor: C.darkCard }}>
      <div className="w-9 h-9 rounded-xl flex items-center justify-center mb-2" style={{ backgroundColor: C.teal }}>
        <Shield size={16} style={{ color: C.white }} />
      </div>
      {items.map(({ id, I }) => (
        <button key={id} className="w-9 h-9 rounded-xl flex items-center justify-center"
          style={{ backgroundColor: id === active ? C.teal : "transparent" }}>
          <I size={16} style={{ color: id === active ? C.white : "#64748B" }} />
        </button>
      ))}
    </div>
  );
}

function AdminLoginScreen() {
  return (
    <div className="flex h-full" style={{ backgroundColor: C.dark }}>
      <div className="flex-1 flex flex-col items-center justify-center px-10" style={{ backgroundColor: C.darkCard }}>
        <div className="text-center mb-8">
          <div className="w-16 h-16 rounded-2xl flex items-center justify-center mx-auto mb-4" style={{ backgroundColor: C.teal }}>
            <Shield size={28} style={{ color: C.white }} />
          </div>
          <h1 className="text-4xl font-black text-white mb-1" style={{ ...TJ }}>سكون</h1>
          <p className="text-sm" style={{ ...TJ, color: C.darkMuted }}>لوحة إدارة سكون</p>
        </div>
        <div className="grid grid-cols-2 gap-3 w-full max-w-xs">
          {[{ n: "2,847", l: "مستخدم" }, { n: "1,203", l: "عقار" }, { n: "487", l: "توثيق معلق" }, { n: "99.2%", l: "وقت التشغيل" }].map((s, i) => (
            <div key={i} className="p-4 rounded-2xl text-center" style={{ backgroundColor: "#334155" }}>
              <p className="text-2xl font-black text-white" style={{ ...TJ }}>{s.n}</p>
              <p className="text-xs" style={{ ...TJ, color: C.darkMuted }}>{s.l}</p>
            </div>
          ))}
        </div>
      </div>
      <div className="w-96 flex items-center justify-center px-8" style={{ backgroundColor: C.dark }}>
        <div className="w-full">
          <h2 className="text-2xl font-black text-white mb-6 text-right" style={{ ...TJ }}>تسجيل الدخول</h2>
          <div className="flex flex-col gap-4 mb-5">
            {[["البريد الإلكتروني", "admin@sokoon.eg"], ["كلمة المرور", "••••••••"]].map(([l, p], i) => (
              <div key={i}>
                <label className="block text-sm text-right mb-1.5" style={{ ...TJ, color: C.darkMuted }}>{l}</label>
                <input dir="rtl" placeholder={p} type={i === 1 ? "password" : "email"} readOnly className="w-full px-4 py-3 rounded-xl text-sm text-white outline-none"
                  style={{ backgroundColor: "#1E293B", border: `1px solid ${C.darkBorder}`, ...TJ }} />
              </div>
            ))}
          </div>
          <div className="flex items-center gap-2 mb-4" dir="rtl">
            <Lock size={12} style={{ color: C.teal }} /><p className="text-xs" style={{ ...TJ, color: C.darkMuted }}>الدخول مخصص لفريق الإدارة فقط</p>
          </div>
          <button className="w-full py-3.5 rounded-xl font-black text-white mb-3" style={{ backgroundColor: C.teal, ...TJ }}>تسجيل الدخول</button>
          <p className="text-center text-xs" style={{ ...TJ, color: "#64748B" }}>نسيت كلمة المرور؟</p>
        </div>
      </div>
    </div>
  );
}

function Admin2FAScreen() {
  return (
    <div className="flex flex-col items-center justify-center h-full" style={{ backgroundColor: C.dark }}>
      <div className="w-full max-w-sm p-8 rounded-3xl" style={{ backgroundColor: C.darkCard }}>
        <div className="text-center mb-6">
          <div className="w-12 h-12 rounded-2xl flex items-center justify-center mx-auto mb-3" style={{ backgroundColor: C.teal }}>
            <Lock size={20} style={{ color: C.white }} />
          </div>
          <h2 className="text-xl font-black text-white mb-1" style={{ ...TJ }}>التحقق بخطوتين</h2>
          <p className="text-sm" style={{ ...TJ, color: C.darkMuted }}>اكتب كود التحقق من تطبيق المصادقة</p>
        </div>
        <div className="flex gap-2 justify-center mb-4">
          {["5", "8", "3", "", "", ""].map((d, i) => (
            <div key={i} className="w-10 h-12 rounded-xl flex items-center justify-center text-lg font-black text-white"
              style={{ backgroundColor: "#334155", border: `2px solid ${i === 3 ? C.teal : "#475569"}` }}>{d}</div>
          ))}
        </div>
        <p className="text-center text-xs mb-5" style={{ ...TJ, color: C.amber }}>الكود بيتغير كل 30 ثانية ⏱</p>
        <button className="w-full py-3.5 rounded-xl font-black text-white mb-3" style={{ backgroundColor: C.teal, ...TJ }}>تأكيد الدخول</button>
        <button className="w-full text-center text-sm" style={{ ...TJ, color: "#64748B" }}>استخدام كود احتياطي</button>
      </div>
    </div>
  );
}

function Admin2FASetupScreen() {
  return (
    <div className="flex flex-col items-center justify-center h-full" style={{ backgroundColor: C.dark }}>
      <div className="w-full max-w-md p-8 rounded-3xl" style={{ backgroundColor: C.darkCard }}>
        <div className="text-center mb-5">
          <div className="w-12 h-12 rounded-2xl flex items-center justify-center mx-auto mb-3" style={{ backgroundColor: C.teal }}>
            <Shield size={20} style={{ color: C.white }} />
          </div>
          <h2 className="text-xl font-black text-white mb-1" style={{ ...TJ }}>إعداد التحقق بخطوتين</h2>
          <p className="text-sm" style={{ ...TJ, color: C.darkMuted }}>افتح تطبيق Authenticator وامسح الكود</p>
        </div>
        <div className="flex justify-center mb-5">
          <div className="w-40 h-40 rounded-2xl flex flex-wrap content-center justify-center gap-1 p-3" style={{ backgroundColor: "#F0F0F0" }}>
            {Array.from({ length: 25 }).map((_, i) => (
              <div key={i} className="w-5 h-5 rounded-sm" style={{ backgroundColor: [0, 1, 4, 5, 6, 10, 12, 14, 18, 19, 20, 23, 24].includes(i) ? C.teal : "transparent" }} />
            ))}
          </div>
        </div>
        <div className="mb-4 px-4 py-3 rounded-xl text-center" style={{ backgroundColor: "#334155" }}>
          <p className="text-xs mb-1" style={{ ...TJ, color: C.darkMuted }}>أو اكتب الكود يدوياً</p>
          <p className="text-base font-black tracking-widest text-white" style={{ ...TJ }}>SKON 4E2A 7Z9M XP</p>
        </div>
        <label className="block text-sm text-right mb-1.5" style={{ ...TJ, color: C.darkMuted }}>اكتب الكود من التطبيق للتحقق</label>
        <input dir="rtl" placeholder="6 أرقام" readOnly className="w-full px-4 py-3 rounded-xl text-sm text-white outline-none mb-4 text-center tracking-widest"
          style={{ backgroundColor: "#1E293B", border: `1px solid ${C.darkBorder}`, ...TJ }} />
        <button className="w-full py-3.5 rounded-xl font-black text-white" style={{ backgroundColor: C.teal, ...TJ }}>تفعيل التحقق بخطوتين</button>
      </div>
    </div>
  );
}

function AdminKYCQueueScreen() {
  return (
    <div className="flex h-full" style={{ backgroundColor: "#F8FAFC" }}>
      <AdminSidebar active="kyc" />
      <div className="flex-1 overflow-y-auto p-4">
        <div className="flex items-center justify-between mb-4">
          <h1 className="text-xl font-black" style={{ ...TJ, color: C.navy }}>طلبات توثيق الهوية</h1>
          <div className="flex items-center gap-2">
            <div className="flex items-center px-3 py-2 rounded-xl gap-2" style={{ backgroundColor: C.white, border: `1px solid ${C.border}` }}>
              <Search size={13} style={{ color: C.gray }} />
              <input placeholder="بحث…" dir="rtl" readOnly className="text-sm outline-none" style={{ width: 100, ...TJ }} />
            </div>
            <div className="w-8 h-8 rounded-full flex items-center justify-center" style={{ backgroundColor: C.tealLight }}><User size={14} style={{ color: C.teal }} /></div>
            <span className="text-xs px-2 py-1 rounded-full font-black" style={{ backgroundColor: C.teal, color: C.white, ...TJ }}>Admin</span>
          </div>
        </div>
        <div className="grid grid-cols-4 gap-3 mb-4">
          {[{ l: "قيد المراجعة", n: 487, c: C.amber }, { l: "مقبول", n: 1920, c: C.green }, { l: "مرفوض", n: 143, c: C.red }, { l: "يحتاج تعديل", n: 67, c: C.blue }].map((s, i) => (
            <div key={i} className="p-4 rounded-2xl" style={{ backgroundColor: C.white, border: `1px solid ${C.border}` }}>
              <p className="text-3xl font-black mb-1" style={{ ...TJ, color: s.c }}>{s.n}</p>
              <p className="text-xs" style={{ ...TJ, color: C.gray }}>{s.l}</p>
            </div>
          ))}
        </div>
        <div className="rounded-2xl overflow-hidden" style={{ backgroundColor: C.white, border: `1px solid ${C.border}` }}>
          <div className="grid px-4 py-2.5 text-xs font-black" style={{ backgroundColor: C.bg, color: C.gray, gridTemplateColumns: "2fr 1fr 1.5fr 1fr 1.5fr 1fr 1.5fr" }}>
            {["الاسم", "النوع", "الموبايل", "الحالة", "وقت الإرسال", "ملفات", "إجراء"].map((h, i) => (
              <div key={i} className="text-right" style={{ ...TJ }}>{h}</div>
            ))}
          </div>
          {[{ n: "سارة أحمد خالد", t: "مستأجر", p: "010****432", s: "pending" as BadgeType, time: "منذ ساعة", docs: 3 },
            { n: "محمود حسن علي", t: "مالك", p: "012****891", s: "verified" as BadgeType, time: "منذ 3 ساعات", docs: 4 },
            { n: "نورا محمد عمر", t: "مستأجر", p: "011****234", s: "rejected" as BadgeType, time: "أمس", docs: 2 }].map((r, i) => (
            <div key={i} className="grid px-4 py-3 items-center" style={{ borderTop: `1px solid ${C.border}`, gridTemplateColumns: "2fr 1fr 1.5fr 1fr 1.5fr 1fr 1.5fr" }}>
              <div className="text-right font-black text-xs" style={{ ...TJ, color: C.navy }}>{r.n}</div>
              <div className="text-right"><span className="px-2 py-0.5 rounded-full text-xs font-bold" style={{ backgroundColor: r.t === "مالك" ? C.goldLight : C.blueLight, color: r.t === "مالك" ? C.gold : C.blue, ...TJ }}>{r.t}</span></div>
              <div className="text-right text-xs" style={{ ...TJ, color: C.gray }}>{r.p}</div>
              <div className="text-right"><Badge type={r.s} /></div>
              <div className="text-right text-xs" style={{ ...TJ, color: C.gray }}>{r.time}</div>
              <div className="text-right text-xs" style={{ ...TJ, color: C.gray }}>{r.docs}</div>
              <div className="text-right">
                <button className="px-3 py-1.5 rounded-xl text-xs font-black text-white" style={{ backgroundColor: C.teal, ...TJ }}>مراجعة</button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function AdminKYCReviewScreen() {
  return (
    <div className="flex h-full" style={{ backgroundColor: "#F8FAFC" }}>
      <AdminSidebar active="kyc" />
      <div className="w-52 p-4 overflow-y-auto flex-shrink-0" style={{ backgroundColor: C.white, borderRight: `1px solid ${C.border}` }}>
        <div className="flex items-center gap-2 mb-4" dir="rtl">
          <button className="w-7 h-7 rounded-lg flex items-center justify-center" style={{ backgroundColor: C.bg, border: `1px solid ${C.border}` }}>
            <ArrowLeft size={13} style={{ color: C.navy }} />
          </button>
          <h3 className="font-black text-sm" style={{ ...TJ, color: C.navy }}>بيانات المستخدم</h3>
        </div>
        <div className="text-center mb-4">
          <div className="w-14 h-14 rounded-full flex items-center justify-center mx-auto mb-2" style={{ backgroundColor: C.tealLight }}><User size={26} style={{ color: C.teal }} /></div>
          <p className="font-black text-sm" style={{ ...TJ, color: C.navy }}>سارة أحمد خالد</p>
          <div className="mt-1"><Badge type="pending" /></div>
        </div>
        {[["النوع", "مستأجر"], ["البريد", "sara@example.com"], ["الموبايل", "010****432"], ["التسجيل", "14 يناير 2026"], ["المحاولة", "الأولى"]].map(([l, v], i) => (
          <div key={i} className="mb-2 text-right">
            <p className="text-xs" style={{ ...TJ, color: C.gray }}>{l}</p>
            <p className="text-sm font-bold" style={{ ...TJ, color: C.navy }}>{v}</p>
          </div>
        ))}
      </div>
      <div className="flex-1 p-4 overflow-y-auto" style={{ backgroundColor: "#F8FAFC" }}>
        <h3 className="font-black text-sm mb-3" style={{ ...TJ, color: C.navy }}>المستندات المرفوعة</h3>
        <div className="grid grid-cols-2 gap-3">
          {["بطاقة الرقم — الأمام", "بطاقة الرقم — الخلف", "سيلفي", "عقد إيجار"].map((doc, i) => (
            <div key={i} className="rounded-2xl overflow-hidden flex flex-col items-center justify-center gap-2"
              style={{ backgroundColor: "#E2E8F0", aspectRatio: "4/3" }}>
              <FileText size={22} style={{ color: "#94A3B8" }} />
              <p className="text-xs text-center px-2" style={{ ...TJ, color: "#94A3B8" }}>{doc}</p>
              <div className="flex gap-1">
                <button className="p-1.5 rounded-lg" style={{ backgroundColor: "rgba(255,255,255,0.8)" }}><ZoomIn size={11} /></button>
                <button className="p-1.5 rounded-lg" style={{ backgroundColor: "rgba(255,255,255,0.8)" }}><RotateCw size={11} /></button>
              </div>
            </div>
          ))}
        </div>
      </div>
      <div className="w-52 p-4 overflow-y-auto flex-shrink-0" style={{ backgroundColor: C.white, borderLeft: `1px solid ${C.border}` }}>
        <h3 className="font-black text-sm mb-3" style={{ ...TJ, color: C.navy }}>لوحة القرار</h3>
        <div className="flex flex-col gap-2 mb-4">
          {[["اسم البطاقة مطابق", true], ["صورة السيلفي مطابقة", true], ["جودة الصور مقبولة", false]].map(([l, checked], i) => (
            <div key={i} className="flex items-center gap-2">
              <div className="w-5 h-5 rounded border-2 flex items-center justify-center flex-shrink-0"
                style={{ borderColor: checked ? C.teal : C.border, backgroundColor: checked ? C.teal : C.white }}>
                {checked && <Check size={10} style={{ color: C.white }} />}
              </div>
              <p className="text-xs" style={{ ...TJ, color: C.gray }}>{l as string}</p>
            </div>
          ))}
        </div>
        <textarea dir="rtl" readOnly placeholder="ملاحظات المراجع…" className="w-full p-2 rounded-xl text-xs mb-3 outline-none resize-none"
          style={{ backgroundColor: C.bg, border: `1px solid ${C.border}`, ...TJ, height: 55 }} />
        <div className="flex flex-col gap-2">
          <button className="w-full py-2.5 rounded-xl text-xs font-black text-white" style={{ backgroundColor: C.green, ...TJ }}>اعتماد التوثيق ✓</button>
          <button className="w-full py-2.5 rounded-xl text-xs font-black text-white" style={{ backgroundColor: C.red, ...TJ }}>رفض الطلب ✗</button>
          <button className="w-full py-2.5 rounded-xl text-xs font-black" style={{ backgroundColor: C.amberLight, color: C.amber, ...TJ }}>طلب بيانات إضافية</button>
        </div>
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════
//  SCREEN REGISTRY
// ═══════════════════════════════════════════════
type ScreenDef = { id: string; label: string; ar: string; C: React.ComponentType; desktop?: boolean };

const AUTH_SCREENS: ScreenDef[] = [
  { id: "a01", label: "AUTH-01: Splash", ar: "الشاشة الترحيبية", C: SplashScreen },
  { id: "a02", label: "AUTH-02: Onboarding Trust", ar: "مقدمة الثقة", C: OnboardingScreen },
  { id: "a03", label: "AUTH-03: Role Selection", ar: "اختيار الدور", C: RoleSelectionScreen },
  { id: "a04", label: "AUTH-04: Login", ar: "تسجيل الدخول", C: LoginScreen },
  { id: "a05", label: "AUTH-05: Register", ar: "إنشاء حساب", C: RegisterScreen },
  { id: "a06", label: "AUTH-06: Account Created", ar: "تم إنشاء الحساب", C: AccountCreatedScreen },
  { id: "a07", label: "AUTH-07: KYC Intro", ar: "مقدمة التوثيق", C: KYCIntroScreen },
  { id: "a08", label: "AUTH-08: National ID Upload", ar: "رفع البطاقة", C: NationalIDScreen },
  { id: "a09", label: "AUTH-09: Selfie Capture", ar: "التقاط سيلفي", C: SelfieScreen },
  { id: "a10", label: "AUTH-10: Tenant Rental History", ar: "عقد الإيجار السابق", C: TenantHistoryScreen },
  { id: "a11", label: "AUTH-11: Owner Verification Note", ar: "ملاحظة توثيق المالك", C: OwnerVerificationNoteScreen },
  { id: "a12", label: "AUTH-12: KYC Review & Submit", ar: "مراجعة وإرسال التوثيق", C: KYCReviewScreen },
  { id: "a13", label: "AUTH-13: Pending Verification", ar: "التوثيق قيد المراجعة", C: PendingVerificationScreen },
  { id: "a14", label: "AUTH-14: Verification Approved ✓", ar: "تم التوثيق بنجاح", C: VerificationApprovedScreen },
  { id: "a15", label: "AUTH-15: Verification Rejected ✗", ar: "تم رفض التوثيق", C: VerificationRejectedScreen },
  { id: "a16", label: "AUTH-16: Account Restricted", ar: "الحساب موقوف", C: AccountRestrictedScreen },
  { id: "a17", label: "AUTH-17: Forgot Password", ar: "نسيت كلمة المرور", C: ForgotPasswordScreen },
  { id: "a18", label: "AUTH-18: Reset Password", ar: "إعادة تعيين كلمة المرور", C: ResetPasswordScreen },
  { id: "a19", label: "AUTH-19: Logout Confirmation", ar: "تأكيد تسجيل الخروج", C: LogoutScreen },
];

const TENANT_SCREENS: ScreenDef[] = [
  { id: "t01", label: "T-01: Home Main", ar: "الرئيسية", C: TenantHomeMain },
  { id: "t02", label: "T-02: Search Focus", ar: "حقل البحث", C: TenantSearchFocusScreen },
  { id: "t03", label: "T-03: Search Results", ar: "نتائج البحث", C: TenantSearchResultsScreen },
  { id: "t04", label: "T-04: Filter Sheet", ar: "لوح الفلاتر", C: TenantFilterSheet },
  { id: "t05", label: "T-05: Nearby Expanded", ar: "عقارات قريبة", C: TenantNearbyScreen },
  { id: "t06", label: "T-06: Property Card States", ar: "حالات بطاقة العقار", C: PropCardStatesScreen },
  { id: "t07", label: "T-07: Property Details", ar: "تفاصيل العقار", C: PropertyDetailsScreen },
  { id: "t08", label: "T-08: Fullscreen Gallery", ar: "معرض الصور الكامل", C: MediaGalleryScreen },
  { id: "t09", label: "T-09: Book Visit Sheet", ar: "حجز زيارة", C: BookVisitSheet },
  { id: "t10", label: "T-10: Visit Request Sent", ar: "تم إرسال طلب الزيارة", C: VisitRequestSentScreen },
  { id: "t11", label: "T-11: Pending Chat Warning", ar: "تحذير الشات (غير موثق)", C: ChatWarningScreen },
  { id: "t12", label: "T-12: Chat from Property", ar: "المحادثة مع المالك", C: TenantChatScreen },
  { id: "t13", label: "T-13: Saved Listings", ar: "العقارات المحفوظة", C: SavedListingsScreen },
  { id: "t14", label: "T-14: Loading Skeleton", ar: "شاشة التحميل", C: TenantSkeletonScreen },
  { id: "t15", label: "T-15: Empty State", ar: "لا توجد نتائج", C: TenantEmptyScreen },
  { id: "t16", label: "T-16: Error State", ar: "خطأ في الاتصال", C: TenantErrorScreen },
];

const OWNER_SCREENS: ScreenDef[] = [
  { id: "o01", label: "O-01: Owner Dashboard", ar: "لوحة تحكم المالك", C: OwnerDashboardMain },
  { id: "o02", label: "O-02: Empty Dashboard", ar: "لوحة التحكم فارغة", C: OwnerDashboardEmpty },
  { id: "o03", label: "O-03: Metrics Expanded", ar: "التحليلات والإحصاءات", C: OwnerMetricsScreen },
  { id: "o04", label: "O-04: Booking Requests List", ar: "قائمة طلبات الزيارة", C: BookingRequestsListScreen },
  { id: "o05", label: "O-05: Booking Request Detail", ar: "تفاصيل طلب الزيارة", C: BookingRequestDetailScreen },
  { id: "o06", label: "O-06: Accept Visit Confirmation", ar: "تأكيد قبول الزيارة", C: AcceptVisitScreen },
  { id: "o07", label: "O-07: Reject Visit Confirmation", ar: "تأكيد رفض الزيارة", C: RejectVisitScreen },
  { id: "o08", label: "O-08: Owner Chat", ar: "شات المالك", C: OwnerChatScreen },
  { id: "o09", label: "O-09: Add Property Intro", ar: "إضافة عقار — مقدمة", C: AddPropertyIntroScreen },
  { id: "o10", label: "O-10: Media Upload (1/6)", ar: "رفع الصور (1/6)", C: AddPropertyMediaScreen },
  { id: "o11", label: "O-11: Basic Details (2/6)", ar: "البيانات الأساسية (2/6)", C: AddPropertyBasicDetailsScreen },
  { id: "o12", label: "O-12: Map Pin (3/6)", ar: "تحديد الموقع (3/6)", C: AddPropertyMapScreen },
  { id: "o13", label: "O-13: Structure Details (4/6)", ar: "المساحة والغرف (4/6)", C: AddPropertyStructureScreen },
  { id: "o14", label: "O-14: Amenities (5/6)", ar: "المرافق والخدمات (5/6)", C: AddPropertyAmenitiesScreen },
  { id: "o15", label: "O-15: Review & Submit (6/6)", ar: "مراجعة وإرسال (6/6)", C: AddPropertyReviewScreen },
  { id: "o16", label: "O-16: Property Pending Review", ar: "العقار قيد المراجعة", C: PropertyPendingReviewScreen },
  { id: "o17", label: "O-17: My Properties Preview", ar: "عقاراتي", C: MyPropertiesScreen },
  { id: "o18", label: "O-18: Property Status Detail", ar: "حالة العقار التفصيلية", C: PropertyStatusDetailScreen },
  { id: "o19", label: "O-19: Edit Property", ar: "تعديل العقار", C: EditPropertyScreen },
  { id: "o20", label: "O-20: Action Bottom Sheets", ar: "أوراق الإجراءات", C: PropertyActionSheetsScreen },
];

const ADMIN_SCREENS: ScreenDef[] = [
  { id: "adm01", label: "ADMIN-A: Login", ar: "دخول الإدارة", C: AdminLoginScreen, desktop: true },
  { id: "adm02", label: "ADMIN-B: 2FA Verification", ar: "التحقق بخطوتين", C: Admin2FAScreen, desktop: true },
  { id: "adm03", label: "ADMIN-C: 2FA Setup", ar: "إعداد 2FA", C: Admin2FASetupScreen, desktop: true },
  { id: "adm04", label: "ADMIN-D: KYC Queue", ar: "طابور طلبات التوثيق", C: AdminKYCQueueScreen, desktop: true },
  { id: "adm05", label: "ADMIN-E: KYC Review Detail", ar: "مراجعة طلب التوثيق", C: AdminKYCReviewScreen, desktop: true },
];

const SECTIONS = [
  { id: "auth", ar: "المصادقة", label: "Auth Flow", color: "#0F766E", screens: AUTH_SCREENS },
  { id: "tenant", ar: "المستأجر", label: "Tenant Flow", color: "#2563EB", screens: TENANT_SCREENS },
  { id: "owner", ar: "المالك", label: "Owner Flow", color: "#D6A84F", screens: OWNER_SCREENS },
  { id: "admin", ar: "الإدارة", label: "Admin Console", color: "#334155", screens: ADMIN_SCREENS },
];

const totalScreens = SECTIONS.reduce((a, s) => a + s.screens.length, 0);

// ═══════════════════════════════════════════════
//  ROOT APP SHELL
// ═══════════════════════════════════════════════
export default function App() {
  const [activeSec, setActiveSec] = useState("auth");
  const [activeScrId, setActiveScrId] = useState("a01");

  const sec = SECTIONS.find(s => s.id === activeSec)!;
  const scr = sec.screens.find(s => s.id === activeScrId) || sec.screens[0];
  const ScrComp = scr.C;
  const isDesktop = !!scr.desktop;
  const scrIdx = sec.screens.findIndex(s => s.id === activeScrId);

  const goSec = (sid: string) => {
    setActiveSec(sid);
    setActiveScrId(SECTIONS.find(s => s.id === sid)!.screens[0].id);
  };
  const goPrev = () => scrIdx > 0 && setActiveScrId(sec.screens[scrIdx - 1].id);
  const goNext = () => scrIdx < sec.screens.length - 1 && setActiveScrId(sec.screens[scrIdx + 1].id);

  return (
    <div className="flex flex-col h-screen overflow-hidden" style={{ ...TJ, backgroundColor: "#0A1628" }}>
      {/* ── Top Bar ── */}
      <div className="flex items-center justify-between px-4 py-2 flex-shrink-0" style={{ backgroundColor: "#0F172A", borderBottom: "1px solid #1E293B" }}>
        <div className="flex items-center gap-2.5">
          <div className="w-7 h-7 rounded-lg flex items-center justify-center" style={{ backgroundColor: C.teal }}>
            <Shield size={13} style={{ color: C.white }} />
          </div>
          <span className="font-black text-white" style={{ fontSize: 15 }}>سكون — Sokoon</span>
          <span className="text-xs ml-1" style={{ color: "#475569" }}>UI Kit · {totalScreens} شاشة</span>
        </div>
        <div className="flex gap-1">
          {SECTIONS.map(s => (
            <button key={s.id} onClick={() => goSec(s.id)}
              className="px-3 py-1.5 rounded-xl text-xs font-black transition-all"
              style={{ backgroundColor: activeSec === s.id ? s.color : "transparent", color: activeSec === s.id ? C.white : "#94A3B8" }}>
              {s.ar}
            </button>
          ))}
        </div>
      </div>

      <div className="flex flex-1 overflow-hidden">
        {/* ── Sidebar ── */}
        <div className="w-52 overflow-y-auto flex-shrink-0 py-2" style={{ backgroundColor: "#1E293B" }}>
          <p className="text-xs font-black px-4 mb-1 mt-1" style={{ color: "#475569" }}>
            {sec.ar} · {sec.screens.length} شاشة
          </p>
          {sec.screens.map(s => {
            const active = s.id === activeScrId;
            return (
              <button key={s.id} onClick={() => setActiveScrId(s.id)}
                className="w-full text-right px-3 py-2 transition-all"
                style={{ backgroundColor: active ? `${sec.color}25` : "transparent", borderRight: `3px solid ${active ? sec.color : "transparent"}` }}>
                <span className="text-xs font-black block leading-tight" style={{ color: active ? sec.color : "#94A3B8" }}>{s.ar}</span>
                <span className="text-xs block mt-0.5" style={{ color: "#475569", fontSize: 10 }}>{s.label}</span>
              </button>
            );
          })}
        </div>

        {/* ── Preview area ── */}
        <div className="flex-1 flex flex-col overflow-hidden" style={{ backgroundColor: "#141E2E" }}>
          {/* Sub-toolbar */}
          <div className="flex items-center justify-between px-4 py-2 flex-shrink-0" style={{ backgroundColor: "#0F172A", borderBottom: "1px solid #1E293B" }}>
            <div className="flex items-center gap-3">
              <button onClick={goPrev} disabled={scrIdx === 0}
                className="w-7 h-7 rounded-lg flex items-center justify-center"
                style={{ backgroundColor: scrIdx === 0 ? "#1E293B" : "#334155" }}>
                <ChevronRight size={14} style={{ color: scrIdx === 0 ? "#475569" : C.white }} />
              </button>
              <button onClick={goNext} disabled={scrIdx === sec.screens.length - 1}
                className="w-7 h-7 rounded-lg flex items-center justify-center"
                style={{ backgroundColor: scrIdx === sec.screens.length - 1 ? "#1E293B" : "#334155" }}>
                <ChevronLeft size={14} style={{ color: scrIdx === sec.screens.length - 1 ? "#475569" : C.white }} />
              </button>
              <div>
                <span className="text-xs font-black text-white">{scr.ar}</span>
                <span className="text-xs ml-2" style={{ color: "#64748B" }}>{scr.label}</span>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-xs px-2 py-1 rounded-lg font-black"
                style={{ backgroundColor: isDesktop ? "#334155" : C.tealLight, color: isDesktop ? C.white : C.teal }}>
                {isDesktop ? "Desktop 1440×900" : "Mobile 390×844"}
              </span>
              <span className="text-xs" style={{ color: "#64748B" }}>{scrIdx + 1} / {sec.screens.length}</span>
            </div>
          </div>

          {/* Frame */}
          <div className="flex-1 overflow-auto flex items-center justify-center p-6">
            {isDesktop ? (
              <div className="w-full rounded-2xl overflow-hidden"
                style={{ maxWidth: 1100, height: 600, boxShadow: "0 0 0 3px #0F172A, 0 24px 60px rgba(0,0,0,0.5)" }}>
                <ScrComp />
              </div>
            ) : (
              <div style={{
                width: 390, height: 844, borderRadius: 48, overflow: "hidden", flexShrink: 0,
                boxShadow: "0 0 0 10px #0A1628, 0 0 0 13px #1E293B, 0 40px 80px rgba(0,0,0,0.65)"
              }}>
                <ScrComp />
              </div>
            )}
          </div>
        </div>
      </div>

      {/* ── Status bar ── */}
      <div className="flex items-center justify-between px-4 py-1 flex-shrink-0" style={{ backgroundColor: "#0F172A", borderTop: "1px solid #1E293B" }}>
        <div className="flex gap-3">
          {SECTIONS.map(s => (
            <span key={s.id} className="text-xs" style={{ color: activeSec === s.id ? s.color : "#475569" }}>
              ● {s.ar}: {s.screens.length}
            </span>
          ))}
        </div>
        <span className="text-xs" style={{ color: "#475569" }}>إجمالي: {totalScreens} شاشة</span>
      </div>
    </div>
  );
}
