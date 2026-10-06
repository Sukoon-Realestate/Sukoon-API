import React, { useState } from "react";
import {
  Home, Bell, User, Building2, Calendar, MessageCircle, Menu,
  Settings, Shield, Lock, CheckCircle, AlertCircle, Clock, Eye, EyeOff,
  Star, MapPin, Heart, Send, Mic, Image as ImageIcon,
  ArrowLeft, ChevronRight, ChevronLeft, X, Plus, Check, AlertTriangle,
  FileText, Users, BarChart2, LogOut, Phone, Key, Edit2, Trash2,
  TrendingUp, TrendingDown, RefreshCw, Filter, Search, Info,
} from "lucide-react";

export const C = {
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
export const TJ: React.CSSProperties = { fontFamily: "Tajawal, sans-serif" };

export type BadgeType = "verified" | "pending" | "rejected" | "approved" | "hidden" | "rented";

export function Badge({ type, text }: { type: BadgeType; text?: string }) {
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

export function PrimaryBtn({ text, onClick, disabled, danger }: { text: string; onClick?: () => void; disabled?: boolean; danger?: boolean }) {
  return (
    <button onClick={onClick} disabled={disabled}
      className="w-full flex items-center justify-center py-4 rounded-2xl font-bold text-base transition-all"
      style={{ ...TJ, backgroundColor: disabled ? "#D1D5DB" : danger ? C.red : C.teal, color: C.white }}>
      {text}
    </button>
  );
}

export function OutlineBtn({ text, onClick }: { text: string; onClick?: () => void }) {
  return (
    <button onClick={onClick}
      className="w-full flex items-center justify-center py-4 rounded-2xl font-bold text-base"
      style={{ ...TJ, backgroundColor: C.white, color: C.navy, border: `1px solid ${C.border}` }}>
      {text}
    </button>
  );
}

export function Card({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  return (
    <div className={`rounded-3xl p-4 ${className}`}
      style={{ backgroundColor: C.white, border: `1px solid ${C.border}`, boxShadow: "0 2px 8px rgba(0,0,0,0.04)" }}>
      {children}
    </div>
  );
}

export function PrivacyBanner({ text }: { text: string }) {
  return (
    <div className="flex items-center gap-2 px-4 py-3 rounded-2xl" style={{ backgroundColor: C.blueLight }}>
      <Lock size={13} style={{ color: C.blue, flexShrink: 0 }} />
      <p className="text-xs font-medium flex-1" style={{ ...TJ, color: C.blue }}>{text}</p>
    </div>
  );
}

export function WarnBanner({ text, action }: { text: string; action?: string }) {
  return (
    <div className="flex items-center gap-2 px-4 py-3 rounded-2xl" style={{ backgroundColor: C.amberLight }}>
      <AlertTriangle size={13} style={{ color: C.amber, flexShrink: 0 }} />
      <p className="text-xs font-medium flex-1" style={{ ...TJ, color: "#92400E" }}>{text}</p>
      {action && <button className="text-xs font-bold flex-shrink-0" style={{ ...TJ, color: C.teal }}>{action}</button>}
    </div>
  );
}

export function StatusBar({ dark: isDark = false }: { dark?: boolean }) {
  return (
    <div className="h-11 flex items-center justify-between px-6 flex-shrink-0">
      <span className="text-sm font-black" style={{ color: isDark ? C.white : C.navy }}>9:41</span>
      <div className="w-24 h-5 rounded-full" style={{ backgroundColor: isDark ? "#334155" : "#1a1a1a" }} />
      <span className="text-xs font-black" style={{ color: isDark ? C.white : C.navy }}>●●●</span>
    </div>
  );
}

export function TenantNav({ active = "home" }: { active?: string }) {
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

export function OwnerNav({ active = "home" }: { active?: string }) {
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

export function StepProgress({ total, current }: { total: number; current: number }) {
  return (
    <div className="flex gap-1.5 mb-5" dir="rtl">
      {Array.from({ length: total }).map((_, i) => (
        <div key={i} className="flex-1 h-1.5 rounded-full"
          style={{ backgroundColor: i < current ? C.teal : C.border }} />
      ))}
    </div>
  );
}

export function TextInput({ label, placeholder, type = "text" }: { label: string; placeholder: string; type?: string }) {
  return (
    <div dir="rtl">
      <p className="font-black text-sm mb-1.5" style={{ ...TJ, color: C.navy }}>{label}</p>
      <div className="px-4 py-3 rounded-2xl border" style={{ borderColor: C.border, backgroundColor: C.white }}>
        <input readOnly type={type} placeholder={placeholder} dir="rtl"
          className="w-full text-sm outline-none bg-transparent"
          style={{ ...TJ, color: "#9CA3AF" }} />
      </div>
    </div>
  );
}
