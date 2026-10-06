import React, { useState } from "react";

// ── Tenant screens ────────────────────────────────────────────────────
import {
  TenantOnboardingScreen, TenantSearchScreen, SearchResultsScreen,
  FilterSheetScreen, PropertyDetailScreen, PhotoGalleryScreen,
  BookVisitScreen, VisitConfirmedScreen, VisitDetailScreen,
  TenantMyVisitsScreen, TenantChatListScreen, TenantChatThreadScreen,
  TenantChatRestrictedScreen, SavedListingsScreen, SavedEmptyStateScreen,
  TenantProfileScreen, TenantSettingsScreen, TenantNotificationsScreen,
  KYCStartScreen, KYCUploadScreen, KYCPendingScreen, KYCApprovedScreen,
  PropertyMapScreen, RatePropertyScreen, TenantPersonalizedHomeScreen,
} from "./screens-tenant";

// ── Owner screens ─────────────────────────────────────────────────────
import {
  OwnerOnboardingScreen, OwnerDashboardScreen, OwnerMyListingsScreen,
  AddPropertyStep1Screen, AddPropertyStep2PhotosScreen,
  AddPropertyStep3PricingScreen, PropertySubmittedScreen,
  OwnerRequestsListScreen, OwnerRequestDetailScreen,
  OwnerChatListScreen, OwnerChatThreadScreen,
  OwnerPropertyAnalyticsScreen, OwnerRevenueScreen,
  OwnerKYCScreen, OwnerProfileScreen, OwnerNotificationsScreen,
  OwnerVisitsDashboardScreen, OwnerMoreScreen,
} from "./screens-owner";

// ── Admin screens ─────────────────────────────────────────────────────
import {
  AdminDashboardScreen, AdminUsersScreen, AdminPropertiesScreen,
  AdminAnalyticsScreen, AdminKYCQueueScreen, AdminKYCReviewDetailScreen,
  AdminUserProfileScreen, AdminSupportConsoleScreen,
  AdminFinanceDashboardScreen, AdminListingModerationScreen,
} from "./screens-admin";

// ── Flow screens ──────────────────────────────────────────────────────
import {
  SplashScreen, RoleSelectScreen,
  TenantLoginScreen, TenantRegisterScreen,
  OwnerLoginScreen, OwnerRegisterScreen,
} from "./screens-flow";

// ── Updated screens ───────────────────────────────────────────────────
import {
  TenantLoginEmailScreen, TenantOTPScreen,
  UpdatedKYCUploadScreen, UpdatedOwnerDashboardScreen,
  SharePropertySheet, UpdatedOwnerRequestsListScreen,
  MergedAddPropertyStep1Screen, MergedAddPropertyStep3Screen,
  FullPropertyDetailScreen, FullFilterSheetScreen, FullSearchResultsScreen,
  UpdatedTenantKYC01Screen, UpdatedOwnerKYC01Screen,
} from "./screens-updates";

// ─── Types ────────────────────────────────────────────────────────────
type Screen = { id: string; label: string; C: React.ComponentType };
type Group  = { id: string; label: string; ar: string; screens: Screen[] };

