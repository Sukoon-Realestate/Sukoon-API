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

function AdminSidebar({ active }: { active: string }) {
  const items = [
    { id: "dashboard", I: Home, label: "لوحة التحكم" },
    { id: "users", I: Users, label: "المستخدمون" },
    { id: "kyc", I: CheckCircle, label: "التوثيق" },
    { id: "properties", I: Building2, label: "العقارات" },
    { id: "analytics", I: BarChart2, label: "التحليلات" },
    { id: "settings", I: Settings, label: "الإعدادات" },
  ];
  return (
    <div className="w-14 flex flex-col items-center py-3 gap-1 flex-shrink-0" style={{ backgroundColor: "#1E293B" }}>
      <div className="w-9 h-9 rounded-xl flex items-center justify-center mb-3" style={{ backgroundColor: C.teal }}>
        <Shield size={16} style={{ color: C.white }} />
      </div>
      {items.map(({ id, I, label }) => (
        <div key={id} className="relative group">
          <button className="w-9 h-9 rounded-xl flex items-center justify-center"
            style={{ backgroundColor: id === active ? C.teal : "transparent" }}>
            <I size={16} style={{ color: id === active ? C.white : "#64748B" }} />
          </button>
        </div>
      ))}
    </div>
  );
}

function AdminDashboardScreen() {
  return (
    <div className="flex h-full" style={{ backgroundColor: "#F8FAFC", fontFamily: "Tajawal, sans-serif" }}>
      <AdminSidebar active="dashboard" />
      <div className="flex-1 overflow-y-auto p-4">
        <div className="flex items-center justify-between mb-4" dir="rtl">
          <div>
            <h1 className="text-xl font-black" style={{ color: C.navy }}>لوحة تحكم سكون</h1>
            <p className="text-xs" style={{ color: C.gray }}>آخر تحديث: اليوم 9:41 ص</p>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-full flex items-center justify-center" style={{ backgroundColor: C.tealLight }}>
              <User size={14} style={{ color: C.teal }} />
            </div>
            <span className="text-xs px-2 py-1 rounded-full font-black text-white" style={{ backgroundColor: C.teal }}>Admin</span>
          </div>
        </div>
        <div className="grid grid-cols-4 gap-3 mb-4">
          {[
            { l: "إجمالي المستخدمين", n: "2,847", delta: "+12%", c: C.blue, bg: C.blueLight, I: Users },
            { l: "عقارات نشطة", n: "1,203", delta: "+8%", c: C.green, bg: C.greenLight, I: Building2 },
            { l: "توثيق معلق", n: "487", delta: "-5%", c: C.amber, bg: C.amberLight, I: Clock },
            { l: "إيرادات المنصة", n: "89,400 ج", delta: "+21%", c: C.teal, bg: C.tealLight, I: TrendingUp },
          ].map(({ l, n, delta, c, bg, I }, i) => (
            <div key={i} className="p-4 rounded-2xl" style={{ backgroundColor: C.white, border: `1px solid ${C.border}` }} dir="rtl">
              <div className="flex items-center justify-between mb-2">
                <div className="w-8 h-8 rounded-xl flex items-center justify-center" style={{ backgroundColor: bg }}><I size={15} style={{ color: c }} /></div>
                <span className="text-xs font-bold" style={{ color: delta.startsWith("+") ? C.green : C.red }}>{delta}</span>
              </div>
              <p className="text-2xl font-black" style={{ color: C.navy }}>{n}</p>
              <p className="text-xs" style={{ color: C.gray }}>{l}</p>
            </div>
          ))}
        </div>
        <div className="grid grid-cols-2 gap-3 mb-4">
          <div className="p-4 rounded-2xl" style={{ backgroundColor: C.white, border: `1px solid ${C.border}` }} dir="rtl">
            <p className="font-black text-sm mb-3" style={{ color: C.navy }}>المستخدمون الجدد (30 يوم)</p>
            <div className="flex items-end gap-1" style={{ height: 80 }}>
              {[30, 55, 42, 70, 58, 85, 65, 92, 75, 100, 82, 95, 68, 88].map((h, i) => (
                <div key={i} className="flex-1 rounded-t-sm" style={{ height: `${h}%`, backgroundColor: i === 13 ? C.teal : `${C.teal}30` }} />
              ))}
            </div>
          </div>
          <div className="p-4 rounded-2xl" style={{ backgroundColor: C.white, border: `1px solid ${C.border}` }} dir="rtl">
            <p className="font-black text-sm mb-3" style={{ color: C.navy }}>توزيع المستخدمين</p>
            <div className="flex flex-col gap-2">
              {[{ l: "مستأجرون", n: "1,924", p: 67, c: C.blue }, { l: "ملاّك", n: "923", p: 33, c: C.gold }].map(({ l, n, p, c }, i) => (
                <div key={i}>
                  <div className="flex justify-between text-xs mb-1" style={{ color: C.gray }}><span style={{ color: C.navy, fontWeight: 700 }}>{l}</span><span>{n}</span></div>
                  <div className="h-2 rounded-full" style={{ backgroundColor: "#E5E7EB" }}>
                    <div className="h-full rounded-full" style={{ width: `${p}%`, backgroundColor: c }} />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
        <div className="rounded-2xl overflow-hidden" style={{ backgroundColor: C.white, border: `1px solid ${C.border}` }}>
          <div className="px-4 py-3 flex items-center justify-between" style={{ borderBottom: `1px solid ${C.border}` }} dir="rtl">
            <h3 className="font-black text-sm" style={{ color: C.navy }}>آخر الأنشطة</h3>
            <button className="text-xs font-bold" style={{ color: C.teal }}>عرض الكل</button>
          </div>
          {[
            { type: "kyc", text: "سارة أحمد أرسلت طلب توثيق", time: "منذ 5 دق", color: C.teal, bg: C.tealLight, I: CheckCircle },
            { type: "prop", text: "عقار جديد في مدينة نصر بانتظار المراجعة", time: "منذ 12 دق", color: C.amber, bg: C.amberLight, I: Building2 },
            { type: "user", text: "محمد علي أنشأ حساباً جديداً كمستأجر", time: "منذ 20 دق", color: C.blue, bg: C.blueLight, I: User },
            { type: "kyc", text: "تم اعتماد توثيق محمود حسن", time: "منذ 35 دق", color: C.green, bg: C.greenLight, I: CheckCircle },
          ].map((a, i) => (
            <div key={i} className="flex items-center gap-3 px-4 py-3" style={{ borderBottom: `1px solid ${C.border}` }} dir="rtl">
              <div className="w-8 h-8 rounded-xl flex items-center justify-center flex-shrink-0" style={{ backgroundColor: a.bg }}>
                <a.I size={14} style={{ color: a.color }} />
              </div>
              <p className="flex-1 text-xs" style={{ color: C.navy }}>{a.text}</p>
              <span className="text-xs flex-shrink-0" style={{ color: C.gray }}>{a.time}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function AdminUsersScreen() {
  return (
    <div className="flex h-full" style={{ backgroundColor: "#F8FAFC", fontFamily: "Tajawal, sans-serif" }}>
      <AdminSidebar active="users" />
      <div className="flex-1 overflow-y-auto p-4">
        <div className="flex items-center justify-between mb-4" dir="rtl">
          <h1 className="text-xl font-black" style={{ color: C.navy }}>إدارة المستخدمين</h1>
          <div className="flex items-center gap-2">
            <div className="flex items-center px-3 py-2 rounded-xl gap-2" style={{ backgroundColor: C.white, border: `1px solid ${C.border}` }}>
              <Search size={13} style={{ color: C.gray }} />
              <input placeholder="بحث باسم أو بريد…" dir="rtl" readOnly className="text-sm outline-none" style={{ width: 140 }} />
            </div>
            <button className="flex items-center gap-1 px-3 py-2 rounded-xl text-sm font-bold" style={{ backgroundColor: C.tealLight, color: C.teal }}>
              <Filter size={13} />فلتر
            </button>
          </div>
        </div>
        <div className="grid grid-cols-4 gap-3 mb-4">
          {[{ l: "الكل", n: "2,847", c: C.navy }, { l: "موثّق", n: "1,920", c: C.green }, { l: "معلّق", n: "487", c: C.amber }, { l: "موقوف", n: "43", c: C.red }].map(({ l, n, c }, i) => (
            <button key={i} className="p-3 rounded-2xl text-center"
              style={{ backgroundColor: i === 0 ? C.teal : C.white, border: `1px solid ${i === 0 ? C.teal : C.border}` }}>
              <p className="text-2xl font-black" style={{ color: i === 0 ? C.white : c }}>{n}</p>
              <p className="text-xs" style={{ color: i === 0 ? "rgba(255,255,255,0.8)" : C.gray }}>{l}</p>
            </button>
          ))}
        </div>
        <div className="rounded-2xl overflow-hidden" style={{ backgroundColor: C.white, border: `1px solid ${C.border}` }}>
          <div className="grid px-4 py-2.5 text-xs font-black" style={{ backgroundColor: "#F8FAFC", color: C.gray, gridTemplateColumns: "2fr 1fr 1.5fr 1fr 1fr 1.5fr 1fr" }} dir="rtl">
            {["الاسم", "النوع", "البريد", "الحالة", "التوثيق", "تاريخ التسجيل", "إجراء"].map((h, i) => (
              <div key={i} className="text-right">{h}</div>
            ))}
          </div>
          {[
            { n: "سارة أحمد خالد", t: "مستأجر", e: "sara@example.com", st: "نشط", kyc: "verified" as BadgeType, date: "14 يناير 2026" },
            { n: "محمود حسن علي", t: "مالك", e: "mahmoud@example.com", st: "نشط", kyc: "verified" as BadgeType, date: "12 يناير 2026" },
            { n: "نورا محمد عمر", t: "مستأجر", e: "noura@example.com", st: "نشط", kyc: "pending" as BadgeType, date: "10 يناير 2026" },
            { n: "كريم طارق سالم", t: "مالك", e: "karim@example.com", st: "موقوف", kyc: "rejected" as BadgeType, date: "8 يناير 2026" },
          ].map((r, i) => (
            <div key={i} className="grid px-4 py-3 items-center" style={{ borderTop: `1px solid ${C.border}`, gridTemplateColumns: "2fr 1fr 1.5fr 1fr 1fr 1.5fr 1fr" }} dir="rtl">
              <div className="flex items-center gap-2">
                <div className="w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0" style={{ backgroundColor: C.tealLight }}>
                  <User size={12} style={{ color: C.teal }} />
                </div>
                <span className="text-xs font-black" style={{ color: C.navy }}>{r.n}</span>
              </div>
              <div><span className="px-2 py-0.5 rounded-full text-xs font-bold" style={{ backgroundColor: r.t === "مالك" ? C.goldLight : C.blueLight, color: r.t === "مالك" ? C.gold : C.blue }}>{r.t}</span></div>
              <div className="text-xs" style={{ color: C.gray }}>{r.e}</div>
              <div><span className="text-xs font-bold" style={{ color: r.st === "نشط" ? C.green : C.red }}>{r.st}</span></div>
              <div><Badge type={r.kyc} /></div>
              <div className="text-xs" style={{ color: C.gray }}>{r.date}</div>
              <div className="flex gap-1">
                <button className="px-2 py-1 rounded-lg text-xs font-black text-white" style={{ backgroundColor: C.teal }}>عرض</button>
                <button className="px-2 py-1 rounded-lg text-xs font-black" style={{ backgroundColor: C.redLight, color: C.red }}>إيقاف</button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function AdminPropertiesScreen() {
  return (
    <div className="flex h-full" style={{ backgroundColor: "#F8FAFC", fontFamily: "Tajawal, sans-serif" }}>
      <AdminSidebar active="properties" />
      <div className="flex-1 overflow-y-auto p-4">
        <div className="flex items-center justify-between mb-4" dir="rtl">
          <h1 className="text-xl font-black" style={{ color: C.navy }}>إدارة العقارات</h1>
          <div className="flex items-center gap-2">
            <div className="flex items-center px-3 py-2 rounded-xl gap-2" style={{ backgroundColor: C.white, border: `1px solid ${C.border}` }}>
              <Search size={13} style={{ color: C.gray }} />
              <input placeholder="بحث في العقارات…" dir="rtl" readOnly className="text-sm outline-none" style={{ width: 140 }} />
            </div>
            <button className="flex items-center gap-1 px-3 py-2 rounded-xl text-sm font-bold" style={{ backgroundColor: C.tealLight, color: C.teal }}>
              <Filter size={13} />فلتر
            </button>
          </div>
        </div>
        <div className="grid grid-cols-4 gap-3 mb-4">
          {[{ l: "إجمالي العقارات", n: "1,203", c: C.navy }, { l: "نشط", n: "890", c: C.green }, { l: "قيد المراجعة", n: "234", c: C.amber }, { l: "مرفوض", n: "79", c: C.red }].map(({ l, n, c }, i) => (
            <div key={i} className="p-4 rounded-2xl text-center" style={{ backgroundColor: C.white, border: `1px solid ${C.border}` }}>
              <p className="text-2xl font-black" style={{ color: c }}>{n}</p>
              <p className="text-xs" style={{ color: C.gray }}>{l}</p>
            </div>
          ))}
        </div>
        <div className="rounded-2xl overflow-hidden" style={{ backgroundColor: C.white, border: `1px solid ${C.border}` }}>
          <div className="grid px-4 py-2.5 text-xs font-black" style={{ backgroundColor: "#F8FAFC", color: C.gray, gridTemplateColumns: "2fr 1fr 1fr 1fr 1fr 1fr 1.5fr" }} dir="rtl">
            {["العقار", "المالك", "النوع", "الحالة", "السعر", "المشاهدات", "إجراء"].map((h, i) => (
              <div key={i} className="text-right">{h}</div>
            ))}
          </div>
          {[
            { t: "شقة مفروشة، مدينة نصر", owner: "أحمد محمد", type: "شقة", status: "نشط", statusType: "approved" as BadgeType, price: "12,000", views: "540" },
            { t: "ستوديو، التجمع الخامس", owner: "منى علي", type: "ستوديو", status: "مراجعة", statusType: "pending" as BadgeType, price: "7,500", views: "0" },
            { t: "غرفة، المعادي", owner: "كريم سالم", type: "غرفة", status: "مرفوض", statusType: "rejected" as BadgeType, price: "4,000", views: "120" },
            { t: "شقة، المهندسين", owner: "نادر طارق", type: "شقة", status: "نشط", statusType: "approved" as BadgeType, price: "15,000", views: "325" },
          ].map((r, i) => (
            <div key={i} className="grid px-4 py-3 items-center" style={{ borderTop: `1px solid ${C.border}`, gridTemplateColumns: "2fr 1fr 1fr 1fr 1fr 1fr 1.5fr" }} dir="rtl">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-xl flex items-center justify-center flex-shrink-0" style={{ backgroundColor: "#E2E8F0" }}>
                  <Building2 size={12} style={{ color: "#94A3B8" }} />
                </div>
                <span className="text-xs font-black" style={{ color: C.navy }}>{r.t}</span>
              </div>
              <div className="text-xs" style={{ color: C.gray }}>{r.owner}</div>
              <div><span className="text-xs font-bold px-2 py-0.5 rounded-full" style={{ backgroundColor: C.tealLight, color: C.teal }}>{r.type}</span></div>
              <div><Badge type={r.statusType} /></div>
              <div className="text-xs font-bold" style={{ color: C.teal }}>{r.price} ج</div>
              <div className="text-xs" style={{ color: C.gray }}>{r.views}</div>
              <div className="flex gap-1">
                <button className="px-2 py-1 rounded-lg text-xs font-black text-white" style={{ backgroundColor: C.teal }}>مراجعة</button>
                <button className="px-2 py-1 rounded-lg text-xs font-black" style={{ backgroundColor: C.redLight, color: C.red }}>رفض</button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function AdminAnalyticsScreen() {
  return (
    <div className="flex h-full" style={{ backgroundColor: "#F8FAFC", fontFamily: "Tajawal, sans-serif" }}>
      <AdminSidebar active="analytics" />
      <div className="flex-1 overflow-y-auto p-4">
        <div className="flex items-center justify-between mb-4" dir="rtl">
          <h1 className="text-xl font-black" style={{ color: C.navy }}>التحليلات والتقارير</h1>
          <div className="flex gap-2">
            {["آخر 7 أيام", "30 يوم", "90 يوم"].map((t, i) => (
              <button key={i} className="px-3 py-1.5 rounded-xl text-xs font-bold"
                style={{ backgroundColor: i === 1 ? C.teal : C.white, color: i === 1 ? C.white : C.navy, border: `1px solid ${i === 1 ? C.teal : C.border}` }}>{t}</button>
            ))}
          </div>
        </div>
        <div className="grid grid-cols-4 gap-3 mb-4">
          {[
            { l: "طلبات الزيارة", n: "1,847", delta: "+23%", up: true, I: Calendar, c: C.teal, bg: C.tealLight },
            { l: "زيارات مكتملة", n: "1,204", delta: "+15%", up: true, I: CheckCircle, c: C.green, bg: C.greenLight },
            { l: "متوسط التقييم", n: "4.7 ★", delta: "+0.2", up: true, I: Star, c: C.amber, bg: C.amberLight },
            { l: "معدل الاحتفاظ", n: "78%", delta: "-2%", up: false, I: Users, c: C.red, bg: C.redLight },
          ].map(({ l, n, delta, up, I, c, bg }, i) => (
            <div key={i} className="p-4 rounded-2xl" style={{ backgroundColor: C.white, border: `1px solid ${C.border}` }} dir="rtl">
              <div className="flex items-center justify-between mb-2">
                <div className="w-8 h-8 rounded-xl flex items-center justify-center" style={{ backgroundColor: bg }}><I size={15} style={{ color: c }} /></div>
                <div className="flex items-center gap-0.5" style={{ color: up ? C.green : C.red }}>
                  {up ? <TrendingUp size={11} /> : <TrendingDown size={11} />}
                  <span className="text-xs font-bold">{delta}</span>
                </div>
              </div>
              <p className="text-2xl font-black" style={{ color: C.navy }}>{n}</p>
              <p className="text-xs" style={{ color: C.gray }}>{l}</p>
            </div>
          ))}
        </div>
        <div className="grid grid-cols-2 gap-3 mb-4">
          <div className="p-4 rounded-2xl" style={{ backgroundColor: C.white, border: `1px solid ${C.border}` }} dir="rtl">
            <p className="font-black text-sm mb-3" style={{ color: C.navy }}>طلبات الزيارة اليومية</p>
            <div className="flex items-end gap-1 justify-between" style={{ height: 100 }}>
              {[45, 70, 55, 90, 72, 100, 80, 95, 68, 85, 78, 92, 60, 88].map((h, i) => (
                <div key={i} className="flex-1 rounded-t-sm" style={{ height: `${h}%`, backgroundColor: i === 13 ? C.teal : `${C.teal}35` }} />
              ))}
            </div>
          </div>
          <div className="p-4 rounded-2xl" style={{ backgroundColor: C.white, border: `1px solid ${C.border}` }} dir="rtl">
            <p className="font-black text-sm mb-3" style={{ color: C.navy }}>أكثر المناطق طلباً</p>
            {[{ l: "مدينة نصر", n: 380, p: 100 }, { l: "التجمع الخامس", n: 265, p: 70 }, { l: "المهندسين", n: 198, p: 52 }, { l: "المعادي", n: 154, p: 40 }].map(({ l, n, p }, i) => (
              <div key={i} className="mb-3">
                <div className="flex justify-between text-xs mb-1" style={{ color: C.gray }}><span style={{ color: C.navy, fontWeight: 700 }}>{l}</span><span>{n} طلب</span></div>
                <div className="h-1.5 rounded-full" style={{ backgroundColor: "#E5E7EB" }}>
                  <div className="h-full rounded-full" style={{ width: `${p}%`, backgroundColor: C.teal }} />
                </div>
              </div>
            ))}
          </div>
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div className="p-4 rounded-2xl" style={{ backgroundColor: C.white, border: `1px solid ${C.border}` }} dir="rtl">
            <p className="font-black text-sm mb-3" style={{ color: C.navy }}>حالة التوثيق</p>
            {[{ l: "موثّق", n: 1920, p: 67, c: C.green }, { l: "معلّق", n: 487, p: 17, c: C.amber }, { l: "مرفوض", n: 143, p: 5, c: C.red }, { l: "جديد (بدون توثيق)", n: 297, p: 11, c: C.gray }].map(({ l, n, p, c }, i) => (
              <div key={i} className="flex items-center gap-2 mb-2">
                <div className="w-2 h-2 rounded-full flex-shrink-0" style={{ backgroundColor: c }} />
                <span className="text-xs flex-1" style={{ color: C.navy }}>{l}</span>
                <span className="text-xs font-bold" style={{ color: C.navy }}>{n}</span>
                <span className="text-xs" style={{ color: C.gray }}>({p}%)</span>
              </div>
            ))}
          </div>
          <div className="p-4 rounded-2xl" style={{ backgroundColor: C.white, border: `1px solid ${C.border}` }} dir="rtl">
            <p className="font-black text-sm mb-3" style={{ color: C.navy }}>نشاط العقارات</p>
            {[{ l: "عرض متاح", n: 890, c: C.green }, { l: "قيد المراجعة", n: 234, c: C.amber }, { l: "مؤجّر", n: 512, c: C.blue }, { l: "مخفي", n: 67, c: C.gray }].map(({ l, n, c }, i) => (
              <div key={i} className="flex items-center justify-between py-2" style={{ borderBottom: i < 3 ? `1px solid ${C.border}` : "none" }}>
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full" style={{ backgroundColor: c }} />
                  <span className="text-xs font-bold" style={{ color: C.navy }}>{n}</span>
                </div>
                <span className="text-xs" style={{ color: C.gray }}>{l}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

function AdminSettingsScreen() {
  return (
    <div className="flex h-full" style={{ backgroundColor: "#F8FAFC", fontFamily: "Tajawal, sans-serif" }}>
      <AdminSidebar active="settings" />
      <div className="flex-1 overflow-y-auto p-4">
        <h1 className="text-xl font-black mb-4" style={{ color: C.navy }}>إعدادات المنصة</h1>
        <div className="grid grid-cols-2 gap-4">
          {[
            { title: "إعدادات التوثيق", items: ["مدة المراجعة القصوى (ساعات)", "مستندات مطلوبة للمستأجر", "مستندات مطلوبة للمالك", "تفعيل التوثيق الآلي"] },
            { title: "إعدادات العقارات", items: ["الحد الأقصى للصور", "مدة المراجعة (أيام)", "تفعيل الموقع التقريبي", "إخفاء الأرقام افتراضياً"] },
          ].map(({ title, items }, gi) => (
            <div key={gi} className="p-4 rounded-2xl" style={{ backgroundColor: C.white, border: `1px solid ${C.border}` }} dir="rtl">
              <p className="font-black text-sm mb-3" style={{ color: C.navy }}>{title}</p>
              {items.map((item, i) => (
                <div key={i} className="flex items-center justify-between py-2.5" style={{ borderBottom: i < items.length - 1 ? `1px solid ${C.border}` : "none" }}>
                  <div className="w-8 h-4 rounded-full relative" style={{ backgroundColor: [0, 2, 3].includes(i) ? C.teal : "#E5E7EB" }}>
                    <div className="absolute top-0.5 w-3 h-3 rounded-full bg-white" style={{ right: [0, 2, 3].includes(i) ? "2px" : "auto", left: [0, 2, 3].includes(i) ? "auto" : "2px" }} />
                  </div>
                  <span className="text-xs" style={{ color: C.navy }}>{item}</span>
                </div>
              ))}
            </div>
          ))}
        </div>
        <div className="mt-4 p-4 rounded-2xl" style={{ backgroundColor: C.white, border: `1px solid ${C.border}` }} dir="rtl">
          <p className="font-black text-sm mb-3" style={{ color: C.navy }}>إدارة المشرفين</p>
          {[{ name: "أحمد العدل", role: "مشرف رئيسي", badge: "مالك" }, { name: "سلمى رشدي", role: "مراجع KYC", badge: "مراجع" }].map((a, i) => (
            <div key={i} className="flex items-center justify-between py-3" style={{ borderBottom: i === 0 ? `1px solid ${C.border}` : "none" }}>
              <div className="flex items-center gap-2">
                <button className="text-xs px-2 py-1 rounded-lg" style={{ backgroundColor: C.redLight, color: C.red }}>حذف</button>
                <span className="text-xs px-2 py-0.5 rounded-full font-bold" style={{ backgroundColor: C.tealLight, color: C.teal }}>{a.badge}</span>
              </div>
              <div className="text-right">
                <p className="text-sm font-black" style={{ color: C.navy }}>{a.name}</p>
                <p className="text-xs" style={{ color: C.gray }}>{a.role}</p>
              </div>
            </div>
          ))}
          <button className="mt-3 flex items-center gap-2 px-3 py-2 rounded-xl text-sm font-bold" style={{ backgroundColor: C.tealLight, color: C.teal }}>
            <Plus size={14} />إضافة مشرف جديد
          </button>
        </div>
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════
//  NEW TENANT SCREENS  (from PDF other_screens-2)
// ═══════════════════════════════════════════════


function AdminSidebar2({ active }: { active: string }) {
  const items = [
    { id: "dash", I: Home, label: "لوحة التحكم" },
    { id: "users", I: Users, label: "المستخدمون" },
    { id: "kyc", I: CheckCircle, label: "التوثيق KYC" },
    { id: "inventory", I: Building2, label: "العقارات" },
    { id: "reports", I: FileText, label: "التقارير" },
    { id: "roles", I: Shield, label: "الأدوار" },
    { id: "system", I: Settings, label: "النظام" },
  ];
  return (
    <div className="flex flex-col flex-shrink-0" style={{ width: 200, backgroundColor: "#1E293B", padding: "12px 0" }}>
      <div className="flex items-center gap-2 px-4 mb-5">
        <div className="w-8 h-8 rounded-xl flex items-center justify-center" style={{ backgroundColor: C.teal }}>
          <Shield size={14} style={{ color: C.white }} />
        </div>
        <span className="font-black text-white text-sm" style={{ fontFamily: "Tajawal, sans-serif" }}>سكون — Admin</span>
      </div>
      {items.map(({ id, I, label }) => (
        <button key={id} className="flex items-center gap-3 px-4 py-2.5 text-right w-full transition-all"
          style={{ backgroundColor: id === active ? `${C.teal}20` : "transparent", borderRight: `3px solid ${id === active ? C.teal : "transparent"}` }}>
          <I size={15} style={{ color: id === active ? C.teal : "#64748B" }} />
          <span className="text-xs font-bold" style={{ fontFamily: "Tajawal, sans-serif", color: id === active ? C.teal : "#94A3B8" }}>{label}</span>
        </button>
      ))}
    </div>
  );
}

function AdminTopBar({ title }: { title: string }) {
  return (
    <div className="flex items-center justify-between px-5 py-3 flex-shrink-0"
      style={{ backgroundColor: C.white, borderBottom: `1px solid ${C.border}` }}>
      <div className="flex items-center gap-2">
        <div className="w-8 h-8 rounded-full flex items-center justify-center" style={{ backgroundColor: C.tealLight }}>
          <User size={14} style={{ color: C.teal }} />
        </div>
        <span className="text-xs px-2 py-1 rounded-full font-black text-white" style={{ backgroundColor: C.teal, fontFamily: "Tajawal, sans-serif" }}>Admin</span>
      </div>
      <h1 className="text-base font-black" style={{ fontFamily: "Tajawal, sans-serif", color: C.navy }}>{title}</h1>
      <div className="flex items-center gap-2">
        <button className="relative w-8 h-8 rounded-full flex items-center justify-center" style={{ backgroundColor: C.bg, border: `1px solid ${C.border}` }}>
          <Bell size={14} style={{ color: C.navy }} />
          <div className="absolute top-0.5 right-0.5 w-2 h-2 rounded-full" style={{ backgroundColor: C.red }} />
        </button>
        <span className="text-xs" style={{ fontFamily: "Tajawal, sans-serif", color: C.gray }}>آخر تحديث: 9:41 ص</span>
      </div>
    </div>
  );
}

function AdminExecutiveDashboardScreen() {
  return (
    <div className="flex h-full" style={{ backgroundColor: "#F8FAFC", fontFamily: "Tajawal, sans-serif" }}>
      <AdminSidebar2 active="dash" />
      <div className="flex-1 flex flex-col overflow-hidden">
        <AdminTopBar title="لوحة التحكم التنفيذية" />
        <div className="flex-1 overflow-y-auto p-4">
          {/* KPI strip */}
          <div className="grid grid-cols-5 gap-3 mb-4">
            {[
              { l: "المستخدمون النشطون", n: "2,847", delta: "+12%", up: true, I: Users, c: C.blue, bg: C.blueLight },
              { l: "عقارات نشطة", n: "1,203", delta: "+8%", up: true, I: Building2, c: C.green, bg: C.greenLight },
              { l: "طلبات الزيارة اليوم", n: "143", delta: "+23%", up: true, I: Calendar, c: C.teal, bg: C.tealLight },
              { l: "توثيق معلق", n: "487", delta: "-5%", up: false, I: Clock, c: C.amber, bg: C.amberLight },
              { l: "بلاغات مفتوحة", n: "31", delta: "+7%", up: false, I: AlertTriangle, c: C.red, bg: C.redLight },
            ].map(({ l, n, delta, up, I, c, bg }, i) => (
              <div key={i} className="p-3 rounded-2xl" style={{ backgroundColor: C.white, border: `1px solid ${C.border}` }} dir="rtl">
                <div className="flex items-center justify-between mb-2">
                  <div className="w-7 h-7 rounded-lg flex items-center justify-center" style={{ backgroundColor: bg }}><I size={13} style={{ color: c }} /></div>
                  <div className="flex items-center gap-0.5" style={{ color: up ? C.green : C.red }}>
                    {up ? <TrendingUp size={10} /> : <TrendingDown size={10} />}
                    <span style={{ fontSize: 10, fontWeight: 700 }}>{delta}</span>
                  </div>
                </div>
                <p className="text-xl font-black" style={{ color: C.navy }}>{n}</p>
                <p style={{ fontSize: 10, color: C.gray }}>{l}</p>
              </div>
            ))}
          </div>

          <div className="grid grid-cols-2 gap-3 mb-4">
            {/* Traffic Trend chart */}
            <div className="p-4 rounded-2xl" style={{ backgroundColor: C.white, border: `1px solid ${C.border}` }} dir="rtl">
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs px-2 py-0.5 rounded-full font-bold" style={{ backgroundColor: C.tealLight, color: C.teal }}>30 يوم</span>
                <p className="font-black text-sm" style={{ color: C.navy }}>Traffic Trend — نشاط المنصة</p>
              </div>
              <div className="flex items-end gap-0.5 justify-between mb-2" style={{ height: 80 }}>
                {[28, 42, 35, 60, 48, 72, 55, 80, 65, 90, 70, 85, 58, 78, 88, 62, 75, 92, 68, 82, 95, 74, 86, 100, 78, 91, 84, 72, 89, 96].map((h, i) => (
                  <div key={i} className="flex-1 rounded-t-sm" style={{ height: `${h}%`, backgroundColor: i >= 27 ? C.teal : `${C.teal}25` }} />
                ))}
              </div>
              <div className="flex justify-between">
                <span style={{ fontSize: 10, color: C.gray }}>اليوم</span>
                <span style={{ fontSize: 10, color: C.gray }}>1 يناير</span>
              </div>
            </div>

            {/* Reports Trend */}
            <div className="p-4 rounded-2xl" style={{ backgroundColor: C.white, border: `1px solid ${C.border}` }} dir="rtl">
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs px-2 py-0.5 rounded-full font-bold" style={{ backgroundColor: C.redLight, color: C.red }}>30 يوم</span>
                <p className="font-black text-sm" style={{ color: C.navy }}>Reports Trend — البلاغات</p>
              </div>
              <div className="flex items-end gap-0.5 justify-between mb-2" style={{ height: 80 }}>
                {[15, 22, 18, 30, 25, 35, 20, 28, 32, 18, 25, 40, 22, 30, 15, 35, 28, 20, 38, 25, 32, 18, 28, 42, 20, 30, 25, 35, 28, 22].map((h, i) => (
                  <div key={i} className="flex-1 rounded-t-sm" style={{ height: `${h}%`, backgroundColor: i >= 27 ? C.red : `${C.red}25` }} />
                ))}
              </div>
              <div className="flex justify-between">
                <span style={{ fontSize: 10, color: C.gray }}>اليوم</span>
                <span style={{ fontSize: 10, color: C.gray }}>1 يناير</span>
              </div>
            </div>
          </div>

          {/* User Summary + Recent Activity */}
          <div className="grid grid-cols-3 gap-3">
            {/* User Summary */}
            <div className="p-4 rounded-2xl" style={{ backgroundColor: C.white, border: `1px solid ${C.border}` }} dir="rtl">
              <p className="font-black text-sm mb-3" style={{ color: C.navy }}>ملخص المستخدمين</p>
              <div className="flex items-center gap-3 mb-3 pb-3" style={{ borderBottom: `1px solid ${C.border}` }}>
                <div className="w-10 h-10 rounded-full flex items-center justify-center" style={{ backgroundColor: C.tealLight }}>
                  <User size={18} style={{ color: C.teal }} />
                </div>
                <div>
                  <p className="font-black text-base" style={{ color: C.navy }}>Admin User</p>
                  <div className="flex items-center gap-1">
                    <div className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: C.green }} />
                    <span style={{ fontSize: 10, color: C.gray }}>نشط الآن</span>
                  </div>
                </div>
              </div>
              {[{ l: "إجمالي المستخدمين", n: "2,847" }, { l: "مستأجرون", n: "1,924" }, { l: "ملاّك", n: "923" }, { l: "موثّقون", n: "1,920" }, { l: "موقوفون", n: "43" }].map(({ l, n }, i) => (
                <div key={i} className="flex justify-between py-1.5" style={{ borderBottom: i < 4 ? `1px solid ${C.border}` : "none" }}>
                  <span className="font-bold text-xs" style={{ color: C.navy }}>{n}</span>
                  <span style={{ fontSize: 10, color: C.gray }}>{l}</span>
                </div>
              ))}
            </div>

            {/* Recent Activity — 2 cols wide */}
            <div className="col-span-2 p-4 rounded-2xl" style={{ backgroundColor: C.white, border: `1px solid ${C.border}` }} dir="rtl">
              <div className="flex items-center justify-between mb-3">
                <button className="text-xs font-bold" style={{ color: C.teal }}>عرض الكل</button>
                <p className="font-black text-sm" style={{ color: C.navy }}>آخر الأنشطة</p>
              </div>
              {[
                { type: "kyc", text: "تم قبول توثيق سارة أحمد خالد", time: "منذ 2 دق", I: CheckCircle, c: C.green, bg: C.greenLight, user: "مستأجر" },
                { type: "flag", text: "بلاغ جديد على ستوديو التجمع الخامس", time: "منذ 8 دق", I: AlertTriangle, c: C.red, bg: C.redLight, user: "عقار" },
                { type: "prop", text: "عقار جديد بانتظار المراجعة — مدينة نصر", time: "منذ 15 دق", I: Building2, c: C.amber, bg: C.amberLight, user: "مالك" },
                { type: "user", text: "تسجيل مستخدم جديد: محمد طارق (مستأجر)", time: "منذ 22 دق", I: User, c: C.blue, bg: C.blueLight, user: "مستأجر" },
                { type: "role", text: "تغيير صلاحية: سلمى رشدي → مراجع كبير", time: "منذ 45 دق", I: Shield, c: C.teal, bg: C.tealLight, user: "Admin" },
              ].map((a, i) => (
                <div key={i} className="flex items-center gap-3 py-2.5" style={{ borderBottom: i < 4 ? `1px solid ${C.border}` : "none" }}>
                  <div className="w-7 h-7 rounded-lg flex items-center justify-center flex-shrink-0" style={{ backgroundColor: a.bg }}>
                    <a.I size={12} style={{ color: a.c }} />
                  </div>
                  <p className="flex-1 text-xs" style={{ color: C.navy }}>{a.text}</p>
                  <span className="text-xs px-2 py-0.5 rounded-full font-bold flex-shrink-0" style={{ backgroundColor: C.bg, color: C.gray }}>{a.user}</span>
                  <span style={{ fontSize: 10, color: "#9CA3AF", flexShrink: 0 }}>{a.time}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function AdminListingModerationScreen() {
  return (
    <div className="flex h-full" style={{ backgroundColor: "#F8FAFC", fontFamily: "Tajawal, sans-serif" }}>
      <AdminSidebar2 active="inventory" />
      <div className="flex-1 flex flex-col overflow-hidden">
        <AdminTopBar title="طابور مراجعة العقارات" />
        <div className="flex-1 overflow-y-auto p-4">
          <div className="grid grid-cols-4 gap-3 mb-4">
            {[{ l: "بانتظار المراجعة", n: "234", c: C.amber }, { l: "مقبول اليوم", n: "89", c: C.green }, { l: "مرفوض اليوم", n: "12", c: C.red }, { l: "بلاغات نشطة", n: "31", c: C.blue }].map(({ l, n, c }, i) => (
              <div key={i} className="p-3 rounded-2xl text-center" style={{ backgroundColor: C.white, border: `1px solid ${C.border}` }}>
                <p className="text-2xl font-black" style={{ color: c }}>{n}</p>
                <p className="text-xs" style={{ color: C.gray }}>{l}</p>
              </div>
            ))}
          </div>

          <div className="flex gap-4">
            {/* Queue list */}
            <div className="flex-1 rounded-2xl overflow-hidden" style={{ backgroundColor: C.white, border: `1px solid ${C.border}` }}>
              <div className="px-4 py-2.5 flex items-center justify-between" style={{ backgroundColor: "#F8FAFC", borderBottom: `1px solid ${C.border}` }} dir="rtl">
                <div className="flex gap-2">
                  {["كل العقارات", "عالي الخطر", "تحتاج صور"].map((t, i) => (
                    <button key={i} className="px-2 py-1 rounded-lg text-xs font-bold"
                      style={{ backgroundColor: i === 0 ? C.teal : "transparent", color: i === 0 ? C.white : C.gray }}>{t}</button>
                  ))}
                </div>
                <p className="font-black text-xs" style={{ color: C.navy }}>قائمة العقارات المعلقة</p>
              </div>
              {[
                { t: "شقة مفروشة، مدينة نصر", owner: "أحمد محمد", risk: "عالي", riskColor: C.red, photos: 6, docs: "مكتملة", sent: "منذ 2 ساعة" },
                { t: "ستوديو، التجمع الخامس", owner: "منى علي", risk: "متوسط", riskColor: C.amber, photos: 4, docs: "ناقصة", sent: "منذ 4 ساعات" },
                { t: "غرفة، المعادي", owner: "كريم سالم", risk: "منخفض", riskColor: C.green, photos: 9, docs: "مكتملة", sent: "منذ 6 ساعات" },
                { t: "شقة، المهندسين", owner: "نادر طارق", risk: "عالي", riskColor: C.red, photos: 3, docs: "ناقصة", sent: "منذ يوم" },
              ].map((r, i) => (
                <div key={i} className="flex items-center gap-3 px-4 py-3" style={{ borderBottom: `1px solid ${C.border}` }} dir="rtl">
                  <div className="w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0" style={{ backgroundColor: "#E2E8F0" }}>
                    <Building2 size={14} style={{ color: "#94A3B8" }} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-xs font-black truncate" style={{ color: C.navy }}>{r.t}</p>
                    <p style={{ fontSize: 10, color: C.gray }}>{r.owner} · {r.photos} صور · {r.sent}</p>
                  </div>
                  <span className="text-xs font-bold px-2 py-0.5 rounded-full flex-shrink-0"
                    style={{ backgroundColor: r.risk === "عالي" ? C.redLight : r.risk === "متوسط" ? C.amberLight : C.greenLight, color: r.riskColor }}>{r.risk} الخطر</span>
                  <button className="px-2 py-1 rounded-lg text-xs font-black text-white flex-shrink-0" style={{ backgroundColor: C.teal }}>مراجعة</button>
                </div>
              ))}
            </div>

            {/* Moderation checklist panel */}
            <div style={{ width: 240 }}>
              <div className="p-4 rounded-2xl mb-3" style={{ backgroundColor: C.white, border: `1px solid ${C.border}` }} dir="rtl">
                <p className="font-black text-sm mb-3" style={{ color: C.navy }}>قائمة التحقق — شقة مدينة نصر</p>
                {[
                  { l: "صور واضحة (9-10 صور)", ok: false },
                  { l: "عنوان العقار مكتمل", ok: true },
                  { l: "السعر منطقي للمنطقة", ok: true },
                  { l: "لا يوجد رقم هاتف في الصور", ok: false },
                  { l: "وصف غير مضلل", ok: true },
                  { l: "بيانات المالك موثّقة", ok: true },
                  { l: "الموقع الجغرافي صحيح", ok: true },
                ].map(({ l, ok }, i) => (
                  <div key={i} className="flex items-center gap-2 py-1.5" style={{ borderBottom: i < 6 ? `1px solid ${C.border}` : "none" }}>
                    <div className="w-4 h-4 rounded flex items-center justify-center flex-shrink-0"
                      style={{ backgroundColor: ok ? C.teal : C.redLight, border: `1px solid ${ok ? C.teal : C.red}` }}>
                      {ok ? <Check size={9} style={{ color: C.white }} /> : <X size={9} style={{ color: C.red }} />}
                    </div>
                    <span style={{ fontSize: 10, color: ok ? C.navy : C.red }}>{l}</span>
                  </div>
                ))}
                <div className="mt-3">
                  <p className="font-black text-xs mb-1" style={{ color: C.navy }}>Risk Flags:</p>
                  <div className="flex flex-col gap-1">
                    {["رقم هاتف محتمل في صورة 3", "عدد الصور أقل من المطلوب"].map((f, i) => (
                      <div key={i} className="flex items-center gap-1.5 px-2 py-1 rounded-lg" style={{ backgroundColor: C.redLight }}>
                        <AlertTriangle size={9} style={{ color: C.red }} />
                        <span style={{ fontSize: 9, color: C.red }}>{f}</span>
                      </div>
                    ))}
                  </div>
                </div>
                <div className="flex flex-col gap-2 mt-3">
                  <button className="w-full py-2 rounded-xl text-xs font-black text-white" style={{ backgroundColor: C.green }}>قبول العقار ✓</button>
                  <button className="w-full py-2 rounded-xl text-xs font-black text-white" style={{ backgroundColor: C.red }}>رفض ✗</button>
                  <button className="w-full py-2 rounded-xl text-xs font-black" style={{ backgroundColor: C.amberLight, color: C.amber }}>طلب تعديل</button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function AdminUsersFlagQueueScreen() {
  return (
    <div className="flex h-full" style={{ backgroundColor: "#F8FAFC", fontFamily: "Tajawal, sans-serif" }}>
      <AdminSidebar2 active="users" />
      <div className="flex-1 flex flex-col overflow-hidden">
        <AdminTopBar title="إدارة المستخدمين — طابور البلاغات" />
        <div className="flex-1 overflow-y-auto p-4">
          <div className="flex items-center justify-between mb-4" dir="rtl">
            <div className="flex gap-2">
              {["بلاغات نشطة (31)", "موقوف مؤقتاً", "محظور نهائياً"].map((t, i) => (
                <button key={i} className="px-3 py-1.5 rounded-xl text-xs font-bold"
                  style={{ backgroundColor: i === 0 ? C.red : C.white, color: i === 0 ? C.white : C.navy, border: `1px solid ${i === 0 ? C.red : C.border}` }}>{t}</button>
              ))}
            </div>
            <div className="flex items-center gap-2">
              <div className="flex items-center px-3 py-1.5 rounded-xl gap-2" style={{ backgroundColor: C.white, border: `1px solid ${C.border}` }}>
                <Search size={12} style={{ color: C.gray }} />
                <input placeholder="بحث…" dir="rtl" readOnly className="text-xs outline-none" style={{ width: 100 }} />
              </div>
            </div>
          </div>

          {/* Automated flag info banner */}
          <div className="flex items-center gap-2 px-4 py-3 rounded-2xl mb-4" style={{ backgroundColor: "#FFF8E7", border: `1px solid ${C.amber}30` }} dir="rtl">
            <Shield size={14} style={{ color: C.amber }} />
            <p className="text-xs font-medium flex-1" style={{ color: "#92400E" }}>
              النظام الآلي يكشف البريد المزعج والاحتيال واللغة المسيئة. كل البلاغات تحتاج مراجعة بشرية قبل اتخاذ إجراء.
            </p>
          </div>

          <div className="rounded-2xl overflow-hidden" style={{ backgroundColor: C.white, border: `1px solid ${C.border}` }}>
            <div className="grid px-4 py-2.5 text-xs font-black" style={{ backgroundColor: "#F8FAFC", color: C.gray, gridTemplateColumns: "2fr 1fr 1.5fr 1fr 1fr 1fr 1.5fr" }} dir="rtl">
              {["المستخدم المُبلَّغ عنه", "النوع", "سبب البلاغ", "المُبلِّغ", "تاريخ", "الأتمتة", "إجراء"].map((h, i) => (
                <div key={i} className="text-right">{h}</div>
              ))}
            </div>
            {[
              { n: "كريم طارق سالم", t: "مالك", reason: "احتيال محتمل", reporter: "سارة أحمد", date: "منذ 1 ساعة", auto: "عالي", autoColor: C.red },
              { n: "محمود حسن", t: "مستأجر", reason: "لغة مسيئة", reporter: "النظام الآلي", date: "منذ 3 ساعات", auto: "تلقائي", autoColor: C.amber },
              { n: "نورا عمر", t: "مستأجر", reason: "معلومات مضللة", reporter: "خالد فاروق", date: "منذ 5 ساعات", auto: "منخفض", autoColor: C.green },
              { n: "طارق محمد", t: "مالك", reason: "رقم هاتف ظاهر", reporter: "النظام الآلي", date: "أمس", auto: "تلقائي", autoColor: C.amber },
            ].map((r, i) => (
              <div key={i} className="grid px-4 py-3 items-center" style={{ borderTop: `1px solid ${C.border}`, gridTemplateColumns: "2fr 1fr 1.5fr 1fr 1fr 1fr 1.5fr" }} dir="rtl">
                <div className="flex items-center gap-2">
                  <div className="w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0" style={{ backgroundColor: C.redLight }}>
                    <User size={10} style={{ color: C.red }} />
                  </div>
                  <span className="text-xs font-black truncate" style={{ color: C.navy }}>{r.n}</span>
                </div>
                <div><span className="text-xs px-1.5 py-0.5 rounded-full font-bold" style={{ backgroundColor: r.t === "مالك" ? C.goldLight : C.blueLight, color: r.t === "مالك" ? C.gold : C.blue }}>{r.t}</span></div>
                <div className="text-xs" style={{ color: C.navy }}>{r.reason}</div>
                <div className="text-xs" style={{ color: C.gray }}>{r.reporter}</div>
                <div className="text-xs" style={{ color: C.gray }}>{r.date}</div>
                <div><span className="text-xs px-1.5 py-0.5 rounded-full font-bold" style={{ backgroundColor: r.auto === "عالي" ? C.redLight : r.auto === "تلقائي" ? C.amberLight : C.greenLight, color: r.autoColor }}>{r.auto}</span></div>
                <div className="flex gap-1">
                  <button className="px-2 py-1 rounded-lg text-xs font-black text-white" style={{ backgroundColor: C.teal }}>مراجعة</button>
                  <button className="px-2 py-1 rounded-lg text-xs font-black text-white" style={{ backgroundColor: C.red }}>إيقاف</button>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

function AdminReportsTicketsScreen() {
  return (
    <div className="flex h-full" style={{ backgroundColor: "#F8FAFC", fontFamily: "Tajawal, sans-serif" }}>
      <AdminSidebar2 active="reports" />
      <div className="flex-1 flex flex-col overflow-hidden">
        <AdminTopBar title="التقارير والتذاكر" />
        <div className="flex-1 overflow-y-auto p-4">
          <div className="grid grid-cols-4 gap-3 mb-4">
            {[{ l: "تذاكر مفتوحة", n: "31", c: C.red }, { l: "حُلّت اليوم", n: "18", c: C.green }, { l: "خلافات نشطة", n: "7", c: C.amber }, { l: "متوسط وقت الحل", n: "4.2 ساعة", c: C.blue }].map(({ l, n, c }, i) => (
              <div key={i} className="p-3 rounded-2xl text-center" style={{ backgroundColor: C.white, border: `1px solid ${C.border}` }}>
                <p className="text-2xl font-black" style={{ color: c }}>{n}</p>
                <p className="text-xs" style={{ color: C.gray }}>{l}</p>
              </div>
            ))}
          </div>

          <div className="flex gap-4">
            {/* Tickets table */}
            <div className="flex-1 rounded-2xl overflow-hidden" style={{ backgroundColor: C.white, border: `1px solid ${C.border}` }}>
              <div className="px-4 py-2.5 flex items-center justify-between" style={{ backgroundColor: "#F8FAFC", borderBottom: `1px solid ${C.border}` }} dir="rtl">
                <div className="flex gap-2">
                  {["كل التذاكر", "خلافات", "بلاغات عقارات", "بلاغات مستخدمين"].map((t, i) => (
                    <button key={i} className="px-2 py-1 rounded-lg text-xs font-bold"
                      style={{ backgroundColor: i === 0 ? C.teal : "transparent", color: i === 0 ? C.white : C.gray }}>{t}</button>
                  ))}
                </div>
                <p className="font-black text-xs" style={{ color: C.navy }}>Ticket ID · سجل التذاكر</p>
              </div>
              <div className="grid px-4 py-2 text-xs font-black" style={{ backgroundColor: "#F8FAFC", color: C.gray, gridTemplateColumns: "1fr 2fr 1.5fr 1fr 1fr 1fr", borderBottom: `1px solid ${C.border}` }} dir="rtl">
                {["Ticket ID", "الموضوع", "المُبلِّغ", "النوع", "الحالة", "المراجع"].map(h => <div key={h} className="text-right">{h}</div>)}
              </div>
              {[
                { id: "TKT-0081", subject: "مالك رفض رد الأمانة", reporter: "سارة أحمد", type: "خلاف", status: "مفتوح", reviewer: "أحمد العدل", statusColor: C.red },
                { id: "TKT-0080", subject: "رقم هاتف ظاهر في صور عقار", reporter: "النظام الآلي", type: "بلاغ عقار", status: "قيد المراجعة", reviewer: "سلمى رشدي", statusColor: C.amber },
                { id: "TKT-0079", subject: "مستخدم يرسل رسائل مسيئة", reporter: "محمد علي", type: "بلاغ مستخدم", status: "محلول", reviewer: "سلمى رشدي", statusColor: C.green },
                { id: "TKT-0078", subject: "عقار غير موجود فعلياً", reporter: "نورا كمال", type: "بلاغ عقار", status: "مغلق", reviewer: "أحمد العدل", statusColor: C.gray },
              ].map((r, i) => (
                <div key={i} className="grid px-4 py-3 items-center text-xs" style={{ borderTop: `1px solid ${C.border}`, gridTemplateColumns: "1fr 2fr 1.5fr 1fr 1fr 1fr" }} dir="rtl">
                  <span className="font-black" style={{ color: C.teal }}>{r.id}</span>
                  <span className="truncate" style={{ color: C.navy }}>{r.subject}</span>
                  <span style={{ color: C.gray }}>{r.reporter}</span>
                  <span className="px-1.5 py-0.5 rounded-full font-bold" style={{ backgroundColor: C.bg, color: C.gray, fontSize: 10 }}>{r.type}</span>
                  <span className="font-bold" style={{ color: r.statusColor }}>{r.status}</span>
                  <span style={{ color: C.gray, fontSize: 10 }}>{r.reviewer}</span>
                </div>
              ))}
            </div>

            {/* Dispute Reason breakdown */}
            <div style={{ width: 200 }}>
              <div className="p-4 rounded-2xl mb-3" style={{ backgroundColor: C.white, border: `1px solid ${C.border}` }} dir="rtl">
                <p className="font-black text-xs mb-3" style={{ color: C.navy }}>Dispute Reason — توزيع أسباب الخلافات</p>
                {[
                  { l: "رد الأمانة", n: 12, p: 100, c: C.red },
                  { l: "دقة المعلومات", n: 8, p: 67, c: C.amber },
                  { l: "إلغاء الزيارة", n: 6, p: 50, c: C.blue },
                  { l: "التواصل", n: 5, p: 42, c: C.teal },
                ].map(({ l, n, p, c }, i) => (
                  <div key={i} className="mb-2.5">
                    <div className="flex justify-between text-xs mb-1">
                      <span className="font-bold" style={{ color: C.navy }}>{n} حالة</span>
                      <span style={{ color: C.gray }}>{l}</span>
                    </div>
                    <div className="h-1.5 rounded-full" style={{ backgroundColor: "#E5E7EB" }}>
                      <div className="h-full rounded-full" style={{ width: `${p}%`, backgroundColor: c }} />
                    </div>
                  </div>
                ))}
              </div>
              {/* Booking Log */}
              <div className="p-4 rounded-2xl" style={{ backgroundColor: C.white, border: `1px solid ${C.border}` }} dir="rtl">
                <p className="font-black text-xs mb-3" style={{ color: C.navy }}>Booking Log — سجل الحجوزات</p>
                {[
                  { id: "BK-441", prop: "شقة نصر", status: "مكتمل", c: C.green },
                  { id: "BK-440", prop: "ستوديو تجمع", status: "ملغي", c: C.red },
                  { id: "BK-439", prop: "غرفة معادي", status: "مكتمل", c: C.green },
                ].map((b, i) => (
                  <div key={i} className="flex justify-between items-center py-1.5" style={{ borderBottom: i < 2 ? `1px solid ${C.border}` : "none" }}>
                    <span className="text-xs font-bold" style={{ color: b.c }}>{b.status}</span>
                    <div className="text-right">
                      <p style={{ fontSize: 10, color: C.navy, fontWeight: 700 }}>{b.id}</p>
                      <p style={{ fontSize: 10, color: C.gray }}>{b.prop}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function AdminRolesManagementScreen() {
  return (
    <div className="flex h-full" style={{ backgroundColor: "#F8FAFC", fontFamily: "Tajawal, sans-serif" }}>
      <AdminSidebar2 active="roles" />
      <div className="flex-1 flex flex-col overflow-hidden">
        <AdminTopBar title="إدارة أدوار المشرفين" />
        <div className="flex-1 overflow-y-auto p-4">
          <div className="grid grid-cols-2 gap-4 mb-4">
            {/* Roles definitions */}
            <div className="p-4 rounded-2xl" style={{ backgroundColor: C.white, border: `1px solid ${C.border}` }} dir="rtl">
              <p className="font-black text-sm mb-3" style={{ color: C.navy }}>الأدوار والصلاحيات</p>
              {[
                { role: "مالك النظام", perms: ["كل الصلاحيات"], color: C.teal, n: 1 },
                { role: "مشرف رئيسي", perms: ["KYC", "عقارات", "مستخدمون", "تقارير"], color: C.blue, n: 2 },
                { role: "مراجع KYC", perms: ["KYC فقط"], color: C.green, n: 3 },
                { role: "مراجع عقارات", perms: ["عقارات فقط"], color: C.amber, n: 2 },
                { role: "دعم العملاء", perms: ["تذاكر دعم"], color: C.gray, n: 4 },
              ].map(({ role, perms, color, n }, i) => (
                <div key={i} className="flex items-center gap-3 py-2.5" style={{ borderBottom: i < 4 ? `1px solid ${C.border}` : "none" }}>
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-0.5">
                      <div className="w-2 h-2 rounded-full flex-shrink-0" style={{ backgroundColor: color }} />
                      <span className="text-xs font-black" style={{ color: C.navy }}>{role}</span>
                    </div>
                    <div className="flex gap-1">
                      {perms.map((p, pi) => (
                        <span key={pi} className="text-xs px-1.5 py-0.5 rounded-full" style={{ backgroundColor: C.bg, color: C.gray }}>{p}</span>
                      ))}
                    </div>
                  </div>
                  <div className="text-center">
                    <p className="font-black text-base" style={{ color: C.navy }}>{n}</p>
                    <p style={{ fontSize: 10, color: C.gray }}>مستخدم</p>
                  </div>
                  <button className="px-2 py-1 rounded-lg text-xs font-bold" style={{ backgroundColor: C.bg, color: C.teal }}>تعديل</button>
                </div>
              ))}
            </div>

            {/* Current admins list */}
            <div className="p-4 rounded-2xl" style={{ backgroundColor: C.white, border: `1px solid ${C.border}` }} dir="rtl">
              <div className="flex items-center justify-between mb-3">
                <button className="flex items-center gap-1 px-2 py-1 rounded-xl text-xs font-bold" style={{ backgroundColor: C.tealLight, color: C.teal }}>
                  <Plus size={11} />دعوة مشرف
                </button>
                <p className="font-black text-sm" style={{ color: C.navy }}>المشرفون الحاليون</p>
              </div>
              {[
                { name: "أحمد العدل", email: "ahmed@sokoon.eg", role: "مشرف رئيسي", color: C.blue, active: true, lastSeen: "الآن" },
                { name: "سلمى رشدي", email: "salma@sokoon.eg", role: "مراجع KYC", color: C.green, active: true, lastSeen: "منذ 5 دق" },
                { name: "كريم فاروق", email: "karim@sokoon.eg", role: "مراجع عقارات", color: C.amber, active: false, lastSeen: "أمس" },
                { name: "دينا حسام", email: "dina@sokoon.eg", role: "دعم العملاء", color: C.gray, active: true, lastSeen: "منذ 20 دق" },
              ].map((a, i) => (
                <div key={i} className="flex items-center gap-3 py-2.5" style={{ borderBottom: i < 3 ? `1px solid ${C.border}` : "none" }}>
                  <div className="relative">
                    <div className="w-9 h-9 rounded-full flex items-center justify-center" style={{ backgroundColor: a.color + "20" }}>
                      <User size={16} style={{ color: a.color }} />
                    </div>
                    <div className="absolute -bottom-0.5 -right-0.5 w-3 h-3 rounded-full border-2 border-white" style={{ backgroundColor: a.active ? C.green : "#D1D5DB" }} />
                  </div>
                  <div className="flex-1">
                    <p className="text-xs font-black" style={{ color: C.navy }}>{a.name}</p>
                    <p style={{ fontSize: 10, color: C.gray }}>{a.role} · {a.lastSeen}</p>
                  </div>
                  <div className="flex gap-1">
                    <button className="px-2 py-1 rounded-lg text-xs font-bold" style={{ backgroundColor: C.bg, color: C.teal }}>تعديل الدور</button>
                    <button className="px-2 py-1 rounded-lg text-xs font-bold" style={{ backgroundColor: C.redLight, color: C.red }}>حذف</button>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Permissions matrix */}
          <div className="p-4 rounded-2xl" style={{ backgroundColor: C.white, border: `1px solid ${C.border}` }} dir="rtl">
            <p className="font-black text-sm mb-3" style={{ color: C.navy }}>مصفوفة الصلاحيات</p>
            <div className="overflow-x-auto">
              <table className="w-full text-xs" style={{ borderCollapse: "collapse" }}>
                <thead>
                  <tr style={{ backgroundColor: "#F8FAFC" }}>
                    <th className="text-right px-3 py-2 font-black" style={{ color: C.navy, borderBottom: `1px solid ${C.border}` }}>الإجراء</th>
                    {["مالك النظام", "مشرف رئيسي", "مراجع KYC", "مراجع عقارات", "دعم"].map(r => (
                      <th key={r} className="text-center px-3 py-2 font-bold" style={{ color: C.gray, borderBottom: `1px solid ${C.border}` }}>{r}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {[
                    { action: "مراجعة KYC", perms: [true, true, true, false, false] },
                    { action: "قبول/رفض عقارات", perms: [true, true, false, true, false] },
                    { action: "إيقاف مستخدم", perms: [true, true, false, false, false] },
                    { action: "حل التذاكر", perms: [true, true, false, false, true] },
                    { action: "تعديل الأدوار", perms: [true, false, false, false, false] },
                  ].map(({ action, perms }, i) => (
                    <tr key={i} style={{ borderBottom: `1px solid ${C.border}` }}>
                      <td className="px-3 py-2 font-bold text-right" style={{ color: C.navy }}>{action}</td>
                      {perms.map((p, pi) => (
                        <td key={pi} className="px-3 py-2 text-center">
                          {p ? <Check size={14} style={{ color: C.green, margin: "0 auto" }} /> : <X size={12} style={{ color: "#D1D5DB", margin: "0 auto" }} />}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function AdminSystemMonitorScreen() {
  return (
    <div className="flex h-full" style={{ backgroundColor: "#F8FAFC", fontFamily: "Tajawal, sans-serif" }}>
      <AdminSidebar2 active="system" />
      <div className="flex-1 flex flex-col overflow-hidden">
        <AdminTopBar title="صحة النظام وسجل التدقيق" />
        <div className="flex-1 overflow-y-auto p-4">
          {/* System health cards */}
          <div className="grid grid-cols-4 gap-3 mb-4">
            {[
              { l: "وقت التشغيل", n: "99.8%", I: TrendingUp, c: C.green, bg: C.greenLight, sub: "آخر 30 يوم" },
              { l: "وقت الاستجابة", n: "142ms", I: RefreshCw, c: C.teal, bg: C.tealLight, sub: "متوسط API" },
              { l: "أخطاء اليوم", n: "3", I: AlertTriangle, c: C.amber, bg: C.amberLight, sub: "أخطاء 5xx" },
              { l: "قاعدة البيانات", n: "طبيعي", I: CheckCircle, c: C.green, bg: C.greenLight, sub: "اتصال مستقر" },
            ].map(({ l, n, I, c, bg, sub }, i) => (
              <div key={i} className="p-4 rounded-2xl" style={{ backgroundColor: C.white, border: `1px solid ${C.border}` }} dir="rtl">
                <div className="flex items-center gap-2 mb-2">
                  <div className="w-8 h-8 rounded-xl flex items-center justify-center" style={{ backgroundColor: bg }}><I size={15} style={{ color: c }} /></div>
                </div>
                <p className="text-2xl font-black" style={{ color: C.navy }}>{n}</p>
                <p className="text-xs font-bold" style={{ color: C.navy }}>{l}</p>
                <p style={{ fontSize: 10, color: C.gray }}>{sub}</p>
              </div>
            ))}
          </div>

          <div className="grid grid-cols-2 gap-4">
            {/* Audit Log */}
            <div className="p-4 rounded-2xl" style={{ backgroundColor: C.white, border: `1px solid ${C.border}` }} dir="rtl">
              <div className="flex items-center justify-between mb-3">
                <button className="text-xs font-bold" style={{ color: C.teal }}>تصدير السجل</button>
                <p className="font-black text-sm" style={{ color: C.navy }}>سجل التدقيق — Admin Actions</p>
              </div>
              {[
                { action: "اعتماد توثيق سارة أحمد", admin: "سلمى رشدي", time: "09:41:23", type: "KYC", c: C.green },
                { action: "رفض عقار كريم سالم", admin: "أحمد العدل", time: "09:35:10", type: "عقار", c: C.red },
                { action: "إيقاف حساب طارق محمد", admin: "أحمد العدل", time: "09:20:04", type: "مستخدم", c: C.amber },
                { action: "تغيير دور دينا حسام", admin: "أحمد العدل", time: "09:10:55", type: "دور", c: C.blue },
                { action: "حل تذكرة TKT-0079", admin: "سلمى رشدي", time: "08:55:30", type: "تذكرة", c: C.teal },
                { action: "رفض بلاغ على شقة المعادي", admin: "كريم فاروق", time: "08:44:18", type: "بلاغ", c: C.gray },
              ].map((a, i) => (
                <div key={i} className="flex items-center gap-2 py-2" style={{ borderBottom: i < 5 ? `1px solid ${C.border}` : "none" }}>
                  <span style={{ fontSize: 10, color: C.gray, flexShrink: 0, fontFamily: "monospace" }}>{a.time}</span>
                  <span className="text-xs px-1.5 py-0.5 rounded font-bold flex-shrink-0"
                    style={{ backgroundColor: C.bg, color: a.c, fontSize: 10 }}>{a.type}</span>
                  <span className="text-xs flex-1" style={{ color: C.navy }}>{a.action}</span>
                  <span style={{ fontSize: 10, color: C.gray, flexShrink: 0 }}>{a.admin}</span>
                </div>
              ))}
            </div>

            {/* API health + notes */}
            <div className="flex flex-col gap-3">
              <div className="p-4 rounded-2xl" style={{ backgroundColor: C.white, border: `1px solid ${C.border}` }} dir="rtl">
                <p className="font-black text-sm mb-3" style={{ color: C.navy }}>أداء API — الساعة الأخيرة</p>
                <div className="flex items-end gap-0.5 justify-between mb-2" style={{ height: 60 }}>
                  {[70, 85, 60, 90, 75, 100, 80, 65, 88, 72, 95, 82, 68, 90, 78, 85, 70, 92, 76, 84].map((h, i) => (
                    <div key={i} className="flex-1 rounded-t-sm" style={{ height: `${h}%`, backgroundColor: h > 85 ? C.green : `${C.teal}40` }} />
                  ))}
                </div>
                <p style={{ fontSize: 10, color: C.gray }}>متوسط وقت استجابة API خلال الساعة الماضية</p>
              </div>
              <div className="p-4 rounded-2xl flex-1" style={{ backgroundColor: C.darkCard, border: `1px solid ${C.darkBorder}` }} dir="rtl">
                <p className="font-black text-sm mb-2 text-white" style={{ fontFamily: "Tajawal, sans-serif" }}>Internal Admin Notes</p>
                {["قاعدة البيانات تعمل بكفاءة 99.8%", "خادم CDN مستقر — لا توجد مشاكل", "النسخ الاحتياطي اليومي: مكتمل 03:00", "تحديث الأمان القادم: الأحد 2:00 ص"].map((n, i) => (
                  <div key={i} className="flex items-start gap-2 mb-2">
                    <Check size={11} style={{ color: C.teal, marginTop: 1, flexShrink: 0 }} />
                    <span style={{ fontSize: 11, color: C.darkMuted, fontFamily: "Tajawal, sans-serif" }}>{n}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════
//  SHARED COMPONENTS SHOWCASE
// ═══════════════════════════════════════════════


function SharedNotificationWidget() {
  return (
    <div className="flex flex-col h-full" style={{ backgroundColor: C.bg }}>
      <StatusBar />
      <div className="flex-1 overflow-y-auto px-5 py-4" dir="rtl">
        <h1 className="text-xl font-black mb-1" style={{ ...TJ, color: C.navy }}>مكوّن الإشعارات</h1>
        <p className="text-xs mb-5" style={{ ...TJ, color: C.gray }}>COMP-01 — مشترك بين المستأجر والمالك</p>

        {/* Bell icon with badge */}
        <Card className="mb-4">
          <p className="font-black text-sm mb-3" style={{ ...TJ, color: C.gray }}>حالات أيقونة الجرس</p>
          <div className="flex items-center gap-6 justify-center py-3">
            {[{ n: 0, label: "بدون إشعار" }, { n: 3, label: "3 جديد" }, { n: 99, label: "+99" }].map(({ n, label }, i) => (
              <div key={i} className="flex flex-col items-center gap-2">
                <div className="relative w-10 h-10 rounded-full flex items-center justify-center" style={{ backgroundColor: C.white, border: `1px solid ${C.border}` }}>
                  <Bell size={18} style={{ color: n > 0 ? C.navy : "#9CA3AF" }} />
                  {n > 0 && (
                    <span className="absolute -top-1 -right-1 min-w-5 h-5 rounded-full flex items-center justify-center text-white font-black"
                      style={{ backgroundColor: C.red, fontSize: 9, padding: "0 4px" }}>{n > 9 ? "+9" : n}</span>
                  )}
                </div>
                <span style={{ fontSize: 10, ...TJ, color: C.gray }}>{label}</span>
              </div>
            ))}
          </div>
        </Card>

        {/* Notification types */}
        <Card className="mb-4">
          <p className="font-black text-sm mb-3" style={{ ...TJ, color: C.gray }}>أنواع الإشعارات</p>
          <div className="flex flex-col gap-2">
            {[
              { bg: C.greenLight, c: C.green, I: CheckCircle, t: "إشعار قبول", sub: "زيارتك تم قبولها" },
              { bg: C.amberLight, c: C.amber, I: Clock, t: "إشعار انتظار", sub: "طلبك قيد المراجعة" },
              { bg: C.redLight, c: C.red, I: AlertCircle, t: "إشعار رفض", sub: "تم رفض طلب التوثيق" },
              { bg: C.blueLight, c: C.blue, I: MessageCircle, t: "إشعار رسالة", sub: "رسالة جديدة من المالك" },
              { bg: C.tealLight, c: C.teal, I: Building2, t: "إشعار عقار", sub: "عقار جديد في منطقتك" },
            ].map(({ bg, c, I, t, sub }, i) => (
              <div key={i} className="flex items-center gap-3 p-3 rounded-2xl"
                style={{ backgroundColor: i === 0 ? C.white : C.bg, border: `1px solid ${i === 0 ? C.border : "transparent"}` }}>
                <div className="w-8 h-8 rounded-xl flex items-center justify-center flex-shrink-0" style={{ backgroundColor: bg }}>
                  <I size={14} style={{ color: c }} />
                </div>
                <div className="flex-1">
                  <p className="text-xs font-black" style={{ ...TJ, color: C.navy }}>{t}</p>
                  <p style={{ fontSize: 10, ...TJ, color: C.gray }}>{sub}</p>
                </div>
                {i === 0 && <div className="w-2 h-2 rounded-full flex-shrink-0" style={{ backgroundColor: C.teal }} />}
              </div>
            ))}
          </div>
        </Card>

        <PrivacyBanner text="إشعارات الزيارات لا تكشف رقم الموبايل" />
      </div>
    </div>
  );
}

function SharedChatInboxWidget() {
  return (
    <div className="flex flex-col h-full" style={{ backgroundColor: C.bg }}>
      <StatusBar />
      <div className="flex-1 overflow-y-auto px-5 py-4" dir="rtl">
        <h1 className="text-xl font-black mb-1" style={{ ...TJ, color: C.navy }}>مكوّن صندوق المحادثات</h1>
        <p className="text-xs mb-5" style={{ ...TJ, color: C.gray }}>COMP-02 — Chat Inbox · مشترك بين المستأجر والمالك</p>

        {/* Chat bubble types */}
        <Card className="mb-4">
          <p className="font-black text-sm mb-3" style={{ ...TJ, color: C.gray }}>أنواع فقاعات الرسائل</p>
          <div className="flex flex-col gap-3">
            <div className="flex justify-end">
              <div className="max-w-xs px-4 py-2.5 text-sm" dir="rtl"
                style={{ backgroundColor: C.teal, color: C.white, ...TJ, borderRadius: "16px 4px 16px 16px" }}>
                رسالة مرسلة (مستخدم حالي)
              </div>
            </div>
            <div className="flex justify-start">
              <div className="max-w-xs px-4 py-2.5 text-sm" dir="rtl"
                style={{ backgroundColor: C.white, color: C.navy, border: `1px solid ${C.border}`, ...TJ, borderRadius: "4px 16px 16px 16px" }}>
                رسالة مستلمة (الطرف الآخر)
              </div>
            </div>
            <div className="flex justify-end">
              <div className="px-4 py-2.5 text-xs flex items-center gap-2" dir="rtl"
                style={{ backgroundColor: C.amberLight, color: "#92400E", ...TJ, borderRadius: "12px", border: `1px solid ${C.amber}30` }}>
                <Lock size={11} />رسالة محظورة — وثّق حسابك أولاً
              </div>
            </div>
          </div>
        </Card>

        {/* Input bar */}
        <Card className="mb-4">
          <p className="font-black text-sm mb-3" style={{ ...TJ, color: C.gray }}>شريط الإدخال</p>
          <div className="flex items-center gap-2">
            <button className="w-9 h-9 rounded-full flex items-center justify-center" style={{ backgroundColor: C.bg }}><Mic size={15} style={{ color: C.gray }} /></button>
            <div className="flex-1 flex items-center px-3 py-2 rounded-2xl gap-2" style={{ backgroundColor: C.bg }}>
              <span className="flex-1 text-sm" style={{ color: "#9CA3AF", ...TJ }}>اكتب رسالة…</span>
              <ImageIcon size={15} style={{ color: C.gray }} />
            </div>
            <button className="w-9 h-9 rounded-full flex items-center justify-center" style={{ backgroundColor: C.teal }}>
              <Send size={15} style={{ color: C.white }} />
            </button>
          </div>
        </Card>

        {/* Privacy note in chat */}
        <Card className="mb-4">
          <p className="font-black text-sm mb-2" style={{ ...TJ, color: C.gray }}>بانر الخصوصية داخل الشات</p>
          <PrivacyBanner text="رقم الموبايل مخفي داخل المحادثة دائماً" />
          <div className="mt-2">
            <div className="flex items-center gap-2 px-4 py-3 rounded-2xl" style={{ backgroundColor: C.greenLight }}>
              <Phone size={13} style={{ color: C.green }} />
              <p className="text-xs font-medium" style={{ ...TJ, color: "#166534" }}>بعد قبول الزيارة — الرقم: 010****432</p>
            </div>
          </div>
        </Card>

        <WarnBanner text="الشات محدود لحد ما توثق حسابك" action="وثّق الآن" />
      </div>
    </div>
  );
}

function SharedVisitRequestWidget() {
  return (
    <div className="flex flex-col h-full" style={{ backgroundColor: C.bg }}>
      <StatusBar />
      <div className="flex-1 overflow-y-auto px-5 py-4" dir="rtl">
        <h1 className="text-xl font-black mb-1" style={{ ...TJ, color: C.navy }}>مكوّن طلبات الزيارة</h1>
        <p className="text-xs mb-5" style={{ ...TJ, color: C.gray }}>COMP-03 — Visit Requests · مشترك بين المستأجر والمالك</p>

        {/* Visit request card - tenant view */}
        <p className="text-xs font-black mb-2" style={{ ...TJ, color: C.blue }}>بطاقة الزيارة — منظور المستأجر</p>
        <Card className="mb-3">
          <div className="flex items-start justify-between mb-3">
            <span className="text-xs font-black px-2 py-1 rounded-full" style={{ backgroundColor: C.greenLight, color: C.green, ...TJ }}>مقبول ✓</span>
            <p className="font-black text-sm" style={{ ...TJ, color: C.navy }}>شقة مفروشة، مدينة نصر</p>
          </div>
          <div className="flex items-center gap-2 mb-2">
            <Calendar size={12} style={{ color: C.teal }} />
            <span className="text-xs" style={{ ...TJ, color: C.gray }}>النهارده 3:00 م</span>
          </div>
          <div className="flex items-center gap-2 mb-3">
            <User size={12} style={{ color: C.gray }} />
            <span className="text-xs" style={{ ...TJ, color: C.gray }}>المالك: أحمد محمد</span>
            <Badge type="verified" />
          </div>
          <PrivacyBanner text="رقمك لسه مخفي حتى يتم الاتفاق" />
          <div className="flex gap-2 mt-3">
            <button className="flex-1 py-2 rounded-xl text-xs font-black" style={{ backgroundColor: C.blueLight, color: C.blue, ...TJ }}>شات</button>
            <button className="flex-1 py-2 rounded-xl text-xs font-black" style={{ backgroundColor: C.redLight, color: C.red, ...TJ }}>إلغاء</button>
            <button className="flex-1 py-2 rounded-xl text-xs font-black" style={{ backgroundColor: C.goldLight, color: C.gold, ...TJ }}>تقييم</button>
          </div>
        </Card>

        {/* Visit request card - owner view */}
        <p className="text-xs font-black mb-2" style={{ ...TJ, color: C.gold }}>بطاقة الزيارة — منظور المالك</p>
        <Card className="mb-3">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-10 h-10 rounded-full flex items-center justify-center" style={{ backgroundColor: C.blueLight }}>
              <User size={18} style={{ color: C.blue }} />
            </div>
            <div className="flex-1">
              <div className="flex items-center gap-2">
                <p className="font-black text-sm" style={{ ...TJ, color: C.navy }}>سارة أحمد</p>
                <Badge type="verified" />
              </div>
              <p className="text-xs" style={{ ...TJ, color: C.gray }}>النهارده 3:00 م · شقة مدينة نصر</p>
            </div>
            <span className="text-xs font-black px-2 py-1 rounded-full" style={{ backgroundColor: C.greenLight, color: C.green, ...TJ }}>جديد</span>
          </div>
          <div className="mb-3">
            <PrivacyBanner text="رقم المستأجر 010****432 — يظهر بعد القبول" />
          </div>
          <div className="flex gap-2">
            <button className="flex-1 py-2 rounded-xl text-xs font-black text-white" style={{ backgroundColor: C.green, ...TJ }}>قبول ✓</button>
            <button className="flex-1 py-2 rounded-xl text-xs font-black" style={{ backgroundColor: C.redLight, color: C.red, ...TJ }}>رفض ✗</button>
            <button className="flex-1 py-2 rounded-xl text-xs font-black" style={{ backgroundColor: C.blueLight, color: C.blue, ...TJ }}>شات</button>
          </div>
        </Card>

        {/* Status chips */}
        <Card>
          <p className="font-black text-sm mb-3" style={{ ...TJ, color: C.gray }}>حالات الزيارة — Status Chips</p>
          <div className="flex flex-wrap gap-2">
            {[
              { l: "جديد", bg: C.tealLight, c: C.teal },
              { l: "مقبول", bg: C.greenLight, c: C.green },
              { l: "مرفوض", bg: C.redLight, c: C.red },
              { l: "بانتظار الرد", bg: C.amberLight, c: C.amber },
              { l: "مكتملة", bg: "#F3F4F6", c: C.gray },
              { l: "ملغاة", bg: C.redLight, c: C.red },
            ].map(({ l, bg, c }, i) => (
              <span key={i} className="px-3 py-1.5 rounded-full text-xs font-black" style={{ backgroundColor: bg, color: c, ...TJ }}>{l}</span>
            ))}
          </div>
        </Card>
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════
//  MISSING SCREENS AUDIT  (checklist frame)
// ═══════════════════════════════════════════════


function MissingScreensAuditScreen() {
  const existing = [
    "T-17 Notifications","T-18 Profile","T-19 My Visits","T-20 Chat List","T-21 Rate & Review","T-22 Settings",
    "T-23 Saved Empty State","T-24 Chat Search","T-25 Report Sheet",
    "O-21 Owner Profile","O-22 More Menu","O-23 Owner Notifications","O-24 Owner Chat List","O-25 Rejection Details","O-26 Visits Dashboard",
    "A-DASH-01 Executive Dashboard","A-USERS-03 Flag Queue","A-INVENTORY-01 Listing Moderation",
    "A-REPORTS-01 Tickets","A-ROLES Roles Mgmt","A-SYSTEM System Monitor",
    "ADMIN-F Main Dashboard","ADMIN-G Users Mgmt","ADMIN-H Properties","ADMIN-I Analytics","ADMIN-J Settings",
  ];
  const missing = [
    "T-SEARCH-01 Search Screen","T-SEARCH-02 Search Results","T-FILTER-01 Filter Sheet",
    "T-PROP-01 Property Detail","T-PROP-02 Photo Gallery","T-PROP-03 Map View",
    "T-VISIT-01 Book Visit","T-VISIT-02 Visit Confirmed","T-VISIT-03 Visit Detail",
    "T-CHAT-01 Chat Thread","T-CHAT-02 Chat Restricted",
    "T-SAVED-02 Saved Listings","T-KYC-01 Start KYC","T-KYC-02 Upload ID","T-KYC-03 KYC Pending","T-KYC-04 KYC Approved",
    "T-SUPPORT-01 Help Center","T-SUPPORT-02 Submit Ticket","T-ONBOARD-01 Onboarding","T-HOME-02 Home Personalized",
    "O-HOME-01 Owner Dashboard","O-PROPERTIES-01 My Listings","O-PROPERTIES-02 Add Property S1",
    "O-PROPERTIES-03 Add Property S2 Photos","O-PROPERTIES-04 Add Property S3 Pricing",
    "O-PROPERTIES-05 Submitted Pending","O-REQUESTS-01 Requests List","O-REQUESTS-02 Request Detail",
    "O-CHAT-01 Chat with Tenant","O-ANALYTICS-01 Property Analytics","O-FINANCE-01 Revenue Overview",
    "O-KYC-01 Owner KYC Upload","O-KYC-02 KYC Status","O-SUPPORT-01 Owner Support",
    "O-ONBOARD-01 Owner Onboarding","O-EDIT-01 Edit Property","O-CALENDAR-01 Availability",
    "A-KYC-01 KYC Queue","A-KYC-02 KYC Review Detail",
    "A-USERS-02 User Profile View","A-USERS-04 Banned Users",
    "A-SUPPORT-01 Support Console","A-SUPPORT-02 Ticket Detail",
    "A-FINANCE-01 Finance Dashboard","A-FINANCE-02 Transaction Log",
    "A-INVENTORY-02 Property Admin View","A-CONTENT-01 Content Moderation",
    "A-NOTIF-01 Push Notifications","A-LOGS-01 Activity Logs",
  ];
  return (
    <div className="flex h-full" style={{ backgroundColor: "#F8FAFC", fontFamily: "Tajawal, sans-serif" }}>
      <div className="flex-1 overflow-y-auto p-5" dir="rtl">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-10 h-10 rounded-2xl flex items-center justify-center" style={{ backgroundColor: C.navy }}>
            <FileText size={18} style={{ color: C.white }} />
          </div>
          <div>
            <h1 className="text-xl font-black" style={{ color: C.navy }}>Missing Screens Audit</h1>
            <p className="text-sm" style={{ color: C.gray }}>مراجعة الشاشات الناقصة</p>
          </div>
        </div>
        <div className="grid grid-cols-3 gap-3 mb-5">
          {[
            { l: "إجمالي الشاشات من PDF", n: "79", c: C.navy, bg: C.bg },
            { l: "شاشات موجودة (قبل الجلسة)", n: "26", c: C.teal, bg: C.tealLight },
            { l: "شاشات تم إنشاؤها الآن", n: `${missing.length}`, c: C.green, bg: C.greenLight },
          ].map(({ l, n, c, bg }, i) => (
            <div key={i} className="p-4 rounded-2xl text-center" style={{ backgroundColor: bg, border: `1px solid ${C.border}` }}>
              <p className="text-3xl font-black mb-1" style={{ color: c }}>{n}</p>
              <p className="text-xs" style={{ color: C.gray }}>{l}</p>
            </div>
          ))}
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div className="p-4 rounded-2xl" style={{ backgroundColor: C.white, border: `1px solid ${C.border}` }}>
            <div className="flex items-center gap-2 mb-3">
              <CheckCircle size={15} style={{ color: C.green }} />
              <p className="font-black text-sm" style={{ color: C.navy }}>شاشات موجودة ({existing.length})</p>
            </div>
            {existing.map((s, i) => (
              <div key={i} className="flex items-center gap-2 py-1.5" style={{ borderBottom: i < existing.length-1 ? `1px solid ${C.border}` : "none" }}>
                <Check size={12} style={{ color: C.green }} />
                <span style={{ fontSize: 11, color: C.gray }}>{s}</span>
              </div>
            ))}
          </div>
          <div className="p-4 rounded-2xl" style={{ backgroundColor: C.white, border: `1px solid ${C.border}` }}>
            <div className="flex items-center gap-2 mb-3">
              <Plus size={15} style={{ color: C.teal }} />
              <p className="font-black text-sm" style={{ color: C.navy }}>شاشات تم إضافتها ({missing.length})</p>
            </div>
            {missing.map((s, i) => (
              <div key={i} className="flex items-center gap-2 py-1.5" style={{ borderBottom: i < missing.length-1 ? `1px solid ${C.border}` : "none" }}>
                <div className="w-3 h-3 rounded-full flex-shrink-0" style={{ backgroundColor: C.teal }} />
                <span style={{ fontSize: 11, color: C.navy }}>{s}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════
//  TENANT MISSING SCREENS — SEARCH & BROWSE
// ═══════════════════════════════════════════════


function AdminKYCQueueScreen() {
  return (
    <div className="flex h-full" style={{ backgroundColor: "#F8FAFC", fontFamily: "Tajawal, sans-serif" }}>
      <AdminSidebar2 active="kyc" />
      <div className="flex-1 flex flex-col overflow-hidden">
        <AdminTopBar title="طابور مراجعة التوثيق KYC" />
        <div className="flex-1 overflow-y-auto p-4">
          <div className="grid grid-cols-4 gap-3 mb-4">
            {[{ l: "انتظار المراجعة", n: "487", c: C.amber }, { l: "مراجع اليوم", n: "124", c: C.teal }, { l: "مقبول اليوم", n: "108", c: C.green }, { l: "مرفوض اليوم", n: "16", c: C.red }].map(({ l, n, c }, i) => (
              <div key={i} className="p-3 rounded-2xl text-center" style={{ backgroundColor: C.white, border: `1px solid ${C.border}` }}>
                <p className="text-2xl font-black" style={{ color: c }}>{n}</p>
                <p className="text-xs" style={{ color: C.gray }}>{l}</p>
              </div>
            ))}
          </div>
          <div className="rounded-2xl overflow-hidden" style={{ backgroundColor: C.white, border: `1px solid ${C.border}` }}>
            <div className="px-4 py-2.5 flex items-center justify-between" style={{ backgroundColor: "#F8FAFC", borderBottom: `1px solid ${C.border}` }} dir="rtl">
              <div className="flex gap-2">
                {["كل الطلبات","ملاك","مستأجرون","مُعلَّق"].map((t, i) => (
                  <button key={i} className="px-2 py-1 rounded-lg text-xs font-bold" style={{ backgroundColor: i===0 ? C.teal : "transparent", color: i===0 ? C.white : C.gray }}>{t}</button>
                ))}
              </div>
              <p className="font-black text-xs" style={{ color: C.navy }}>قائمة طلبات التوثيق</p>
            </div>
            <div className="grid px-4 py-2 text-xs font-black" style={{ backgroundColor: "#F8FAFC", color: C.gray, gridTemplateColumns: "2fr 1fr 1fr 1fr 1.5fr", borderBottom: `1px solid ${C.border}` }} dir="rtl">
              {["المستخدم","النوع","البطاقة","الانتظار","إجراء"].map(h => <div key={h} className="text-right">{h}</div>)}
            </div>
            {[
              { n: "سارة أحمد خالد", t: "مستأجر", id: "29•••12", w: "2 ساعة", flag: false },
              { n: "أحمد محمد إبراهيم", t: "مالك", id: "28•••34", w: "4 ساعات", flag: true },
              { n: "نورا عمر طارق", t: "مستأجر", id: "30•••56", w: "6 ساعات", flag: false },
              { n: "كريم سالم فاروق", t: "مالك", id: "27•••78", w: "8 ساعات", flag: false },
              { n: "منى حسام علي", t: "مستأجر", id: "29•••90", w: "يوم", flag: true },
            ].map((r, i) => (
              <div key={i} className="grid px-4 py-3 items-center" style={{ borderTop: `1px solid ${C.border}`, gridTemplateColumns: "2fr 1fr 1fr 1fr 1.5fr" }} dir="rtl">
                <div className="flex items-center gap-2">
                  <div className="w-7 h-7 rounded-full flex items-center justify-center" style={{ backgroundColor: C.tealLight }}>
                    <User size={12} style={{ color: C.teal }} />
                  </div>
                  <span className="text-xs font-black truncate" style={{ color: C.navy }}>{r.n}</span>
                  {r.flag && <AlertTriangle size={11} style={{ color: C.amber }} />}
                </div>
                <span className="text-xs px-1.5 py-0.5 rounded-full font-bold" style={{ backgroundColor: r.t==="مالك" ? C.goldLight : C.blueLight, color: r.t==="مالك" ? C.gold : C.blue, fontSize:10 }}>{r.t}</span>
                <span className="text-xs" style={{ color: C.gray }}>{r.id}</span>
                <span className="text-xs" style={{ color: C.amber }}>{r.w}</span>
                <div className="flex gap-1">
                  <button className="px-2 py-1 rounded-lg text-xs font-black text-white" style={{ backgroundColor: C.teal }}>مراجعة</button>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

function AdminKYCReviewDetailScreen() {
  return (
    <div className="flex h-full" style={{ backgroundColor: "#F8FAFC", fontFamily: "Tajawal, sans-serif" }}>
      <AdminSidebar2 active="kyc" />
      <div className="flex-1 flex flex-col overflow-hidden">
        <AdminTopBar title="مراجعة توثيق — سارة أحمد خالد" />
        <div className="flex-1 overflow-y-auto p-4">
          <div className="grid grid-cols-3 gap-4">
            {/* User info */}
            <div className="p-4 rounded-2xl" style={{ backgroundColor: C.white, border: `1px solid ${C.border}` }} dir="rtl">
              <p className="font-black text-sm mb-3" style={{ color: C.navy }}>معلومات المستخدم</p>
              <div className="flex items-center gap-3 mb-3 pb-3" style={{ borderBottom: `1px solid ${C.border}` }}>
                <div className="w-12 h-12 rounded-full flex items-center justify-center" style={{ backgroundColor: C.tealLight }}>
                  <User size={22} style={{ color: C.teal }} />
                </div>
                <div>
                  <p className="font-black text-base" style={{ color: C.navy }}>سارة أحمد خالد</p>
                  <p style={{ fontSize: 10, color: C.gray }}>مستأجر · عضو منذ 2024</p>
                  <Badge type="pending" />
                </div>
              </div>
              {[{ l: "رقم الهاتف", v: "01•••••432" }, { l: "البريد", v: "sara@gmail.com" }, { l: "تاريخ التسجيل", v: "1 يناير 2024" }, { l: "عدد الطلبات", v: "3 طلبات زيارة" }].map(({ l, v }, i) => (
                <div key={i} className="flex justify-between py-1.5" style={{ borderBottom: i<3 ? `1px solid ${C.border}` : "none" }}>
                  <span className="text-xs font-bold" style={{ color: C.navy }}>{v}</span>
                  <span style={{ fontSize: 10, color: C.gray }}>{l}</span>
                </div>
              ))}
            </div>
            {/* Documents preview */}
            <div className="p-4 rounded-2xl" style={{ backgroundColor: C.white, border: `1px solid ${C.border}` }} dir="rtl">
              <p className="font-black text-sm mb-3" style={{ color: C.navy }}>المستندات المرفوعة</p>
              {["وجه البطاقة القومية", "ظهر البطاقة القومية", "صورة السيلفي"].map((doc, i) => (
                <div key={i} className="mb-3">
                  <p style={{ fontSize: 10, color: C.gray, marginBottom: 4 }}>{doc}</p>
                  <div className="h-24 rounded-2xl flex items-center justify-center" style={{ backgroundColor: "#E2E8F0" }}>
                    <FileText size={22} style={{ color: "#94A3B8" }} />
                  </div>
                </div>
              ))}
              <div className="flex items-center gap-2 px-3 py-2 rounded-xl" style={{ backgroundColor: C.redLight }}>
                <AlertTriangle size={12} style={{ color: C.red }} />
                <span style={{ fontSize: 10, color: C.red }}>هذه البيانات سرية — للمراجع فقط</span>
              </div>
            </div>
            {/* Actions panel */}
            <div className="flex flex-col gap-3">
              <div className="p-4 rounded-2xl" style={{ backgroundColor: C.white, border: `1px solid ${C.border}` }} dir="rtl">
                <p className="font-black text-sm mb-3" style={{ color: C.navy }}>قرار التوثيق</p>
                <div className="flex flex-col gap-2 mb-3">
                  <button className="w-full py-3 rounded-xl font-black text-white text-sm" style={{ backgroundColor: C.green }}>قبول التوثيق ✓</button>
                  <button className="w-full py-3 rounded-xl font-black text-white text-sm" style={{ backgroundColor: C.red }}>رفض ✗</button>
                  <button className="w-full py-3 rounded-xl font-black text-sm" style={{ backgroundColor: C.amberLight, color: C.amber }}>طلب إعادة رفع</button>
                </div>
                <div>
                  <p style={{ fontSize: 11, color: C.gray, marginBottom: 4 }}>ملاحظات داخلية (اختياري)</p>
                  <textarea readOnly dir="rtl" placeholder="اكتب ملاحظاتك…" className="w-full px-3 py-2 rounded-xl border text-xs outline-none resize-none"
                    style={{ borderColor: C.border, height: 60 }} />
                </div>
              </div>
              <div className="p-4 rounded-2xl" style={{ backgroundColor: C.darkCard, border: `1px solid ${C.darkBorder}` }} dir="rtl">
                <p className="font-black text-xs mb-2 text-white">سجل التوثيق</p>
                {["إرسال الطلب: 9:30 ص", "مراجعة أولية: 9:41 ص", "قيد المراجعة البشرية"].map((l, i) => (
                  <div key={i} className="flex items-center gap-2 py-1">
                    <div className="w-1.5 h-1.5 rounded-full flex-shrink-0" style={{ backgroundColor: i===2 ? C.amber : C.teal }} />
                    <span style={{ fontSize: 10, color: C.darkMuted }}>{l}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════
//  ADMIN MISSING SCREENS — USERS, SUPPORT, FINANCE
// ═══════════════════════════════════════════════

function AdminUserProfileScreen() {
  return (
    <div className="flex h-full" style={{ backgroundColor: "#F8FAFC", fontFamily: "Tajawal, sans-serif" }}>
      <AdminSidebar2 active="users" />
      <div className="flex-1 flex flex-col overflow-hidden">
        <AdminTopBar title="ملف المستخدم — سارة أحمد خالد" />
        <div className="flex-1 overflow-y-auto p-4">
          <div className="grid grid-cols-3 gap-4">
            <div className="p-4 rounded-2xl" style={{ backgroundColor: C.white, border: `1px solid ${C.border}` }} dir="rtl">
              <div className="flex flex-col items-center mb-4 pb-4" style={{ borderBottom: `1px solid ${C.border}` }}>
                <div className="w-16 h-16 rounded-full flex items-center justify-center mb-2" style={{ backgroundColor: C.tealLight }}>
                  <User size={28} style={{ color: C.teal }} />
                </div>
                <p className="font-black text-base" style={{ color: C.navy }}>سارة أحمد خالد</p>
                <Badge type="verified" />
                <span className="text-xs mt-1" style={{ color: C.gray }}>مستأجر</span>
              </div>
              {[{ l: "رقم الهاتف (admin)", v: "01012345432" }, { l: "البريد الإلكتروني", v: "sara@gmail.com" }, { l: "تاريخ الانضمام", v: "1 يناير 2024" }, { l: "آخر نشاط", v: "منذ 5 دقائق" }, { l: "توثيق الهوية", v: "موثّق ✓" }].map(({ l, v }, i) => (
                <div key={i} className="flex justify-between py-2" style={{ borderBottom: i<4 ? `1px solid ${C.border}` : "none" }}>
                  <span className="text-xs font-bold" style={{ color: C.navy }}>{v}</span>
                  <span style={{ fontSize: 10, color: C.gray }}>{l}</span>
                </div>
              ))}
            </div>
            <div className="col-span-2 flex flex-col gap-3">
              <div className="grid grid-cols-3 gap-3">
                {[{ l: "طلبات زيارة", n: "12", c: C.teal }, { l: "تقييمات", n: "4.7★", c: C.amber }, { l: "بلاغات ضده", n: "0", c: C.green }].map(({ l, n, c }, i) => (
                  <div key={i} className="p-3 rounded-2xl text-center" style={{ backgroundColor: C.white, border: `1px solid ${C.border}` }}>
                    <p className="text-2xl font-black" style={{ color: c }}>{n}</p>
                    <p style={{ fontSize: 10, color: C.gray }}>{l}</p>
                  </div>
                ))}
              </div>
              <div className="p-4 rounded-2xl" style={{ backgroundColor: C.white, border: `1px solid ${C.border}` }} dir="rtl">
                <p className="font-black text-sm mb-3" style={{ color: C.navy }}>سجل النشاط</p>
                {[
                  { a: "حجز زيارة — شقة مدينة نصر", t: "اليوم 9:30 ص", I: Calendar, c: C.teal },
                  { a: "تم توثيق الهوية", t: "أمس 3:00 م", I: CheckCircle, c: C.green },
                  { a: "إرسال رسالة للمالك أحمد", t: "أمس 2:45 م", I: MessageCircle, c: C.blue },
                  { a: "حفظ عقار ستوديو التجمع", t: "الأحد 10:00 ص", I: Heart, c: C.red },
                ].map((a, i) => (
                  <div key={i} className="flex items-center gap-3 py-2" style={{ borderBottom: i<3 ? `1px solid ${C.border}` : "none" }}>
                    <div className="w-7 h-7 rounded-lg flex items-center justify-center flex-shrink-0" style={{ backgroundColor: a.c + "20" }}>
                      <a.I size={12} style={{ color: a.c }} />
                    </div>
                    <span className="flex-1 text-xs" style={{ color: C.navy }}>{a.a}</span>
                    <span style={{ fontSize: 10, color: C.gray }}>{a.t}</span>
                  </div>
                ))}
              </div>
              <div className="flex gap-3">
                <button className="flex-1 py-2.5 rounded-xl font-black text-xs text-white" style={{ backgroundColor: C.amber }}>تحذير</button>
                <button className="flex-1 py-2.5 rounded-xl font-black text-xs text-white" style={{ backgroundColor: C.red }}>إيقاف مؤقت</button>
                <button className="flex-1 py-2.5 rounded-xl font-black text-xs" style={{ backgroundColor: C.bg, color: C.gray, border: `1px solid ${C.border}` }}>تصدير البيانات</button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function AdminBannedUsersScreen() {
  return (
    <div className="flex h-full" style={{ backgroundColor: "#F8FAFC", fontFamily: "Tajawal, sans-serif" }}>
      <AdminSidebar2 active="users" />
      <div className="flex-1 flex flex-col overflow-hidden">
        <AdminTopBar title="المستخدمون الموقوفون والمحظورون" />
        <div className="flex-1 overflow-y-auto p-4">
          <div className="grid grid-cols-3 gap-3 mb-4">
            {[{ l: "موقوف مؤقتاً", n: "43", c: C.amber }, { l: "محظور نهائياً", n: "12", c: C.red }, { l: "بانتظار القرار", n: "8", c: C.blue }].map(({ l, n, c }, i) => (
              <div key={i} className="p-3 rounded-2xl text-center" style={{ backgroundColor: C.white, border: `1px solid ${C.border}` }}>
                <p className="text-2xl font-black" style={{ color: c }}>{n}</p>
                <p className="text-xs" style={{ color: C.gray }}>{l}</p>
              </div>
            ))}
          </div>
          <div className="rounded-2xl overflow-hidden" style={{ backgroundColor: C.white, border: `1px solid ${C.border}` }}>
            <div className="px-4 py-2.5 flex items-center justify-between" style={{ backgroundColor: "#F8FAFC", borderBottom: `1px solid ${C.border}` }} dir="rtl">
              <div className="flex gap-2">
                {["الكل","موقوف مؤقتاً","محظور"].map((t, i) => (
                  <button key={i} className="px-2 py-1 rounded-lg text-xs font-bold" style={{ backgroundColor: i===0 ? C.red : "transparent", color: i===0 ? C.white : C.gray }}>{t}</button>
                ))}
              </div>
              <p className="font-black text-xs" style={{ color: C.navy }}>قائمة المستخدمين الموقوفين</p>
            </div>
            {[
              { n: "طارق محمد علي", t: "مالك", reason: "لغة مسيئة", status: "موقوف", date: "3 يونيو", admin: "أحمد العدل" },
              { n: "كريم سالم", t: "مستأجر", reason: "احتيال", status: "محظور", date: "1 يونيو", admin: "سلمى رشدي" },
              { n: "هدى محمود", t: "مستأجر", reason: "معلومات مضللة", status: "موقوف", date: "28 مايو", admin: "أحمد العدل" },
            ].map((r, i) => (
              <div key={i} className="flex items-center gap-3 px-4 py-3" style={{ borderTop: `1px solid ${C.border}` }} dir="rtl">
                <div className="w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0" style={{ backgroundColor: C.redLight }}>
                  <User size={14} style={{ color: C.red }} />
                </div>
                <div className="flex-1">
                  <p className="text-xs font-black" style={{ color: C.navy }}>{r.n}</p>
                  <p style={{ fontSize: 10, color: C.gray }}>{r.reason} · {r.date} · بواسطة {r.admin}</p>
                </div>
                <span className="text-xs px-2 py-0.5 rounded-full font-bold"
                  style={{ backgroundColor: r.status==="محظور" ? C.redLight : C.amberLight, color: r.status==="محظور" ? C.red : C.amber }}>{r.status}</span>
                <div className="flex gap-1">
                  <button className="px-2 py-1 rounded-lg text-xs font-bold text-white" style={{ backgroundColor: C.green }}>رفع الإيقاف</button>
                  <button className="px-2 py-1 rounded-lg text-xs font-bold" style={{ backgroundColor: C.bg, color: C.gray }}>عرض</button>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

function AdminSupportConsoleScreen() {
  return (
    <div className="flex h-full" style={{ backgroundColor: "#F8FAFC", fontFamily: "Tajawal, sans-serif" }}>
      <AdminSidebar2 active="reports" />
      <div className="flex-1 flex flex-col overflow-hidden">
        <AdminTopBar title="دعم العملاء — تذاكر الدعم" />
        <div className="flex-1 overflow-y-auto p-4">
          <div className="grid grid-cols-4 gap-3 mb-4">
            {[{ l: "مفتوحة", n: "31", c: C.red }, { l: "قيد المعالجة", n: "18", c: C.amber }, { l: "محلولة اليوم", n: "45", c: C.green }, { l: "متوسط الحل", n: "4.2h", c: C.blue }].map(({ l, n, c }, i) => (
              <div key={i} className="p-3 rounded-2xl text-center" style={{ backgroundColor: C.white, border: `1px solid ${C.border}` }}>
                <p className="text-2xl font-black" style={{ color: c }}>{n}</p>
                <p className="text-xs" style={{ color: C.gray }}>{l}</p>
              </div>
            ))}
          </div>
          <div className="flex gap-4">
            <div className="flex-1 rounded-2xl overflow-hidden" style={{ backgroundColor: C.white, border: `1px solid ${C.border}` }}>
              <div className="px-4 py-2.5 flex items-center justify-between" style={{ backgroundColor: "#F8FAFC", borderBottom: `1px solid ${C.border}` }} dir="rtl">
                <div className="flex gap-2">
                  {["كل التذاكر","أولوية عالية","مالك","مستأجر"].map((t, i) => (
                    <button key={i} className="px-2 py-1 rounded-lg text-xs font-bold" style={{ backgroundColor: i===0 ? C.teal : "transparent", color: i===0 ? C.white : C.gray }}>{t}</button>
                  ))}
                </div>
                <p className="font-black text-xs" style={{ color: C.navy }}>تذاكر الدعم</p>
              </div>
              {[
                { id: "SUP-201", subject: "مشكلة في تأكيد الزيارة", user: "سارة أحمد", type: "مستأجر", priority: "عالي", status: "مفتوح", time: "منذ 1 ساعة" },
                { id: "SUP-200", subject: "عقاري مش ظاهر في البحث", user: "أحمد محمد", type: "مالك", priority: "متوسط", status: "قيد المعالجة", time: "منذ 3 ساعات" },
                { id: "SUP-199", subject: "مشكلة في رفع صور العقار", user: "منى طارق", type: "مالك", priority: "منخفض", status: "محلول", time: "أمس" },
              ].map((r, i) => (
                <div key={i} className="flex items-center gap-3 px-4 py-3" style={{ borderTop: `1px solid ${C.border}` }} dir="rtl">
                  <div>
                    <p className="text-xs font-black" style={{ color: C.teal }}>{r.id}</p>
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-xs font-black truncate" style={{ color: C.navy }}>{r.subject}</p>
                    <p style={{ fontSize: 10, color: C.gray }}>{r.user} · {r.time}</p>
                  </div>
                  <span className="text-xs px-1.5 py-0.5 rounded-full font-bold" style={{ backgroundColor: r.type==="مالك" ? C.goldLight : C.blueLight, color: r.type==="مالك" ? C.gold : C.blue, fontSize: 10 }}>{r.type}</span>
                  <span className="text-xs font-bold" style={{ color: r.priority==="عالي" ? C.red : r.priority==="متوسط" ? C.amber : C.gray }}>{r.priority}</span>
                  <button className="px-2 py-1 rounded-lg text-xs font-black text-white flex-shrink-0" style={{ backgroundColor: C.teal }}>فتح</button>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function AdminSupportTicketDetailScreen() {
  return (
    <div className="flex h-full" style={{ backgroundColor: "#F8FAFC", fontFamily: "Tajawal, sans-serif" }}>
      <AdminSidebar2 active="reports" />
      <div className="flex-1 flex flex-col overflow-hidden">
        <AdminTopBar title="تذكرة SUP-201 — تفاصيل" />
        <div className="flex-1 overflow-y-auto p-4">
          <div className="grid grid-cols-3 gap-4">
            <div className="p-4 rounded-2xl" style={{ backgroundColor: C.white, border: `1px solid ${C.border}` }} dir="rtl">
              <p className="font-black text-sm mb-3" style={{ color: C.navy }}>معلومات التذكرة</p>
              {[{ l: "رقم التذكرة", v: "SUP-201" }, { l: "الموضوع", v: "مشكلة في تأكيد الزيارة" }, { l: "المستخدم", v: "سارة أحمد خالد" }, { l: "النوع", v: "مستأجر" }, { l: "الأولوية", v: "عالي" }, { l: "الحالة", v: "مفتوح" }, { l: "وقت الفتح", v: "منذ ساعة" }, { l: "المسند إلى", v: "دينا حسام" }].map(({ l, v }, i) => (
                <div key={i} className="flex justify-between py-1.5" style={{ borderBottom: i<7 ? `1px solid ${C.border}` : "none" }}>
                  <span className="text-xs font-bold" style={{ color: C.navy }}>{v}</span>
                  <span style={{ fontSize: 10, color: C.gray }}>{l}</span>
                </div>
              ))}
            </div>
            <div className="col-span-2 flex flex-col gap-3">
              <div className="p-4 rounded-2xl" style={{ backgroundColor: C.white, border: `1px solid ${C.border}` }} dir="rtl">
                <p className="font-black text-sm mb-3" style={{ color: C.navy }}>المحادثة مع المستخدم</p>
                <div className="flex flex-col gap-3 mb-3">
                  <div className="flex justify-end">
                    <div className="max-w-xs px-3 py-2 text-xs" style={{ backgroundColor: C.tealLight, borderRadius: "12px 4px 12px 12px", color: C.navy }}>
                      أهلاً، أنا بحاول أأكد زيارة من ساعتين ومش بتتأكد. فيه مشكلة؟
                    </div>
                  </div>
                  <div className="flex justify-start">
                    <div className="max-w-xs px-3 py-2 text-xs" style={{ backgroundColor: "#F8FAFC", border: `1px solid ${C.border}`, borderRadius: "4px 12px 12px 12px", color: C.navy }}>
                      أهلاً سارة، شكراً للتواصل. هنشوف الموضوع دلوقتي وهنرد عليكي خلال ساعة.
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <input dir="rtl" readOnly placeholder="اكتب رداً…" className="flex-1 px-3 py-2 rounded-xl border text-xs outline-none"
                    style={{ borderColor: C.border }} />
                  <button className="px-3 py-2 rounded-xl text-xs font-black text-white" style={{ backgroundColor: C.teal }}>إرسال</button>
                </div>
              </div>
              <div className="p-4 rounded-2xl" style={{ backgroundColor: C.white, border: `1px solid ${C.border}` }} dir="rtl">
                <p className="font-black text-sm mb-2" style={{ color: C.navy }}>ملاحظات داخلية (لا تُشارك مع المستخدم)</p>
                <textarea readOnly dir="rtl" placeholder="ملاحظات الفريق الداخلي…" className="w-full px-3 py-2 rounded-xl border text-xs outline-none resize-none"
                  style={{ borderColor: C.border, height: 60 }} />
                <div className="flex gap-2 mt-3">
                  <button className="flex-1 py-2 rounded-xl text-xs font-black text-white" style={{ backgroundColor: C.green }}>إغلاق كـ محلول</button>
                  <button className="flex-1 py-2 rounded-xl text-xs font-black" style={{ backgroundColor: C.amberLight, color: C.amber }}>تصعيد</button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function AdminFinanceDashboardScreen() {
  return (
    <div className="flex h-full" style={{ backgroundColor: "#F8FAFC", fontFamily: "Tajawal, sans-serif" }}>
      <AdminSidebar2 active="reports" />
      <div className="flex-1 flex flex-col overflow-hidden">
        <AdminTopBar title="لوحة الإيرادات والمالية" />
        <div className="flex-1 overflow-y-auto p-4">
          <div className="grid grid-cols-4 gap-3 mb-4">
            {[{ l: "إجمالي الإيرادات هذا الشهر", n: "248,500 ج", c: C.green }, { l: "رسوم المنصة", n: "12,425 ج", c: C.teal }, { l: "معاملات نشطة", n: "1,203", c: C.blue }, { l: "متوسط الإيجار", n: "6,200 ج", c: C.amber }].map(({ l, n, c }, i) => (
              <div key={i} className="p-4 rounded-2xl" style={{ backgroundColor: C.white, border: `1px solid ${C.border}` }} dir="rtl">
                <p className="text-2xl font-black" style={{ color: c }}>{n}</p>
                <p className="text-xs mt-1" style={{ color: C.gray }}>{l}</p>
              </div>
            ))}
          </div>
          <div className="grid grid-cols-2 gap-4 mb-4">
            <div className="p-4 rounded-2xl" style={{ backgroundColor: C.white, border: `1px solid ${C.border}` }} dir="rtl">
              <p className="font-black text-sm mb-3" style={{ color: C.navy }}>إيرادات آخر 6 أشهر</p>
              <div className="flex items-end gap-2 justify-between" style={{ height: 80 }}>
                {[180,210,195,230,215,248].map((v, i) => (
                  <div key={i} className="flex-1 flex flex-col items-center gap-1">
                    <div className="w-full rounded-t-xl" style={{ height: `${(v/248)*100}%`, backgroundColor: i===5 ? C.teal : `${C.teal}30` }} />
                    <span style={{ fontSize: 9, color: C.gray }}>{["ي","ف","م","أ","م","ي"][i]}</span>
                  </div>
                ))}
              </div>
            </div>
            <div className="p-4 rounded-2xl" style={{ backgroundColor: C.white, border: `1px solid ${C.border}` }} dir="rtl">
              <p className="font-black text-sm mb-3" style={{ color: C.navy }}>توزيع الإيرادات</p>
              {[{ l: "رسوم المنصة (5%)", p: 5, n: "12,425 ج", c: C.teal }, { l: "إيجارات مُدارة", p: 85, n: "211,225 ج", c: C.blue }, { l: "رسوم توثيق", p: 10, n: "24,850 ج", c: C.amber }].map(({ l, p, n, c }, i) => (
                <div key={i} className="mb-3">
                  <div className="flex justify-between text-xs mb-1">
                    <span className="font-bold" style={{ color: C.navy }}>{n}</span>
                    <span style={{ color: C.gray }}>{l}</span>
                  </div>
                  <div className="h-2 rounded-full" style={{ backgroundColor: "#E5E7EB" }}>
                    <div className="h-full rounded-full" style={{ width: `${p*10}%`, backgroundColor: c }} />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function AdminTransactionLogScreen() {
  return (
    <div className="flex h-full" style={{ backgroundColor: "#F8FAFC", fontFamily: "Tajawal, sans-serif" }}>
      <AdminSidebar2 active="reports" />
      <div className="flex-1 flex flex-col overflow-hidden">
        <AdminTopBar title="سجل المعاملات المالية" />
        <div className="flex-1 overflow-y-auto p-4">
          <div className="flex items-center gap-3 mb-4" dir="rtl">
            <div className="flex items-center px-3 py-2 rounded-xl gap-2" style={{ backgroundColor: C.white, border: `1px solid ${C.border}` }}>
              <Search size={13} style={{ color: C.gray }} />
              <input placeholder="بحث برقم المعاملة…" dir="rtl" readOnly className="text-xs outline-none" style={{ width: 120 }} />
            </div>
            <button className="px-3 py-2 rounded-xl text-xs font-bold" style={{ backgroundColor: C.white, border: `1px solid ${C.border}`, color: C.navy }}>تصدير Excel</button>
            <div className="flex gap-2">
              {["كل","مدفوع","معلق","مسترد"].map((t, i) => (
                <button key={i} className="px-2 py-1 rounded-lg text-xs font-bold" style={{ backgroundColor: i===0 ? C.teal : "transparent", color: i===0 ? C.white : C.gray }}>{t}</button>
              ))}
            </div>
          </div>
          <div className="rounded-2xl overflow-hidden" style={{ backgroundColor: C.white, border: `1px solid ${C.border}` }}>
            <div className="grid px-4 py-2 text-xs font-black" style={{ backgroundColor: "#F8FAFC", color: C.gray, gridTemplateColumns: "1fr 2fr 1.5fr 1.5fr 1fr 1fr", borderBottom: `1px solid ${C.border}` }} dir="rtl">
              {["TXN ID","الوصف","المالك","المستأجر","المبلغ","الحالة"].map(h => <div key={h} className="text-right">{h}</div>)}
            </div>
            {[
              { id: "TXN-8821", desc: "إيجار شهري — شقة نصر", owner: "أحمد محمد", tenant: "سارة أحمد", amt: "+6,500 ج", status: "مدفوع", sc: C.green },
              { id: "TXN-8820", desc: "رسوم توثيق KYC", owner: "—", tenant: "محمد علي", amt: "+50 ج", status: "مدفوع", sc: C.green },
              { id: "TXN-8819", desc: "إيجار — ستوديو تجمع", owner: "نادر طارق", tenant: "نورا كمال", amt: "+4,200 ج", status: "معلق", sc: C.amber },
              { id: "TXN-8818", desc: "استرداد — إلغاء زيارة", owner: "—", tenant: "كريم سالم", amt: "-200 ج", status: "مسترد", sc: C.red },
            ].map((r, i) => (
              <div key={i} className="grid px-4 py-3 text-xs items-center" style={{ borderTop: `1px solid ${C.border}`, gridTemplateColumns: "1fr 2fr 1.5fr 1.5fr 1fr 1fr" }} dir="rtl">
                <span className="font-black" style={{ color: C.teal }}>{r.id}</span>
                <span className="truncate" style={{ color: C.navy }}>{r.desc}</span>
                <span style={{ color: C.gray }}>{r.owner}</span>
                <span style={{ color: C.gray }}>{r.tenant}</span>
                <span className="font-black" style={{ color: r.amt.startsWith("-") ? C.red : C.green }}>{r.amt}</span>
                <span className="font-bold" style={{ color: r.sc }}>{r.status}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

function AdminPropertyDetailViewScreen() {
  return (
    <div className="flex h-full" style={{ backgroundColor: "#F8FAFC", fontFamily: "Tajawal, sans-serif" }}>
      <AdminSidebar2 active="inventory" />
      <div className="flex-1 flex flex-col overflow-hidden">
        <AdminTopBar title="تفاصيل العقار — Admin View" />
        <div className="flex-1 overflow-y-auto p-4">
          <div className="grid grid-cols-3 gap-4">
            <div className="p-4 rounded-2xl" style={{ backgroundColor: C.white, border: `1px solid ${C.border}` }} dir="rtl">
              <div className="h-32 rounded-2xl mb-3 flex items-center justify-center" style={{ backgroundColor: "#E2E8F0" }}>
                <Building2 size={32} style={{ color: "#94A3B8" }} />
              </div>
              <p className="font-black text-sm mb-1" style={{ color: C.navy }}>شقة مفروشة — مدينة نصر</p>
              <Badge type="verified" />
              <div className="mt-3">
                {[{ l: "المالك", v: "أحمد محمد إبراهيم" }, { l: "السعر", v: "6,500 ج/شهر" }, { l: "المساحة", v: "90م²" }, { l: "الغرف", v: "3 غرف" }, { l: "تاريخ الإضافة", v: "1 مايو 2025" }, { l: "آخر تحديث", v: "اليوم" }].map(({ l, v }, i) => (
                  <div key={i} className="flex justify-between py-1.5" style={{ borderBottom: i<5 ? `1px solid ${C.border}` : "none" }}>
                    <span className="text-xs font-bold" style={{ color: C.navy }}>{v}</span>
                    <span style={{ fontSize: 10, color: C.gray }}>{l}</span>
                  </div>
                ))}
              </div>
            </div>
            <div className="col-span-2 flex flex-col gap-3">
              <div className="grid grid-cols-3 gap-3">
                {[{ l: "مشاهدات", n: "1,247", c: C.blue }, { l: "طلبات زيارة", n: "23", c: C.teal }, { l: "بلاغات", n: "0", c: C.green }].map(({ l, n, c }, i) => (
                  <div key={i} className="p-3 rounded-2xl text-center" style={{ backgroundColor: C.white, border: `1px solid ${C.border}` }}>
                    <p className="text-2xl font-black" style={{ color: c }}>{n}</p>
                    <p style={{ fontSize: 10, color: C.gray }}>{l}</p>
                  </div>
                ))}
              </div>
              <div className="p-4 rounded-2xl" style={{ backgroundColor: C.white, border: `1px solid ${C.border}` }} dir="rtl">
                <p className="font-black text-sm mb-3" style={{ color: C.navy }}>سجل المراجعة</p>
                {[
                  { a: "تم قبول العقار", t: "1 مايو 9:30 ص", reviewer: "أحمد العدل", c: C.green },
                  { a: "مراجعة أولية آلية — لم تُكتشف مشاكل", t: "1 مايو 9:20 ص", reviewer: "النظام", c: C.teal },
                  { a: "إرسال العقار من المالك", t: "1 مايو 9:00 ص", reviewer: "أحمد محمد", c: C.blue },
                ].map((a, i) => (
                  <div key={i} className="flex items-center gap-3 py-2" style={{ borderBottom: i<2 ? `1px solid ${C.border}` : "none" }}>
                    <div className="w-2 h-2 rounded-full flex-shrink-0" style={{ backgroundColor: a.c }} />
                    <div className="flex-1">
                      <p className="text-xs" style={{ color: C.navy }}>{a.a}</p>
                      <p style={{ fontSize: 9, color: C.gray }}>{a.t} · {a.reviewer}</p>
                    </div>
                  </div>
                ))}
              </div>
              <div className="flex gap-3">
                <button className="flex-1 py-2.5 rounded-xl text-xs font-black" style={{ backgroundColor: C.amberLight, color: C.amber }}>إخفاء العقار</button>
                <button className="flex-1 py-2.5 rounded-xl text-xs font-black text-white" style={{ backgroundColor: C.red }}>حذف</button>
                <button className="flex-1 py-2.5 rounded-xl text-xs font-black" style={{ backgroundColor: C.bg, color: C.gray, border: `1px solid ${C.border}` }}>تصدير</button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function AdminContentModerationScreen() {
  return (
    <div className="flex h-full" style={{ backgroundColor: "#F8FAFC", fontFamily: "Tajawal, sans-serif" }}>
      <AdminSidebar2 active="inventory" />
      <div className="flex-1 flex flex-col overflow-hidden">
        <AdminTopBar title="مراجعة المحتوى — Content Moderation" />
        <div className="flex-1 overflow-y-auto p-4">
          <div className="grid grid-cols-4 gap-3 mb-4">
            {[{ l: "صور مشبوهة", n: "14", c: C.red }, { l: "أوصاف مضللة", n: "8", c: C.amber }, { l: "أرقام هواتف في صور", n: "6", c: C.red }, { l: "محتوى غير لائق", n: "3", c: C.amber }].map(({ l, n, c }, i) => (
              <div key={i} className="p-3 rounded-2xl text-center" style={{ backgroundColor: C.white, border: `1px solid ${C.border}` }}>
                <p className="text-2xl font-black" style={{ color: c }}>{n}</p>
                <p className="text-xs" style={{ color: C.gray }}>{l}</p>
              </div>
            ))}
          </div>
          <div className="flex gap-4">
            <div className="flex-1 rounded-2xl overflow-hidden" style={{ backgroundColor: C.white, border: `1px solid ${C.border}` }}>
              <div className="px-4 py-2.5 flex items-center justify-between" style={{ backgroundColor: "#F8FAFC", borderBottom: `1px solid ${C.border}` }} dir="rtl">
                <p className="font-black text-xs" style={{ color: C.navy }}>محتوى مشبوه بانتظار المراجعة</p>
                <div className="flex gap-2">
                  {["صور","نصوص","الكل"].map((t, i) => (
                    <button key={i} className="px-2 py-1 rounded-lg text-xs font-bold" style={{ backgroundColor: i===2 ? C.teal : "transparent", color: i===2 ? C.white : C.gray }}>{t}</button>
                  ))}
                </div>
              </div>
              {[
                { type: "صورة", prop: "شقة مدينة نصر", issue: "رقم هاتف ظاهر في صورة", severity: "عالي", owner: "أحمد محمد" },
                { type: "نص", prop: "ستوديو التجمع", issue: "وصف غير دقيق — مساحة مبالغ فيها", severity: "متوسط", owner: "نادر طارق" },
                { type: "صورة", prop: "غرفة المعادي", issue: "صورة غير واضحة", severity: "منخفض", owner: "كريم سالم" },
              ].map((r, i) => (
                <div key={i} className="flex items-center gap-3 px-4 py-3" style={{ borderTop: `1px solid ${C.border}` }} dir="rtl">
                  <div className="w-12 h-12 rounded-xl flex items-center justify-center flex-shrink-0" style={{ backgroundColor: "#E2E8F0" }}>
                    {r.type==="صورة" ? <ImageIcon size={18} style={{ color: "#94A3B8" }} /> : <FileText size={18} style={{ color: "#94A3B8" }} />}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-xs font-black" style={{ color: C.navy }}>{r.prop}</p>
                    <p style={{ fontSize: 10, color: C.gray }}>{r.issue} · {r.owner}</p>
                  </div>
                  <span className="text-xs px-1.5 py-0.5 rounded-full font-bold"
                    style={{ backgroundColor: r.severity==="عالي" ? C.redLight : r.severity==="متوسط" ? C.amberLight : C.greenLight, color: r.severity==="عالي" ? C.red : r.severity==="متوسط" ? C.amber : C.green }}>{r.severity}</span>
                  <div className="flex gap-1">
                    <button className="px-2 py-1 rounded-lg text-xs font-black text-white" style={{ backgroundColor: C.teal }}>مراجعة</button>
                    <button className="px-2 py-1 rounded-lg text-xs font-black text-white" style={{ backgroundColor: C.red }}>حذف</button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function AdminPushNotificationsScreen() {
  return (
    <div className="flex h-full" style={{ backgroundColor: "#F8FAFC", fontFamily: "Tajawal, sans-serif" }}>
      <AdminSidebar2 active="system" />
      <div className="flex-1 flex flex-col overflow-hidden">
        <AdminTopBar title="إدارة الإشعارات المدفوعة" />
        <div className="flex-1 overflow-y-auto p-4">
          <div className="grid grid-cols-2 gap-4 mb-4">
            <div className="p-4 rounded-2xl" style={{ backgroundColor: C.white, border: `1px solid ${C.border}` }} dir="rtl">
              <p className="font-black text-sm mb-4" style={{ color: C.navy }}>إرسال إشعار جديد</p>
              <div className="flex flex-col gap-3">
                <div>
                  <p style={{ fontSize: 11, color: C.gray, marginBottom: 4 }}>الجمهور المستهدف</p>
                  <div className="flex flex-wrap gap-2">
                    {["كل المستخدمين","مستأجرون","ملاك","موثّقون فقط"].map((t, i) => (
                      <button key={i} className="px-2 py-1 rounded-lg text-xs font-bold"
                        style={{ backgroundColor: i===0 ? C.teal : C.bg, color: i===0 ? C.white : C.gray, border: `1px solid ${i===0 ? C.teal : C.border}` }}>{t}</button>
                    ))}
                  </div>
                </div>
                <div>
                  <p style={{ fontSize: 11, color: C.gray, marginBottom: 4 }}>عنوان الإشعار</p>
                  <input dir="rtl" readOnly placeholder="مثال: عروض الصيف على سكون!" className="w-full px-3 py-2 rounded-xl border text-xs outline-none"
                    style={{ borderColor: C.border }} />
                </div>
                <div>
                  <p style={{ fontSize: 11, color: C.gray, marginBottom: 4 }}>نص الإشعار</p>
                  <textarea readOnly dir="rtl" placeholder="نص الإشعار…" className="w-full px-3 py-2 rounded-xl border text-xs outline-none resize-none"
                    style={{ borderColor: C.border, height: 60 }} />
                </div>
                <div className="flex gap-2">
                  <button className="flex-1 py-2 rounded-xl text-xs font-black text-white" style={{ backgroundColor: C.teal }}>إرسال الآن</button>
                  <button className="flex-1 py-2 rounded-xl text-xs font-black" style={{ backgroundColor: C.bg, color: C.gray, border: `1px solid ${C.border}` }}>جدولة</button>
                </div>
              </div>
            </div>
            <div className="p-4 rounded-2xl" style={{ backgroundColor: C.white, border: `1px solid ${C.border}` }} dir="rtl">
              <p className="font-black text-sm mb-3" style={{ color: C.navy }}>سجل الإشعارات المرسلة</p>
              {[
                { t: "عروض الصيف!", body: "احجز زيارتك واستمتع بخصم 20%", sent: "النهارده 9:00 ص", reach: "2,847", open: "34%" },
                { t: "عقارات جديدة!", body: "شقق جديدة في مدينة نصر", sent: "أمس 3:00 م", reach: "1,924", open: "28%" },
                { t: "تذكير توثيق", body: "وثّق هويتك وابدأ التواصل", sent: "قبل 3 أيام", reach: "923", open: "45%" },
              ].map((n, i) => (
                <div key={i} className="py-2.5" style={{ borderBottom: i<2 ? `1px solid ${C.border}` : "none" }}>
                  <div className="flex justify-between items-center mb-0.5">
                    <span style={{ fontSize: 10, color: C.gray }}>{n.sent}</span>
                    <p className="text-xs font-black" style={{ color: C.navy }}>{n.t}</p>
                  </div>
                  <p style={{ fontSize: 10, color: C.gray, marginBottom: 4 }}>{n.body}</p>
                  <div className="flex gap-3">
                    <span style={{ fontSize: 10, color: C.teal }}>{n.reach} وصل</span>
                    <span style={{ fontSize: 10, color: C.green }}>{n.open} فتح</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function AdminActivityLogsScreen() {
  return (
    <div className="flex h-full" style={{ backgroundColor: "#F8FAFC", fontFamily: "Tajawal, sans-serif" }}>
      <AdminSidebar2 active="system" />
      <div className="flex-1 flex flex-col overflow-hidden">
        <AdminTopBar title="سجل النشاط — Activity Logs" />
        <div className="flex-1 overflow-y-auto p-4">
          <div className="flex items-center gap-3 mb-4" dir="rtl">
            <div className="flex items-center px-3 py-2 rounded-xl gap-2" style={{ backgroundColor: C.white, border: `1px solid ${C.border}` }}>
              <Search size={13} style={{ color: C.gray }} />
              <input placeholder="بحث في السجل…" dir="rtl" readOnly className="text-xs outline-none" style={{ width: 120 }} />
            </div>
            <div className="flex gap-2">
              {["كل الإجراءات","KYC","عقارات","مستخدمون","نظام"].map((t, i) => (
                <button key={i} className="px-2 py-1 rounded-lg text-xs font-bold" style={{ backgroundColor: i===0 ? C.teal : C.white, color: i===0 ? C.white : C.gray, border: `1px solid ${i===0 ? C.teal : C.border}` }}>{t}</button>
              ))}
            </div>
            <button className="px-3 py-2 rounded-xl text-xs font-bold mr-auto" style={{ backgroundColor: C.white, border: `1px solid ${C.border}`, color: C.navy }}>تصدير CSV</button>
          </div>
          <div className="rounded-2xl overflow-hidden" style={{ backgroundColor: C.white, border: `1px solid ${C.border}` }}>
            <div className="grid px-4 py-2 text-xs font-black" style={{ backgroundColor: "#F8FAFC", color: C.gray, gridTemplateColumns: "1fr 3fr 1fr 1fr 1.5fr", borderBottom: `1px solid ${C.border}` }} dir="rtl">
              {["الوقت","الإجراء","النوع","المستهدف","المشرف"].map(h => <div key={h} className="text-right">{h}</div>)}
            </div>
            {[
              { t: "09:41:23", a: "قبول توثيق هوية — سارة أحمد خالد", type: "KYC", target: "مستأجر", admin: "سلمى رشدي", c: C.green },
              { t: "09:35:10", a: "رفض عقار — كريم سالم فاروق", type: "عقار", target: "مالك", admin: "أحمد العدل", c: C.red },
              { t: "09:20:04", a: "إيقاف حساب طارق محمد — لغة مسيئة", type: "مستخدم", target: "مستأجر", admin: "أحمد العدل", c: C.amber },
              { t: "09:10:55", a: "تغيير دور دينا حسام → دعم عملاء", type: "دور", target: "Admin", admin: "أحمد العدل", c: C.blue },
              { t: "08:55:30", a: "حل تذكرة SUP-199 — مشكلة صور", type: "دعم", target: "مالك", admin: "سلمى رشدي", c: C.teal },
              { t: "08:44:18", a: "رفض بلاغ على شقة المعادي — غير مؤكد", type: "بلاغ", target: "عقار", admin: "كريم فاروق", c: C.gray },
              { t: "08:30:00", a: "إرسال إشعار — عروض الصيف 2,847 مستخدم", type: "نظام", target: "الكل", admin: "أحمد العدل", c: C.teal },
            ].map((r, i) => (
              <div key={i} className="grid px-4 py-2.5 text-xs items-center" style={{ borderTop: `1px solid ${C.border}`, gridTemplateColumns: "1fr 3fr 1fr 1fr 1.5fr" }} dir="rtl">
                <span style={{ fontFamily: "monospace", color: C.gray, fontSize: 10 }}>{r.t}</span>
                <span className="truncate" style={{ color: C.navy }}>{r.a}</span>
                <span className="px-1.5 py-0.5 rounded font-bold" style={{ backgroundColor: r.c + "20", color: r.c, fontSize: 10 }}>{r.type}</span>
                <span style={{ color: C.gray }}>{r.target}</span>
                <span style={{ color: C.gray }}>{r.admin}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════
//  SCREEN REGISTRY — NEW SCREENS
// ═══════════════════════════════════════════════


export {
  AdminSidebar,
  AdminDashboardScreen,
  AdminUsersScreen,
  AdminPropertiesScreen,
  AdminAnalyticsScreen,
  AdminSettingsScreen,
  AdminSidebar2,
  AdminTopBar,
  AdminExecutiveDashboardScreen,
  AdminListingModerationScreen,
  AdminUsersFlagQueueScreen,
  AdminReportsTicketsScreen,
  AdminRolesManagementScreen,
  AdminSystemMonitorScreen,
  SharedNotificationWidget,
  SharedChatInboxWidget,
  SharedVisitRequestWidget,
  MissingScreensAuditScreen,
  AdminKYCQueueScreen,
  AdminKYCReviewDetailScreen,
  AdminUserProfileScreen,
  AdminBannedUsersScreen,
  AdminSupportConsoleScreen,
  AdminSupportTicketDetailScreen,
  AdminFinanceDashboardScreen,
  AdminTransactionLogScreen,
  AdminPropertyDetailViewScreen,
  AdminContentModerationScreen,
  AdminPushNotificationsScreen,
  AdminActivityLogsScreen
};
