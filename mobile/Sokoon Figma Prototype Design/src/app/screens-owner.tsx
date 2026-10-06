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

function OwnerProfileScreen() {
  return (
    <div className="flex flex-col h-full" style={{ backgroundColor: C.bg }}>
      <StatusBar />
      <div className="flex-1 overflow-y-auto">
        <div className="px-5 pt-3 pb-4" dir="rtl">
          <div className="flex items-center justify-between mb-5">
            <h1 className="text-xl font-black" style={{ ...TJ, color: C.navy }}>ملفي الشخصي</h1>
            <button className="w-9 h-9 rounded-xl flex items-center justify-center" style={{ backgroundColor: C.white, border: `1px solid ${C.border}` }}>
              <Edit2 size={16} style={{ color: C.navy }} />
            </button>
          </div>
          <Card className="mb-4">
            <div className="flex items-center gap-4">
              <div className="relative">
                <div className="w-16 h-16 rounded-full flex items-center justify-center" style={{ backgroundColor: C.goldLight }}>
                  <User size={30} style={{ color: C.gold }} />
                </div>
                <div className="absolute -bottom-1 -right-1 w-6 h-6 rounded-full flex items-center justify-center" style={{ backgroundColor: C.gold }}>
                  <Check size={10} style={{ color: C.white }} />
                </div>
              </div>
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <h2 className="font-black text-lg" style={{ ...TJ, color: C.navy }}>أحمد محمد علي</h2>
                  <Badge type="verified" text="مالك موثّق" />
                </div>
                <div className="flex items-center gap-1">
                  <Star size={12} fill={C.amber} style={{ color: C.amber }} />
                  <span className="text-xs" style={{ ...TJ, color: C.gray }}>4.8 (42 تقييم)</span>
                </div>
                <p className="text-xs mt-0.5" style={{ ...TJ, color: C.gray }}>عضو منذ يناير 2025</p>
              </div>
            </div>
            <div className="mt-4 pt-3 grid grid-cols-3 gap-3" style={{ borderTop: `1px solid ${C.border}` }}>
              {[{ n: "3", l: "عقارات" }, { n: "42", l: "تقييم" }, { n: "96%", l: "قبول" }].map(({ n, l }, i) => (
                <div key={i} className="text-center p-2 rounded-xl" style={{ backgroundColor: C.bg }}>
                  <p className="font-black text-base" style={{ ...TJ, color: C.navy }}>{n}</p>
                  <p className="text-xs" style={{ ...TJ, color: C.gray }}>{l}</p>
                </div>
              ))}
            </div>
          </Card>
          <Card className="mb-4">
            <p className="font-black text-sm mb-3" style={{ ...TJ, color: C.navy }}>بيانات الحساب</p>
            {[["الاسم", "أحمد محمد علي"], ["البريد", "ahmed@example.com"], ["الموبايل", "010****432"]].map(([l, v], i) => (
              <div key={i} className="flex justify-between items-center py-2.5" style={{ borderBottom: i < 2 ? `1px solid ${C.border}` : "none" }}>
                <span className="text-sm font-bold" style={{ ...TJ, color: C.navy }}>{v}</span>
                <span className="text-xs" style={{ ...TJ, color: C.gray }}>{l}</span>
              </div>
            ))}
          </Card>
          <div className="mb-4">
            <PrivacyBanner text="رقمك لا يُعرض للمستأجرين — يظهر فقط بعد قبول الزيارة" />
          </div>
          <Card>
            <p className="font-black text-sm mb-3" style={{ ...TJ, color: C.navy }}>آخر التقييمات</p>
            {[
              { n: "سارة أحمد", r: 5, t: "مالك ممتاز ومتعاون جداً" },
              { n: "محمد علي", r: 4, t: "سريع في الرد والتواصل كان سهل" },
            ].map((rev, i) => (
              <div key={i} className="py-3" style={{ borderBottom: i === 0 ? `1px solid ${C.border}` : "none" }}>
                <div className="flex items-center justify-between mb-1">
                  <div className="flex gap-0.5">{[1,2,3,4,5].map(s => <Star key={s} size={12} fill={s <= rev.r ? C.amber : "none"} style={{ color: s <= rev.r ? C.amber : "#D1D5DB" }} />)}</div>
                  <span className="text-xs font-bold" style={{ ...TJ, color: C.navy }}>{rev.n}</span>
                </div>
                <p className="text-xs" style={{ ...TJ, color: C.gray }}>{rev.t}</p>
              </div>
            ))}
          </Card>
        </div>
      </div>
      <OwnerNav active="more" />
    </div>
  );
}

function OwnerMoreScreen() {
  return (
    <div className="flex flex-col h-full" style={{ backgroundColor: C.bg }}>
      <StatusBar />
      <div className="px-5 pt-3 pb-4" dir="rtl">
        <div className="flex items-center gap-3 mb-5">
          <div className="w-12 h-12 rounded-full flex items-center justify-center" style={{ backgroundColor: C.goldLight }}>
            <User size={24} style={{ color: C.gold }} />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="font-black text-base" style={{ ...TJ, color: C.navy }}>أحمد محمد علي</h1>
              <Badge type="verified" text="مالك موثّق" />
            </div>
            <p className="text-xs" style={{ ...TJ, color: C.gray }}>عرض الملف الشخصي</p>
          </div>
        </div>
      </div>
      <div className="flex-1 overflow-y-auto px-5 pb-4" dir="rtl">
        {[
          { label: "الحساب والملف الشخصي", items: [
            { Icon: User, l: "ملفي الشخصي", color: C.teal, bg: C.tealLight },
            { Icon: Shield, l: "التوثيق والوثائق", color: C.green, bg: C.greenLight },
            { Icon: Lock, l: "الخصوصية والأمان", color: C.blue, bg: C.blueLight },
          ]},
          { label: "إدارة العقارات", items: [
            { Icon: Building2, l: "عقاراتي", color: C.gold, bg: C.goldLight },
            { Icon: BarChart2, l: "التحليلات والإحصاءات", color: C.blue, bg: C.blueLight },
            { Icon: Calendar, l: "جدول الزيارات", color: C.teal, bg: C.tealLight },
          ]},
          { label: "الدعم", items: [
            { Icon: Info, l: "مركز المساعدة", color: C.gray, bg: "#F3F4F6" },
            { Icon: FileText, l: "الشروط والسياسات", color: C.gray, bg: "#F3F4F6" },
          ]},
        ].map(({ label, items }, gi) => (
          <div key={gi} className="mb-5">
            <p className="text-xs font-black mb-2" style={{ ...TJ, color: C.gray }}>{label}</p>
            <Card>
              {items.map(({ Icon, l, color, bg }, i) => (
                <button key={i} className="w-full flex items-center gap-3 py-3 text-right"
                  style={{ borderBottom: i < items.length - 1 ? `1px solid ${C.border}` : "none" }}>
                  <div className="w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0" style={{ backgroundColor: bg }}>
                    <Icon size={16} style={{ color }} />
                  </div>
                  <span className="flex-1 text-sm font-bold" style={{ ...TJ, color: C.navy }}>{l}</span>
                  <ChevronLeft size={15} style={{ color: C.gray }} />
                </button>
              ))}
            </Card>
          </div>
        ))}
        <button className="w-full flex items-center justify-center gap-2 py-4 rounded-2xl font-bold mb-3"
          style={{ backgroundColor: C.redLight, color: C.red, ...TJ }}>
          <LogOut size={16} />تسجيل الخروج
        </button>
      </div>
      <OwnerNav active="more" />
    </div>
  );
}

