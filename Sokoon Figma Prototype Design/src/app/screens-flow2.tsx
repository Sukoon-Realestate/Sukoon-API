import React, { useState } from "react";
import {
  ArrowLeft, Bell, Check, CheckCircle, ChevronRight, X,
  Camera, Image as Img, File, MapPin, Mic, MicOff, Send,
  Phone, Lock, Eye, EyeOff, Info, Star, Shield,
  Home, Building2, Calendar, MessageCircle, User, Heart,
  ToggleLeft, ToggleRight, Trash2, LogOut, AlertTriangle,
  Clock, Globe, HelpCircle, Mail, Edit2, Plus,
} from "lucide-react";
import {
  C, TJ as tj, PrimaryBtn, OutlineBtn, StatusBar,
  TenantNav, OwnerNav, Badge, Card,
} from "./design-system";

const W = 390, H = 844;
const base: React.CSSProperties = {
  width: W, height: H, background: C.bg, ...tj,
  direction: "rtl", overflow: "hidden", position: "relative",
  fontFamily: "Tajawal, sans-serif",
};

// ── CHAT: Attachments Sheet ──────────────────────────────────────────
export function TenantChatAttachmentsSheet() {
  const actions = [
    { icon: Camera, label: "الكاميرا",  color: C.teal,  bg: C.tealLight },
    { icon: Img,    label: "الصور",     color: C.blue,  bg: C.blueLight },
    { icon: File,   label: "ملف",       color: C.gold,  bg: C.goldLight },
    { icon: MapPin, label: "الموقع",    color: C.red,   bg: C.redLight },
  ];
  return (
    <div style={base}>
      {/* Dimmed chat background */}
      <div style={{ padding: "16px 20px 0" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 16 }}>
          <button style={{ background: "none", border: "none", cursor: "pointer" }}><ArrowLeft size={22} color={C.navy} style={{ transform: "scaleX(-1)" }} /></button>
          <div style={{ width: 38, height: 38, borderRadius: "50%", background: C.teal, display: "flex", alignItems: "center", justifyContent: "center" }}>
            <span style={{ color: "white", fontWeight: 900, fontSize: 16 }}>م</span>
          </div>
          <div style={{ flex: 1 }}><p style={{ margin: 0, fontWeight: 800, fontSize: 14, color: C.navy }}>محمد السيد</p><p style={{ margin: 0, fontSize: 11, color: C.gray }}>متصل الآن</p></div>
        </div>
        {[
          { me: false, text: "السلام عليكم، هل الشقة لا تزال متاحة؟" },
          { me: true,  text: "أهلاً، نعم الشقة متاحة. تفضل بزيارتها." },
          { me: false, text: "ممتاز، هل يمكنني إرسال بعض الأسئلة؟" },
        ].map((m, i) => (
          <div key={i} style={{ display: "flex", justifyContent: m.me ? "flex-start" : "flex-end", marginBottom: 8 }}>
            <div style={{ maxWidth: "70%", background: m.me ? C.teal : "white", borderRadius: 16, padding: "10px 14px", boxShadow: "0 1px 4px rgba(0,0,0,0.08)" }}>
              <p style={{ margin: 0, fontSize: 13, color: m.me ? "white" : C.navy, lineHeight: 1.5 }}>{m.text}</p>
            </div>
          </div>
        ))}
      </div>

      {/* Dark overlay */}
      <div style={{ position: "absolute", inset: 0, background: "rgba(0,0,0,0.5)", top: 200 }} />

      {/* Attachment sheet */}
      <div style={{
        position: "absolute", bottom: 0, left: 0, right: 0,
        background: "white", borderRadius: "24px 24px 0 0",
        padding: "12px 24px 40px",
      }}>
        <div style={{ width: 36, height: 4, borderRadius: 2, background: C.border, margin: "0 auto 24px" }} />
        <p style={{ fontSize: 14, fontWeight: 800, color: C.navy, margin: "0 0 20px" }}>إرسال مرفق</p>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 16 }}>
          {actions.map(({ icon: I, label, color, bg }) => (
            <div key={label} style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 8, cursor: "pointer" }}>
              <div style={{ width: 60, height: 60, borderRadius: 18, background: bg, display: "flex", alignItems: "center", justifyContent: "center" }}>
                <I size={26} color={color} />
              </div>
              <span style={{ fontSize: 11, fontWeight: 700, color: C.navy }}>{label}</span>
            </div>
          ))}
        </div>
        <div style={{ marginTop: 24 }}><OutlineBtn text="إلغاء" /></div>
      </div>
    </div>
  );
}