// ─── Screen groups ────────────────────────────────────────────────────
const GROUPS: Group[] = [
  {
    id: "onboarding", label: "Onboarding", ar: "التهيئة",
    screens: [
      { id: "splash",    label: "Splash",          C: SplashScreen },
      { id: "role",      label: "اختر دورك",        C: RoleSelectScreen },
      { id: "t-onb",     label: "Tenant Onboarding",C: TenantOnboardingScreen },
      { id: "o-onb",     label: "Owner Onboarding", C: OwnerOnboardingScreen },
    ],
  },
  {
    id: "auth", label: "Auth", ar: "الدخول",
    screens: [
      { id: "t-login",   label: "Tenant Login",     C: TenantLoginScreen },
      { id: "t-login-e", label: "Login (Email)",     C: TenantLoginEmailScreen },
      { id: "t-otp",     label: "OTP",               C: TenantOTPScreen },
      { id: "t-reg",     label: "Register",          C: TenantRegisterScreen },
      { id: "o-login",   label: "Owner Login",       C: OwnerLoginScreen },
      { id: "o-reg",     label: "Owner Register",    C: OwnerRegisterScreen },
    ],
  },
  {
    id: "tenant", label: "Tenant", ar: "المستأجر",
    screens: [
      { id: "t-home",    label: "Home",              C: TenantPersonalizedHomeScreen },
      { id: "t-search",  label: "Search",            C: TenantSearchScreen },
      { id: "t-results", label: "Results (Full)",    C: FullSearchResultsScreen },
      { id: "t-filter",  label: "Filter (Full)",     C: FullFilterSheetScreen },
      { id: "t-prop",    label: "Property Detail",   C: FullPropertyDetailScreen },
      { id: "t-gallery", label: "Gallery",           C: PhotoGalleryScreen },
      { id: "t-map",     label: "Property Map",      C: PropertyMapScreen },
      { id: "t-book",    label: "Book Visit",        C: BookVisitScreen },
      { id: "t-conf",    label: "Visit Confirmed",   C: VisitConfirmedScreen },
      { id: "t-visits",  label: "My Visits",         C: TenantMyVisitsScreen },
      { id: "t-visit-d", label: "Visit Detail",      C: VisitDetailScreen },
      { id: "t-rate",    label: "Rate Property",     C: RatePropertyScreen },
      { id: "t-saved",   label: "Saved",             C: SavedListingsScreen },
      { id: "t-chat-l",  label: "Chat List",         C: TenantChatListScreen },
      { id: "t-chat",    label: "Chat Thread",       C: TenantChatThreadScreen },
      { id: "t-notif",   label: "Notifications",     C: TenantNotificationsScreen },
      { id: "t-profile", label: "Profile",           C: TenantProfileScreen },
      { id: "t-settings",label: "Settings",          C: TenantSettingsScreen },
    ],
  },
  {
    id: "kyc", label: "KYC", ar: "التوثيق",
    screens: [
      { id: "t-kyc-s",   label: "KYC Start",         C: KYCStartScreen },
      { id: "t-kyc-u",   label: "KYC Upload",        C: UpdatedKYCUploadScreen },
      { id: "t-kyc-p",   label: "KYC Pending",       C: KYCPendingScreen },
      { id: "t-kyc-ok",  label: "KYC Approved",      C: KYCApprovedScreen },
      { id: "t-kyc-01",  label: "Tenant KYC (new)",  C: UpdatedTenantKYC01Screen },
      { id: "o-kyc",     label: "Owner KYC",         C: OwnerKYCScreen },
      { id: "o-kyc-01",  label: "Owner KYC (new)",   C: UpdatedOwnerKYC01Screen },
    ],
  },
  {
    id: "owner", label: "Owner", ar: "المالك",
    screens: [
      { id: "o-dash",    label: "Dashboard",         C: UpdatedOwnerDashboardScreen },
      { id: "o-list",    label: "My Listings",       C: OwnerMyListingsScreen },
      { id: "o-add1",    label: "Add Prop Step 1",   C: MergedAddPropertyStep1Screen },
      { id: "o-add2",    label: "Add Prop Step 2",   C: AddPropertyStep2PhotosScreen },
      { id: "o-add3",    label: "Add Prop Step 3",   C: MergedAddPropertyStep3Screen },
      { id: "o-submitted",label:"Submitted",         C: PropertySubmittedScreen },
      { id: "o-requests",label: "Requests",          C: UpdatedOwnerRequestsListScreen },
      { id: "o-req-d",   label: "Request Detail",    C: OwnerRequestDetailScreen },
      { id: "o-visits",  label: "Visits Dashboard",  C: OwnerVisitsDashboardScreen },
      { id: "o-chat-l",  label: "Chat List",         C: OwnerChatListScreen },
      { id: "o-chat",    label: "Chat Thread",       C: OwnerChatThreadScreen },
      { id: "o-analytics",label:"Analytics",         C: OwnerPropertyAnalyticsScreen },
      { id: "o-revenue", label: "Revenue",           C: OwnerRevenueScreen },
      { id: "o-notif",   label: "Notifications",     C: OwnerNotificationsScreen },
      { id: "o-profile", label: "Profile",           C: OwnerProfileScreen },
      { id: "o-more",    label: "More",              C: OwnerMoreScreen },
    ],
  },
  {
    id: "admin", label: "Admin", ar: "الإدارة",
    screens: [
      { id: "a-dash",    label: "Dashboard",         C: AdminDashboardScreen },
      { id: "a-users",   label: "Users",             C: AdminUsersScreen },
      { id: "a-props",   label: "Properties",        C: AdminPropertiesScreen },
      { id: "a-analytics",label:"Analytics",         C: AdminAnalyticsScreen },
      { id: "a-kyc-q",   label: "KYC Queue",         C: AdminKYCQueueScreen },
      { id: "a-kyc-d",   label: "KYC Review",        C: AdminKYCReviewDetailScreen },
      { id: "a-user-p",  label: "User Profile",      C: AdminUserProfileScreen },
      { id: "a-support", label: "Support Console",   C: AdminSupportConsoleScreen },
      { id: "a-finance", label: "Finance",           C: AdminFinanceDashboardScreen },
      { id: "a-moderation",label:"Moderation",       C: AdminListingModerationScreen },
    ],
  },
];

