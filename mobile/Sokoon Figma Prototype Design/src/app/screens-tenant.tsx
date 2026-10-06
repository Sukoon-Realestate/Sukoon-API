import React, { useState } from "react";
import {
  Home, Bell, User, Building2, Calendar, MessageCircle, Menu,
  Settings, Shield, Lock, CheckCircle, AlertCircle, Clock, Eye, EyeOff,
  Star, MapPin, Heart, Send, Mic, Image as ImageIcon,
  ArrowLeft, ChevronRight, ChevronLeft, X, Plus, Check, AlertTriangle,
  FileText, Users, BarChart2, LogOut, Phone, Key, Edit2, Trash2,
  TrendingUp, TrendingDown, RefreshCw, Filter, Search, Info,
} from "lucide-react";
import { C, TJ, Badge, BadgeType, PrimaryBtn, OutlineBtn, Card, PrivacyBanner, WarnBanner, StatusBar, TenantNav, OwnerNav, StepProgress, TextInput } from "./design-system";

function TenantNotificationsScreen() {
  const notifs = [
    { icon: CheckCircle, bg: C.greenLight, color: C.green, title: "تم قبول طلب زيارتك", sub: "المالك أحمد محمد وافق على موعد الزيارة", time: "منذ 5 دقائق", unread: true },
    { icon: Bell, bg: C.tealLight, color: C.teal, title: "عقار جديد في منطقتك", sub: "شقة مفروشة 3 غرف — مدينة نصر 11,500 ج.م/شهر", time: "منذ ساعة", unread: true },
    { icon: AlertTriangle, bg: C.amberLight, color: C.amber, title: "أكمل توثيق حسابك", sub: "وثّق هويتك عشان تستخدم الشات بدون قيود", time: "منذ يومين", unread: false },
    { icon: Star, bg: C.goldLight, color: C.gold, title: "قيّم تجربتك بعد الزيارة", sub: "شقة مدينة نصر — اضغط لتقديم تقييمك", time: "منذ 3 أيام", unread: false },
    { icon: MessageCircle, bg: C.blueLight, color: C.blue, title: "رسالة جديدة من المالك", sub: "أحمد محمد: الشقة لسه متاحة، هل تريد معلومات أكتر؟", time: "منذ أسبوع", unread: false },
  ];
  return (
    <div className="flex flex-col h-full" style={{ backgroundColor: C.bg }}>
      <StatusBar />
      <div className="px-5 pt-1 pb-3 flex items-center justify-between" dir="rtl">
        <h1 className="text-xl font-black" style={{ ...TJ, color: C.navy }}>الإشعارات</h1>
        <button className="text-sm font-bold" style={{ ...TJ, color: C.teal }}>تحديد الكل كمقروء</button>
      </div>
      <div className="flex-1 overflow-y-auto px-5 pb-4">
        <div className="flex flex-col gap-2">
          {notifs.map((n, i) => (
            <div key={i} className="flex items-start gap-3 p-4 rounded-2xl"
              style={{ backgroundColor: n.unread ? C.white : C.bg, border: `1px solid ${n.unread ? C.teal + "30" : C.border}`, boxShadow: n.unread ? "0 2px 8px rgba(0,0,0,0.06)" : "none" }}
              dir="rtl">
              <div className="w-10 h-10 rounded-2xl flex items-center justify-center flex-shrink-0" style={{ backgroundColor: n.bg }}>
                <n.icon size={18} style={{ color: n.color }} />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-start justify-between gap-2">
                  <p className="font-black text-sm leading-tight" style={{ ...TJ, color: C.navy }}>{n.title}</p>
                  {n.unread && <div className="w-2 h-2 rounded-full flex-shrink-0 mt-1" style={{ backgroundColor: C.teal }} />}
                </div>
                <p className="text-xs mt-0.5 leading-relaxed" style={{ ...TJ, color: C.gray }}>{n.sub}</p>
                <p className="text-xs mt-1" style={{ ...TJ, color: "#D1D5DB" }}>{n.time}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
      <TenantNav active="notif" />
    </div>
  );
}

function TenantProfileScreen() {
  return (
    <div className="flex flex-col h-full" style={{ backgroundColor: C.bg }}>
      <StatusBar />
      <div className="flex-1 overflow-y-auto">
        <div className="px-5 pt-3 pb-4" dir="rtl">
          <div className="flex items-center justify-between mb-5">
            <h1 className="text-xl font-black" style={{ ...TJ, color: C.navy }}>حسابي</h1>
            <button className="w-9 h-9 rounded-xl flex items-center justify-center" style={{ backgroundColor: C.white, border: `1px solid ${C.border}` }}>
              <Settings size={16} style={{ color: C.navy }} />
            </button>
          </div>
          <Card className="mb-4">
            <div className="flex items-center gap-4">
              <div className="relative">
                <div className="w-16 h-16 rounded-full flex items-center justify-center" style={{ backgroundColor: C.tealLight }}>
                  <User size={30} style={{ color: C.teal }} />
                </div>
                <button className="absolute -bottom-1 -right-1 w-6 h-6 rounded-full flex items-center justify-center" style={{ backgroundColor: C.teal }}>
                  <Edit2 size={10} style={{ color: C.white }} />
                </button>
              </div>
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <h2 className="font-black text-lg" style={{ ...TJ, color: C.navy }}>أحمد محمد علي</h2>
                  <Badge type="verified" />
                </div>
                <p className="text-sm" style={{ ...TJ, color: C.gray }}>مستأجر · عضو منذ يناير 2026</p>
              </div>
            </div>
            <div className="mt-4 pt-3 grid grid-cols-3 gap-3" style={{ borderTop: `1px solid ${C.border}` }}>
              {[{ n: "12", l: "محفوظ" }, { n: "4", l: "زيارات" }, { n: "2", l: "تقييمات" }].map(({ n, l }, i) => (
                <div key={i} className="text-center p-2 rounded-xl" style={{ backgroundColor: C.bg }}>
                  <p className="font-black text-base" style={{ ...TJ, color: C.navy }}>{n}</p>
                  <p className="text-xs" style={{ ...TJ, color: C.gray }}>{l}</p>
                </div>
              ))}
            </div>
          </Card>
          <div className="flex flex-col gap-2 mb-4">
            {[
              { Icon: Calendar, label: "طلبات الزيارة", sub: "4 طلبات", color: C.teal, bg: C.tealLight },
              { Icon: FileText, label: "عقودي", sub: "1 عقد نشط", color: C.blue, bg: C.blueLight },
              { Icon: Star, label: "تقييماتي", sub: "2 تقييم", color: C.amber, bg: C.amberLight },
              { Icon: Shield, label: "التوثيق والخصوصية", sub: "موثّق ✓", color: C.green, bg: C.greenLight },
            ].map(({ Icon, label, sub, color, bg }, i) => (
              <button key={i} className="flex items-center gap-3 p-4 rounded-2xl text-right w-full"
                style={{ backgroundColor: C.white, border: `1px solid ${C.border}` }}>
                <div className="w-10 h-10 rounded-2xl flex items-center justify-center flex-shrink-0" style={{ backgroundColor: bg }}>
                  <Icon size={17} style={{ color }} />
                </div>
                <div className="flex-1">
                  <p className="font-bold text-sm" style={{ ...TJ, color: C.navy }}>{label}</p>
                  <p className="text-xs" style={{ ...TJ, color: C.gray }}>{sub}</p>
                </div>
                <ChevronLeft size={16} style={{ color: C.gray }} />
              </button>
            ))}
          </div>
          <Card className="mb-4">
            <p className="font-black text-sm mb-3" style={{ ...TJ, color: C.navy }}>بيانات الحساب</p>
            {[["الاسم", "أحمد محمد علي"], ["البريد", "ahmed@example.com"], ["الموبايل", "010****432"]].map(([l, v], i) => (
              <div key={i} className="flex justify-between items-center py-2.5" style={{ borderBottom: i < 2 ? `1px solid ${C.border}` : "none" }}>
                <div className="flex items-center gap-2">
                  <span className="text-sm font-bold" style={{ ...TJ, color: C.navy }}>{v}</span>
                </div>
                <span className="text-xs" style={{ ...TJ, color: C.gray }}>{l}</span>
              </div>
            ))}
          </Card>
          <button className="w-full flex items-center justify-center gap-2 py-4 rounded-2xl font-bold"
            style={{ backgroundColor: C.redLight, color: C.red, border: `1px solid ${C.red}30`, ...TJ }}>
            <LogOut size={16} />تسجيل الخروج
          </button>
        </div>
      </div>
      <TenantNav active="profile" />
    </div>
  );
}

function TenantMyVisitsScreen() {
  const visits = [
    { prop: "شقة مفروشة، مدينة نصر", owner: "أحمد محمد", date: "النهارده 3:00 م", status: "مقبول", statusColor: C.green, statusBg: C.greenLight },
    { prop: "ستوديو، التجمع الخامس", owner: "منى علي", date: "غداً 12:00 م", status: "بانتظار الرد", statusColor: C.amber, statusBg: C.amberLight },
    { prop: "شقة، المهندسين", owner: "خالد حسن", date: "الخميس 5:00 م", status: "مرفوض", statusColor: C.red, statusBg: C.redLight },
  ];
  return (
    <div className="flex flex-col h-full" style={{ backgroundColor: C.bg }}>
      <StatusBar />
      <div className="px-5 pt-1 pb-3 flex items-center gap-3" dir="rtl">
        <button><ArrowLeft size={20} style={{ color: C.navy }} /></button>
        <h1 className="text-xl font-black flex-1" style={{ ...TJ, color: C.navy }}>طلبات الزيارة</h1>
      </div>
      <div className="px-5 mb-3 flex gap-2" dir="rtl">
        {["الكل", "مقبولة", "بانتظار", "مرفوضة"].map((t, i) => (
          <button key={i} className="px-3 py-1.5 rounded-full text-xs font-bold"
            style={{ backgroundColor: i === 0 ? C.teal : C.white, color: i === 0 ? C.white : C.navy, border: `1px solid ${i === 0 ? C.teal : C.border}`, ...TJ }}>{t}</button>
        ))}
      </div>
      <div className="flex-1 overflow-y-auto px-5 pb-4">
        <div className="flex flex-col gap-3">
          {visits.map((v, i) => (
            <Card key={i}>
              <div className="flex items-start justify-between mb-3" dir="rtl">
                <div>
                  <p className="font-black text-sm" style={{ ...TJ, color: C.navy }}>{v.prop}</p>
                  <p className="text-xs" style={{ ...TJ, color: C.gray }}>المالك: {v.owner}</p>
                </div>
                <span className="text-xs font-black px-2 py-1 rounded-full flex-shrink-0"
                  style={{ backgroundColor: v.statusBg, color: v.statusColor, ...TJ }}>{v.status}</span>
              </div>
              <div className="flex items-center gap-2 mb-3" dir="rtl">
                <Calendar size={13} style={{ color: C.gray }} />
                <span className="text-xs" style={{ ...TJ, color: C.gray }}>{v.date}</span>
              </div>
              <div className="flex gap-2">
                {v.status === "مقبول" && (
                  <>
                    <button className="flex-1 py-2 rounded-xl text-xs font-black" style={{ backgroundColor: C.blueLight, color: C.blue, ...TJ }}>شات</button>
                    <button className="flex-1 py-2 rounded-xl text-xs font-black" style={{ backgroundColor: C.goldLight, color: C.gold, ...TJ }}>تقييم</button>
                  </>
                )}
                {v.status === "بانتظار الرد" && (
                  <button className="flex-1 py-2 rounded-xl text-xs font-black" style={{ backgroundColor: C.redLight, color: C.red, ...TJ }}>إلغاء الطلب</button>
                )}
                {v.status === "مرفوض" && (
                  <button className="flex-1 py-2 rounded-xl text-xs font-black text-white" style={{ backgroundColor: C.teal, ...TJ }}>البحث عن بديل</button>
                )}
              </div>
            </Card>
          ))}
        </div>
      </div>
      <TenantNav />
    </div>
  );
}

function TenantChatListScreen() {
  const chats = [
    { name: "أحمد محمد", prop: "شقة مدينة نصر", last: "ممتاز، العنوان: شارع عباس العقاد...", time: "9:30 ص", unread: 0, verified: true },
    { name: "منى علي", prop: "ستوديو التجمع", last: "متى تريد تعمل الزيارة؟", time: "أمس", unread: 2, verified: true },
    { name: "كريم طارق", prop: "شقة المعادي", last: "الشقة متاحة للعرض طول الأسبوع", time: "الأثنين", unread: 0, verified: false },
  ];
  return (
    <div className="flex flex-col h-full" style={{ backgroundColor: C.bg }}>
      <StatusBar />
      <div className="px-5 pt-1 pb-3" dir="rtl">
        <h1 className="text-xl font-black" style={{ ...TJ, color: C.navy }}>المحادثات</h1>
      </div>
      <div className="px-5 mb-3">
        <div className="flex items-center gap-2 px-4 py-3 rounded-2xl" style={{ backgroundColor: C.white, border: `1px solid ${C.border}` }}>
          <Search size={15} style={{ color: C.gray }} />
          <span className="flex-1 text-sm" style={{ color: "#9CA3AF", ...TJ }}>ابحث في المحادثات…</span>
        </div>
      </div>
      <div className="flex-1 overflow-y-auto pb-4">
        <div className="px-2">
          <PrivacyBanner text="رقم الموبايل مخفي داخل المحادثات دائماً" />
        </div>
        <div className="mt-3">
          {chats.map((c, i) => (
            <button key={i} className="w-full flex items-center gap-3 px-5 py-4 text-right"
              style={{ borderBottom: `1px solid ${C.border}` }}>
              <div className="w-12 h-12 rounded-full flex items-center justify-center flex-shrink-0 relative"
                style={{ backgroundColor: C.tealLight }}>
                <User size={22} style={{ color: C.teal }} />
                {c.unread > 0 && (
                  <span className="absolute -top-1 -right-1 w-5 h-5 rounded-full flex items-center justify-center text-white font-black"
                    style={{ backgroundColor: C.red, fontSize: 10 }}>{c.unread}</span>
                )}
              </div>
              <div className="flex-1 min-w-0" dir="rtl">
                <div className="flex items-center justify-between mb-0.5">
                  <div className="flex items-center gap-1.5">
                    <span className="font-black text-sm" style={{ ...TJ, color: C.navy }}>{c.name}</span>
                    {c.verified && <Badge type="verified" />}
                  </div>
                  <span className="text-xs flex-shrink-0" style={{ ...TJ, color: C.gray }}>{c.time}</span>
                </div>
                <p className="text-xs truncate" style={{ ...TJ, color: C.gray }}>{c.prop}</p>
                <p className="text-xs truncate mt-0.5" style={{ ...TJ, color: c.unread > 0 ? C.navy : "#9CA3AF", fontWeight: c.unread > 0 ? 700 : 400 }}>{c.last}</p>
              </div>
            </button>
          ))}
        </div>
      </div>
      <TenantNav active="chat" />
    </div>
  );
}

function RatePropertyScreen() {
  const [rating, setRating] = useState(0);
  const [hovered, setHovered] = useState(0);
  return (
    <div className="flex flex-col h-full" style={{ backgroundColor: "rgba(0,0,0,0.35)" }}>
      <div className="flex-1" />
      <div className="rounded-t-3xl px-6 py-6" style={{ backgroundColor: C.white }}>
        <div className="w-12 h-1.5 rounded-full mx-auto mb-4" style={{ backgroundColor: C.border }} />
        <div className="text-center mb-5" dir="rtl">
          <div className="w-14 h-14 rounded-full flex items-center justify-center mx-auto mb-3" style={{ backgroundColor: C.goldLight }}>
            <Star size={24} style={{ color: C.gold }} fill={C.gold} />
          </div>
          <h2 className="text-xl font-black mb-1" style={{ ...TJ, color: C.navy }}>قيّم تجربة الزيارة</h2>
          <p className="text-sm" style={{ ...TJ, color: C.gray }}>شقة مفروشة، مدينة نصر</p>
        </div>
        <div className="flex justify-center gap-3 mb-5" dir="ltr">
          {[1, 2, 3, 4, 5].map(s => (
            <button key={s} onMouseEnter={() => setHovered(s)} onMouseLeave={() => setHovered(0)} onClick={() => setRating(s)}>
              <Star size={36} fill={(hovered || rating) >= s ? C.gold : "none"} style={{ color: (hovered || rating) >= s ? C.gold : "#D1D5DB" }} />
            </button>
          ))}
        </div>
        <div className="flex flex-col gap-3 mb-5" dir="rtl">
          {["النظافة", "الدقة في البيانات", "تعامل المالك"].map((l, i) => (
            <div key={i} className="flex items-center justify-between">
              <div className="flex gap-2" dir="ltr">
                {[1, 2, 3, 4, 5].map(s => (
                  <Star key={s} size={18} fill={s <= 4 ? C.amber : "none"} style={{ color: s <= 4 ? C.amber : "#D1D5DB" }} />
                ))}
              </div>
              <span className="text-sm font-bold" style={{ ...TJ, color: C.navy }}>{l}</span>
            </div>
          ))}
        </div>
        <textarea dir="rtl" readOnly placeholder="اكتب تعليقك… (اختياري)"
          className="w-full px-4 py-3 rounded-2xl border text-sm outline-none resize-none mb-4"
          style={{ borderColor: C.border, ...TJ, color: C.navy, height: 80 }} />
        <PrimaryBtn text="إرسال التقييم" />
      </div>
    </div>
  );
}

function TenantSettingsScreen() {
  return (
    <div className="flex flex-col h-full" style={{ backgroundColor: C.bg }}>
      <StatusBar />
      <div className="px-5 pt-1 pb-3 flex items-center gap-3" dir="rtl">
        <button><ArrowLeft size={20} style={{ color: C.navy }} /></button>
        <h1 className="text-xl font-black flex-1" style={{ ...TJ, color: C.navy }}>الإعدادات والخصوصية</h1>
      </div>
      <div className="flex-1 overflow-y-auto px-5 pb-4" dir="rtl">
        <p className="text-xs font-black mb-2" style={{ ...TJ, color: C.gray }}>الإشعارات</p>
        <Card className="mb-4">
          {[{ l: "إشعارات الزيارات", on: true }, { l: "عقارات جديدة في منطقتي", on: true }, { l: "رسائل المالك", on: true }, { l: "التحديثات والعروض", on: false }].map(({ l, on }, i, arr) => (
            <div key={i} className="flex items-center justify-between py-2.5" style={{ borderBottom: i < arr.length - 1 ? `1px solid ${C.border}` : "none" }}>
              <div className="w-10 h-5 rounded-full relative flex-shrink-0" style={{ backgroundColor: on ? C.teal : "#E5E7EB" }}>
                <div className="absolute top-0.5 w-4 h-4 rounded-full" style={{ backgroundColor: C.white, right: on ? "2px" : "auto", left: on ? "auto" : "2px" }} />
              </div>
              <span className="text-sm" style={{ ...TJ, color: C.navy }}>{l}</span>
            </div>
          ))}
        </Card>
        <p className="text-xs font-black mb-2" style={{ ...TJ, color: C.gray }}>الخصوصية</p>
        <Card className="mb-4">
          {[{ l: "إخفاء رقم الموبايل دائماً", on: true, fixed: true }, { l: "مشاركة موقعي للبحث", on: true, fixed: false }, { l: "ظهور حسابي في البحث", on: false, fixed: false }].map(({ l, on, fixed }, i, arr) => (
            <div key={i} className="flex items-center justify-between py-2.5" style={{ borderBottom: i < arr.length - 1 ? `1px solid ${C.border}` : "none" }}>
              <div className="w-10 h-5 rounded-full relative flex-shrink-0 cursor-not-allowed"
                style={{ backgroundColor: on ? (fixed ? C.gold : C.teal) : "#E5E7EB" }}>
                <div className="absolute top-0.5 w-4 h-4 rounded-full" style={{ backgroundColor: C.white, right: on ? "2px" : "auto", left: on ? "auto" : "2px" }} />
              </div>
              <div className="text-right">
                <span className="text-sm" style={{ ...TJ, color: C.navy }}>{l}</span>
                {fixed && <p className="text-xs" style={{ ...TJ, color: C.gold }}>لا يمكن تغييره — لحماية خصوصيتك</p>}
              </div>
            </div>
          ))}
        </Card>
        <div className="mb-4">
          <PrivacyBanner text="رقمك الموبايل مخفي دائماً ولا يُشارك مع أي طرف بدون موافقتك" />
        </div>
        <p className="text-xs font-black mb-2" style={{ ...TJ, color: C.gray }}>الحساب</p>
        <Card className="mb-4">
          {["تغيير كلمة المرور", "تعديل بيانات الحساب", "حذف الحساب نهائياً"].map((t, i, arr) => (
            <button key={i} className="w-full flex items-center justify-between py-2.5 text-right"
              style={{ borderBottom: i < arr.length - 1 ? `1px solid ${C.border}` : "none" }}>
              <ChevronLeft size={16} style={{ color: C.gray }} />
              <span className="text-sm" style={{ ...TJ, color: i === arr.length - 1 ? C.red : C.navy }}>{t}</span>
            </button>
          ))}
        </Card>
      </div>
    </div>
  );
}

function SavedEmptyStateScreen() {
  return (
    <div className="flex flex-col h-full" style={{ backgroundColor: C.bg }}>
      <StatusBar />
      <div className="px-5 pt-1 pb-3" dir="rtl">
        <h1 className="text-xl font-black" style={{ ...TJ, color: C.navy }}>المحفوظات</h1>
        <p className="text-sm" style={{ ...TJ, color: C.gray }}>0 عقارات في قائمتك</p>
      </div>
      <div className="px-5 mb-3 flex gap-2" dir="rtl">
        {["الكل", "شقة", "ستوديو"].map((t, i) => (
          <button key={i} className="px-4 py-1.5 rounded-full text-sm font-bold"
            style={{ backgroundColor: i === 0 ? C.teal : C.white, color: i === 0 ? C.white : C.navy, border: `1px solid ${i === 0 ? C.teal : C.border}`, ...TJ }}>{t}</button>
        ))}
      </div>
      <div className="flex-1 flex flex-col items-center justify-center px-8 gap-5" dir="rtl">
        <div className="w-24 h-24 rounded-3xl flex items-center justify-center"
          style={{ backgroundColor: C.bg, border: `2px dashed ${C.border}` }}>
          <Heart size={40} style={{ color: "#D1D5DB" }} />
        </div>
        <div className="text-center">
          <h2 className="font-black text-xl mb-2" style={{ ...TJ, color: C.navy }}>لسه معندكش محفوظات</h2>
          <p className="text-sm" style={{ ...TJ, color: C.gray }}>احفظ العقارات اللي تعجبك عشان تقدر ترجعلها بسهولة</p>
        </div>
        <div className="w-full flex flex-col gap-3">
          <PrimaryBtn text="ابدأ البحث عن سكن" />
          <button className="text-center text-sm font-medium" style={{ ...TJ, color: C.gray }}>اضغط على ♡ على أي عقار لحفظه</button>
        </div>
        <div className="w-full">
          <p className="text-xs font-black mb-3 text-center" style={{ ...TJ, color: C.gray }}>جرب البحث عن:</p>
          <div className="flex flex-wrap gap-2 justify-center">
            {["شقة مفروشة مدينة نصر", "ستوديو التجمع", "غرفة بالمعادي", "دوبلكس المهندسين"].map((s, i) => (
              <button key={i} className="px-3 py-1.5 rounded-xl text-xs font-medium"
                style={{ backgroundColor: C.white, border: `1px solid ${C.border}`, ...TJ, color: C.navy }}>{s}</button>
            ))}
          </div>
        </div>
      </div>
      <TenantNav active="saved" />
    </div>
  );
}

function TenantChatSearchScreen() {
  return (
    <div className="flex flex-col h-full" style={{ backgroundColor: C.white }}>
      <StatusBar />
      <div className="px-5 pt-2 pb-3">
        <div className="flex items-center gap-3" dir="rtl">
          <button><ArrowLeft size={20} style={{ color: C.navy }} /></button>
          <div className="flex-1 flex items-center gap-2 px-4 py-3 rounded-2xl"
            style={{ backgroundColor: C.bg, border: `2px solid ${C.teal}` }}>
            <Search size={15} style={{ color: C.teal }} />
            <input placeholder="ابحث في المحادثات…" dir="rtl" readOnly className="flex-1 text-sm outline-none bg-transparent" style={{ ...TJ, color: C.navy }} />
            <X size={15} style={{ color: C.gray }} />
          </div>
        </div>
      </div>
      <div className="flex-1 overflow-y-auto px-5" dir="rtl">
        <p className="text-xs font-black mb-2 mt-1" style={{ ...TJ, color: C.gray }}>نتائج البحث عن "أحمد"</p>
        {[
          { name: "أحمد محمد", prop: "شقة مدينة نصر", match: "أحمد محمد: الشقة لسه متاحة، هل تريد المزيد؟", time: "9:30 ص" },
          { name: "أحمد طارق", prop: "ستوديو الزمالك", match: "أحمد طارق: تفضل بأي استفسار...", time: "أمس" },
        ].map((r, i) => (
          <div key={i} className="flex items-start gap-3 py-3" style={{ borderBottom: `1px solid ${C.border}` }}>
            <div className="w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0" style={{ backgroundColor: C.tealLight }}>
              <User size={18} style={{ color: C.teal }} />
            </div>
            <div className="flex-1">
              <div className="flex justify-between mb-0.5">
                <span className="font-black text-sm" style={{ ...TJ, color: C.navy }}>{r.name}</span>
                <span className="text-xs" style={{ ...TJ, color: C.gray }}>{r.time}</span>
              </div>
              <p className="text-xs" style={{ ...TJ, color: C.gray }}>{r.prop}</p>
              <p className="text-xs mt-0.5" style={{ ...TJ, color: C.teal }}>{r.match}</p>
            </div>
          </div>
        ))}
        <p className="text-xs font-black mb-2 mt-4" style={{ ...TJ, color: C.gray }}>عقارات مذكورة في المحادثات</p>
        {["شقة مدينة نصر", "ستوديو الزمالك"].map((p, i) => (
          <div key={i} className="flex items-center gap-3 py-3" style={{ borderBottom: `1px solid ${C.border}` }}>
            <div className="w-9 h-9 rounded-xl flex items-center justify-center" style={{ backgroundColor: "#E2E8F0" }}>
              <Building2 size={14} style={{ color: "#94A3B8" }} />
            </div>
            <span className="text-sm flex-1" style={{ ...TJ, color: C.navy }}>{p}</span>
            <ChevronLeft size={13} style={{ color: C.gray }} />
          </div>
        ))}
      </div>
    </div>
  );
}

function ReportSheetScreen() {
  const [selected, setSelected] = useState(0);
  const reasons = [
    "معلومات العقار غير صحيحة أو مضللة",
    "محتوى مسيء أو غير لائق",
    "احتيال أو نصب محتمل",
    "رقم هاتف ظاهر في الصور",
    "عقار غير موجود أو محجوز مسبقاً",
    "سبب آخر",
  ];
  return (
    <div className="flex flex-col h-full" style={{ backgroundColor: "rgba(0,0,0,0.4)" }}>
      <div className="flex-1" />
      <div className="rounded-t-3xl overflow-y-auto" style={{ backgroundColor: C.white, maxHeight: "88%" }}>
        <div className="px-5 pt-4 pb-2">
          <div className="w-12 h-1.5 rounded-full mx-auto mb-4" style={{ backgroundColor: C.border }} />
          <div className="flex items-center justify-between mb-1">
            <button><X size={20} style={{ color: C.navy }} /></button>
            <h2 className="text-lg font-black" style={{ ...TJ, color: C.navy }}>الإبلاغ عن مشكلة</h2>
            <div style={{ width: 20 }} />
          </div>
          <p className="text-sm text-center mb-4" style={{ ...TJ, color: C.gray }}>اختار سبب الإبلاغ</p>
        </div>
        <div className="px-5 pb-5" dir="rtl">
          <div className="flex flex-col gap-2 mb-5">
            {reasons.map((r, i) => (
              <button key={i} onClick={() => setSelected(i)}
                className="flex items-center gap-3 px-4 py-3.5 rounded-2xl text-right"
                style={{ backgroundColor: selected === i ? C.redLight : C.bg, border: `1px solid ${selected === i ? C.red : C.border}` }}>
                <div className="w-5 h-5 rounded-full border-2 flex items-center justify-center flex-shrink-0"
                  style={{ borderColor: selected === i ? C.red : C.border }}>
                  {selected === i && <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: C.red }} />}
                </div>
                <span className="text-sm flex-1" style={{ ...TJ, color: C.navy }}>{r}</span>
              </button>
            ))}
          </div>
          {selected === reasons.length - 1 && (
            <textarea dir="rtl" readOnly placeholder="اكتب تفاصيل المشكلة…"
              className="w-full px-4 py-3 rounded-2xl border text-sm outline-none resize-none mb-4"
              style={{ borderColor: C.border, ...TJ, color: C.navy, height: 80 }} />
          )}
          <div className="mb-4">
            <PrivacyBanner text="التقريرك سري ولن يُشارك مع الطرف الآخر" />
          </div>
          <button className="w-full py-4 rounded-2xl font-bold text-white" style={{ backgroundColor: C.red, ...TJ }}>
            إرسال البلاغ
          </button>
          <button className="w-full text-center mt-3 text-sm font-medium" style={{ ...TJ, color: C.gray }}>إلغاء</button>
        </div>
      </div>
    </div>
  );
}


function TenantSearchScreen() {
  return (
    <div className="flex flex-col h-full" style={{ backgroundColor: C.bg }}>
      <StatusBar />
      <div className="px-5 pt-2 pb-3" dir="rtl">
        <h1 className="text-xl font-black mb-3" style={{ ...TJ, color: C.navy }}>ابحث عن سكن</h1>
        <div className="flex items-center gap-3 px-4 py-3 rounded-2xl mb-3" style={{ backgroundColor: C.white, border: `2px solid ${C.teal}` }}>
          <Search size={16} style={{ color: C.teal }} />
          <span className="flex-1 text-sm" style={{ ...TJ, color: "#9CA3AF" }}>مدينة نصر، القاهرة…</span>
          <button className="text-xs font-bold px-2 py-1 rounded-xl" style={{ backgroundColor: C.tealLight, color: C.teal, ...TJ }}>بحث</button>
        </div>
        <div className="flex gap-2 overflow-x-auto pb-1">
          {["الكل", "شقة", "ستوديو", "غرفة", "دوبلكس", "فيلا"].map((t, i) => (
            <button key={i} className="px-3 py-1.5 rounded-full text-xs font-bold flex-shrink-0"
              style={{ backgroundColor: i===0 ? C.teal : C.white, color: i===0 ? C.white : C.navy, border: `1px solid ${i===0 ? C.teal : C.border}`, ...TJ }}>{t}</button>
          ))}
        </div>
      </div>
      <div className="flex-1 overflow-y-auto px-5 pb-4" dir="rtl">
        <p className="text-xs font-black mb-2" style={{ ...TJ, color: C.gray }}>مناطق مقترحة</p>
        <div className="grid grid-cols-3 gap-2 mb-4">
          {[
            { name: "مدينة نصر", n: 142, bg: "#E0F2F1" },
            { name: "التجمع الخامس", n: 89, bg: "#EEF5FF" },
            { name: "المهندسين", n: 76, bg: "#FFF7E6" },
            { name: "الزمالك", n: 34, bg: "#EAFBF1" },
            { name: "المعادي", n: 58, bg: "#FFF1F1" },
            { name: "مصر الجديدة", n: 47, bg: "#F3F4F6" },
          ].map((a, i) => (
            <button key={i} className="p-3 rounded-2xl text-right" style={{ backgroundColor: a.bg }}>
              <MapPin size={14} style={{ color: C.teal }} />
              <p className="font-black text-xs mt-1" style={{ ...TJ, color: C.navy }}>{a.name}</p>
              <p style={{ fontSize: 10, ...TJ, color: C.gray }}>{a.n} عقار</p>
            </button>
          ))}
        </div>
        <p className="text-xs font-black mb-2" style={{ ...TJ, color: C.gray }}>بحثت عنها مؤخراً</p>
        {["شقة مفروشة مدينة نصر", "ستوديو التجمع الخامس", "غرفة في الزمالك"].map((s, i) => (
          <div key={i} className="flex items-center gap-3 py-2.5" style={{ borderBottom: `1px solid ${C.border}` }}>
            <Clock size={14} style={{ color: C.gray }} />
            <span className="flex-1 text-sm" style={{ ...TJ, color: C.navy }}>{s}</span>
            <X size={13} style={{ color: "#D1D5DB" }} />
          </div>
        ))}
      </div>
      <TenantNav active="search" />
    </div>
  );
}

function SearchResultsScreen() {
  const props = [
    { t: "شقة مفروشة — مدينة نصر", p: "6,500", r: 4.8, n: 24, beds: 2, area: "90م²", badge: "verified" as const },
    { t: "ستوديو عصري — التجمع الخامس", p: "4,200", r: 4.6, n: 15, beds: 1, area: "55م²", badge: null },
    { t: "شقة 3 غرف — المهندسين", p: "8,800", r: 4.9, n: 32, beds: 3, area: "120م²", badge: "verified" as const },
    { t: "غرفة بحمام — الزمالك", p: "2,800", r: 4.4, n: 11, beds: 1, area: "30م²", badge: null },
  ];
  return (
    <div className="flex flex-col h-full" style={{ backgroundColor: C.bg }}>
      <StatusBar />
      <div className="px-5 pt-2 pb-2" dir="rtl">
        <div className="flex items-center gap-2 mb-2">
          <button><ArrowLeft size={18} style={{ color: C.navy }} /></button>
          <div className="flex-1 flex items-center gap-2 px-3 py-2 rounded-2xl" style={{ backgroundColor: C.white, border: `1px solid ${C.border}` }}>
            <Search size={13} style={{ color: C.gray }} />
            <span className="text-sm" style={{ ...TJ, color: C.navy }}>مدينة نصر، القاهرة</span>
          </div>
          <button className="w-9 h-9 rounded-2xl flex items-center justify-center" style={{ backgroundColor: C.white, border: `1px solid ${C.border}` }}>
            <Filter size={14} style={{ color: C.navy }} />
          </button>
        </div>
        <div className="flex items-center justify-between">
          <span className="text-xs" style={{ ...TJ, color: C.gray }}>142 عقار</span>
          <div className="flex gap-1">
            {["الأقرب", "السعر", "التقييم"].map((s, i) => (
              <button key={i} className="px-2.5 py-1 rounded-full text-xs font-bold"
                style={{ backgroundColor: i===0 ? C.navy : C.white, color: i===0 ? C.white : C.gray, border: `1px solid ${i===0 ? C.navy : C.border}`, ...TJ }}>{s}</button>
            ))}
          </div>
        </div>
      </div>
      <div className="flex-1 overflow-y-auto px-5 pb-4">
        <div className="flex flex-col gap-3">
          {props.map((p, i) => (
            <div key={i} className="rounded-3xl overflow-hidden" style={{ backgroundColor: C.white, border: `1px solid ${C.border}` }}>
              <div className="relative h-36" style={{ backgroundColor: "#E2E8F0" }}>
                <div className="absolute inset-0 flex items-center justify-center">
                  <Building2 size={32} style={{ color: "#94A3B8" }} />
                </div>
                <button className="absolute top-2.5 left-2.5 w-8 h-8 rounded-full flex items-center justify-center" style={{ backgroundColor: "rgba(255,255,255,0.9)" }}>
                  <Heart size={14} style={{ color: "#9CA3AF" }} />
                </button>
                {p.badge && (
                  <div className="absolute top-2.5 right-2.5">
                    <Badge type={p.badge} />
                  </div>
                )}
                <div className="absolute bottom-2.5 right-2.5 px-2 py-0.5 rounded-full text-xs font-black text-white" style={{ backgroundColor: C.teal, ...TJ }}>
                  {p.p} ج/شهر
                </div>
              </div>
              <div className="px-4 py-3" dir="rtl">
                <p className="font-black text-sm mb-1" style={{ ...TJ, color: C.navy }}>{p.t}</p>
                <div className="flex items-center gap-3 text-xs mb-2" style={{ color: C.gray }}>
                  <span style={TJ}>{p.beds} غرفة</span>
                  <span>·</span>
                  <span style={TJ}>{p.area}</span>
                  <span>·</span>
                  <div className="flex items-center gap-1">
                    <Star size={10} fill={C.amber} style={{ color: C.amber }} />
                    <span style={TJ}>{p.r} ({p.n})</span>
                  </div>
                </div>
                <PrimaryBtn text="اعرض التفاصيل" />
              </div>
            </div>
          ))}
        </div>
      </div>
      <TenantNav active="search" />
    </div>
  );
}

function FilterSheetScreen() {
  const [price, setPrice] = useState(8000);
  return (
    <div className="flex flex-col h-full" style={{ backgroundColor: "rgba(0,0,0,0.4)" }}>
      <div className="flex-1" />
      <div className="rounded-t-3xl overflow-y-auto" style={{ backgroundColor: C.white, maxHeight: "92%" }}>
        <div className="px-5 pt-4 pb-2">
          <div className="w-12 h-1.5 rounded-full mx-auto mb-4" style={{ backgroundColor: C.border }} />
          <div className="flex items-center justify-between mb-4">
            <button className="text-sm font-bold" style={{ ...TJ, color: C.gray }}>إعادة تعيين</button>
            <h2 className="text-lg font-black" style={{ ...TJ, color: C.navy }}>فلترة النتائج</h2>
            <button><X size={20} style={{ color: C.navy }} /></button>
          </div>
        </div>
        <div className="px-5 pb-6" dir="rtl">
          <p className="font-black text-sm mb-3" style={{ ...TJ, color: C.navy }}>نوع العقار</p>
          <div className="flex flex-wrap gap-2 mb-5">
            {["شقة", "ستوديو", "غرفة", "دوبلكس", "فيلا", "روف"].map((t, i) => (
              <button key={i} className="px-3 py-2 rounded-2xl text-sm font-bold"
                style={{ backgroundColor: i<2 ? C.teal : C.bg, color: i<2 ? C.white : C.navy, border: `1px solid ${i<2 ? C.teal : C.border}`, ...TJ }}>{t}</button>
            ))}
          </div>
          <p className="font-black text-sm mb-3" style={{ ...TJ, color: C.navy }}>الحد الأقصى للسعر — {price.toLocaleString()} ج/شهر</p>
          <input type="range" min={1000} max={20000} step={500} value={price} onChange={e => setPrice(+e.target.value)}
            className="w-full mb-5" style={{ accentColor: C.teal }} />
          <p className="font-black text-sm mb-3" style={{ ...TJ, color: C.navy }}>عدد الغرف</p>
          <div className="flex gap-2 mb-5">
            {["أي عدد", "1", "2", "3", "+4"].map((n, i) => (
              <button key={i} className="flex-1 py-2.5 rounded-2xl text-sm font-bold"
                style={{ backgroundColor: i===0 ? C.teal : C.bg, color: i===0 ? C.white : C.navy, border: `1px solid ${i===0 ? C.teal : C.border}`, ...TJ }}>{n}</button>
            ))}
          </div>
          <p className="font-black text-sm mb-3" style={{ ...TJ, color: C.navy }}>مرافق</p>
          <div className="grid grid-cols-3 gap-2 mb-5">
            {["مفروش", "واي فاي", "مكيف", "جراج", "حارس", "أسانسير"].map((f, i) => (
              <button key={i} className="flex items-center gap-2 px-3 py-2 rounded-2xl text-xs font-bold"
                style={{ backgroundColor: i<3 ? C.tealLight : C.bg, color: i<3 ? C.teal : C.gray, border: `1px solid ${i<3 ? C.teal : C.border}`, ...TJ }}>
                <Check size={11} style={{ color: i<3 ? C.teal : "transparent" }} />{f}
              </button>
            ))}
          </div>
          <PrimaryBtn text="عرض 142 نتيجة" />
        </div>
      </div>
    </div>
  );
}

function PropertyDetailScreen() {
  return (
    <div className="flex flex-col h-full" style={{ backgroundColor: C.bg }}>
      <div className="relative h-52" style={{ backgroundColor: "#CBD5E1" }}>
        <div className="absolute inset-0 flex items-center justify-center">
          <Building2 size={48} style={{ color: "#94A3B8" }} />
        </div>
        <div className="absolute top-0 left-0 right-0 p-4 flex items-center justify-between">
          <div className="flex gap-2">
            <button className="w-8 h-8 rounded-full flex items-center justify-center" style={{ backgroundColor: "rgba(255,255,255,0.9)" }}>
              <Heart size={14} style={{ color: "#9CA3AF" }} />
            </button>
            <button className="w-8 h-8 rounded-full flex items-center justify-center" style={{ backgroundColor: "rgba(255,255,255,0.9)" }}>
              <Send size={14} style={{ color: "#9CA3AF" }} />
            </button>
          </div>
          <button className="w-8 h-8 rounded-full flex items-center justify-center" style={{ backgroundColor: "rgba(255,255,255,0.9)" }}>
            <ArrowLeft size={16} style={{ color: C.navy }} />
          </button>
        </div>
        <div className="absolute bottom-2.5 left-2.5 flex gap-1">
          {[0,1,2,3,4].map(i => (
            <div key={i} className="rounded-full" style={{ width: i===0?16:6, height:6, backgroundColor: i===0 ? C.teal : "rgba(255,255,255,0.6)" }} />
          ))}
        </div>
      </div>
      <div className="flex-1 overflow-y-auto" dir="rtl">
        <div className="px-5 py-4">
          <div className="flex items-start justify-between mb-2">
            <Badge type="verified" />
            <div>
              <p className="text-xl font-black" style={{ ...TJ, color: C.navy }}>شقة مفروشة — مدينة نصر</p>
              <div className="flex items-center gap-1 mt-0.5">
                <MapPin size={12} style={{ color: C.gray }} />
                <span className="text-xs" style={{ ...TJ, color: C.gray }}>منطقة تقريبية · مدينة نصر</span>
              </div>
            </div>
          </div>
          <div className="flex items-center gap-2 mb-4">
            <Star size={14} fill={C.amber} style={{ color: C.amber }} />
            <span className="font-bold text-sm" style={{ ...TJ, color: C.navy }}>4.8</span>
            <span className="text-sm" style={{ ...TJ, color: C.gray }}>(24 تقييم)</span>
            <div className="flex-1" />
            <span className="text-xl font-black" style={{ ...TJ, color: C.teal }}>6,500</span>
            <span className="text-sm" style={{ ...TJ, color: C.gray }}>ج/شهر</span>
          </div>
          <div className="flex gap-3 mb-4">
            {[{ I: Building2, v: "3 غرف" }, { I: Users, v: "90م²" }, { I: CheckCircle, v: "مفروش" }].map(({ I, v }, i) => (
              <div key={i} className="flex-1 flex flex-col items-center gap-1 py-3 rounded-2xl" style={{ backgroundColor: C.white, border: `1px solid ${C.border}` }}>
                <I size={16} style={{ color: C.teal }} />
                <span className="text-xs font-bold" style={{ ...TJ, color: C.navy }}>{v}</span>
              </div>
            ))}
          </div>
          <Card className="mb-3">
            <p className="font-black text-sm mb-2" style={{ ...TJ, color: C.navy }}>الوصف</p>
            <p className="text-sm leading-6" style={{ ...TJ, color: C.gray }}>شقة مفروشة بالكامل في قلب مدينة نصر، قريبة من مترو الأنفاق والخدمات. الشقة مجددة حديثاً وتحتوي على كل الأجهزة الكهربائية.</p>
          </Card>
          <Card className="mb-3">
            <p className="font-black text-sm mb-2" style={{ ...TJ, color: C.navy }}>المرافق والخدمات</p>
            <div className="flex flex-wrap gap-2">
              {["واي فاي","مكيف","غسالة","ثلاجة","جراج","أسانسير","حارس","كاميرات"].map((f,i) => (
                <span key={i} className="px-2.5 py-1 rounded-full text-xs font-medium" style={{ backgroundColor: C.tealLight, color: C.teal, ...TJ }}>{f}</span>
              ))}
            </div>
          </Card>
          <Card className="mb-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full flex items-center justify-center" style={{ backgroundColor: C.tealLight }}>
                <User size={18} style={{ color: C.teal }} />
              </div>
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <p className="font-black text-sm" style={{ ...TJ, color: C.navy }}>أحمد محمد إبراهيم</p>
                  <Badge type="verified" />
                </div>
                <p className="text-xs" style={{ ...TJ, color: C.gray }}>مالك موثّق · 3 عقارات · 4.9 ★</p>
              </div>
            </div>
          </Card>
          <PrivacyBanner text="رقم الموبايل مخفي — يظهر بعد تأكيد الزيارة" />
        </div>
      </div>
      <div className="px-5 py-3 flex gap-3" style={{ borderTop: `1px solid ${C.border}`, backgroundColor: C.white }}>
        <OutlineBtn text="شات" />
        <PrimaryBtn text="احجز زيارة" />
      </div>
    </div>
  );
}

function PhotoGalleryScreen() {
  return (
    <div className="flex flex-col h-full" style={{ backgroundColor: "#0F172A" }}>
      <div className="flex items-center justify-between px-5 pt-10 pb-4">
        <div className="flex gap-2">
          <button className="w-9 h-9 rounded-full flex items-center justify-center" style={{ backgroundColor: "rgba(255,255,255,0.1)" }}>
            <Heart size={16} style={{ color: C.white }} />
          </button>
          <button className="w-9 h-9 rounded-full flex items-center justify-center" style={{ backgroundColor: "rgba(255,255,255,0.1)" }}>
            <Send size={16} style={{ color: C.white }} />
          </button>
        </div>
        <button className="w-9 h-9 rounded-full flex items-center justify-center" style={{ backgroundColor: "rgba(255,255,255,0.1)" }}>
          <X size={18} style={{ color: C.white }} />
        </button>
      </div>
      <div className="flex-1 flex items-center justify-center px-4">
        <div className="w-full rounded-3xl flex items-center justify-center" style={{ backgroundColor: "#1E293B", height: 280 }}>
          <Building2 size={56} style={{ color: "#334155" }} />
        </div>
      </div>
      <div className="px-5 py-4">
        <p className="text-center text-white font-bold mb-3 text-sm" style={TJ}>3 / 9 — صالة المعيشة</p>
        <div className="flex gap-2 justify-center">
          {[0,1,2,3,4,5,6,7,8].map(i => (
            <div key={i} className="rounded-xl flex items-center justify-center" style={{ width: i===2?40:32, height: i===2?40:32, backgroundColor: i===2 ? C.teal : "#334155", border: i===2 ? `2px solid ${C.white}` : "none" }}>
              <Building2 size={i===2?14:10} style={{ color: i===2 ? C.white : "#64748B" }} />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function PropertyMapScreen() {
  return (
    <div className="flex flex-col h-full" style={{ backgroundColor: C.bg }}>
      <StatusBar />
      <div className="flex items-center gap-3 px-5 pt-2 pb-3" dir="rtl">
        <button><ArrowLeft size={20} style={{ color: C.navy }} /></button>
        <h1 className="text-lg font-black flex-1" style={{ ...TJ, color: C.navy }}>الموقع التقريبي</h1>
      </div>
      {/* Map placeholder */}
      <div className="mx-5 rounded-3xl overflow-hidden mb-4 flex items-center justify-center" style={{ height: 240, backgroundColor: "#E2E8F0", position: "relative" }}>
        <div style={{ position: "absolute", inset: 0, background: "linear-gradient(135deg, #d1e8ff 0%, #c8e6c9 50%, #ffe0b2 100%)" }} />
        {/* Grid lines */}
        {[0,1,2,3].map(r => (
          <div key={r} style={{ position: "absolute", left: 0, right: 0, top: `${25*r}%`, height: 1, backgroundColor: "rgba(255,255,255,0.4)" }} />
        ))}
        {[0,1,2,3].map(c => (
          <div key={c} style={{ position: "absolute", top: 0, bottom: 0, left: `${25*c}%`, width: 1, backgroundColor: "rgba(255,255,255,0.4)" }} />
        ))}
        {/* Blurred pin area */}
        <div style={{ position: "absolute", width: 80, height: 80, borderRadius: "50%", backgroundColor: `${C.teal}30`, border: `2px dashed ${C.teal}` }} />
        <div className="rounded-full flex items-center justify-center" style={{ width: 36, height: 36, backgroundColor: C.teal, position: "relative" }}>
          <MapPin size={16} style={{ color: C.white }} />
        </div>
      </div>
      <div className="px-5 mb-4">
        <PrivacyBanner text="الموقع المعروض تقريبي لحماية خصوصية المالك" />
      </div>
      <div className="px-5">
        <Card>
          <p className="font-black text-sm mb-3" style={{ ...TJ, color: C.navy }}>قريب من</p>
          {[{ I: MapPin, t: "مترو كلية البنات", d: "5 دقائق سير" }, { I: Building2, t: "مول العرب", d: "10 دقائق سيارة" }, { I: CheckCircle, t: "مستشفى النزهة", d: "8 دقائق سيارة" }].map(({ I, t, d }, i) => (
            <div key={i} className="flex items-center gap-3 py-2.5" style={{ borderBottom: i<2 ? `1px solid ${C.border}` : "none" }} dir="rtl">
              <div className="w-7 h-7 rounded-xl flex items-center justify-center flex-shrink-0" style={{ backgroundColor: C.tealLight }}>
                <I size={13} style={{ color: C.teal }} />
              </div>
              <div className="flex-1">
                <p className="text-xs font-bold" style={{ ...TJ, color: C.navy }}>{t}</p>
                <p style={{ fontSize: 10, ...TJ, color: C.gray }}>{d}</p>
              </div>
            </div>
          ))}
        </Card>
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════
//  TENANT MISSING SCREENS — VISIT BOOKING
// ═══════════════════════════════════════════════

function BookVisitScreen() {
  return (
    <div className="flex flex-col h-full" style={{ backgroundColor: C.bg }}>
      <StatusBar />
      <div className="flex items-center gap-3 px-5 pt-2 pb-3" dir="rtl">
        <button><ArrowLeft size={20} style={{ color: C.navy }} /></button>
        <h1 className="text-xl font-black flex-1" style={{ ...TJ, color: C.navy }}>احجز زيارة</h1>
      </div>
      <div className="flex-1 overflow-y-auto px-5 pb-4" dir="rtl">
        <Card className="mb-3">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl flex items-center justify-center" style={{ backgroundColor: C.tealLight }}>
              <Building2 size={18} style={{ color: C.teal }} />
            </div>
            <div>
              <p className="font-black text-sm" style={{ ...TJ, color: C.navy }}>شقة مفروشة — مدينة نصر</p>
              <p className="text-xs" style={{ ...TJ, color: C.gray }}>6,500 ج/شهر · 3 غرف</p>
            </div>
          </div>
        </Card>
        <p className="font-black text-sm mb-2" style={{ ...TJ, color: C.navy }}>اختار يوم الزيارة</p>
        <div className="flex gap-2 mb-5 overflow-x-auto pb-1">
          {["الجمعة 14","السبت 15","الأحد 16","الاثنين 17","الثلاثاء 18"].map((d, i) => (
            <button key={i} className="flex flex-col items-center px-3 py-3 rounded-2xl flex-shrink-0"
              style={{ backgroundColor: i===1 ? C.teal : C.white, border: `1px solid ${i===1 ? C.teal : C.border}` }}>
              <span className="text-xs font-bold" style={{ color: i===1 ? C.white : C.gray, ...TJ }}>{d.split(" ")[0]}</span>
              <span className="text-lg font-black" style={{ color: i===1 ? C.white : C.navy, ...TJ }}>{d.split(" ")[1]}</span>
            </button>
          ))}
        </div>
        <p className="font-black text-sm mb-2" style={{ ...TJ, color: C.navy }}>اختار الوقت</p>
        <div className="grid grid-cols-3 gap-2 mb-5">
          {["10:00 ص","11:00 ص","12:00 م","2:00 م","3:00 م","5:00 م"].map((t, i) => (
            <button key={i} className="py-2.5 rounded-2xl text-sm font-bold"
              style={{ backgroundColor: i===3 ? C.teal : i===2 ? "#F3F4F6" : C.white, color: i===3 ? C.white : i===2 ? "#9CA3AF" : C.navy, border: `1px solid ${i===3 ? C.teal : C.border}`, ...TJ }}>
              {t}{i===2 && " ✗"}
            </button>
          ))}
        </div>
        <div className="mb-4">
          <p className="font-black text-sm mb-2" style={{ ...TJ, color: C.navy }}>ملاحظة للمالك (اختياري)</p>
          <textarea dir="rtl" readOnly placeholder="أي تفاصيل تريد ذكرها…" className="w-full px-4 py-3 rounded-2xl border text-sm outline-none resize-none"
            style={{ borderColor: C.border, ...TJ, color: C.navy, height: 72 }} />
        </div>
        <PrivacyBanner text="رقمك لن يُشارك مع المالك حتى تأكيد الزيارة" />
        <div className="mt-4">
          <PrimaryBtn text="تأكيد طلب الزيارة" />
        </div>
      </div>
    </div>
  );
}

function VisitConfirmedScreen() {
  return (
    <div className="flex flex-col h-full items-center justify-center px-8" style={{ backgroundColor: C.bg }}>
      <div className="w-24 h-24 rounded-full flex items-center justify-center mb-5" style={{ backgroundColor: C.greenLight }}>
        <CheckCircle size={44} style={{ color: C.green }} />
      </div>
      <h1 className="text-2xl font-black text-center mb-2" style={{ ...TJ, color: C.navy }}>تم إرسال طلب الزيارة!</h1>
      <p className="text-sm text-center mb-6" style={{ ...TJ, color: C.gray }}>المالك سيرد عليك خلال 24 ساعة. هتلاقي تحديثات في الإشعارات.</p>
      <Card className="w-full mb-6">
        <div className="flex flex-col gap-3" dir="rtl">
          {[{ l: "العقار", v: "شقة مفروشة — مدينة نصر" }, { l: "اليوم", v: "السبت 15 يونيو" }, { l: "الوقت", v: "2:00 م" }, { l: "الحالة", v: "بانتظار رد المالك" }].map(({ l, v }, i) => (
            <div key={i} className="flex justify-between items-center py-1.5" style={{ borderBottom: i<3 ? `1px solid ${C.border}` : "none" }}>
              <span className="text-sm font-bold" style={{ ...TJ, color: C.navy }}>{v}</span>
              <span className="text-xs" style={{ ...TJ, color: C.gray }}>{l}</span>
            </div>
          ))}
        </div>
      </Card>
      <div className="w-full flex flex-col gap-3">
        <PrimaryBtn text="متابعة طلباتي" />
        <OutlineBtn text="ارجع للبحث" />
      </div>
    </div>
  );
}

function VisitDetailScreen() {
  return (
    <div className="flex flex-col h-full" style={{ backgroundColor: C.bg }}>
      <StatusBar />
      <div className="flex items-center gap-3 px-5 pt-2 pb-3" dir="rtl">
        <button><ArrowLeft size={20} style={{ color: C.navy }} /></button>
        <h1 className="text-xl font-black flex-1" style={{ ...TJ, color: C.navy }}>تفاصيل الزيارة</h1>
      </div>
      <div className="flex-1 overflow-y-auto px-5 pb-4" dir="rtl">
        <div className="text-center py-4 mb-4">
          <div className="w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-3" style={{ backgroundColor: C.greenLight }}>
            <CheckCircle size={28} style={{ color: C.green }} />
          </div>
          <span className="text-sm font-black px-3 py-1.5 rounded-full" style={{ backgroundColor: C.greenLight, color: C.green, ...TJ }}>مقبول ✓</span>
          <h2 className="text-lg font-black mt-2" style={{ ...TJ, color: C.navy }}>زيارتك مؤكدة</h2>
        </div>
        <Card className="mb-3">
          {[{ l: "العقار", v: "شقة مفروشة، مدينة نصر" }, { l: "التاريخ", v: "السبت 15 يونيو 2025" }, { l: "الوقت", v: "2:00 م" }, { l: "المالك", v: "أحمد محمد" }].map(({ l, v }, i) => (
            <div key={i} className="flex justify-between items-center py-2.5" style={{ borderBottom: i<3 ? `1px solid ${C.border}` : "none" }}>
              <span className="text-sm font-bold" style={{ ...TJ, color: C.navy }}>{v}</span>
              <span className="text-xs" style={{ ...TJ, color: C.gray }}>{l}</span>
            </div>
          ))}
        </Card>
        <Card className="mb-3">
          <p className="font-black text-sm mb-2" style={{ ...TJ, color: C.navy }}>معلومات التواصل</p>
          <div className="flex items-center gap-2 px-3 py-3 rounded-2xl" style={{ backgroundColor: C.greenLight }}>
            <Phone size={14} style={{ color: C.green }} />
            <div className="flex-1" dir="rtl">
              <p className="text-xs font-black" style={{ ...TJ, color: "#166534" }}>رقم المالك — بعد التأكيد</p>
              <p className="font-black" style={{ ...TJ, color: "#166534" }}>010****432</p>
            </div>
          </div>
        </Card>
        <div className="flex flex-col gap-3">
          <PrimaryBtn text="فتح المحادثة مع المالك" />
          <OutlineBtn text="إلغاء الزيارة" />
        </div>
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════
//  TENANT MISSING SCREENS — CHAT
// ═══════════════════════════════════════════════

function TenantChatThreadScreen() {
  const msgs = [
    { me: false, t: "أهلاً! الشقة لسه متاحة، تحب تحجز زيارة؟", time: "9:10 ص" },
    { me: true, t: "أيوه عايز أزور يوم السبت الساعة 2م", time: "9:12 ص" },
    { me: false, t: "تمام، هينفع معايا. هبعتلك تأكيد", time: "9:13 ص" },
    { me: true, t: "شكراً جزيلاً", time: "9:14 ص" },
  ];
  return (
    <div className="flex flex-col h-full" style={{ backgroundColor: C.bg }}>
      <StatusBar />
      <div className="flex items-center gap-3 px-5 pt-2 pb-3" style={{ backgroundColor: C.white, borderBottom: `1px solid ${C.border}` }} dir="rtl">
        <button><ArrowLeft size={18} style={{ color: C.navy }} /></button>
        <div className="w-9 h-9 rounded-full flex items-center justify-center" style={{ backgroundColor: C.tealLight }}>
          <User size={16} style={{ color: C.teal }} />
        </div>
        <div className="flex-1">
          <p className="font-black text-sm" style={{ ...TJ, color: C.navy }}>أحمد محمد</p>
          <p className="text-xs" style={{ ...TJ, color: C.gray }}>شقة مدينة نصر · نشط الآن</p>
        </div>
        <Badge type="verified" />
      </div>
      <div className="flex-1 overflow-y-auto px-4 py-3 flex flex-col gap-2">
        <div className="text-center mb-2">
          <span className="text-xs px-2 py-0.5 rounded-full" style={{ backgroundColor: C.bg, color: C.gray, ...TJ }}>النهارده</span>
        </div>
        {msgs.map((m, i) => (
          <div key={i} className={`flex ${m.me ? "justify-start" : "justify-end"}`}>
            <div className="max-w-xs">
              <div className="px-4 py-2.5 text-sm" style={{ ...TJ, backgroundColor: m.me ? C.white : C.teal, color: m.me ? C.navy : C.white, border: m.me ? `1px solid ${C.border}` : "none", borderRadius: m.me ? "4px 16px 16px 16px" : "16px 4px 16px 16px" }}>{m.t}</div>
              <p className="text-xs mt-0.5 px-1" style={{ ...TJ, color: C.gray, textAlign: m.me ? "right" : "left" }}>{m.time}</p>
            </div>
          </div>
        ))}
        <PrivacyBanner text="رقم الموبايل مخفي في المحادثة" />
      </div>
      <div className="px-4 py-3 flex items-center gap-2" style={{ backgroundColor: C.white, borderTop: `1px solid ${C.border}` }}>
        <button className="w-9 h-9 rounded-full flex items-center justify-center flex-shrink-0" style={{ backgroundColor: C.bg }}>
          <ImageIcon size={14} style={{ color: C.gray }} />
        </button>
        <div className="flex-1 flex items-center px-3 py-2.5 rounded-2xl gap-2" style={{ backgroundColor: C.bg, border: `1px solid ${C.border}` }}>
          <input dir="rtl" readOnly placeholder="اكتب رسالة…" className="flex-1 text-sm outline-none bg-transparent" style={{ ...TJ, color: C.navy }} />
          <Mic size={14} style={{ color: C.gray }} />
        </div>
        <button className="w-9 h-9 rounded-full flex items-center justify-center flex-shrink-0" style={{ backgroundColor: C.teal }}>
          <Send size={14} style={{ color: C.white }} />
        </button>
      </div>
    </div>
  );
}

function TenantChatRestrictedScreen() {
  return (
    <div className="flex flex-col h-full" style={{ backgroundColor: C.bg }}>
      <StatusBar />
      <div className="flex items-center gap-3 px-5 pt-2 pb-3" style={{ backgroundColor: C.white, borderBottom: `1px solid ${C.border}` }} dir="rtl">
        <button><ArrowLeft size={18} style={{ color: C.navy }} /></button>
        <div className="w-9 h-9 rounded-full flex items-center justify-center" style={{ backgroundColor: "#E5E7EB" }}>
          <User size={16} style={{ color: "#9CA3AF" }} />
        </div>
        <div className="flex-1">
          <p className="font-black text-sm" style={{ ...TJ, color: C.navy }}>محمد طارق</p>
          <p className="text-xs" style={{ ...TJ, color: C.gray }}>ستوديو الزمالك</p>
        </div>
      </div>
      <div className="flex-1 flex flex-col items-center justify-center px-8 gap-4" dir="rtl">
        <div className="w-20 h-20 rounded-3xl flex items-center justify-center" style={{ backgroundColor: C.amberLight }}>
          <Lock size={32} style={{ color: C.amber }} />
        </div>
        <div className="text-center">
          <h2 className="text-lg font-black mb-2" style={{ ...TJ, color: C.navy }}>الشات محدود لحسابات موثّقة</h2>
          <p className="text-sm" style={{ ...TJ, color: C.gray }}>عشان تقدر تتواصل مع الملاك، لازم توثّق هويتك الأول</p>
        </div>
        <WarnBanner text="الشات لمستخدمين موثّقين فقط" action="وثّق الآن" />
        <div className="w-full flex flex-col gap-3">
          <PrimaryBtn text="ابدأ التوثيق KYC" />
          <OutlineBtn text="اعرف أكتر عن التوثيق" />
        </div>
      </div>
      <div className="px-4 py-3" style={{ backgroundColor: C.white, borderTop: `1px solid ${C.border}` }}>
        <div className="flex items-center gap-2 px-3 py-3 rounded-2xl opacity-50" style={{ backgroundColor: C.bg }}>
          <Lock size={14} style={{ color: C.gray }} />
          <span className="text-sm" style={{ ...TJ, color: "#9CA3AF" }}>الكتابة معطلة — وثّق أولاً</span>
        </div>
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════
//  TENANT MISSING SCREENS — SAVED & KYC
// ═══════════════════════════════════════════════

function SavedListingsScreen() {
  const items = [
    { t: "شقة مفروشة — مدينة نصر", p: "6,500", r: 4.8, area: "90م²" },
    { t: "ستوديو عصري — التجمع", p: "4,200", r: 4.6, area: "55م²" },
    { t: "شقة 3 غرف — المهندسين", p: "8,800", r: 4.9, area: "120م²" },
  ];
  return (
    <div className="flex flex-col h-full" style={{ backgroundColor: C.bg }}>
      <StatusBar />
      <div className="px-5 pt-1 pb-3 flex items-center justify-between" dir="rtl">
        <div>
          <h1 className="text-xl font-black" style={{ ...TJ, color: C.navy }}>المحفوظات</h1>
          <p className="text-xs" style={{ ...TJ, color: C.gray }}>{items.length} عقارات محفوظة</p>
        </div>
        <button className="text-xs font-bold" style={{ ...TJ, color: C.gray }}>تحديد الكل</button>
      </div>
      <div className="flex-1 overflow-y-auto px-5 pb-4 flex flex-col gap-3">
        {items.map((p, i) => (
          <div key={i} className="rounded-3xl overflow-hidden" style={{ backgroundColor: C.white, border: `1px solid ${C.border}` }}>
            <div className="relative h-32" style={{ backgroundColor: "#E2E8F0" }}>
              <div className="absolute inset-0 flex items-center justify-center">
                <Building2 size={28} style={{ color: "#94A3B8" }} />
              </div>
              <button className="absolute top-2.5 left-2.5 w-8 h-8 rounded-full flex items-center justify-center" style={{ backgroundColor: "rgba(255,255,255,0.9)" }}>
                <Heart size={14} fill={C.red} style={{ color: C.red }} />
              </button>
            </div>
            <div className="px-4 py-3" dir="rtl">
              <p className="font-black text-sm mb-1" style={{ ...TJ, color: C.navy }}>{p.t}</p>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 text-xs" style={{ color: C.gray }}>
                  <Star size={10} fill={C.amber} style={{ color: C.amber }} />
                  <span style={TJ}>{p.r}</span>
                  <span>·</span>
                  <span style={TJ}>{p.area}</span>
                </div>
                <span className="font-black text-sm" style={{ ...TJ, color: C.teal }}>{p.p} ج</span>
              </div>
            </div>
          </div>
        ))}
      </div>
      <TenantNav active="saved" />
    </div>
  );
}

function KYCStartScreen() {
  return (
    <div className="flex flex-col h-full" style={{ backgroundColor: C.bg }}>
      <StatusBar />
      <div className="flex items-center gap-3 px-5 pt-2 pb-3" dir="rtl">
        <button><ArrowLeft size={20} style={{ color: C.navy }} /></button>
        <h1 className="text-xl font-black flex-1" style={{ ...TJ, color: C.navy }}>توثيق الهوية</h1>
      </div>
      <div className="flex-1 overflow-y-auto px-5 pb-6" dir="rtl">
        <StepProgress total={4} current={1} />
        <div className="text-center py-6 mb-4">
          <div className="w-20 h-20 rounded-3xl flex items-center justify-center mx-auto mb-4" style={{ backgroundColor: C.tealLight }}>
            <Shield size={36} style={{ color: C.teal }} />
          </div>
          <h2 className="text-xl font-black mb-2" style={{ ...TJ, color: C.navy }}>وثّق هويتك وابدأ</h2>
          <p className="text-sm leading-6" style={{ ...TJ, color: C.gray }}>التوثيق بيحمي الملاك والمستأجرين، ويفتح إمكانية التواصل المباشر والحجز.</p>
        </div>
        <div className="flex flex-col gap-3 mb-6">
          {[
            { I: CheckCircle, t: "الوصول الكامل للشات", sub: "تواصل مباشر مع الملاك" },
            { I: Shield, t: "مصداقية أعلى", sub: "ملفك يظهر كـ موثّق ✓" },
            { I: Star, t: "أولوية في الحجز", sub: "طلباتك تحصل أسبقية" },
          ].map(({ I, t, sub }, i) => (
            <div key={i} className="flex items-center gap-3 p-3 rounded-2xl" style={{ backgroundColor: C.white, border: `1px solid ${C.border}` }}>
              <div className="w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0" style={{ backgroundColor: C.tealLight }}>
                <I size={16} style={{ color: C.teal }} />
              </div>
              <div>
                <p className="font-black text-sm" style={{ ...TJ, color: C.navy }}>{t}</p>
                <p className="text-xs" style={{ ...TJ, color: C.gray }}>{sub}</p>
              </div>
            </div>
          ))}
        </div>
        <Card className="mb-4">
          <p className="font-black text-sm mb-2" style={{ ...TJ, color: C.navy }}>هتحتاج</p>
          {["بطاقة الرقم القومي (وجه وظهر)", "صورة سيلفي واضحة", "رقم موبايل فعّال"].map((r, i) => (
            <div key={i} className="flex items-center gap-2 py-1.5" style={{ borderBottom: i<2 ? `1px solid ${C.border}` : "none" }}>
              <CheckCircle size={13} style={{ color: C.teal }} />
              <span className="text-sm" style={{ ...TJ, color: C.navy }}>{r}</span>
            </div>
          ))}
        </Card>
        <PrimaryBtn text="ابدأ التوثيق" />
        <button className="w-full text-center mt-3 text-sm" style={{ ...TJ, color: C.gray }}>بعدين</button>
      </div>
    </div>
  );
}

function KYCUploadScreen() {
  return (
    <div className="flex flex-col h-full" style={{ backgroundColor: C.bg }}>
      <StatusBar />
      <div className="flex items-center gap-3 px-5 pt-2 pb-3" dir="rtl">
        <button><ArrowLeft size={20} style={{ color: C.navy }} /></button>
        <h1 className="text-xl font-black flex-1" style={{ ...TJ, color: C.navy }}>رفع المستندات</h1>
      </div>
      <div className="flex-1 overflow-y-auto px-5 pb-4" dir="rtl">
        <StepProgress total={4} current={2} />
        <p className="text-sm mb-5" style={{ ...TJ, color: C.gray }}>ارفع صورة واضحة للبطاقة الشخصية</p>
        {["وجه البطاقة (أمامية)", "ظهر البطاقة (خلفية)"].map((label, i) => (
          <div key={i} className="mb-4">
            <p className="font-black text-sm mb-2" style={{ ...TJ, color: C.navy }}>{label}</p>
            <div className="h-36 rounded-3xl border-2 border-dashed flex flex-col items-center justify-center gap-2"
              style={{ borderColor: i===0 ? C.teal : C.border, backgroundColor: i===0 ? C.tealLight : C.white }}>
              {i===0 ? (
                <>
                  <CheckCircle size={24} style={{ color: C.teal }} />
                  <p className="text-xs font-bold" style={{ ...TJ, color: C.teal }}>تم الرفع ✓</p>
                  <p style={{ fontSize: 10, ...TJ, color: C.teal }}>national_id_front.jpg</p>
                </>
              ) : (
                <>
                  <Plus size={24} style={{ color: "#9CA3AF" }} />
                  <p className="text-xs font-bold" style={{ ...TJ, color: C.gray }}>اضغط للرفع</p>
                  <p style={{ fontSize: 10, ...TJ, color: "#9CA3AF" }}>JPG أو PNG حتى 5MB</p>
                </>
              )}
            </div>
          </div>
        ))}
        <Card className="mb-4">
          <p className="font-black text-sm mb-2" style={{ ...TJ, color: C.navy }}>صورة سيلفي</p>
          <div className="h-28 rounded-2xl border-2 border-dashed flex flex-col items-center justify-center gap-2"
            style={{ borderColor: C.border, backgroundColor: C.bg }}>
            <User size={22} style={{ color: "#9CA3AF" }} />
            <p className="text-xs font-bold" style={{ ...TJ, color: C.gray }}>التقط صورة</p>
          </div>
        </Card>
        <PrivacyBanner text="مستنداتك مشفّرة ولن تُشارك إلا مع فريق المراجعة" />
        <div className="mt-4">
          <PrimaryBtn text="التالي — مراجعة البيانات" />
        </div>
      </div>
    </div>
  );
}

function KYCPendingScreen() {
  return (
    <div className="flex flex-col h-full items-center justify-center px-8" style={{ backgroundColor: C.bg }}>
      <div className="w-24 h-24 rounded-full flex items-center justify-center mb-5" style={{ backgroundColor: C.amberLight }}>
        <Clock size={44} style={{ color: C.amber }} />
      </div>
      <Badge type="pending" />
      <h1 className="text-2xl font-black text-center mt-3 mb-2" style={{ ...TJ, color: C.navy }}>طلبك قيد المراجعة</h1>
      <p className="text-sm text-center mb-6" style={{ ...TJ, color: C.gray }}>فريقنا بيراجع مستنداتك. هيوصلك إشعار خلال 24 ساعة.</p>
      <Card className="w-full mb-6" dir="rtl">
        {[{ l: "الاسم", v: "سارة أحمد خالد" }, { l: "رقم البطاقة", v: "29•••••••••12" }, { l: "وقت الإرسال", v: "النهارده 9:41 ص" }, { l: "المتوقع", v: "خلال 24 ساعة" }].map(({ l, v }, i) => (
          <div key={i} className="flex justify-between py-2" style={{ borderBottom: i<3 ? `1px solid ${C.border}` : "none" }}>
            <span className="text-sm font-bold" style={{ ...TJ, color: C.navy }}>{v}</span>
            <span className="text-xs" style={{ ...TJ, color: C.gray }}>{l}</span>
          </div>
        ))}
      </Card>
      <PrimaryBtn text="الرجوع للرئيسية" />
    </div>
  );
}

function KYCApprovedScreen() {
  return (
    <div className="flex flex-col h-full items-center justify-center px-8" style={{ backgroundColor: C.bg }}>
      <div className="w-28 h-28 rounded-full flex items-center justify-center mb-5" style={{ backgroundColor: C.tealLight }}>
        <Shield size={52} style={{ color: C.teal }} />
      </div>
      <div className="mb-2"><Badge type="verified" /></div>
      <h1 className="text-2xl font-black text-center mt-2 mb-2" style={{ ...TJ, color: C.navy }}>تم توثيق هويتك! 🎉</h1>
      <p className="text-sm text-center mb-6" style={{ ...TJ, color: C.gray }}>أنت دلوقتي مستأجر موثّق. يمكنك التواصل مع الملاك وحجز الزيارات.</p>
      <div className="flex flex-col gap-3 w-full mb-6">
        {[
          { I: CheckCircle, t: "الشات مفعّل", c: C.green },
          { I: Shield, t: "حسابك يحمل شارة موثّق", c: C.teal },
          { I: Star, t: "أولوية في حجز الزيارات", c: C.amber },
        ].map(({ I, t, c }, i) => (
          <div key={i} className="flex items-center gap-3 px-4 py-3 rounded-2xl" style={{ backgroundColor: C.white, border: `1px solid ${C.border}` }}>
            <I size={18} style={{ color: c }} />
            <span className="font-bold text-sm" style={{ ...TJ, color: C.navy }}>{t}</span>
          </div>
        ))}
      </div>
      <PrimaryBtn text="ابدأ البحث عن سكن" />
    </div>
  );
}

// ═══════════════════════════════════════════════
//  TENANT MISSING SCREENS — SUPPORT & ONBOARDING
// ═══════════════════════════════════════════════

function TenantSupportScreen() {
  return (
    <div className="flex flex-col h-full" style={{ backgroundColor: C.bg }}>
      <StatusBar />
      <div className="flex items-center gap-3 px-5 pt-2 pb-3" dir="rtl">
        <button><ArrowLeft size={20} style={{ color: C.navy }} /></button>
        <h1 className="text-xl font-black flex-1" style={{ ...TJ, color: C.navy }}>مركز المساعدة</h1>
      </div>
      <div className="flex-1 overflow-y-auto px-5 pb-4" dir="rtl">
        <div className="flex items-center gap-2 px-4 py-3 rounded-2xl mb-4" style={{ backgroundColor: C.white, border: `1px solid ${C.border}` }}>
          <Search size={15} style={{ color: C.gray }} />
          <input dir="rtl" readOnly placeholder="ابحث في الأسئلة الشائعة…" className="flex-1 text-sm outline-none" style={{ ...TJ, color: C.navy }} />
        </div>
        <p className="font-black text-sm mb-3" style={{ ...TJ, color: C.navy }}>تواصل معنا</p>
        <div className="grid grid-cols-2 gap-3 mb-5">
          {[{ I: MessageCircle, t: "شات مباشر", sub: "متاح 9ص–11م", c: C.teal, bg: C.tealLight }, { I: Phone, t: "اتصل بنا", sub: "16xxx", c: C.blue, bg: C.blueLight }].map(({ I, t, sub, c, bg }, i) => (
            <button key={i} className="flex flex-col items-center gap-2 py-4 rounded-2xl" style={{ backgroundColor: bg }}>
              <I size={22} style={{ color: c }} />
              <p className="font-black text-sm" style={{ ...TJ, color: C.navy }}>{t}</p>
              <p style={{ fontSize: 10, ...TJ, color: C.gray }}>{sub}</p>
            </button>
          ))}
        </div>
        <p className="font-black text-sm mb-3" style={{ ...TJ, color: C.navy }}>أسئلة شائعة</p>
        {[
          { q: "إزاي أحجز زيارة؟", a: "افتح صفحة العقار واضغط 'احجز زيارة'، اختار اليوم والوقت وأكّد." },
          { q: "إزاي أوثّق حسابي؟", a: "من الإعدادات، اضغط 'توثيق الهوية' وارفع صورة البطاقة وسيلفي." },
          { q: "ليه الرقم مخفي؟", a: "رقم المالك بيظهر بس بعد قبول الزيارة، لحماية الخصوصية." },
          { q: "ممكن أعمل بلاغ على عقار؟", a: "أيوه، من صفحة العقار اضغط على القائمة ثم 'الإبلاغ عن مشكلة'." },
        ].map(({ q, a }, i) => (
          <div key={i} className="mb-2">
            <button className="w-full flex items-center justify-between px-4 py-3 rounded-2xl text-right" style={{ backgroundColor: C.white, border: `1px solid ${C.border}` }}>
              <ChevronLeft size={14} style={{ color: C.gray }} />
              <span className="font-bold text-sm flex-1" style={{ ...TJ, color: C.navy }}>{q}</span>
            </button>
            <div className="px-4 py-2.5 mx-1 rounded-b-2xl" style={{ backgroundColor: C.bg, borderLeft: `2px solid ${C.teal}` }}>
              <p className="text-xs leading-5" style={{ ...TJ, color: C.gray }}>{a}</p>
            </div>
          </div>
        ))}
      </div>
      <TenantNav active="profile" />
    </div>
  );
}

function TenantSubmitTicketScreen() {
  return (
    <div className="flex flex-col h-full" style={{ backgroundColor: C.bg }}>
      <StatusBar />
      <div className="flex items-center gap-3 px-5 pt-2 pb-3" dir="rtl">
        <button><ArrowLeft size={20} style={{ color: C.navy }} /></button>
        <h1 className="text-xl font-black flex-1" style={{ ...TJ, color: C.navy }}>فتح تذكرة دعم</h1>
      </div>
      <div className="flex-1 overflow-y-auto px-5 pb-4" dir="rtl">
        <p className="text-sm mb-4" style={{ ...TJ, color: C.gray }}>اوصفلنا مشكلتك وهنرد عليك في أقرب وقت</p>
        <div className="flex flex-col gap-3 mb-4">
          <div>
            <p className="font-black text-sm mb-1.5" style={{ ...TJ, color: C.navy }}>نوع المشكلة</p>
            <div className="flex flex-wrap gap-2">
              {["حجز زيارة", "مشكلة في الدفع", "توثيق الهوية", "شكوى على مالك", "عقار مضلل", "أخرى"].map((t, i) => (
                <button key={i} className="px-3 py-1.5 rounded-full text-xs font-bold"
                  style={{ backgroundColor: i===0 ? C.teal : C.white, color: i===0 ? C.white : C.navy, border: `1px solid ${i===0 ? C.teal : C.border}`, ...TJ }}>{t}</button>
              ))}
            </div>
          </div>
          <TextInput label="الموضوع" placeholder="اكتب موضوع تذكرتك…" />
          <div>
            <p className="font-black text-sm mb-1.5" style={{ ...TJ, color: C.navy }}>التفاصيل</p>
            <textarea dir="rtl" readOnly placeholder="اوصف المشكلة بالتفصيل…" className="w-full px-4 py-3 rounded-2xl border text-sm outline-none resize-none"
              style={{ borderColor: C.border, ...TJ, color: C.navy, height: 100 }} />
          </div>
          <div>
            <p className="font-black text-sm mb-1.5" style={{ ...TJ, color: C.navy }}>إرفاق صور (اختياري)</p>
            <button className="w-full h-20 rounded-2xl border-2 border-dashed flex flex-col items-center justify-center gap-2"
              style={{ borderColor: C.border, backgroundColor: C.bg }}>
              <ImageIcon size={18} style={{ color: C.gray }} />
              <span className="text-xs" style={{ ...TJ, color: C.gray }}>اضغط لإضافة صور</span>
            </button>
          </div>
        </div>
        <PrimaryBtn text="إرسال التذكرة" />
      </div>
    </div>
  );
}

function TenantOnboardingScreen() {
  return (
    <div className="flex flex-col h-full" style={{ backgroundColor: C.bg }}>
      <div className="flex-1 flex flex-col items-center justify-center px-8">
        <div className="w-28 h-28 rounded-3xl flex items-center justify-center mb-6" style={{ backgroundColor: C.tealLight }}>
          <Shield size={52} style={{ color: C.teal }} />
        </div>
        <h1 className="text-3xl font-black text-center mb-2" style={{ ...TJ, color: C.navy }}>أهلاً في سكون</h1>
        <p className="text-sm text-center mb-8" style={{ ...TJ, color: C.gray }}>ابحث عن سكنك المناسب بأمان وشفافية مع منصة سكون المصرية الأولى في تأجير العقارات</p>
        <div className="flex flex-col gap-4 w-full mb-8">
          {[
            { I: Search, t: "ابحث بسهولة", sub: "آلاف العقارات في كل أنحاء مصر", c: C.teal, bg: C.tealLight },
            { I: Shield, t: "أمان وموثوقية", sub: "ملاك موثّقون وعقارات مراجعة", c: C.green, bg: C.greenLight },
            { I: MessageCircle, t: "تواصل مباشر", sub: "شات مباشر مع الملاك بعد التوثيق", c: C.blue, bg: C.blueLight },
          ].map(({ I, t, sub, c, bg }, i) => (
            <div key={i} className="flex items-center gap-4 px-4 py-3 rounded-2xl" style={{ backgroundColor: C.white, border: `1px solid ${C.border}` }}>
              <div className="w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0" style={{ backgroundColor: bg }}>
                <I size={18} style={{ color: c }} />
              </div>
              <div>
                <p className="font-black text-sm" style={{ ...TJ, color: C.navy }}>{t}</p>
                <p className="text-xs" style={{ ...TJ, color: C.gray }}>{sub}</p>
              </div>
            </div>
          ))}
        </div>
        <div className="flex gap-2 mb-6">
          {[0,1,2].map(i => <div key={i} className="rounded-full" style={{ width: i===0?20:8, height:8, backgroundColor: i===0 ? C.teal : C.border }} />)}
        </div>
        <PrimaryBtn text="ابدأ البحث عن سكن" />
        <button className="mt-3 text-sm font-medium" style={{ ...TJ, color: C.gray }}>لدي حساب — تسجيل دخول</button>
      </div>
    </div>
  );
}

function TenantPersonalizedHomeScreen() {
  return (
    <div className="flex flex-col h-full" style={{ backgroundColor: C.bg }}>
      <StatusBar />
      <div className="flex-1 overflow-y-auto">
        <div className="px-5 pt-3 pb-3" dir="rtl">
          <div className="flex items-center justify-between mb-4">
            <button className="relative w-9 h-9 rounded-full flex items-center justify-center" style={{ backgroundColor: C.white, border: `1px solid ${C.border}` }}>
              <Bell size={16} style={{ color: C.navy }} />
              <div className="absolute top-0.5 right-0.5 w-2 h-2 rounded-full" style={{ backgroundColor: C.red }} />
            </button>
            <div>
              <p className="font-black text-lg" style={{ ...TJ, color: C.navy }}>أهلاً سارة 👋</p>
              <p className="text-xs" style={{ ...TJ, color: C.gray }}>دلوقتي في مدينة نصر</p>
            </div>
            <div className="w-9 h-9 rounded-full flex items-center justify-center" style={{ backgroundColor: C.tealLight }}>
              <User size={16} style={{ color: C.teal }} />
            </div>
          </div>
          <div className="flex items-center gap-3 px-4 py-3 rounded-2xl mb-4" style={{ backgroundColor: C.white, border: `1px solid ${C.border}` }}>
            <Search size={15} style={{ color: C.gray }} />
            <span className="flex-1 text-sm" style={{ ...TJ, color: "#9CA3AF" }}>ابحث عن منطقة أو حي…</span>
            <button className="w-8 h-8 rounded-xl flex items-center justify-center" style={{ backgroundColor: C.teal }}>
              <Filter size={13} style={{ color: C.white }} />
            </button>
          </div>
          {/* Active visit banner */}
          <div className="flex items-center gap-3 px-4 py-3 rounded-2xl mb-4" style={{ backgroundColor: C.tealLight, border: `1px solid ${C.teal}30` }}>
            <Calendar size={18} style={{ color: C.teal }} />
            <div className="flex-1">
              <p className="font-black text-sm" style={{ ...TJ, color: C.teal }}>عندك زيارة النهارده 3:00 م</p>
              <p className="text-xs" style={{ ...TJ, color: C.teal }}>شقة مدينة نصر</p>
            </div>
            <ChevronLeft size={14} style={{ color: C.teal }} />
          </div>
        </div>
        <div className="px-5 mb-4" dir="rtl">
          <div className="flex items-center justify-between mb-2">
            <button className="text-xs font-bold" style={{ ...TJ, color: C.teal }}>عرض الكل</button>
            <p className="font-black text-sm" style={{ ...TJ, color: C.navy }}>مقترح ليك</p>
          </div>
          <div className="flex flex-col gap-3">
            {[
              { t: "شقة مفروشة — مدينة نصر", p: "6,500", r: 4.8, area: "90م²" },
              { t: "ستوديو التجمع الخامس", p: "4,200", r: 4.6, area: "55م²" },
            ].map((p, i) => (
              <div key={i} className="flex gap-3 rounded-2xl overflow-hidden" style={{ backgroundColor: C.white, border: `1px solid ${C.border}` }}>
                <div className="w-24 flex-shrink-0 flex items-center justify-center" style={{ backgroundColor: "#E2E8F0" }}>
                  <Building2 size={20} style={{ color: "#94A3B8" }} />
                </div>
                <div className="flex-1 px-3 py-3" dir="rtl">
                  <p className="font-black text-sm mb-1" style={{ ...TJ, color: C.navy }}>{p.t}</p>
                  <div className="flex items-center gap-2 text-xs mb-1" style={{ color: C.gray }}>
                    <Star size={10} fill={C.amber} style={{ color: C.amber }} />
                    <span style={TJ}>{p.r}</span>
                    <span>·</span>
                    <span style={TJ}>{p.area}</span>
                  </div>
                  <span className="font-black text-sm" style={{ ...TJ, color: C.teal }}>{p.p} ج/شهر</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
      <TenantNav active="home" />
    </div>
  );
}

// ═══════════════════════════════════════════════
//  OWNER MISSING SCREENS — HOME & PROPERTIES


export {
  TenantNotificationsScreen,
  TenantProfileScreen,
  TenantMyVisitsScreen,
  TenantChatListScreen,
  RatePropertyScreen,
  TenantSettingsScreen,
  SavedEmptyStateScreen,
  TenantChatSearchScreen,
  ReportSheetScreen,
  TenantSearchScreen,
  SearchResultsScreen,
  FilterSheetScreen,
  PropertyDetailScreen,
  PhotoGalleryScreen,
  PropertyMapScreen,
  BookVisitScreen,
  VisitConfirmedScreen,
  VisitDetailScreen,
  TenantChatThreadScreen,
  TenantChatRestrictedScreen,
  SavedListingsScreen,
  KYCStartScreen,
  KYCUploadScreen,
  KYCPendingScreen,
  KYCApprovedScreen,
  TenantSupportScreen,
  TenantSubmitTicketScreen,
  TenantOnboardingScreen,
  TenantPersonalizedHomeScreen
};