function OwnerNotificationsScreen() {
  const notifs = [
    { icon: Calendar, bg: C.greenLight, color: C.green, title: "طلب زيارة جديد!", sub: "سارة أحمد تطلب زيارة شقة مدينة نصر — النهارده 3م", time: "منذ 5 دقائق", unread: true },
    { icon: MessageCircle, bg: C.blueLight, color: C.blue, title: "رسالة جديدة من مستأجر", sub: "محمد علي: هل الشقة لسه متاحة؟", time: "منذ ساعة", unread: true },
    { icon: Eye, bg: C.tealLight, color: C.teal, title: "شقتك حصلت على 50 مشاهدة", sub: "شقة مفروشة، مدينة نصر — أداء متميز هذا الأسبوع", time: "اليوم 9 ص", unread: false },
    { icon: CheckCircle, bg: C.goldLight, color: C.gold, title: "عقارك تم توثيقه", sub: "ستوديو، التجمع الخامس — يظهر الآن في نتائج البحث", time: "أمس", unread: false },
    { icon: AlertTriangle, bg: C.amberLight, color: C.amber, title: "تحديث الظهور اليومي", sub: "حدّث عقاراتك يومياً للحفاظ على ترتيبها في البحث", time: "منذ يومين", unread: false },
  ];
  return (
    <div className="flex flex-col h-full" style={{ backgroundColor: C.bg }}>
      <StatusBar />
      <div className="px-5 pt-1 pb-3 flex items-center justify-between" dir="rtl">
        <h1 className="text-xl font-black" style={{ ...TJ, color: C.navy }}>الإشعارات</h1>
        <button className="text-sm font-bold" style={{ ...TJ, color: C.teal }}>تحديد الكل</button>
      </div>
      <div className="flex-1 overflow-y-auto px-5 pb-4">
        <div className="flex flex-col gap-2">
          {notifs.map((n, i) => (
            <div key={i} className="flex items-start gap-3 p-4 rounded-2xl"
              style={{ backgroundColor: n.unread ? C.white : C.bg, border: `1px solid ${n.unread ? C.teal + "30" : C.border}` }}
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
      <OwnerNav active="home" />
    </div>
  );
}

function OwnerChatListScreen() {
  const chats = [
    { name: "سارة أحمد", prop: "شقة مدينة نصر", last: "شكراً جداً! هكون موجودة في الوقت", time: "9:30 ص", unread: 0, status: "مقبول" },
    { name: "محمد علي", prop: "شقة مدينة نصر", last: "هل الشقة لسه متاحة؟", time: "أمس", unread: 1, status: "جديد" },
    { name: "نورا كمال", prop: "ستوديو التجمع", last: "متى ممكن أعمل الزيارة؟", time: "الأثنين", unread: 0, status: "قيد الانتظار" },
  ];
  return (
    <div className="flex flex-col h-full" style={{ backgroundColor: C.bg }}>
      <StatusBar />
      <div className="px-5 pt-1 pb-3" dir="rtl">
        <h1 className="text-xl font-black" style={{ ...TJ, color: C.navy }}>المحادثات</h1>
      </div>
      <div className="flex-1 overflow-y-auto pb-4">
        <div className="px-5 mb-2">
          <PrivacyBanner text="أرقام المستأجرين تظهر فقط بعد قبول الزيارة" />
        </div>
        {chats.map((c, i) => (
          <button key={i} className="w-full flex items-center gap-3 px-5 py-4 text-right"
            style={{ borderBottom: `1px solid ${C.border}` }}>
            <div className="w-12 h-12 rounded-full flex items-center justify-center flex-shrink-0 relative" style={{ backgroundColor: C.blueLight }}>
              <User size={22} style={{ color: C.blue }} />
              {c.unread > 0 && (
                <span className="absolute -top-1 -right-1 w-5 h-5 rounded-full flex items-center justify-center text-white font-black"
                  style={{ backgroundColor: C.red, fontSize: 10 }}>{c.unread}</span>
              )}
            </div>
            <div className="flex-1 min-w-0" dir="rtl">
              <div className="flex items-center justify-between mb-0.5">
                <span className="font-black text-sm" style={{ ...TJ, color: C.navy }}>{c.name}</span>
                <div className="flex items-center gap-2">
                  <span className="text-xs px-2 py-0.5 rounded-full font-bold"
                    style={{ backgroundColor: c.status === "مقبول" ? C.greenLight : c.status === "جديد" ? C.tealLight : C.amberLight, color: c.status === "مقبول" ? C.green : c.status === "جديد" ? C.teal : C.amber, ...TJ }}>
                    {c.status}
                  </span>
                  <span className="text-xs" style={{ ...TJ, color: C.gray }}>{c.time}</span>
                </div>
              </div>
              <p className="text-xs" style={{ ...TJ, color: C.gray }}>{c.prop}</p>
              <p className="text-xs truncate mt-0.5" style={{ ...TJ, color: c.unread > 0 ? C.navy : "#9CA3AF", fontWeight: c.unread > 0 ? 700 : 400 }}>{c.last}</p>
            </div>
          </button>
        ))}
      </div>
      <OwnerNav active="chat" />
    </div>
  );
}

// ═══════════════════════════════════════════════
//  NEW ADMIN SCREENS
// ═══════════════════════════════════════════════

function PropertyRejectionDetailScreen() {
  return (
    <div className="flex flex-col h-full" style={{ backgroundColor: C.bg }}>
      <StatusBar />
      <div className="px-5 pt-1 pb-3 flex items-center gap-3" dir="rtl">
        <button><ArrowLeft size={20} style={{ color: C.navy }} /></button>
        <h1 className="text-xl font-black flex-1" style={{ ...TJ, color: C.navy }}>سبب الرفض</h1>
      </div>
      <div className="flex-1 overflow-y-auto px-5 pb-4" dir="rtl">
        <div className="text-center py-4 mb-4">
          <div className="w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-3" style={{ backgroundColor: C.redLight }}>
            <AlertCircle size={28} style={{ color: C.red }} />
          </div>
          <Badge type="rejected" />
          <h2 className="text-lg font-black mt-2 mb-1" style={{ ...TJ, color: C.navy }}>تم رفض عقارك</h2>
          <p className="text-sm" style={{ ...TJ, color: C.gray }}>شقة مفروشة، مدينة نصر</p>
        </div>
        <Card className="mb-3">
          <p className="font-black text-sm mb-3" style={{ ...TJ, color: C.navy }}>أسباب الرفض</p>
          {[
            { r: "الصور غير واضحة أو لا تعبر عن العقار", icon: ImageIcon },
            { r: "المعلومات المدخلة غير مكتملة", icon: FileText },
          ].map(({ r, icon: Icon }, i) => (
            <div key={i} className="flex items-start gap-3 py-2.5" style={{ borderBottom: i === 0 ? `1px solid ${C.border}` : "none" }}>
              <div className="w-7 h-7 rounded-lg flex items-center justify-center flex-shrink-0" style={{ backgroundColor: C.redLight }}>
                <Icon size={13} style={{ color: C.red }} />
              </div>
              <p className="text-sm flex-1" style={{ ...TJ, color: C.navy }}>{r}</p>
            </div>
          ))}
        </Card>
        <Card className="mb-4">
          <p className="font-black text-sm mb-2" style={{ ...TJ, color: C.navy }}>ملاحظات المراجع</p>
          <p className="text-sm leading-6" style={{ ...TJ, color: C.gray }}>
            يرجى إعادة تصوير غرف النوم والمطبخ بإضاءة أوضح. تأكد أن كل الزوايا ظاهرة وبدون فلاتر. أضف أيضاً عدد الطوابق وسنة البناء.
          </p>
        </Card>
        <WarnBanner text="العقار لن يظهر في البحث حتى تُصحح البيانات وتُعيد الإرسال" />
        <div className="flex flex-col gap-3 mt-4">
          <PrimaryBtn text="تعديل وإعادة الإرسال" />
          <OutlineBtn text="تواصل مع الدعم" />
        </div>
      </div>
    </div>
  );
}

function OwnerVisitsDashboardScreen() {
  const upcoming = [
    { tenant: "سارة أحمد", prop: "شقة مدينة نصر", date: "النهارده 3:00 م", verified: true, phone: "010****432" },
    { tenant: "محمد علي", prop: "شقة مدينة نصر", date: "غداً 12:00 م", verified: true, phone: "012****567" },
    { tenant: "نورا كمال", prop: "ستوديو التجمع", date: "الخميس 5:00 م", verified: false, phone: null },
  ];
  const completed = [
    { tenant: "كريم سالم", prop: "شقة المهندسين", date: "الأثنين 2م", rated: true },
    { tenant: "منى طارق", prop: "شقة مدينة نصر", date: "الأحد 11ص", rated: false },
  ];
  return (
    <div className="flex flex-col h-full" style={{ backgroundColor: C.bg }}>
      <StatusBar />
      <div className="px-5 pt-1 pb-3" dir="rtl">
        <h1 className="text-xl font-black" style={{ ...TJ, color: C.navy }}>إدارة الزيارات</h1>
      </div>
      <div className="px-5 mb-3 flex gap-2" dir="rtl">
        {["القادمة (3)", "المكتملة", "المرفوضة"].map((t, i) => (
          <button key={i} className="px-3 py-1.5 rounded-full text-xs font-bold"
            style={{ backgroundColor: i === 0 ? C.teal : C.white, color: i === 0 ? C.white : C.navy, border: `1px solid ${i === 0 ? C.teal : C.border}`, ...TJ }}>{t}</button>
        ))}
      </div>
      <div className="flex-1 overflow-y-auto px-5 pb-4">
        <p className="text-xs font-black mb-2" style={{ ...TJ, color: C.gray }}>الزيارات القادمة</p>
        <div className="flex flex-col gap-3 mb-4">
          {upcoming.map((v, i) => (
            <Card key={i}>
              <div className="flex items-center gap-3 mb-3" dir="rtl">
                <div className="w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0" style={{ backgroundColor: C.tealLight }}>
                  <User size={18} style={{ color: C.teal }} />
                </div>
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <p className="font-black text-sm" style={{ ...TJ, color: C.navy }}>{v.tenant}</p>
                    {v.verified && <Badge type="verified" />}
                  </div>
                  <p className="text-xs" style={{ ...TJ, color: C.gray }}>{v.prop}</p>
                </div>
                <div className="text-right">
                  <span className="text-xs px-2 py-1 rounded-full font-bold" style={{ backgroundColor: C.greenLight, ...TJ, color: C.green }}>مقبول</span>
                </div>
              </div>
              <div className="flex items-center gap-2 mb-2 px-1" dir="rtl">
                <Calendar size={13} style={{ color: C.teal }} />
                <span className="text-xs font-bold" style={{ ...TJ, color: C.navy }}>{v.date}</span>
              </div>
              {v.phone ? (
                <div className="flex items-center gap-2 px-3 py-2 rounded-xl mb-3" style={{ backgroundColor: C.greenLight }}>
                  <Phone size={12} style={{ color: C.green }} />
                  <span className="text-xs font-bold" style={{ ...TJ, color: "#166534" }}>الرقم بعد القبول: {v.phone}</span>
                </div>
              ) : (
                <div className="mb-3">
                  <PrivacyBanner text="الرقم سيظهر بعد تأكيد التوثيق" />
                </div>
              )}
              <div className="flex gap-2">
                <button className="flex-1 py-2 rounded-xl text-xs font-black" style={{ backgroundColor: C.blueLight, color: C.blue, ...TJ }}>شات</button>
                <button className="flex-1 py-2 rounded-xl text-xs font-black" style={{ backgroundColor: C.redLight, color: C.red, ...TJ }}>إلغاء الزيارة</button>
              </div>
            </Card>
          ))}
        </div>
        <p className="text-xs font-black mb-2" style={{ ...TJ, color: C.gray }}>الزيارات المكتملة</p>
        <div className="flex flex-col gap-3">
          {completed.map((v, i) => (
            <Card key={i}>
              <div className="flex items-center justify-between" dir="rtl">
                <div className="flex items-center gap-3">
                  <div className="w-9 h-9 rounded-full flex items-center justify-center" style={{ backgroundColor: "#E5E7EB" }}>
                    <User size={16} style={{ color: C.gray }} />
                  </div>
                  <div>
                    <p className="font-bold text-sm" style={{ ...TJ, color: C.navy }}>{v.tenant}</p>
                    <p className="text-xs" style={{ ...TJ, color: C.gray }}>{v.prop} · {v.date}</p>
                  </div>
                </div>
                {v.rated ? (
                  <div className="flex gap-0.5">{[1,2,3,4,5].map(s => <Star key={s} size={12} fill={s <= 4 ? C.amber : "none"} style={{ color: s <= 4 ? C.amber : "#D1D5DB" }} />)}</div>
                ) : (
                  <button className="text-xs font-bold px-2 py-1 rounded-lg" style={{ backgroundColor: C.goldLight, color: C.gold, ...TJ }}>طلب تقييم</button>
                )}
              </div>
            </Card>
          ))}
        </div>
      </div>
      <OwnerNav active="requests" />
    </div>
  );
}

// ═══════════════════════════════════════════════
//  NEW ADMIN CONSOLE SCREENS  (from PDF other_screens-2)
// ═══════════════════════════════════════════════



function OwnerDashboardScreen() {
  return (
    <div className="flex flex-col h-full" style={{ backgroundColor: C.bg }}>
      <StatusBar />
      <div className="flex-1 overflow-y-auto px-5 py-3" dir="rtl">
        <div className="flex items-center justify-between mb-4">
          <button className="relative w-9 h-9 rounded-full flex items-center justify-center" style={{ backgroundColor: C.white, border: `1px solid ${C.border}` }}>
            <Bell size={16} style={{ color: C.navy }} />
            <div className="absolute top-0.5 right-0.5 w-2 h-2 rounded-full" style={{ backgroundColor: C.red }} />
          </button>
          <div className="text-right">
            <p className="font-black text-lg" style={{ ...TJ, color: C.navy }}>أهلاً أحمد 👋</p>
            <div className="flex items-center gap-1"><Badge type="verified" /></div>
          </div>
          <div className="w-9 h-9 rounded-full flex items-center justify-center" style={{ backgroundColor: C.goldLight }}>
            <User size={16} style={{ color: C.gold }} />
          </div>
        </div>
        <div className="grid grid-cols-2 gap-3 mb-4">
          {[{ l: "عقارات نشطة", n: "3", I: Building2, c: C.teal, bg: C.tealLight }, { l: "زيارات هذا الأسبوع", n: "7", I: Calendar, c: C.blue, bg: C.blueLight }, { l: "طلبات معلقة", n: "2", I: Clock, c: C.amber, bg: C.amberLight }, { l: "التقييم العام", n: "4.9★", I: Star, c: C.gold, bg: C.goldLight }].map(({ l, n, I, c, bg }, i) => (
            <div key={i} className="p-4 rounded-2xl" style={{ backgroundColor: C.white, border: `1px solid ${C.border}` }}>
              <div className="w-8 h-8 rounded-xl flex items-center justify-center mb-2" style={{ backgroundColor: bg }}>
                <I size={15} style={{ color: c }} />
              </div>
              <p className="text-xl font-black" style={{ ...TJ, color: C.navy }}>{n}</p>
              <p className="text-xs" style={{ ...TJ, color: C.gray }}>{l}</p>
            </div>
          ))}
        </div>
        <p className="font-black text-sm mb-2" style={{ ...TJ, color: C.navy }}>طلبات انتظار الرد</p>
        <div className="flex flex-col gap-3 mb-4">
          {[{ t: "سارة أحمد", p: "شقة مدينة نصر", d: "النهارده 3م" }, { t: "محمد علي", p: "شقة مدينة نصر", d: "غداً 12م" }].map((r, i) => (
            <Card key={i}>
              <div className="flex items-center gap-3" dir="rtl">
                <div className="w-9 h-9 rounded-full flex items-center justify-center flex-shrink-0" style={{ backgroundColor: C.blueLight }}>
                  <User size={16} style={{ color: C.blue }} />
                </div>
                <div className="flex-1">
                  <p className="font-black text-sm" style={{ ...TJ, color: C.navy }}>{r.t}</p>
                  <p className="text-xs" style={{ ...TJ, color: C.gray }}>{r.p} · {r.d}</p>
                </div>
                <div className="flex gap-1">
                  <button className="px-2 py-1 rounded-lg text-xs font-black text-white" style={{ backgroundColor: C.green, ...TJ }}>قبول</button>
                  <button className="px-2 py-1 rounded-lg text-xs font-black" style={{ backgroundColor: C.redLight, color: C.red, ...TJ }}>رفض</button>
                </div>
              </div>
            </Card>
          ))}
        </div>
      </div>
      <OwnerNav active="home" />
    </div>
  );
}

function OwnerMyListingsScreen() {
  return (
    <div className="flex flex-col h-full" style={{ backgroundColor: C.bg }}>
      <StatusBar />
      <div className="flex items-center justify-between px-5 pt-2 pb-3" dir="rtl">
        <button className="flex items-center gap-1.5 px-3 py-2 rounded-xl text-sm font-black" style={{ backgroundColor: C.teal, color: C.white, ...TJ }}>
          <Plus size={14} />إضافة عقار
        </button>
        <h1 className="text-xl font-black" style={{ ...TJ, color: C.navy }}>عقاراتي</h1>
      </div>
      <div className="flex-1 overflow-y-auto px-5 pb-4 flex flex-col gap-3">
        {[
          { t: "شقة مفروشة — مدينة نصر", p: "6,500", status: "verified" as const, views: 142, visits: 3 },
          { t: "ستوديو — التجمع الخامس", p: "4,200", status: "pending" as const, views: 67, visits: 0 },
          { t: "شقة 3 غرف — المهندسين", p: "8,800", status: "hidden" as const, views: 0, visits: 0 },
        ].map((p, i) => (
          <Card key={i}>
            <div className="flex gap-3" dir="rtl">
              <div className="w-20 h-20 rounded-2xl flex-shrink-0 flex items-center justify-center" style={{ backgroundColor: "#E2E8F0" }}>
                <Building2 size={22} style={{ color: "#94A3B8" }} />
              </div>
              <div className="flex-1">
                <p className="font-black text-sm mb-1" style={{ ...TJ, color: C.navy }}>{p.t}</p>
                <Badge type={p.status} />
                <p className="font-black text-base mt-1" style={{ ...TJ, color: C.teal }}>{p.p} ج/شهر</p>
                <div className="flex items-center gap-3 text-xs mt-1" style={{ color: C.gray }}>
                  <span style={TJ}>{p.views} مشاهدة</span>
                  <span>·</span>
                  <span style={TJ}>{p.visits} زيارة</span>
                </div>
              </div>
            </div>
            <div className="flex gap-2 mt-3">
              <button className="flex-1 py-2 rounded-xl text-xs font-black" style={{ backgroundColor: C.blueLight, color: C.blue, ...TJ }}>تعديل</button>
              <button className="flex-1 py-2 rounded-xl text-xs font-black" style={{ backgroundColor: C.tealLight, color: C.teal, ...TJ }}>إحصاءات</button>
              <button className="flex-1 py-2 rounded-xl text-xs font-black" style={{ backgroundColor: C.redLight, color: C.red, ...TJ }}>حذف</button>
            </div>
          </Card>
        ))}
      </div>
      <OwnerNav active="properties" />
    </div>
  );
}

function AddPropertyStep1Screen() {
  return (
    <div className="flex flex-col h-full" style={{ backgroundColor: C.bg }}>
      <StatusBar />
      <div className="flex items-center gap-3 px-5 pt-2 pb-3" dir="rtl">
        <button><ArrowLeft size={20} style={{ color: C.navy }} /></button>
        <h1 className="text-xl font-black flex-1" style={{ ...TJ, color: C.navy }}>إضافة عقار جديد</h1>
      </div>
      <div className="flex-1 overflow-y-auto px-5 pb-4" dir="rtl">
        <StepProgress total={4} current={1} />
        <p className="font-black text-sm mb-3" style={{ ...TJ, color: C.navy }}>نوع العقار</p>
        <div className="grid grid-cols-3 gap-3 mb-5">
          {[{ I: Building2, t: "شقة" }, { I: Home, t: "ستوديو" }, { I: Users, t: "غرفة" }, { I: Building2, t: "دوبلكس" }, { I: Home, t: "فيلا" }, { I: Building2, t: "روف" }].map(({ I, t }, i) => (
            <button key={i} className="flex flex-col items-center gap-2 py-4 rounded-2xl"
              style={{ backgroundColor: i===0 ? C.teal : C.white, border: `2px solid ${i===0 ? C.teal : C.border}` }}>
              <I size={22} style={{ color: i===0 ? C.white : C.gray }} />
              <span className="text-sm font-bold" style={{ ...TJ, color: i===0 ? C.white : C.navy }}>{t}</span>
            </button>
          ))}
        </div>
        <p className="font-black text-sm mb-3" style={{ ...TJ, color: C.navy }}>المنطقة والعنوان</p>
        <div className="flex flex-col gap-3 mb-5">
          <TextInput label="المحافظة" placeholder="القاهرة" />
          <TextInput label="المنطقة" placeholder="مدينة نصر" />
          <TextInput label="الشارع" placeholder="شارع النصر" />
        </div>
        <p className="font-black text-sm mb-3" style={{ ...TJ, color: C.navy }}>تفاصيل العقار</p>
        <div className="grid grid-cols-2 gap-3 mb-5">
          <TextInput label="عدد الغرف" placeholder="3" />
          <TextInput label="المساحة" placeholder="90م²" />
          <TextInput label="الدور" placeholder="3" />
          <TextInput label="سنة البناء" placeholder="2020" />
        </div>
        <PrimaryBtn text="التالي — الصور" />
      </div>
    </div>
  );
}

function AddPropertyStep2PhotosScreen() {
  return (
    <div className="flex flex-col h-full" style={{ backgroundColor: C.bg }}>
      <StatusBar />
      <div className="flex items-center gap-3 px-5 pt-2 pb-3" dir="rtl">
        <button><ArrowLeft size={20} style={{ color: C.navy }} /></button>
        <h1 className="text-xl font-black flex-1" style={{ ...TJ, color: C.navy }}>صور العقار</h1>
      </div>
      <div className="flex-1 overflow-y-auto px-5 pb-4" dir="rtl">
        <StepProgress total={4} current={2} />
        <WarnBanner text="10 صور على الأقل — تأكد إن الصور واضحة وبدون أرقام هواتف" />
        <div className="mt-4 mb-4">
          <div className="grid grid-cols-3 gap-2">
            {[1,2,3,4,5,6].map(i => (
              <div key={i} className="aspect-square rounded-2xl flex items-center justify-center overflow-hidden"
                style={{ backgroundColor: i<=4 ? "#E2E8F0" : C.bg, border: `1.5px dashed ${i<=4 ? "transparent" : C.border}` }}>
                {i<=4 ? (
                  <div className="relative w-full h-full flex items-center justify-center" style={{ backgroundColor: "#CBD5E1" }}>
                    <Building2 size={20} style={{ color: "#94A3B8" }} />
                    <button className="absolute top-1 left-1 w-5 h-5 rounded-full flex items-center justify-center" style={{ backgroundColor: C.red }}>
                      <X size={10} style={{ color: C.white }} />
                    </button>
                  </div>
                ) : (
                  <div className="flex flex-col items-center gap-1">
                    <Plus size={20} style={{ color: "#9CA3AF" }} />
                    <span style={{ fontSize: 9, color: "#9CA3AF", ...TJ }}>إضافة</span>
                  </div>
                )}
              </div>
            ))}
          </div>
          <p className="text-xs mt-2 text-center" style={{ ...TJ, color: C.gray }}>4 / 10 صور مرفوعة (الحد الأدنى 10)</p>
        </div>
        <Card className="mb-4">
          <p className="font-black text-sm mb-2" style={{ ...TJ, color: C.navy }}>نصائح للصور</p>
          {["صوّر كل الغرف: صالة، غرف نوم، مطبخ، حمام", "استخدم إضاءة طبيعية", "تأكد من خلو الصور من أي أرقام هواتف أو معلومات شخصية", "الحد الأدنى 10 صور، الأفضل 15-20"].map((t, i) => (
            <div key={i} className="flex items-start gap-2 py-1.5" style={{ borderBottom: i<3 ? `1px solid ${C.border}` : "none" }}>
              <Check size={12} style={{ color: C.teal, marginTop: 2 }} />
              <span className="text-xs flex-1" style={{ ...TJ, color: C.gray }}>{t}</span>
            </div>
          ))}
        </Card>
        <PrimaryBtn text="التالي — التسعير" />
      </div>
    </div>
  );
}

function AddPropertyStep3PricingScreen() {
  return (
    <div className="flex flex-col h-full" style={{ backgroundColor: C.bg }}>
      <StatusBar />
      <div className="flex items-center gap-3 px-5 pt-2 pb-3" dir="rtl">
        <button><ArrowLeft size={20} style={{ color: C.navy }} /></button>
        <h1 className="text-xl font-black flex-1" style={{ ...TJ, color: C.navy }}>التسعير والتفاصيل</h1>
      </div>
      <div className="flex-1 overflow-y-auto px-5 pb-4" dir="rtl">
        <StepProgress total={4} current={3} />
        <div className="flex flex-col gap-3 mb-5">
          <TextInput label="الإيجار الشهري (جنيه)" placeholder="6,500" />
          <TextInput label="تأمين الشقة" placeholder="شهر واحد" />
          <div>
            <p className="font-black text-sm mb-2" style={{ ...TJ, color: C.navy }}>فترة التأجير</p>
            <div className="flex gap-2">
              {["شهر", "3 شهور", "6 شهور", "سنة"].map((t, i) => (
                <button key={i} className="flex-1 py-2 rounded-xl text-xs font-bold"
                  style={{ backgroundColor: i===2 ? C.teal : C.bg, color: i===2 ? C.white : C.navy, border: `1px solid ${i===2 ? C.teal : C.border}`, ...TJ }}>{t}</button>
              ))}
            </div>
          </div>
        </div>
        <p className="font-black text-sm mb-3" style={{ ...TJ, color: C.navy }}>المرافق المتضمنة</p>
        <div className="flex flex-wrap gap-2 mb-5">
          {["مفروش","واي فاي","مكيف","غسالة","ثلاجة","بوتوجاز","جراج","أسانسير","حارس"].map((f, i) => (
            <button key={i} className="px-3 py-1.5 rounded-full text-xs font-bold"
              style={{ backgroundColor: i<5 ? C.teal : C.bg, color: i<5 ? C.white : C.gray, border: `1px solid ${i<5 ? C.teal : C.border}`, ...TJ }}>{f}</button>
          ))}
        </div>
        <div className="mb-4">
          <p className="font-black text-sm mb-2" style={{ ...TJ, color: C.navy }}>وصف العقار</p>
          <textarea dir="rtl" readOnly placeholder="اكتب وصفاً جذاباً للعقار…" className="w-full px-4 py-3 rounded-2xl border text-sm outline-none resize-none"
            style={{ borderColor: C.border, ...TJ, color: C.navy, height: 80 }} />
        </div>
        <PrimaryBtn text="التالي — مراجعة وإرسال" />
      </div>
    </div>
  );
}

function PropertySubmittedScreen() {
  return (
    <div className="flex flex-col h-full items-center justify-center px-8" style={{ backgroundColor: C.bg }}>
      <div className="w-24 h-24 rounded-full flex items-center justify-center mb-5" style={{ backgroundColor: C.amberLight }}>
        <Clock size={44} style={{ color: C.amber }} />
      </div>
      <Badge type="pending" />
      <h1 className="text-2xl font-black text-center mt-3 mb-2" style={{ ...TJ, color: C.navy }}>تم إرسال العقار للمراجعة</h1>
      <p className="text-sm text-center mb-6" style={{ ...TJ, color: C.gray }}>فريقنا هيراجع عقارك خلال 24-48 ساعة وهتلاقي النتيجة في الإشعارات.</p>
      <Card className="w-full mb-6" dir="rtl">
        {[{ l: "نوع العقار", v: "شقة مفروشة" }, { l: "المنطقة", v: "مدينة نصر، القاهرة" }, { l: "السعر", v: "6,500 ج/شهر" }, { l: "الصور", v: "12 صورة" }, { l: "وقت الإرسال", v: "النهارده 10:30 ص" }].map(({ l, v }, i) => (
          <div key={i} className="flex justify-between py-2" style={{ borderBottom: i<4 ? `1px solid ${C.border}` : "none" }}>
            <span className="text-sm font-bold" style={{ ...TJ, color: C.navy }}>{v}</span>
            <span className="text-xs" style={{ ...TJ, color: C.gray }}>{l}</span>
          </div>
        ))}
      </Card>
      <div className="w-full flex flex-col gap-3">
        <PrimaryBtn text="عرض عقاراتي" />
        <OutlineBtn text="إضافة عقار آخر" />
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════
//  OWNER MISSING SCREENS — REQUESTS & CHAT
// ═══════════════════════════════════════════════

function OwnerRequestsListScreen() {
  const requests = [
    { name: "سارة أحمد", prop: "شقة مدينة نصر", date: "النهارده 3م", verified: true, status: "new" },
    { name: "محمد علي", prop: "شقة مدينة نصر", date: "غداً 12م", verified: true, status: "new" },
    { name: "نورا كمال", prop: "ستوديو التجمع", date: "الخميس 5م", verified: false, status: "pending" },
    { name: "كريم سالم", prop: "شقة المهندسين", date: "الجمعة 4م", verified: true, status: "accepted" },
  ];
  return (
    <div className="flex flex-col h-full" style={{ backgroundColor: C.bg }}>
      <StatusBar />
      <div className="px-5 pt-1 pb-3" dir="rtl">
        <h1 className="text-xl font-black" style={{ ...TJ, color: C.navy }}>طلبات الزيارة</h1>
      </div>
      <div className="px-5 mb-3 flex gap-2" dir="rtl">
        {["الجديدة (2)","قيد الانتظار","المقبولة","المرفوضة"].map((t, i) => (
          <button key={i} className="px-3 py-1.5 rounded-full text-xs font-bold flex-shrink-0"
            style={{ backgroundColor: i===0 ? C.teal : C.white, color: i===0 ? C.white : C.navy, border: `1px solid ${i===0 ? C.teal : C.border}`, ...TJ }}>{t}</button>
        ))}
      </div>
      <div className="flex-1 overflow-y-auto px-5 pb-4 flex flex-col gap-3">
        {requests.map((r, i) => (
          <Card key={i}>
            <div className="flex items-center gap-3 mb-3" dir="rtl">
              <div className="w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0" style={{ backgroundColor: C.blueLight }}>
                <User size={18} style={{ color: C.blue }} />
              </div>
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <p className="font-black text-sm" style={{ ...TJ, color: C.navy }}>{r.name}</p>
                  {r.verified && <Badge type="verified" />}
                </div>
                <p className="text-xs" style={{ ...TJ, color: C.gray }}>{r.prop} · {r.date}</p>
              </div>
              <span className="text-xs font-black px-2 py-1 rounded-full"
                style={{ backgroundColor: r.status==="new" ? C.tealLight : r.status==="accepted" ? C.greenLight : C.amberLight, color: r.status==="new" ? C.teal : r.status==="accepted" ? C.green : C.amber, ...TJ }}>
                {r.status==="new" ? "جديد" : r.status==="accepted" ? "مقبول" : "انتظار"}
              </span>
            </div>
            {!r.verified && <PrivacyBanner text="هذا المستأجر لم يوثق هويته بعد" />}
            {r.status === "new" && (
              <div className="flex gap-2 mt-2">
                <button className="flex-1 py-2 rounded-xl text-xs font-black text-white" style={{ backgroundColor: C.green, ...TJ }}>قبول</button>
                <button className="flex-1 py-2 rounded-xl text-xs font-black" style={{ backgroundColor: C.redLight, color: C.red, ...TJ }}>رفض</button>
                <button className="flex-1 py-2 rounded-xl text-xs font-black" style={{ backgroundColor: C.blueLight, color: C.blue, ...TJ }}>شات</button>
              </div>
            )}
          </Card>
        ))}
      </div>
      <OwnerNav active="requests" />
    </div>
  );
}

function OwnerRequestDetailScreen() {
  return (
    <div className="flex flex-col h-full" style={{ backgroundColor: C.bg }}>
      <StatusBar />
      <div className="flex items-center gap-3 px-5 pt-2 pb-3" dir="rtl">
        <button><ArrowLeft size={20} style={{ color: C.navy }} /></button>
        <h1 className="text-xl font-black flex-1" style={{ ...TJ, color: C.navy }}>تفاصيل الطلب</h1>
      </div>
      <div className="flex-1 overflow-y-auto px-5 pb-4" dir="rtl">
        <Card className="mb-3">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-14 h-14 rounded-full flex items-center justify-center flex-shrink-0" style={{ backgroundColor: C.blueLight }}>
              <User size={26} style={{ color: C.blue }} />
            </div>
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-0.5">
                <p className="font-black text-base" style={{ ...TJ, color: C.navy }}>سارة أحمد خالد</p>
                <Badge type="verified" />
              </div>
              <p className="text-xs" style={{ ...TJ, color: C.gray }}>مستأجر موثّق · عضو منذ 2024</p>
            </div>
          </div>
          {[{ l: "العقار المطلوب", v: "شقة مفروشة — مدينة نصر" }, { l: "تاريخ الزيارة", v: "السبت 15 يونيو 2025" }, { l: "الوقت", v: "3:00 م" }].map(({ l, v }, i) => (
            <div key={i} className="flex justify-between py-2" style={{ borderBottom: i<2 ? `1px solid ${C.border}` : "none" }}>
              <span className="text-sm font-bold" style={{ ...TJ, color: C.navy }}>{v}</span>
              <span className="text-xs" style={{ ...TJ, color: C.gray }}>{l}</span>
            </div>
          ))}
        </Card>
        <Card className="mb-3">
          <p className="font-black text-sm mb-2" style={{ ...TJ, color: C.navy }}>ملاحظة المستأجر</p>
          <p className="text-sm leading-6" style={{ ...TJ, color: C.gray }}>مهتمة بالشقة ومحتاجة تاكدي من المساحة وحالة التشطيب.</p>
        </Card>
        <PrivacyBanner text="رقم المستأجر 010****432 — يظهر بعد القبول فقط" />
        <div className="flex flex-col gap-3 mt-4">
          <button className="w-full py-4 rounded-2xl font-black text-white" style={{ backgroundColor: C.green, ...TJ }}>قبول الزيارة ✓</button>
          <OutlineBtn text="رفض الطلب" />
          <button className="w-full py-3.5 rounded-2xl font-black" style={{ backgroundColor: C.blueLight, color: C.blue, ...TJ }}>فتح المحادثة</button>
        </div>
      </div>
    </div>
  );
}

function OwnerChatThreadScreen() {
  const msgs = [
    { me: false, t: "أهلاً! مهتمة بالشقة، ممكن أعرف تفاصيل أكتر؟", time: "9:00 ص" },
    { me: true, t: "أهلاً بيكي! الشقة مفروشة بالكامل وفيها مكيفات ومطبخ مجهز.", time: "9:05 ص" },
    { me: false, t: "تمام جداً، ممكن نحدد موعد زيارة يوم السبت؟", time: "9:08 ص" },
    { me: true, t: "بالتأكيد، انتظري تأكيد الزيارة من التطبيق", time: "9:10 ص" },
  ];
  return (
    <div className="flex flex-col h-full" style={{ backgroundColor: C.bg }}>
      <StatusBar />
      <div className="flex items-center gap-3 px-5 pt-2 pb-3" style={{ backgroundColor: C.white, borderBottom: `1px solid ${C.border}` }} dir="rtl">
        <button><ArrowLeft size={18} style={{ color: C.navy }} /></button>
        <div className="w-9 h-9 rounded-full flex items-center justify-center" style={{ backgroundColor: C.blueLight }}>
          <User size={16} style={{ color: C.blue }} />
        </div>
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <p className="font-black text-sm" style={{ ...TJ, color: C.navy }}>سارة أحمد</p>
            <Badge type="verified" />
          </div>
          <p className="text-xs" style={{ ...TJ, color: C.gray }}>شقة مدينة نصر</p>
        </div>
      </div>
      <div className="flex-1 overflow-y-auto px-4 py-3 flex flex-col gap-2">
        {msgs.map((m, i) => (
          <div key={i} className={`flex ${m.me ? "justify-start" : "justify-end"}`}>
            <div className="max-w-xs px-4 py-2.5 text-sm" style={{ ...TJ, backgroundColor: m.me ? "#F1F5F9" : C.teal, color: m.me ? C.navy : C.white, borderRadius: m.me ? "4px 16px 16px 16px" : "16px 4px 16px 16px" }}>{m.t}</div>
          </div>
        ))}
        <PrivacyBanner text="رقم الموبايل مخفي في المحادثة دائماً" />
      </div>
      <div className="px-4 py-3 flex items-center gap-2" style={{ backgroundColor: C.white, borderTop: `1px solid ${C.border}` }}>
        <button className="w-9 h-9 rounded-full flex items-center justify-center flex-shrink-0" style={{ backgroundColor: C.bg }}>
          <ImageIcon size={14} style={{ color: C.gray }} />
        </button>
        <div className="flex-1 px-3 py-2.5 rounded-2xl" style={{ backgroundColor: C.bg, border: `1px solid ${C.border}` }}>
          <span className="text-sm" style={{ ...TJ, color: "#9CA3AF" }}>اكتب رسالة…</span>
        </div>
        <button className="w-9 h-9 rounded-full flex items-center justify-center flex-shrink-0" style={{ backgroundColor: C.teal }}>
          <Send size={14} style={{ color: C.white }} />
        </button>
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════
//  OWNER MISSING SCREENS — ANALYTICS, FINANCE, KYC, EDIT
// ═══════════════════════════════════════════════

function OwnerPropertyAnalyticsScreen() {
  return (
    <div className="flex flex-col h-full" style={{ backgroundColor: C.bg }}>
      <StatusBar />
      <div className="flex items-center gap-3 px-5 pt-2 pb-3" dir="rtl">
        <button><ArrowLeft size={20} style={{ color: C.navy }} /></button>
        <h1 className="text-xl font-black flex-1" style={{ ...TJ, color: C.navy }}>إحصاءات العقار</h1>
        <button className="text-xs font-bold px-2 py-1 rounded-xl" style={{ backgroundColor: C.bg, ...TJ, color: C.gray }}>30 يوم</button>
      </div>
      <div className="flex-1 overflow-y-auto px-5 pb-4" dir="rtl">
        <div className="grid grid-cols-2 gap-3 mb-4">
          {[{ l: "مشاهدات", n: "1,247", I: Eye, c: C.blue, bg: C.blueLight }, { l: "طلبات زيارة", n: "23", I: Calendar, c: C.teal, bg: C.tealLight }, { l: "محفوظات", n: "84", I: Heart, c: C.red, bg: C.redLight }, { l: "معدل القبول", n: "78%", I: CheckCircle, c: C.green, bg: C.greenLight }].map(({ l, n, I, c, bg }, i) => (
            <div key={i} className="p-4 rounded-2xl" style={{ backgroundColor: C.white, border: `1px solid ${C.border}` }}>
              <div className="w-8 h-8 rounded-xl flex items-center justify-center mb-2" style={{ backgroundColor: bg }}>
                <I size={15} style={{ color: c }} />
              </div>
              <p className="text-xl font-black" style={{ ...TJ, color: C.navy }}>{n}</p>
              <p className="text-xs" style={{ ...TJ, color: C.gray }}>{l}</p>
            </div>
          ))}
        </div>
        <Card className="mb-3">
          <p className="font-black text-sm mb-3" style={{ ...TJ, color: C.navy }}>مشاهدات آخر 14 يوم</p>
          <div className="flex items-end gap-1 justify-between" style={{ height: 60 }}>
            {[40,65,50,80,60,90,70,85,55,95,75,88,65,100].map((h, i) => (
              <div key={i} className="flex-1 rounded-t-sm" style={{ height: `${h}%`, backgroundColor: i===13 ? C.teal : `${C.teal}30` }} />
            ))}
          </div>
        </Card>
        <Card>
          <p className="font-black text-sm mb-3" style={{ ...TJ, color: C.navy }}>أكثر ما يبحث عنه الزوار</p>
          {[{ l: "المساحة", p: 78 }, { l: "السعر", p: 65 }, { l: "الموقع", p: 55 }, { l: "المرافق", p: 42 }].map(({ l, p }, i) => (
            <div key={i} className="mb-2.5">
              <div className="flex justify-between text-xs mb-1">
                <span className="font-bold" style={{ color: C.navy, ...TJ }}>{p}%</span>
                <span style={{ color: C.gray, ...TJ }}>{l}</span>
              </div>
              <div className="h-1.5 rounded-full" style={{ backgroundColor: "#E5E7EB" }}>
                <div className="h-full rounded-full" style={{ width: `${p}%`, backgroundColor: C.teal }} />
              </div>
            </div>
          ))}
        </Card>
      </div>
    </div>
  );
}

function OwnerRevenueScreen() {
  return (
    <div className="flex flex-col h-full" style={{ backgroundColor: C.bg }}>
      <StatusBar />
      <div className="flex items-center gap-3 px-5 pt-2 pb-3" dir="rtl">
        <button><ArrowLeft size={20} style={{ color: C.navy }} /></button>
        <h1 className="text-xl font-black flex-1" style={{ ...TJ, color: C.navy }}>الإيرادات</h1>
      </div>
      <div className="flex-1 overflow-y-auto px-5 pb-4" dir="rtl">
        <Card className="mb-4">
          <div className="text-center py-2">
            <p className="text-xs mb-1" style={{ ...TJ, color: C.gray }}>إجمالي هذا الشهر</p>
            <p className="text-3xl font-black" style={{ ...TJ, color: C.teal }}>21,500 ج</p>
            <div className="flex items-center gap-1 justify-center mt-1">
              <TrendingUp size={12} style={{ color: C.green }} />
              <span className="text-xs font-bold" style={{ ...TJ, color: C.green }}>+8% عن الشهر السابق</span>
            </div>
          </div>
        </Card>
        <div className="grid grid-cols-2 gap-3 mb-4">
          {[{ l: "شقة مدينة نصر", n: "6,500 ج", status: "مدفوع", c: C.green }, { l: "ستوديو التجمع", n: "4,200 ج", status: "قادم 15 يونيو", c: C.amber }, { l: "شقة المهندسين", n: "8,800 ج", status: "مدفوع", c: C.green }, { l: "غرفة الزمالك", n: "2,000 ج", status: "متأخر", c: C.red }].map(({ l, n, status, c }, i) => (
            <div key={i} className="p-3 rounded-2xl" style={{ backgroundColor: C.white, border: `1px solid ${C.border}` }}>
              <p className="text-xs mb-1" style={{ ...TJ, color: C.gray }}>{l}</p>
              <p className="font-black text-base" style={{ ...TJ, color: C.navy }}>{n}</p>
              <span className="text-xs font-bold" style={{ ...TJ, color: c }}>{status}</span>
            </div>
          ))}
        </div>
        <Card>
          <p className="font-black text-sm mb-3" style={{ ...TJ, color: C.navy }}>آخر المعاملات</p>
          {[{ d: "1 يونيو", desc: "إيجار شهري — شقة نصر", amt: "+6,500", c: C.green }, { d: "1 يونيو", desc: "إيجار — شقة المهندسين", amt: "+8,800", c: C.green }, { d: "28 مايو", desc: "رسوم المنصة", amt: "-350", c: C.red }].map((t, i) => (
            <div key={i} className="flex justify-between items-center py-2.5" style={{ borderBottom: i<2 ? `1px solid ${C.border}` : "none" }}>
              <span className="font-black text-sm" style={{ ...TJ, color: t.c }}>{t.amt} ج</span>
              <div className="text-right">
                <p className="text-xs font-bold" style={{ ...TJ, color: C.navy }}>{t.desc}</p>
                <p style={{ fontSize: 10, ...TJ, color: C.gray }}>{t.d}</p>
              </div>
            </div>
          ))}
        </Card>
      </div>
      <OwnerNav active="more" />
    </div>
  );
}

function OwnerKYCScreen() {
  return (
    <div className="flex flex-col h-full" style={{ backgroundColor: C.bg }}>
      <StatusBar />
      <div className="flex items-center gap-3 px-5 pt-2 pb-3" dir="rtl">
        <button><ArrowLeft size={20} style={{ color: C.navy }} /></button>
        <h1 className="text-xl font-black flex-1" style={{ ...TJ, color: C.navy }}>توثيق هوية المالك</h1>
      </div>
      <div className="flex-1 overflow-y-auto px-5 pb-4" dir="rtl">
        <StepProgress total={3} current={1} />
        <div className="text-center py-4 mb-4">
          <div className="w-20 h-20 rounded-3xl flex items-center justify-center mx-auto mb-3" style={{ backgroundColor: C.goldLight }}>
            <Building2 size={36} style={{ color: C.gold }} />
          </div>
          <h2 className="text-xl font-black mb-2" style={{ ...TJ, color: C.navy }}>وثّق هويتك كمالك</h2>
          <p className="text-sm leading-6" style={{ ...TJ, color: C.gray }}>التوثيق إلزامي لعرض عقاراتك والتواصل مع المستأجرين</p>
        </div>
        <div className="flex flex-col gap-3 mb-5">
          {["بطاقة الرقم القومي (وجه وظهر)", "مستند ملكية العقار أو عقد إيجار", "صورة سيلفي واضحة"].map((doc, i) => (
            <div key={i} className="flex items-center gap-3 px-4 py-3 rounded-2xl" style={{ backgroundColor: C.white, border: `1px solid ${C.border}` }}>
              <div className="w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0" style={{ backgroundColor: i===0 ? C.tealLight : C.bg }}>
                <FileText size={16} style={{ color: i===0 ? C.teal : "#9CA3AF" }} />
              </div>
              <div className="flex-1">
                <p className="font-bold text-sm" style={{ ...TJ, color: C.navy }}>{doc}</p>
              </div>
              {i===0 && <CheckCircle size={16} style={{ color: C.green }} />}
            </div>
          ))}
        </div>
        <PrivacyBanner text="مستنداتك مشفّرة ولن تُشارك مع المستأجرين" />
        <div className="mt-4">
          <PrimaryBtn text="رفع المستندات" />
        </div>
      </div>
    </div>
  );
}

function OwnerSupportScreen() {
  return (
    <div className="flex flex-col h-full" style={{ backgroundColor: C.bg }}>
      <StatusBar />
      <div className="flex items-center gap-3 px-5 pt-2 pb-3" dir="rtl">
        <button><ArrowLeft size={20} style={{ color: C.navy }} /></button>
        <h1 className="text-xl font-black flex-1" style={{ ...TJ, color: C.navy }}>دعم الملاك</h1>
      </div>
      <div className="flex-1 overflow-y-auto px-5 pb-4" dir="rtl">
        <div className="py-4 mb-4 text-center">
          <div className="w-16 h-16 rounded-2xl flex items-center justify-center mx-auto mb-2" style={{ backgroundColor: C.goldLight }}>
            <Building2 size={28} style={{ color: C.gold }} />
          </div>
          <p className="text-sm" style={{ ...TJ, color: C.gray }}>فريق دعم متخصص للملاك</p>
        </div>
        <div className="grid grid-cols-2 gap-3 mb-5">
          {[{ I: MessageCircle, t: "شات مباشر", sub: "أولوية للملاك", c: C.gold, bg: C.goldLight }, { I: Phone, t: "اتصال مباشر", sub: "16xxx (ملاك)", c: C.teal, bg: C.tealLight }].map(({ I, t, sub, c, bg }, i) => (
            <button key={i} className="flex flex-col items-center gap-2 py-4 rounded-2xl" style={{ backgroundColor: bg }}>
              <I size={22} style={{ color: c }} />
              <p className="font-black text-sm" style={{ ...TJ, color: C.navy }}>{t}</p>
              <p style={{ fontSize: 10, ...TJ, color: C.gray }}>{sub}</p>
            </button>
          ))}
        </div>
        <p className="font-black text-sm mb-3" style={{ ...TJ, color: C.navy }}>أسئلة شائعة للملاك</p>
        {["إزاي أضيف عقار جديد؟", "إيه متطلبات الصور؟", "إزاي أرد على طلبات الزيارة؟", "ليه عقاري اترفض؟", "إزاي أشوف إحصاءات عقاري؟"].map((q, i, arr) => (
          <div key={i} className="flex items-center justify-between px-4 py-3 rounded-2xl mb-2 text-right" style={{ backgroundColor: C.white, border: `1px solid ${C.border}` }}>
            <ChevronLeft size={14} style={{ color: C.gray }} />
            <span className="font-bold text-sm flex-1" style={{ ...TJ, color: C.navy }}>{q}</span>
          </div>
        ))}
      </div>
      <OwnerNav active="more" />
    </div>
  );
}

function OwnerOnboardingScreen() {
  return (
    <div className="flex flex-col h-full items-center justify-center px-8" style={{ backgroundColor: C.bg }}>
      <div className="w-28 h-28 rounded-3xl flex items-center justify-center mb-6" style={{ backgroundColor: C.goldLight }}>
        <Building2 size={52} style={{ color: C.gold }} />
      </div>
      <h1 className="text-2xl font-black text-center mb-2" style={{ ...TJ, color: C.navy }}>ابدأ تأجير عقاراتك</h1>
      <p className="text-sm text-center mb-6" style={{ ...TJ, color: C.gray }}>انضم لآلاف الملاك على سكون وأجّر عقاراتك بأمان وشفافية</p>
      <div className="flex flex-col gap-4 w-full mb-6">
        {[{ I: Building2, t: "أضف عقاراتك بسهولة", sub: "4 خطوات بسيطة وعقارك على الهواء", c: C.gold, bg: C.goldLight }, { I: Shield, t: "مستأجرون موثّقون فقط", sub: "كل المستأجرين موثّقو الهوية", c: C.teal, bg: C.tealLight }, { I: TrendingUp, t: "إحصاءات تفصيلية", sub: "تابع مشاهداتك وطلبات الزيارة", c: C.blue, bg: C.blueLight }].map(({ I, t, sub, c, bg }, i) => (
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
      <PrimaryBtn text="ابدأ كمالك" />
      <button className="mt-3 text-sm font-medium" style={{ ...TJ, color: C.gray }}>لدي حساب مالك — دخول</button>
    </div>
  );
}

function EditPropertyScreen() {
  return (
    <div className="flex flex-col h-full" style={{ backgroundColor: C.bg }}>
      <StatusBar />
      <div className="flex items-center gap-3 px-5 pt-2 pb-3" dir="rtl">
        <button><ArrowLeft size={20} style={{ color: C.navy }} /></button>
        <h1 className="text-xl font-black flex-1" style={{ ...TJ, color: C.navy }}>تعديل العقار</h1>
        <button className="text-sm font-black" style={{ ...TJ, color: C.red }}>حذف</button>
      </div>
      <div className="flex-1 overflow-y-auto px-5 pb-4" dir="rtl">
        <div className="flex gap-2 overflow-x-auto pb-3 mb-4">
          <div className="w-24 h-24 rounded-2xl flex-shrink-0 flex items-center justify-center relative" style={{ backgroundColor: "#E2E8F0" }}>
            <Building2 size={20} style={{ color: "#94A3B8" }} />
            <button className="absolute top-1 left-1 w-5 h-5 rounded-full flex items-center justify-center" style={{ backgroundColor: C.red }}>
              <X size={9} style={{ color: C.white }} />
            </button>
          </div>
          {[0,1,2].map(i => (
            <div key={i} className="w-24 h-24 rounded-2xl flex-shrink-0 flex items-center justify-center" style={{ backgroundColor: "#E2E8F0" }}>
              <Building2 size={20} style={{ color: "#94A3B8" }} />
            </div>
          ))}
          <button className="w-24 h-24 rounded-2xl flex-shrink-0 flex flex-col items-center justify-center gap-1 border-2 border-dashed" style={{ borderColor: C.border }}>
            <Plus size={18} style={{ color: C.gray }} />
            <span style={{ fontSize: 10, ...TJ, color: C.gray }}>إضافة</span>
          </button>
        </div>
        <div className="flex flex-col gap-3 mb-5">
          <TextInput label="اسم العقار" placeholder="شقة مفروشة — مدينة نصر" />
          <TextInput label="السعر الشهري" placeholder="6,500 ج" />
          <TextInput label="عدد الغرف" placeholder="3" />
          <TextInput label="المساحة" placeholder="90م²" />
          <div>
            <p className="font-black text-sm mb-2" style={{ ...TJ, color: C.navy }}>الوصف</p>
            <textarea dir="rtl" readOnly className="w-full px-4 py-3 rounded-2xl border text-sm outline-none resize-none"
              style={{ borderColor: C.border, ...TJ, color: C.navy, height: 80 }}
              placeholder="وصف العقار…" />
          </div>
        </div>
        <div className="flex gap-3">
          <PrimaryBtn text="حفظ التعديلات" />
          <button className="flex-1 py-4 rounded-2xl font-black" style={{ backgroundColor: C.bg, border: `1px solid ${C.border}`, ...TJ, color: C.gray }}>معاينة</button>
        </div>
      </div>
    </div>
  );
}

function OwnerAvailabilityScreen() {
  const days = ["الأحد","الاثنين","الثلاثاء","الأربعاء","الخميس","الجمعة","السبت"];
  const slots = ["9:00 ص","10:00 ص","11:00 ص","12:00 م","2:00 م","3:00 م","4:00 م","5:00 م"];
  const booked = new Set(["9:00 ص-0","10:00 ص-2","3:00 م-1"]);
  return (
    <div className="flex flex-col h-full" style={{ backgroundColor: C.bg }}>
      <StatusBar />
      <div className="flex items-center gap-3 px-5 pt-2 pb-3" dir="rtl">
        <button><ArrowLeft size={20} style={{ color: C.navy }} /></button>
        <h1 className="text-xl font-black flex-1" style={{ ...TJ, color: C.navy }}>مواعيد الاتاحة</h1>
      </div>
      <div className="flex-1 overflow-y-auto px-5 pb-4" dir="rtl">
        <p className="text-sm mb-4" style={{ ...TJ, color: C.gray }}>اختر الأوقات المتاحة للزيارة هذا الأسبوع</p>
        <div className="flex gap-1 overflow-x-auto pb-2 mb-4">
          {days.map((d, i) => (
            <button key={i} className="flex flex-col items-center px-2.5 py-2 rounded-2xl flex-shrink-0"
              style={{ backgroundColor: i===1 ? C.teal : C.white, border: `1px solid ${i===1 ? C.teal : C.border}`, minWidth: 44 }}>
              <span style={{ fontSize: 9, color: i===1 ? C.white : C.gray, ...TJ }}>{d.slice(0,3)}</span>
              <span className="font-black text-sm" style={{ color: i===1 ? C.white : C.navy, ...TJ }}>{14+i}</span>
            </button>
          ))}
        </div>
        <p className="font-black text-sm mb-2" style={{ ...TJ, color: C.navy }}>الاثنين 15 يونيو</p>
        <div className="grid grid-cols-4 gap-2 mb-4">
          {slots.map((s, i) => {
            const b = booked.has(`${s}-1`);
            return (
              <button key={i} className="py-2.5 rounded-2xl text-xs font-bold"
                style={{ backgroundColor: b ? C.redLight : i%3===0 ? C.tealLight : C.white, color: b ? C.red : i%3===0 ? C.teal : C.gray, border: `1px solid ${b ? C.red : i%3===0 ? C.teal : C.border}`, ...TJ }}>
                {s}{b?" ✗":""}
              </button>
            );
          })}
        </div>
        <div className="flex gap-3 mb-3">
          {[{ bg: C.tealLight, c: C.teal, l: "متاح" }, { bg: C.redLight, c: C.red, l: "محجوز" }, { bg: C.white, c: C.gray, l: "غير محدد" }].map(({ bg, c, l }, i) => (
            <div key={i} className="flex items-center gap-1.5">
              <div className="w-4 h-4 rounded" style={{ backgroundColor: bg, border: `1px solid ${c}` }} />
              <span style={{ fontSize: 11, ...TJ, color: C.gray }}>{l}</span>
            </div>
          ))}
        </div>
        <PrimaryBtn text="حفظ مواعيد الاتاحة" />
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════
//  ADMIN MISSING SCREENS — KYC REVIEW
// ═══════════════════════════════════════════════


export {
  OwnerProfileScreen,
  OwnerMoreScreen,
  OwnerNotificationsScreen,
  OwnerChatListScreen,
  PropertyRejectionDetailScreen,
  OwnerVisitsDashboardScreen,
  OwnerDashboardScreen,
  OwnerMyListingsScreen,
  AddPropertyStep1Screen,
  AddPropertyStep2PhotosScreen,
  AddPropertyStep3PricingScreen,
  PropertySubmittedScreen,
  OwnerRequestsListScreen,
  OwnerRequestDetailScreen,
  OwnerChatThreadScreen,
  OwnerPropertyAnalyticsScreen,
  OwnerRevenueScreen,
  OwnerKYCScreen,
  OwnerSupportScreen,
  OwnerOnboardingScreen,
  EditPropertyScreen,
  OwnerAvailabilityScreen
};