// ─── Colours (inline, no import needed) ──────────────────────────────
const TEAL  = "#0F766E";
const NAVY  = "#0B1628";
const GOLD  = "#D4A84B";
const WHITE = "#FFFFFF";
const SLATE = "#64748B";
const BOARD = "#06101B";

const TJ_S  = { fontFamily: "'Tajawal', sans-serif" } as React.CSSProperties;
const MONO_S = { fontFamily: "'DM Mono', monospace" } as React.CSSProperties;
const INT_S  = { fontFamily: "'Inter', sans-serif" } as React.CSSProperties;

// ─── Device frame ─────────────────────────────────────────────────────
function DeviceFrame({ children, scale = 1 }: { children: React.ReactNode; scale?: number }) {
  return (
    <div style={{
      width: 390 * scale, height: 844 * scale,
      borderRadius: 50 * scale, flexShrink: 0,
      background: "#1A1A1C",
      boxShadow: `0 0 0 ${2 * scale}px #3A3A3C, 0 ${24 * scale}px ${72 * scale}px rgba(0,0,0,0.8), inset 0 0 0 ${1 * scale}px rgba(255,255,255,0.06)`,
      padding: 10 * scale, overflow: "hidden",
    }}>
      <div style={{
        width: "100%", height: "100%",
        borderRadius: 40 * scale, overflow: "hidden",
        background: "#FAFAF8", position: "relative",
      }}>
        {/* Dynamic island */}
        <div style={{
          position: "absolute", top: 14 * scale, left: "50%", transform: "translateX(-50%)",
          width: 120 * scale, height: 34 * scale,
          background: "#1A1A1C", borderRadius: 20 * scale, zIndex: 10,
        }} />
        <div style={{ width: "100%", height: "100%", overflow: "hidden", transform: `scale(${scale})`, transformOrigin: "top left" }}>
          <div style={{ width: 390, height: 844, overflow: "hidden" }}>
            {children}
          </div>
        </div>
      </div>
    </div>
  );
}