// ── CHAT: Voice Note State ───────────────────────────────────────────
export function TenantChatVoiceNoteState() {
  return (
    <div style={base}>
      <div style={{ padding: "16px 20px", display: "flex", alignItems: "center", gap: 12, borderBottom: `1px solid ${C.border}`, background: "white" }}>
        <button style={{ background: "none", border: "none", cursor: "pointer" }}><ArrowLeft size={22} color={C.navy} style={{ transform: "scaleX(-1)" }} /></button>
        <div style={{ width: 38, height: 38, borderRadius: "50%", background: C.teal, display: "flex", alignItems: "center", justifyContent: "center" }}>
          <span style={{ color: "white", fontWeight: 900, fontSize: 16 }}>م</span>
        </div>
        <div style={{ flex: 1 }}><p style={{ margin: 0, fontWeight: 800, fontSize: 14, color: C.navy }}>محمد السيد</p><p style={{ margin: 0, fontSize: 11, color: C.green }}>● يسجّل...</p></div>
      </div>

      <div style={{ padding: "20px", flex: 1 }}>
        {/* Voice note bubble sent */}
        <div style={{ display: "flex", justifyContent: "flex-start", marginBottom: 12 }}>
          <div style={{ background: C.teal, borderRadius: 16, padding: "12px 16px", display: "flex", alignItems: "center", gap: 10 }}>
            <div style={{ width: 32, height: 32, borderRadius: "50%", background: "rgba(255,255,255,0.25)", display: "flex", alignItems: "center", justifyContent: "center" }}>
              <Mic size={16} color="white" />
            </div>
            <div style={{ display: "flex", gap: 2, alignItems: "center" }}>
              {[8,14,6,18,10,16,4,12,9,15].map((h,i) => (
                <div key={i} style={{ width: 3, height: h, borderRadius: 2, background: "rgba(255,255,255,0.7)" }} />
              ))}
            </div>
            <span style={{ color: "rgba(255,255,255,0.8)", fontSize: 12 }}>0:08</span>
          </div>
        </div>
      </div>

      {/* Recording bar */}
      <div style={{ position: "absolute", bottom: 0, left: 0, right: 0, background: "white", borderTop: `1px solid ${C.border}`, padding: "16px 16px 36px" }}>
        <div style={{ background: "#FFF1F1", borderRadius: 16, padding: "16px 16px", display: "flex", alignItems: "center", gap: 12 }}>
          <button style={{ width: 40, height: 40, borderRadius: "50%", background: "#EF4444", border: "none", cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center" }}>
            <X size={18} color="white" />
          </button>
          <div style={{ flex: 1, display: "flex", alignItems: "center", gap: 6 }}>
            <div style={{ width: 8, height: 8, borderRadius: "50%", background: "#EF4444" }} />
            <span style={{ fontSize: 13, fontWeight: 700, color: "#EF4444" }}>جارٍ التسجيل...</span>
            <span style={{ fontSize: 13, color: C.gray, marginRight: "auto" }}>0:24</span>
          </div>
          <button style={{ width: 44, height: 44, borderRadius: "50%", background: C.teal, border: "none", cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center" }}>
            <Send size={18} color="white" />
          </button>
        </div>
      </div>
    </div>
  );
}

// ── CHAT: Empty State ────────────────────────────────────────────────
export function TenantChatEmptyScreen() {
  return (
    <div style={base}>
      <StatusBar />
      <div style={{ padding: "16px 20px", borderBottom: `1px solid ${C.border}` }}>
        <h3 style={{ fontSize: 18, fontWeight: 900, color: C.navy, margin: 0 }}>المحادثات</h3>
      </div>
      <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", padding: "80px 40px", textAlign: "center" }}>
        <div style={{ width: 88, height: 88, borderRadius: 28, background: C.tealLight, display: "flex", alignItems: "center", justifyContent: "center", marginBottom: 24 }}>
          <MessageCircle size={40} color={C.teal} />
        </div>
        <h3 style={{ fontSize: 20, fontWeight: 900, color: C.navy, margin: "0 0 10px" }}>لا محادثات حتى الآن</h3>
        <p style={{ fontSize: 14, color: C.gray, lineHeight: 1.7, margin: "0 0 32px" }}>
          ابدأ بالتحدث مع أصحاب العقارات مباشرةً من صفحة تفاصيل العقار
        </p>
        <PrimaryBtn text="استكشف العقارات" />
      </div>
      <div style={{ position: "absolute", bottom: 0, left: 0, right: 0 }}><TenantNav active="chat" /></div>
    </div>
  );
}

// ── NOTIFICATION SETTINGS ────────────────────────────────────────────
export function NotifSettingsScreen() {
  const cats = [
    { label: "طلبات الزيارة",    sub: "قبول ورفض مواعيد الزيارة",   on: true },
    { label: "الرسائل الجديدة",  sub: "إشعار عند وصول رسالة",         on: true },
    { label: "تحديثات العقارات", sub: "تغيير السعر أو الحالة",        on: false },
    { label: "التنبيهات الأمنية",sub: "دخول جديد وتغيير كلمة المرور", on: true },
    { label: "العروض الترويجية", sub: "أخبار وعروض سكون",             on: false },
  ];
  const [state, setState] = useState(cats.map(c => c.on));
  return (
    <div style={base}>
      <StatusBar />
      <div style={{ padding: "16px 20px", display: "flex", alignItems: "center", gap: 12, borderBottom: `1px solid ${C.border}` }}>
        <button style={{ background: "none", border: "none", cursor: "pointer" }}><ArrowLeft size={22} color={C.navy} style={{ transform: "scaleX(-1)" }} /></button>
        <h3 style={{ fontSize: 17, fontWeight: 800, color: C.navy, margin: 0 }}>إعدادات الإشعارات</h3>
      </div>
      <div style={{ padding: "12px 0" }}>
        {cats.map((cat, i) => (
          <div key={i} style={{ display: "flex", alignItems: "center", gap: 14, padding: "16px 20px", borderBottom: `1px solid ${C.border}`, background: "white" }}>
            <div style={{ flex: 1 }}>
              <p style={{ fontSize: 14, fontWeight: 700, color: C.navy, margin: 0 }}>{cat.label}</p>
              <p style={{ fontSize: 12, color: C.gray, margin: "3px 0 0" }}>{cat.sub}</p>
            </div>
            <button onClick={() => setState(s => s.map((v, j) => j === i ? !v : v))} style={{ background: "none", border: "none", cursor: "pointer", padding: 0 }}>
              {state[i] ? <ToggleRight size={30} color={C.teal} /> : <ToggleLeft size={30} color={C.gray} />}
            </button>
          </div>
        ))}
        <div style={{ margin: "24px 20px" }}>
          <div style={{ background: C.tealLight, borderRadius: 14, padding: "14px 16px", display: "flex", gap: 10 }}>
            <Info size={18} color={C.teal} style={{ flexShrink: 0, marginTop: 1 }} />
            <p style={{ fontSize: 12, color: C.teal, margin: 0, lineHeight: 1.6 }}>
              يمكنك أيضاً إدارة إشعارات التطبيق من إعدادات هاتفك مباشرةً.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

// ── OWNER: Accept Request Sheet ──────────────────────────────────────
export function OwnerAcceptRequestSheet() {
  return (
    <div style={base}>
      {/* Dimmed background */}
      <div style={{ padding: "20px", opacity: 0.4 }}>
        <div style={{ background: "white", borderRadius: 16, padding: 16, marginBottom: 12 }}>
          <div style={{ display: "flex", gap: 12 }}>
            <div style={{ width: 56, height: 56, borderRadius: 12, background: C.tealLight }} />
            <div><div style={{ width: 140, height: 14, background: C.border, borderRadius: 6, marginBottom: 6 }} /><div style={{ width: 100, height: 12, background: C.border, borderRadius: 6 }} /></div>
          </div>
        </div>
      </div>
      <div style={{ position: "absolute", inset: 0, background: "rgba(0,0,0,0.45)" }} />

      {/* Sheet */}
      <div style={{ position: "absolute", bottom: 0, left: 0, right: 0, background: "white", borderRadius: "24px 24px 0 0", padding: "12px 24px 44px" }}>
        <div style={{ width: 36, height: 4, borderRadius: 2, background: C.border, margin: "0 auto 20px" }} />
        <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 20 }}>
          <div style={{ width: 40, height: 40, borderRadius: 12, background: C.greenLight, display: "flex", alignItems: "center", justifyContent: "center" }}>
            <CheckCircle size={22} color={C.green} />
          </div>
          <div>
            <p style={{ fontSize: 16, fontWeight: 900, color: C.navy, margin: 0 }}>قبول طلب الزيارة</p>
            <p style={{ fontSize: 12, color: C.gray, margin: "2px 0 0" }}>سيتم إشعار المستأجر فوراً</p>
          </div>
        </div>

        <div style={{ background: C.bg, borderRadius: 14, padding: "16px", marginBottom: 20 }}>
          <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 10 }}>
            <span style={{ fontSize: 13, color: C.gray }}>المستأجر</span>
            <span style={{ fontSize: 13, fontWeight: 700, color: C.navy }}>محمد أحمد</span>
          </div>
          <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 10 }}>
            <span style={{ fontSize: 13, color: C.gray }}>التاريخ</span>
            <span style={{ fontSize: 13, fontWeight: 700, color: C.navy }}>الثلاثاء 14 يناير</span>
          </div>
          <div style={{ display: "flex", justifyContent: "space-between" }}>
            <span style={{ fontSize: 13, color: C.gray }}>الوقت</span>
            <span style={{ fontSize: 13, fontWeight: 700, color: C.navy }}>3:00 م</span>
          </div>
        </div>

        <button style={{ width: "100%", height: 52, borderRadius: 14, background: C.green, border: "none", color: "white", fontSize: 16, fontWeight: 800, cursor: "pointer", ...tj, marginBottom: 12 }}>
          تأكيد القبول
        </button>
        <OutlineBtn text="إلغاء" />
      </div>
    </div>
  );
}