// ─── Proto (interactive single-screen viewer) ─────────────────────────
function ProtoView() {
  const allScreens: Screen[] = GROUPS.flatMap(g => g.screens);
  const [activeId, setActiveId] = useState("splash");
  const [groupId, setGroupId] = useState("onboarding");

  const active = allScreens.find(s => s.id === activeId) ?? allScreens[0];
  const ScreenComp = active.C;

  return (
    <div style={{ display: "flex", gap: 36, alignItems: "flex-start" }}>

      {/* Left sidebar — screen navigator */}
      <div style={{
        width: 240, flexShrink: 0, background: "#09151F",
        borderRadius: 20, border: "1px solid rgba(255,255,255,0.06)",
        overflow: "hidden",
      }}>
        {/* Header */}
        <div style={{ padding: "16px 16px 12px", borderBottom: "1px solid rgba(255,255,255,0.06)" }}>
          <div style={{ fontSize: 9, color: GOLD, letterSpacing: 3, ...MONO_S }}>PROTO MODE</div>
          <div style={{ fontSize: 13, fontWeight: 700, color: WHITE, marginTop: 4, ...TJ_S }}>التنقل بين الشاشات</div>
        </div>

        {/* Group tabs */}
        <div style={{ display: "flex", gap: 4, padding: "8px 10px", flexWrap: "wrap", borderBottom: "1px solid rgba(255,255,255,0.06)" }}>
          {GROUPS.map(g => (
            <button key={g.id} onClick={() => setGroupId(g.id)} style={{
              padding: "4px 10px", borderRadius: 8, border: "none", cursor: "pointer",
              background: groupId === g.id ? TEAL : "rgba(255,255,255,0.05)",
              fontSize: 10, fontWeight: 600, color: groupId === g.id ? WHITE : SLATE,
              ...TJ_S,
            }}>{g.ar}</button>
          ))}
        </div>

        {/* Screen list */}
        <div style={{ maxHeight: 560, overflowY: "auto", padding: "6px 8px" }}>
          {GROUPS.filter(g => g.id === groupId).flatMap(g => g.screens).map(s => (
            <button key={s.id} onClick={() => setActiveId(s.id)} style={{
              display: "flex", alignItems: "center", justifyContent: "space-between",
              width: "100%", padding: "8px 10px", borderRadius: 10, border: "none", cursor: "pointer",
              background: activeId === s.id ? `${TEAL}20` : "transparent",
              borderLeft: activeId === s.id ? `2px solid ${TEAL}` : "2px solid transparent",
              marginBottom: 2, textAlign: "right",
            }}>
              <span style={{ fontSize: 11, color: activeId === s.id ? WHITE : SLATE, ...TJ_S }}>{s.label}</span>
              <span style={{ fontSize: 8, color: `${SLATE}60`, ...MONO_S }}>{s.id}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Center — device with screen */}
      <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 20 }}>
        <DeviceFrame scale={0.72}>
          <ScreenComp />
        </DeviceFrame>
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <div style={{ height: 1, width: 40, background: `rgba(255,255,255,0.08)` }} />
          <span style={{ fontSize: 9, color: SLATE, letterSpacing: 2, ...MONO_S }}>{active.id} · {active.label}</span>
          <div style={{ height: 1, width: 40, background: `rgba(255,255,255,0.08)` }} />
        </div>
      </div>

    </div>
  );
}