// ── OWNER: Reject Request Sheet ──────────────────────────────────────
export function OwnerRejectRequestSheet() {
  const [reason, setReason] = useState(0);
  const reasons = ["الموعد غير مناسب", "العقار مؤجر حالياً", "المستأجر لا يستوفي الشروط", "سبب آخر"];
  return (
    <div style={base}>
      <div style={{ position: "absolute", inset: 0, background: "rgba(0,0,0,0.45)" }} />
      <div style={{ position: "absolute", bottom: 0, left: 0, right: 0, background: "white", borderRadius: "24px 24px 0 0", padding: "12px 24px 44px" }}>
        <div style={{ width: 36, height: 4, borderRadius: 2, background: C.border, margin: "0 auto 20px" }} />
        <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 20 }}>
          <div style={{ width: 40, height: 40, borderRadius: 12, background: C.redLight, display: "flex", alignItems: "center", justifyContent: "center" }}>
            <X size={22} color={C.red} />
          </div>
          <div>
            <p style={{ fontSize: 16, fontWeight: 900, color: C.navy, margin: 0 }}>رفض طلب الزيارة</p>
            <p style={{ fontSize: 12, color: C.gray, margin: "2px 0 0" }}>اختر سبب الرفض</p>
          </div>
        </div>

        {reasons.map((r, i) => (
          <button key={i} onClick={() => setReason(i)} style={{
            width: "100%", background: "none", border: `1.5px solid ${i === reason ? C.red : C.border}`,
            borderRadius: 12, padding: "12px 16px", display: "flex", alignItems: "center", gap: 12,
            cursor: "pointer", marginBottom: 8, textAlign: "right", direction: "rtl",
          }}>
            <div style={{ width: 20, height: 20, borderRadius: "50%", border: `2px solid ${i === reason ? C.red : C.border}`, background: i === reason ? C.red : "white", display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
              {i === reason && <div style={{ width: 8, height: 8, borderRadius: "50%", background: "white" }} />}
            </div>
            <span style={{ fontSize: 14, color: C.navy, ...tj }}>{r}</span>
          </button>
        ))}

        <div style={{ marginTop: 16 }}>
          <button style={{ width: "100%", height: 52, borderRadius: 14, background: C.red, border: "none", color: "white", fontSize: 16, fontWeight: 800, cursor: "pointer", ...tj }}>
            تأكيد الرفض
          </button>
        </div>
      </div>
    </div>
  );
}

// ── OWNER: Requests Calendar ─────────────────────────────────────────
export function OwnerRequestsCalendarScreen() {
  const days = ["أح", "إث", "ثل", "أر", "خم", "جم", "سب"];
  const grid = [null, null, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, null, null];
  const hasVisit = new Set([5, 8, 12, 15, 19, 22, 26]);
  const [sel, setSel] = useState(15);
  return (
    <div style={base}>
      <StatusBar />
      <div style={{ padding: "16px 20px", display: "flex", alignItems: "center", justifyContent: "space-between", borderBottom: `1px solid ${C.border}` }}>
        <h3 style={{ fontSize: 18, fontWeight: 900, color: C.navy, margin: 0 }}>تقويم الزيارات</h3>
        <span style={{ fontSize: 13, color: C.gold, fontWeight: 700 }}>يناير 2025</span>
      </div>

      <div style={{ padding: "16px 16px 0" }}>
        {/* Day headers */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(7, 1fr)", marginBottom: 8 }}>
          {days.map(d => <div key={d} style={{ textAlign: "center", fontSize: 11, fontWeight: 700, color: C.gray, padding: "4px 0" }}>{d}</div>)}
        </div>
        {/* Day grid */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(7, 1fr)", gap: 4 }}>
          {grid.map((d, i) => (
            <div key={i} onClick={() => d && setSel(d)} style={{
              height: 36, borderRadius: 10, display: "flex", flexDirection: "column",
              alignItems: "center", justifyContent: "center", cursor: d ? "pointer" : "default",
              background: d === sel ? C.gold : "transparent",
              position: "relative",
            }}>
              {d && <>
                <span style={{ fontSize: 13, fontWeight: d === sel ? 900 : 500, color: d === sel ? "white" : C.navy }}>{d}</span>
                {hasVisit.has(d) && (
                  <div style={{ width: 5, height: 5, borderRadius: "50%", background: d === sel ? "white" : C.teal, position: "absolute", bottom: 3 }} />
                )}
              </>}
            </div>
          ))}
        </div>
      </div>

      {/* Visit list for selected day */}
      <div style={{ padding: "16px 20px" }}>
        <p style={{ fontSize: 13, fontWeight: 800, color: C.gray, margin: "0 0 12px" }}>زيارات يوم {sel}</p>
        {[
          { name: "محمد أحمد", time: "3:00 م", badge: "confirmed" as const },
          { name: "سارة محمود", time: "5:30 م", badge: "pending" as const },
        ].map((v, i) => (
          <div key={i} style={{ background: "white", borderRadius: 14, padding: "14px 16px", display: "flex", alignItems: "center", gap: 12, marginBottom: 10, boxShadow: "0 2px 8px rgba(0,0,0,0.06)" }}>
            <div style={{ width: 40, height: 40, borderRadius: "50%", background: C.teal, display: "flex", alignItems: "center", justifyContent: "center" }}>
              <span style={{ color: "white", fontWeight: 900 }}>{v.name[0]}</span>
            </div>
            <div style={{ flex: 1 }}>
              <p style={{ fontSize: 14, fontWeight: 700, color: C.navy, margin: 0 }}>{v.name}</p>
              <p style={{ fontSize: 12, color: C.gray, margin: "2px 0 0" }}>{v.time}</p>
            </div>
            <Badge type={v.badge === "confirmed" ? "approved" : "pending"} text={v.badge === "confirmed" ? "مؤكدة" : "معلقة"} />
          </div>
        ))}
      </div>
    </div>
  );
}

// ── OWNER: Property Action Sheet ─────────────────────────────────────
export function OwnerPropertyActionSheet() {
  const actions = [
    { icon: Edit2,        label: "تعديل العقار",    color: C.teal,  bg: C.tealLight },
    { icon: Clock,        label: "إيقاف مؤقت",      color: C.amber, bg: C.amberLight },
    { icon: CheckCircle,  label: "وضع علامة مؤجّر", color: C.green, bg: C.greenLight },
    { icon: Trash2,       label: "حذف العقار",      color: C.red,   bg: C.redLight },
  ];
  return (
    <div style={base}>
      {/* Background preview */}
      <div style={{ padding: "20px", opacity: 0.35 }}>
        <div style={{ background: "white", borderRadius: 20, overflow: "hidden", boxShadow: "0 2px 12px rgba(0,0,0,0.1)" }}>
          <div style={{ height: 160, background: C.tealLight }} />
          <div style={{ padding: 16 }}>
            <div style={{ width: 180, height: 16, background: C.border, borderRadius: 8, marginBottom: 8 }} />
            <div style={{ width: 120, height: 12, background: C.border, borderRadius: 6 }} />
          </div>
        </div>
      </div>
      <div style={{ position: "absolute", inset: 0, background: "rgba(0,0,0,0.5)" }} />
      <div style={{ position: "absolute", bottom: 0, left: 0, right: 0, background: "white", borderRadius: "24px 24px 0 0", padding: "12px 24px 44px" }}>
        <div style={{ width: 36, height: 4, borderRadius: 2, background: C.border, margin: "0 auto 20px" }} />
        <p style={{ fontSize: 15, fontWeight: 900, color: C.navy, margin: "0 0 20px" }}>خيارات العقار</p>
        {actions.map(({ icon: I, label, color, bg }) => (
          <button key={label} style={{
            width: "100%", background: "white", border: `1px solid ${C.border}`,
            borderRadius: 14, padding: "14px 16px", display: "flex", alignItems: "center",
            gap: 14, marginBottom: 10, cursor: "pointer", textAlign: "right", direction: "rtl",
          }}>
            <div style={{ width: 40, height: 40, borderRadius: 12, background: bg, display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
              <I size={20} color={color} />
            </div>
            <span style={{ fontSize: 14, fontWeight: 700, color, ...tj }}>{label}</span>
          </button>
        ))}
      </div>
    </div>
  );
}

// ── PROFILE: Tenant Account Summary ─────────────────────────────────
export function TenantAccountSummaryScreen() {
  const stats = [
    { label: "عقارات محفوظة", value: "12" },
    { label: "زيارات مكتملة", value: "4" },
    { label: "محادثات نشطة", value: "3" },
  ];
  return (
    <div style={base}>
      <StatusBar />
      <div style={{ padding: "16px 20px", display: "flex", alignItems: "center", gap: 12, borderBottom: `1px solid ${C.border}` }}>
        <button style={{ background: "none", border: "none", cursor: "pointer" }}><ArrowLeft size={22} color={C.navy} style={{ transform: "scaleX(-1)" }} /></button>
        <h3 style={{ fontSize: 17, fontWeight: 800, color: C.navy, margin: 0 }}>ملخص الحساب</h3>
      </div>
      <div style={{ overflowY: "auto", padding: "20px" }}>
        {/* Profile card */}
        <div style={{ background: `linear-gradient(135deg, ${C.teal}, #065F57)`, borderRadius: 20, padding: "24px 20px", marginBottom: 20, color: "white" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 14, marginBottom: 16 }}>
            <div style={{ width: 56, height: 56, borderRadius: "50%", background: "rgba(255,255,255,0.2)", display: "flex", alignItems: "center", justifyContent: "center" }}>
              <span style={{ fontSize: 24, fontWeight: 900 }}>م</span>
            </div>
            <div>
              <p style={{ fontSize: 18, fontWeight: 900, margin: 0 }}>محمد أحمد</p>
              <p style={{ fontSize: 12, color: "rgba(255,255,255,0.7)", margin: "2px 0 0" }}>مستأجر · منذ يناير 2024</p>
            </div>
          </div>
          {/* Completion */}
          <div>
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6 }}>
              <span style={{ fontSize: 12, color: "rgba(255,255,255,0.8)" }}>اكتمال الملف</span>
              <span style={{ fontSize: 12, fontWeight: 800 }}>80%</span>
            </div>
            <div style={{ height: 6, background: "rgba(255,255,255,0.25)", borderRadius: 3 }}>
              <div style={{ width: "80%", height: "100%", background: "white", borderRadius: 3 }} />
            </div>
          </div>
        </div>

        {/* KYC status */}
        <div style={{ background: C.greenLight, borderRadius: 14, padding: "14px 16px", display: "flex", alignItems: "center", gap: 12, marginBottom: 20 }}>
          <CheckCircle size={22} color={C.green} />
          <div>
            <p style={{ fontSize: 13, fontWeight: 800, color: C.green, margin: 0 }}>هويتك موثّقة</p>
            <p style={{ fontSize: 11, color: C.gray, margin: "2px 0 0" }}>تم التحقق من بطاقة الهوية</p>
          </div>
        </div>

        {/* Stats */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 12, marginBottom: 20 }}>
          {stats.map(s => (
            <div key={s.label} style={{ background: "white", borderRadius: 14, padding: "16px 12px", textAlign: "center", boxShadow: "0 2px 8px rgba(0,0,0,0.06)" }}>
              <p style={{ fontSize: 22, fontWeight: 900, color: C.teal, margin: "0 0 4px" }}>{s.value}</p>
              <p style={{ fontSize: 10, color: C.gray, margin: 0, lineHeight: 1.4 }}>{s.label}</p>
            </div>
          ))}
        </div>

        {/* Shortcuts */}
        {[
          { icon: Heart, label: "العقارات المحفوظة", value: "12 عقار" },
          { icon: Calendar, label: "سجل الزيارات", value: "4 زيارات" },
          { icon: Shield, label: "التحقق من الهوية", value: "مكتمل" },
        ].map(({ icon: I, label, value }) => (
          <div key={label} style={{ background: "white", borderRadius: 14, padding: "14px 16px", display: "flex", alignItems: "center", gap: 14, marginBottom: 10, boxShadow: "0 1px 6px rgba(0,0,0,0.05)" }}>
            <div style={{ width: 38, height: 38, borderRadius: 10, background: C.tealLight, display: "flex", alignItems: "center", justifyContent: "center" }}>
              <I size={18} color={C.teal} />
            </div>
            <span style={{ flex: 1, fontSize: 14, fontWeight: 700, color: C.navy }}>{label}</span>
            <span style={{ fontSize: 12, color: C.gray }}>{value}</span>
            <ChevronRight size={16} color={C.gray} style={{ transform: "scaleX(-1)" }} />
          </div>
        ))}
      </div>
    </div>
  );
}

// ── SETTINGS: Change Password ────────────────────────────────────────
export function SettingsChangePasswordScreen() {
  const [show, setShow] = useState([false, false, false]);
  const toggle = (i: number) => setShow(s => s.map((v, j) => j === i ? !v : v));
  const fields = ["كلمة المرور الحالية", "كلمة المرور الجديدة", "تأكيد كلمة المرور الجديدة"];
  return (
    <div style={base}>
      <StatusBar />
      <div style={{ padding: "16px 20px", display: "flex", alignItems: "center", gap: 12, borderBottom: `1px solid ${C.border}` }}>
        <button style={{ background: "none", border: "none", cursor: "pointer" }}><ArrowLeft size={22} color={C.navy} style={{ transform: "scaleX(-1)" }} /></button>
        <h3 style={{ fontSize: 17, fontWeight: 800, color: C.navy, margin: 0 }}>تغيير كلمة المرور</h3>
      </div>
      <div style={{ padding: "28px 20px" }}>
        <div style={{ display: "flex", flexDirection: "column", gap: 16, marginBottom: 28 }}>
          {fields.map((label, i) => (
            <div key={i}>
              <p style={{ fontSize: 13, fontWeight: 700, color: C.navy, margin: "0 0 8px" }}>{label}</p>
              <div style={{ background: "white", borderRadius: 12, border: `1px solid ${C.border}`, padding: "14px 16px", display: "flex", alignItems: "center", gap: 10 }}>
                <input type={show[i] ? "text" : "password"} placeholder="••••••••" style={{ flex: 1, border: "none", background: "none", fontSize: 14, color: C.navy, outline: "none", textAlign: "right", fontFamily: "Tajawal, sans-serif" }} />
                <button onClick={() => toggle(i)} style={{ background: "none", border: "none", cursor: "pointer", color: C.gray, padding: 0 }}>
                  {show[i] ? <EyeOff size={18} /> : <Eye size={18} />}
                </button>
              </div>
            </div>
          ))}
        </div>
        <div style={{ background: C.amberLight, borderRadius: 12, padding: "12px 14px", display: "flex", gap: 10, marginBottom: 28 }}>
          <AlertTriangle size={16} color={C.amber} style={{ flexShrink: 0, marginTop: 1 }} />
          <p style={{ fontSize: 12, color: C.amber, margin: 0, lineHeight: 1.5 }}>يجب أن تكون كلمة المرور 8 أحرف على الأقل وتحتوي على أرقام وحروف.</p>
        </div>
        <PrimaryBtn text="حفظ كلمة المرور" />
      </div>
    </div>
  );
}

// ── SETTINGS: Terms & Conditions ────────────────────────────────────
export function SettingsTermsScreen() {
  const sections = [
    { title: "قبول الشروط", body: "باستخدامك لتطبيق سكون، فإنك توافق على الالتزام بهذه الشروط والأحكام. يُرجى قراءتها بعناية قبل استخدام الخدمة." },
    { title: "الخصوصية وحماية البيانات", body: "نلتزم بحماية بياناتك الشخصية وفق أعلى معايير الأمان. لن يتم مشاركة بياناتك مع أطراف ثالثة دون موافقتك الصريحة." },
    { title: "استخدام الخدمة", body: "يُحظر استخدام التطبيق لأغراض غير مشروعة أو نشر محتوى مضلل. يحق لنا إيقاف أي حساب يخالف هذه السياسات." },
    { title: "المسؤولية", body: "تعمل سكون كوسيط بين المستأجرين وأصحاب العقارات. لا تتحمل المنصة مسؤولية العقود المبرمة بين الأطراف." },
  ];
  return (
    <div style={base}>
      <StatusBar />
      <div style={{ padding: "16px 20px", display: "flex", alignItems: "center", gap: 12, borderBottom: `1px solid ${C.border}` }}>
        <button style={{ background: "none", border: "none", cursor: "pointer" }}><ArrowLeft size={22} color={C.navy} style={{ transform: "scaleX(-1)" }} /></button>
        <h3 style={{ fontSize: 17, fontWeight: 800, color: C.navy, margin: 0 }}>الشروط والأحكام</h3>
      </div>
      <div style={{ overflowY: "auto", padding: "24px 20px" }}>
        <p style={{ fontSize: 12, color: C.gray, margin: "0 0 24px" }}>آخر تحديث: 1 يناير 2025</p>
        {sections.map((s, i) => (
          <div key={i} style={{ marginBottom: 24 }}>
            <h4 style={{ fontSize: 15, fontWeight: 900, color: C.navy, margin: "0 0 8px" }}>{i + 1}. {s.title}</h4>
            <p style={{ fontSize: 13, color: C.gray, lineHeight: 1.75, margin: 0 }}>{s.body}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

// ── SETTINGS: About ──────────────────────────────────────────────────
export function SettingsAboutScreen() {
  return (
    <div style={base}>
      <StatusBar />
      <div style={{ padding: "16px 20px", display: "flex", alignItems: "center", gap: 12, borderBottom: `1px solid ${C.border}` }}>
        <button style={{ background: "none", border: "none", cursor: "pointer" }}><ArrowLeft size={22} color={C.navy} style={{ transform: "scaleX(-1)" }} /></button>
        <h3 style={{ fontSize: 17, fontWeight: 800, color: C.navy, margin: 0 }}>عن سكون</h3>
      </div>
      <div style={{ padding: "40px 24px", display: "flex", flexDirection: "column", alignItems: "center", textAlign: "center" }}>
        <div style={{ width: 80, height: 80, borderRadius: 24, background: C.teal, display: "flex", alignItems: "center", justifyContent: "center", marginBottom: 16, boxShadow: "0 8px 24px rgba(15,118,110,0.35)" }}>
          <svg width="40" height="40" viewBox="0 0 40 40" fill="none">
            <path d="M20,4 L34,16 L30,16 L30,36 L10,36 L10,16 L6,16 Z" fill="white"/>
            <rect x="13" y="21" width="5" height="4" rx="1.5" fill={C.teal}/>
            <rect x="22" y="21" width="5" height="4" rx="1.5" fill={C.teal}/>
            <path d="M16,36 L16,29 Q20,25 24,29 L24,36 Z" fill={C.teal}/>
          </svg>
        </div>
        <h2 style={{ fontSize: 26, fontWeight: 900, color: C.navy, margin: "0 0 4px" }}>سكون</h2>
        <p style={{ fontSize: 14, color: C.teal, fontWeight: 600, margin: "0 0 6px", letterSpacing: 1 }}>Sokoon</p>
        <p style={{ fontSize: 12, color: C.gray, margin: "0 0 32px" }}>الإصدار 2.1.0</p>
        <p style={{ fontSize: 13, color: C.gray, lineHeight: 1.7, margin: "0 0 36px" }}>
          سكون منصة عقارية مصرية تُسهّل البحث عن السكن الآمن والموثوق، وتربط المستأجرين بأصحاب العقارات بشكل مريح وشفاف.
        </p>
        {[
          { label: "الموقع الإلكتروني", sub: "www.sokoon.com" },
          { label: "التواصل الاجتماعي", sub: "@sokoon.eg" },
          { label: "البريد الإلكتروني", sub: "support@sokoon.com" },
          { label: "سياسة الخصوصية", sub: "" },
        ].map(({ label, sub }) => (
          <div key={label} style={{ width: "100%", background: "white", borderRadius: 14, padding: "14px 16px", display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 10, boxShadow: "0 1px 6px rgba(0,0,0,0.05)" }}>
            <span style={{ fontSize: 14, fontWeight: 700, color: C.navy }}>{label}</span>
            <span style={{ fontSize: 12, color: C.teal }}>{sub || "عرض ←"}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

// ── SETTINGS: Delete Account ─────────────────────────────────────────
export function SettingsDeleteAccountScreen() {
  const [confirmed, setConfirmed] = useState(false);
  return (
    <div style={base}>
      <StatusBar />
      <div style={{ padding: "16px 20px", display: "flex", alignItems: "center", gap: 12, borderBottom: `1px solid ${C.border}` }}>
        <button style={{ background: "none", border: "none", cursor: "pointer" }}><ArrowLeft size={22} color={C.navy} style={{ transform: "scaleX(-1)" }} /></button>
        <h3 style={{ fontSize: 17, fontWeight: 800, color: C.red, margin: 0 }}>حذف الحساب</h3>
      </div>
      <div style={{ padding: "28px 20px" }}>
        <div style={{ background: C.redLight, borderRadius: 16, padding: "20px", marginBottom: 24, textAlign: "center" }}>
          <AlertTriangle size={36} color={C.red} style={{ marginBottom: 12 }} />
          <h3 style={{ fontSize: 16, fontWeight: 900, color: C.red, margin: "0 0 8px" }}>تحذير: لا يمكن التراجع</h3>
          <p style={{ fontSize: 13, color: C.red, margin: 0, lineHeight: 1.6 }}>
            سيتم حذف حسابك وجميع بياناتك ومحادثاتك نهائياً.
          </p>
        </div>
        <p style={{ fontSize: 13, fontWeight: 800, color: C.navy, margin: "0 0 12px" }}>ماذا ستفقد:</p>
        {["سجل زياراتك ومحادثاتك", "قائمة العقارات المحفوظة", "توثيق هويتك (KYC)", "نقاط الولاء والمكافآت"].map(item => (
          <div key={item} style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 10 }}>
            <X size={16} color={C.red} />
            <span style={{ fontSize: 13, color: C.gray }}>{item}</span>
          </div>
        ))}
        <div style={{ marginTop: 28 }}>
          <label style={{ display: "flex", alignItems: "flex-start", gap: 12, marginBottom: 24, cursor: "pointer" }}>
            <input type="checkbox" checked={confirmed} onChange={e => setConfirmed(e.target.checked)} style={{ marginTop: 3 }} />
            <span style={{ fontSize: 13, color: C.gray, lineHeight: 1.6 }}>أفهم أن حذف الحساب نهائي ولا يمكن استعادة البيانات.</span>
          </label>
          <button style={{ width: "100%", height: 52, borderRadius: 14, background: confirmed ? C.red : C.border, border: "none", color: "white", fontSize: 16, fontWeight: 800, cursor: confirmed ? "pointer" : "default", ...tj }}>
            حذف حسابي نهائياً
          </button>
        </div>
      </div>
    </div>
  );
}

// ── SETTINGS: Logout Sheet ───────────────────────────────────────────
export function SettingsLogoutSheet() {
  return (
    <div style={base}>
      <div style={{ position: "absolute", inset: 0, background: "rgba(0,0,0,0.5)" }} />
      <div style={{ position: "absolute", bottom: 0, left: 0, right: 0, background: "white", borderRadius: "24px 24px 0 0", padding: "12px 24px 48px" }}>
        <div style={{ width: 36, height: 4, borderRadius: 2, background: C.border, margin: "0 auto 24px" }} />
        <div style={{ display: "flex", flexDirection: "column", alignItems: "center", textAlign: "center", marginBottom: 32 }}>
          <div style={{ width: 56, height: 56, borderRadius: 18, background: C.amberLight, display: "flex", alignItems: "center", justifyContent: "center", marginBottom: 14 }}>
            <LogOut size={28} color={C.amber} />
          </div>
          <h3 style={{ fontSize: 18, fontWeight: 900, color: C.navy, margin: "0 0 8px" }}>تسجيل الخروج</h3>
          <p style={{ fontSize: 14, color: C.gray, margin: 0, lineHeight: 1.6 }}>هل أنت متأكد من تسجيل الخروج؟ ستحتاج إلى تسجيل الدخول مجدداً.</p>
        </div>
        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          <button style={{ width: "100%", height: 52, borderRadius: 14, background: C.red, border: "none", color: "white", fontSize: 16, fontWeight: 800, cursor: "pointer", ...tj }}>
            تسجيل الخروج
          </button>
          <OutlineBtn text="إلغاء" />
        </div>
      </div>
    </div>
  );
}

// ── SUPPORT: Ticket Detail ───────────────────────────────────────────
export function SupportTicketDetailScreen() {
  const msgs = [
    { from: "user", text: "واجهت مشكلة في حجز زيارة، الزر لا يعمل.", time: "10:22 ص" },
    { from: "support", text: "مرحباً! شكراً على تواصلك. نحن نفحص المشكلة الآن.", time: "10:35 ص" },
    { from: "support", text: "تم حل المشكلة، يُرجى المحاولة مجدداً وإخبارنا.", time: "10:40 ص" },
    { from: "user", text: "نجح الأمر، شكراً جزيلاً!", time: "10:45 ص" },
  ];
  return (
    <div style={base}>
      <StatusBar />
      <div style={{ padding: "14px 20px", borderBottom: `1px solid ${C.border}`, background: "white" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 8 }}>
          <button style={{ background: "none", border: "none", cursor: "pointer" }}><ArrowLeft size={22} color={C.navy} style={{ transform: "scaleX(-1)" }} /></button>
          <div style={{ flex: 1 }}>
            <p style={{ fontSize: 14, fontWeight: 900, color: C.navy, margin: 0 }}>تذكرة دعم #00142</p>
          </div>
          <Badge type="approved" text="محلولة" />
        </div>
        <p style={{ fontSize: 12, color: C.gray, margin: 0, paddingRight: 34 }}>مشكلة في حجز الزيارة · 14 يناير</p>
      </div>

      <div style={{ overflowY: "auto", padding: "16px 16px 80px" }}>
        {msgs.map((m, i) => {
          const isUser = m.from === "user";
          return (
            <div key={i} style={{ display: "flex", justifyContent: isUser ? "flex-end" : "flex-start", marginBottom: 12, gap: 8 }}>
              {!isUser && (
                <div style={{ width: 32, height: 32, borderRadius: "50%", background: C.teal, display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
                  <HelpCircle size={16} color="white" />
                </div>
              )}
              <div>
                <div style={{ background: isUser ? C.teal : "white", borderRadius: 16, padding: "10px 14px", boxShadow: "0 1px 6px rgba(0,0,0,0.08)", maxWidth: 240 }}>
                  <p style={{ margin: 0, fontSize: 13, color: isUser ? "white" : C.navy, lineHeight: 1.5 }}>{m.text}</p>
                </div>
                <p style={{ fontSize: 10, color: C.gray, margin: "4px 4px 0", textAlign: isUser ? "left" : "right" }}>{m.time}</p>
              </div>
            </div>
          );
        })}

        <div style={{ background: C.greenLight, borderRadius: 12, padding: "12px 14px", display: "flex", gap: 10, margin: "12px 0" }}>
          <CheckCircle size={16} color={C.green} style={{ flexShrink: 0, marginTop: 1 }} />
          <p style={{ fontSize: 12, color: C.green, margin: 0 }}>تم تحديد هذه التذكرة كمحلولة.</p>
        </div>
      </div>

      <div style={{ position: "absolute", bottom: 0, left: 0, right: 0, padding: "12px 16px 28px", background: "white", borderTop: `1px solid ${C.border}` }}>
        <div style={{ background: C.bg, borderRadius: 12, padding: "12px 14px", display: "flex", alignItems: "center", gap: 10 }}>
          <input placeholder="اكتب رداً..." style={{ flex: 1, border: "none", background: "none", fontSize: 13, color: C.gray, outline: "none", textAlign: "right", fontFamily: "Tajawal, sans-serif" }} />
          <button style={{ width: 36, height: 36, borderRadius: "50%", background: C.teal, border: "none", display: "flex", alignItems: "center", justifyContent: "center", cursor: "pointer" }}>
            <Send size={16} color="white" />
          </button>
        </div>
      </div>
    </div>
  );
}

// ══ SHARED COMPONENT PANELS ══════════════════════════════════════════

// ── Shared: Bottom Navigation Demo ──────────────────────────────────
export function SharedBottomNavDemo() {
  return (
    <div style={{ ...base, background: C.bg, padding: "0 0 20px" }}>
      <StatusBar />
      <div style={{ padding: "20px" }}>
        <p style={{ fontSize: 16, fontWeight: 900, color: C.navy, margin: "0 0 20px" }}>Bottom Navigation</p>
        <p style={{ fontSize: 12, fontWeight: 700, color: C.gray, margin: "0 0 8px", letterSpacing: 0.8 }}>TENANT NAV</p>
        <div style={{ border: `1px solid ${C.border}`, borderRadius: 14, overflow: "hidden", marginBottom: 24 }}>
          <TenantNav active="home" />
        </div>
        <p style={{ fontSize: 12, fontWeight: 700, color: C.gray, margin: "0 0 8px", letterSpacing: 0.8 }}>OWNER NAV</p>
        <div style={{ border: `1px solid ${C.border}`, borderRadius: 14, overflow: "hidden", marginBottom: 24 }}>
          <OwnerNav active="home" />
        </div>
        <p style={{ fontSize: 12, fontWeight: 700, color: C.gray, margin: "0 0 8px", letterSpacing: 0.8 }}>ACTIVE STATES</p>
        {["home", "search", "saved", "chat", "more"].map(tab => (
          <div key={tab} style={{ border: `1px solid ${C.border}`, borderRadius: 12, overflow: "hidden", marginBottom: 8 }}>
            <TenantNav active={tab} />
          </div>
        ))}
      </div>
    </div>
  );
}

// ── Shared: Status Badges ────────────────────────────────────────────
export function SharedStatusBadgesPanel() {
  const badges: Array<{ type: "verified"|"pending"|"rejected"|"approved"|"hidden"|"rented"; label: string }> = [
    { type: "verified",  label: "موثّق — Verified" },
    { type: "approved",  label: "مقبول — Approved" },
    { type: "pending",   label: "قيد المراجعة — Pending" },
    { type: "rejected",  label: "مرفوض — Rejected" },
    { type: "hidden",    label: "مخفي — Hidden" },
    { type: "rented",    label: "مؤجّر — Rented" },
  ];
  return (
    <div style={{ ...base, padding: "20px" }}>
      <StatusBar />
      <p style={{ fontSize: 16, fontWeight: 900, color: C.navy, margin: "16px 0 20px" }}>Status Badges</p>
      {badges.map(b => (
        <div key={b.type} style={{ display: "flex", alignItems: "center", justifyContent: "space-between", background: "white", borderRadius: 12, padding: "14px 16px", marginBottom: 10, boxShadow: "0 1px 6px rgba(0,0,0,0.05)" }}>
          <span style={{ fontSize: 13, color: C.gray }}>{b.label}</span>
          <Badge type={b.type} />
        </div>
      ))}
      <p style={{ fontSize: 12, fontWeight: 700, color: C.gray, margin: "20px 0 8px", letterSpacing: 0.8 }}>CUSTOM TEXT</p>
      <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
        <Badge type="verified" text="توثيق كامل" />
        <Badge type="pending" text="قيد الفحص" />
        <Badge type="approved" text="تمت الموافقة" />
        <Badge type="rejected" text="رفض" />
      </div>
    </div>
  );
}

// ── Shared: Property Mini Cards ──────────────────────────────────────
export function SharedPropertyMiniCards() {
  const props = [
    { title: "شقة مفروشة — مدينة نصر", price: "11,500 ج.م/شهر", beds: 3, badge: "verified" as const },
    { title: "استوديو — المهندسين",     price: "7,200 ج.م/شهر",  beds: 1, badge: "approved" as const },
    { title: "دوبلكس — التجمع الخامس", price: "18,000 ج.م/شهر", beds: 4, badge: "pending" as const },
  ];
  return (
    <div style={{ ...base, padding: "20px 16px" }}>
      <StatusBar />
      <p style={{ fontSize: 16, fontWeight: 900, color: C.navy, margin: "16px 0 20px" }}>Property Cards</p>
      {props.map((p, i) => (
        <div key={i} style={{ background: "white", borderRadius: 18, overflow: "hidden", marginBottom: 16, boxShadow: "0 2px 12px rgba(0,0,0,0.07)" }}>
          <div style={{ height: 120, background: `linear-gradient(135deg, ${C.tealLight}, ${C.teal}30)`, display: "flex", alignItems: "center", justifyContent: "center" }}>
            <Home size={32} color={C.teal} opacity={0.4} />
          </div>
          <div style={{ padding: "14px 16px" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 6 }}>
              <Badge type={p.badge} />
            </div>
            <p style={{ fontSize: 14, fontWeight: 800, color: C.navy, margin: "0 0 4px" }}>{p.title}</p>
            <p style={{ fontSize: 15, fontWeight: 900, color: C.teal, margin: "0 0 8px" }}>{p.price}</p>
            <p style={{ fontSize: 12, color: C.gray, margin: 0 }}>🛏 {p.beds} غرف</p>
          </div>
        </div>
      ))}
    </div>
  );
}

// ── Shared: User Mini Cards ──────────────────────────────────────────
export function SharedUserMiniCards() {
  const users = [
    { name: "محمد أحمد",  role: "مستأجر",     badge: "verified" as const, avatar: "م", color: C.teal },
    { name: "أحمد محمود", role: "مالك",        badge: "verified" as const, avatar: "أ", color: C.gold },
    { name: "سارة علي",   role: "مستأجر",     badge: "pending" as const,  avatar: "س", color: C.blue },
    { name: "مها سامي",   role: "مالك",        badge: "rejected" as const, avatar: "م", color: C.red },
  ];
  return (
    <div style={{ ...base, padding: "20px" }}>
      <StatusBar />
      <p style={{ fontSize: 16, fontWeight: 900, color: C.navy, margin: "16px 0 20px" }}>User Cards</p>
      {users.map((u, i) => (
        <div key={i} style={{ background: "white", borderRadius: 16, padding: "16px", display: "flex", alignItems: "center", gap: 14, marginBottom: 12, boxShadow: "0 2px 8px rgba(0,0,0,0.06)" }}>
          <div style={{ width: 48, height: 48, borderRadius: "50%", background: u.color, display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
            <span style={{ color: "white", fontSize: 20, fontWeight: 900 }}>{u.avatar}</span>
          </div>
          <div style={{ flex: 1 }}>
            <p style={{ fontSize: 14, fontWeight: 800, color: C.navy, margin: "0 0 3px" }}>{u.name}</p>
            <p style={{ fontSize: 12, color: C.gray, margin: 0 }}>{u.role}</p>
          </div>
          <Badge type={u.badge} />
        </div>
      ))}
    </div>
  );
}

// ── Shared: Empty States ─────────────────────────────────────────────
export function SharedEmptyStatesPanel() {
  const states = [
    { icon: Heart,          bg: "#FFF1F5", color: "#E11D48", title: "لا محفوظات",    sub: "لم تحفظ أي عقار بعد" },
    { icon: MessageCircle,  bg: C.tealLight, color: C.teal,  title: "لا محادثات",   sub: "ابدأ بالتحدث مع مالك" },
    { icon: Bell,           bg: C.blueLight, color: C.blue,  title: "لا إشعارات",   sub: "ستظهر هنا تنبيهاتك" },
    { icon: Calendar,       bg: C.goldLight, color: C.gold,  title: "لا زيارات",    sub: "احجز زيارتك الأولى" },
  ];
  return (
    <div style={{ ...base, padding: "20px 16px" }}>
      <StatusBar />
      <p style={{ fontSize: 16, fontWeight: 900, color: C.navy, margin: "16px 0 20px" }}>Empty States</p>
      {states.map(({ icon: I, bg, color, title, sub }) => (
        <div key={title} style={{ background: "white", borderRadius: 16, padding: "20px", display: "flex", alignItems: "center", gap: 16, marginBottom: 12, boxShadow: "0 1px 8px rgba(0,0,0,0.05)" }}>
          <div style={{ width: 52, height: 52, borderRadius: 16, background: bg, display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
            <I size={24} color={color} />
          </div>
          <div>
            <p style={{ fontSize: 14, fontWeight: 900, color: C.navy, margin: "0 0 3px" }}>{title}</p>
            <p style={{ fontSize: 12, color: C.gray, margin: 0 }}>{sub}</p>
          </div>
        </div>
      ))}
    </div>
  );
}

// ── Shared: Loading Skeletons ────────────────────────────────────────
export function SharedLoadingSkeletons() {
  const Sk = ({ w, h = 14, r = 6 }: { w: string; h?: number; r?: number }) => (
    <div style={{ width: w, height: h, borderRadius: r, background: "#EEF0F3" }} />
  );
  return (
    <div style={{ ...base, padding: "20px 16px" }}>
      <StatusBar />
      <p style={{ fontSize: 16, fontWeight: 900, color: C.navy, margin: "16px 0 20px" }}>Loading Skeletons</p>

      {/* Property card skeleton */}
      <p style={{ fontSize: 11, fontWeight: 700, color: C.gray, margin: "0 0 8px", letterSpacing: 0.8 }}>PROPERTY CARD</p>
      <div style={{ background: "white", borderRadius: 18, overflow: "hidden", marginBottom: 20, boxShadow: "0 2px 10px rgba(0,0,0,0.06)" }}>
        <div style={{ height: 110, background: "#EEF0F3" }} />
        <div style={{ padding: "14px 16px", display: "flex", flexDirection: "column", gap: 8 }}>
          <Sk w="60%" h={16} />
          <Sk w="45%" h={20} />
          <Sk w="30%" />
        </div>
      </div>

      {/* User row skeleton */}
      <p style={{ fontSize: 11, fontWeight: 700, color: C.gray, margin: "0 0 8px", letterSpacing: 0.8 }}>USER ROW</p>
      {[1, 2, 3].map(i => (
        <div key={i} style={{ background: "white", borderRadius: 14, padding: "14px 16px", display: "flex", gap: 12, alignItems: "center", marginBottom: 10, boxShadow: "0 1px 6px rgba(0,0,0,0.04)" }}>
          <div style={{ width: 44, height: 44, borderRadius: "50%", background: "#EEF0F3", flexShrink: 0 }} />
          <div style={{ flex: 1, display: "flex", flexDirection: "column", gap: 6 }}>
            <Sk w="55%" h={13} />
            <Sk w="35%" h={11} />
          </div>
          <Sk w="48px" h={22} r={10} />
        </div>
      ))}
    </div>
  );
}

// ── Shared: Bottom Sheets Demo ───────────────────────────────────────
export function SharedBottomSheetsDemo() {
  return (
    <div style={base}>
      <StatusBar />
      <div style={{ padding: "20px" }}>
        <p style={{ fontSize: 16, fontWeight: 900, color: C.navy, margin: "16px 0 4px" }}>Bottom Sheets</p>
        <p style={{ fontSize: 12, color: C.gray, margin: "0 0 20px" }}>مكونات الأوراق السفلية</p>
        {/* Mini sheet preview 1 */}
        <div style={{ background: "white", borderRadius: 20, padding: "16px", marginBottom: 16, boxShadow: "0 4px 20px rgba(0,0,0,0.1)" }}>
          <div style={{ width: 32, height: 3, borderRadius: 2, background: C.border, margin: "0 auto 16px" }} />
          <p style={{ fontSize: 13, fontWeight: 800, color: C.navy, margin: "0 0 12px" }}>تصفية النتائج</p>
          {["السعر", "عدد الغرف", "المنطقة"].map(f => (
            <div key={f} style={{ display: "flex", justifyContent: "space-between", padding: "10px 0", borderBottom: `1px solid ${C.border}` }}>
              <span style={{ fontSize: 13, color: C.gray }}>{f}</span>
              <ChevronRight size={16} color={C.gray} style={{ transform: "scaleX(-1)" }} />
            </div>
          ))}
        </div>
        {/* Mini sheet preview 2 */}
        <div style={{ background: "white", borderRadius: 20, padding: "16px", boxShadow: "0 4px 20px rgba(0,0,0,0.1)" }}>
          <div style={{ width: 32, height: 3, borderRadius: 2, background: C.border, margin: "0 auto 16px" }} />
          <p style={{ fontSize: 13, fontWeight: 800, color: C.navy, margin: "0 0 12px" }}>إجراء سريع</p>
          {[
            { icon: Edit2, label: "تعديل", color: C.teal, bg: C.tealLight },
            { icon: Trash2, label: "حذف", color: C.red, bg: C.redLight },
          ].map(({ icon: I, label, color, bg }) => (
            <div key={label} style={{ display: "flex", alignItems: "center", gap: 12, padding: "10px 0" }}>
              <div style={{ width: 34, height: 34, borderRadius: 10, background: bg, display: "flex", alignItems: "center", justifyContent: "center" }}>
                <I size={16} color={color} />
              </div>
              <span style={{ fontSize: 13, fontWeight: 700, color }}>{label}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// ── Shared: Admin Table Components ──────────────────────────────────
export function SharedAdminTableDemo() {
  const rows = [
    { name: "محمد أحمد", role: "مستأجر", status: "verified" as const, date: "14 يناير" },
    { name: "أحمد محمود", role: "مالك",   status: "approved" as const, date: "12 يناير" },
    { name: "سارة علي",  role: "مستأجر", status: "pending" as const,  date: "10 يناير" },
    { name: "مها سامي",  role: "مالك",   status: "rejected" as const, date: "9 يناير" },
  ];
  return (
    <div style={{ ...base, background: "#F8FAFC", padding: "20px 16px" }}>
      <StatusBar dark />
      <p style={{ fontSize: 16, fontWeight: 900, color: C.navy, margin: "16px 0 16px" }}>Admin Table Components</p>
      {/* Table header */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 80px 100px 80px", gap: 8, padding: "8px 12px", marginBottom: 4 }}>
        {["الاسم", "الدور", "الحالة", "التاريخ"].map(h => (
          <span key={h} style={{ fontSize: 10, fontWeight: 800, color: C.gray, letterSpacing: 0.6 }}>{h}</span>
        ))}
      </div>
      {/* Rows */}
      {rows.map((r, i) => (
        <div key={i} style={{ display: "grid", gridTemplateColumns: "1fr 80px 100px 80px", gap: 8, padding: "12px 12px", background: "white", borderRadius: 10, marginBottom: 6, alignItems: "center", boxShadow: "0 1px 4px rgba(0,0,0,0.05)" }}>
          <span style={{ fontSize: 13, fontWeight: 700, color: C.navy }}>{r.name}</span>
          <span style={{ fontSize: 12, color: C.gray }}>{r.role}</span>
          <Badge type={r.status} />
          <span style={{ fontSize: 11, color: C.gray }}>{r.date}</span>
        </div>
      ))}
      {/* Pagination preview */}
      <div style={{ display: "flex", justifyContent: "center", gap: 6, marginTop: 16 }}>
        {[1, 2, 3, "...", 8].map((p, i) => (
          <div key={i} style={{ width: 30, height: 30, borderRadius: 8, background: p === 1 ? C.teal : "white", display: "flex", alignItems: "center", justifyContent: "center", boxShadow: "0 1px 4px rgba(0,0,0,0.08)" }}>
            <span style={{ fontSize: 12, fontWeight: 700, color: p === 1 ? "white" : C.gray }}>{p}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

// ── Shared: Role Chips ───────────────────────────────────────────────
export function SharedRoleChipsDemo() {
  const roles = [
    { label: "مستأجر",         color: C.blue,  bg: C.blueLight },
    { label: "مالك",            color: C.gold,  bg: C.goldLight },
    { label: "مشرف النظام",     color: C.teal,  bg: C.tealLight },
    { label: "مراجع محتوى",     color: C.amber, bg: C.amberLight },
    { label: "دعم فني",         color: "#7C3AED", bg: "#F3E8FF" },
    { label: "محظور",           color: C.red,   bg: C.redLight },
  ];
  const perms = ["عرض الملفات", "تعديل المستخدمين", "الموافقة على العقارات", "إصدار رد المبالغ", "حذف المحتوى", "إدارة الأدوار"];
  return (
    <div style={{ ...base, padding: "20px" }}>
      <StatusBar />
      <p style={{ fontSize: 16, fontWeight: 900, color: C.navy, margin: "16px 0 20px" }}>Role & Permission Chips</p>
      <p style={{ fontSize: 11, fontWeight: 700, color: C.gray, margin: "0 0 10px", letterSpacing: 0.8 }}>ROLES</p>
      <div style={{ display: "flex", flexWrap: "wrap", gap: 8, marginBottom: 28 }}>
        {roles.map(r => (
          <div key={r.label} style={{ background: r.bg, borderRadius: 20, padding: "6px 14px", border: `1px solid ${r.color}33` }}>
            <span style={{ fontSize: 13, fontWeight: 700, color: r.color }}>{r.label}</span>
          </div>
        ))}
      </div>
      <p style={{ fontSize: 11, fontWeight: 700, color: C.gray, margin: "0 0 10px", letterSpacing: 0.8 }}>PERMISSIONS</p>
      {perms.map((p, i) => (
        <div key={i} style={{ display: "flex", alignItems: "center", justifyContent: "space-between", background: "white", borderRadius: 12, padding: "12px 14px", marginBottom: 8, boxShadow: "0 1px 5px rgba(0,0,0,0.05)" }}>
          <span style={{ fontSize: 13, color: C.navy }}>{p}</span>
          <div style={{ display: "flex", gap: 6 }}>
            {[C.teal, C.gold, C.blue].map((c, j) => (
              <div key={j} style={{ width: 20, height: 20, borderRadius: 6, background: j === 0 || (j === 1 && i < 3) ? c : C.border, display: "flex", alignItems: "center", justifyContent: "center" }}>
                {(j === 0 || (j === 1 && i < 3)) && <Check size={12} color="white" />}
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