// ─── Gallery view (all screens as mini tiles) ──────────────────────────
function GalleryView() {
  const [activeGroup, setActiveGroup] = useState<string>("all");

  const displayed = activeGroup === "all"
    ? GROUPS
    : GROUPS.filter(g => g.id === activeGroup);

  return (
    <div>
      {/* Group filter */}
      <div style={{ display: "flex", gap: 6, marginBottom: 28, flexWrap: "wrap" }}>
        <button onClick={() => setActiveGroup("all")} style={{
          padding: "6px 16px", borderRadius: 20, border: "none", cursor: "pointer",
          background: activeGroup === "all" ? TEAL : "rgba(255,255,255,0.06)",
          fontSize: 11, color: activeGroup === "all" ? WHITE : SLATE, ...TJ_S,
        }}>الكل</button>
        {GROUPS.map(g => (
          <button key={g.id} onClick={() => setActiveGroup(g.id)} style={{
            padding: "6px 16px", borderRadius: 20, border: "none", cursor: "pointer",
            background: activeGroup === g.id ? TEAL : "rgba(255,255,255,0.06)",
            fontSize: 11, color: activeGroup === g.id ? WHITE : SLATE, ...TJ_S,
          }}>{g.ar}</button>
        ))}
      </div>

      {displayed.map(group => (
        <div key={group.id} style={{ marginBottom: 52 }}>
          {/* Group header */}
          <div style={{ display: "flex", alignItems: "center", gap: 14, marginBottom: 20 }}>
            <span style={{ fontSize: 9, color: GOLD, letterSpacing: 3, ...MONO_S }}>{group.label.toUpperCase()}</span>
            <div style={{ flex: 1, height: 1, background: `linear-gradient(90deg, ${GOLD}20, transparent)` }} />
            <span style={{ fontSize: 9, color: SLATE, ...MONO_S }}>{group.screens.length} screens</span>
          </div>

          {/* Screen tiles */}
          <div style={{ display: "flex", gap: 16, flexWrap: "wrap" }}>
            {group.screens.map(screen => {
              const SC = screen.C;
              return (
                <div key={screen.id} style={{ display: "flex", flexDirection: "column", alignItems: "center" }}>
                  {/* Mini device frame */}
                  <div style={{
                    width: 118, height: 256, borderRadius: 22, flexShrink: 0,
                    background: "#1A1A1C",
                    boxShadow: "0 0 0 1.5px #3A3A3C, 0 8px 28px rgba(0,0,0,0.6)",
                    padding: 4, overflow: "hidden",
                  }}>
                    <div style={{
                      width: "100%", height: "100%",
                      borderRadius: 18, overflow: "hidden",
                      background: "#FAFAF8", position: "relative",
                    }}>
                      {/* Island */}
                      <div style={{
                        position: "absolute", top: 4, left: "50%", transform: "translateX(-50%)",
                        width: 36, height: 10, background: "#1A1A1C", borderRadius: 6, zIndex: 10,
                      }} />
                      {/* Scaled screen */}
                      <div style={{
                        transformOrigin: "top left",
                        transform: `scale(${110 / 390})`,
                        width: 390, height: 844,
                        pointerEvents: "none",
                      }}>
                        <SC />
                      </div>
                    </div>
                  </div>
                  {/* Label */}
                  <div style={{ marginTop: 8, textAlign: "center", maxWidth: 118 }}>
                    <div style={{ fontSize: 9.5, color: WHITE, fontWeight: 500, ...TJ_S }}>{screen.label}</div>
                    <div style={{ fontSize: 7.5, color: SLATE, marginTop: 1, ...MONO_S }}>{screen.id}</div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      ))}
    </div>
  );
}

// ─── Main export ──────────────────────────────────────────────────────
type AppView = "proto" | "gallery";

export function SokoonApp() {
  const [view, setView] = useState<AppView>("proto");

  const totalScreens = GROUPS.reduce((acc, g) => acc + g.screens.length, 0);

  return (
    <div>
      {/* Sub-header */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 36, paddingBottom: 28, borderBottom: "1px solid rgba(212,168,75,0.10)" }}>
        <div>
          <div style={{ fontSize: 9.5, color: GOLD, letterSpacing: 5, ...MONO_S, marginBottom: 8 }}>
            Sokoon App Prototype
          </div>
          <div style={{ fontSize: 34, fontWeight: 900, color: WHITE, lineHeight: 1, ...TJ_S, marginBottom: 6 }}>
            التطبيق
          </div>
          <div style={{ fontSize: 11.5, color: SLATE, ...INT_S }}>
            {totalScreens} screens · Tenant · Owner · Admin · Auth · KYC
          </div>
        </div>

        {/* View switcher */}
        <div style={{ display: "flex", gap: 4, background: "rgba(255,255,255,0.04)", padding: 4, borderRadius: 12, border: "1px solid rgba(255,255,255,0.06)" }}>
          {([
            { id: "proto" as AppView, ar: "بروتوتايب", count: "تفاعلي" },
            { id: "gallery" as AppView, ar: "معرض",    count: `${totalScreens}` },
          ] as { id: AppView; ar: string; count: string }[]).map(v => (
            <button key={v.id} onClick={() => setView(v.id)} style={{
              display: "flex", alignItems: "center", gap: 8,
              padding: "8px 18px", borderRadius: 9, border: "none", cursor: "pointer",
              background: view === v.id ? TEAL : "transparent",
            }}>
              <span style={{ fontSize: 13, fontWeight: view === v.id ? 700 : 400, color: view === v.id ? WHITE : SLATE, ...TJ_S }}>{v.ar}</span>
              <span style={{ fontSize: 8, color: view === v.id ? `${WHITE}70` : `${SLATE}60`, background: view === v.id ? `${WHITE}20` : "rgba(255,255,255,0.05)", padding: "1px 6px", borderRadius: 8, ...MONO_S }}>{v.count}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Content */}
      {view === "proto"   && <ProtoView />}
      {view === "gallery" && <GalleryView />}
    </div>
  );
}
