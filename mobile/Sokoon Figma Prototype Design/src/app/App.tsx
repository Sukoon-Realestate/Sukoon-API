import React, { useState } from "react";
import { FutureGraphicsTab, LogoConceptsTab } from "./brand-concepts";
import { SharedView } from "./shared-library";
import { LandingPage } from "./landing-page";
import {
  TenantLoginEmailScreen, TenantOTPScreen,
  OwnerLoginEmailScreen, OwnerOTPScreen,
  VisitorRestrictedSheet,
  UpdatedAddPropertyStep3Screen,
  SharePropertySheet, FullFilterSheetScreen, FullSearchResultsScreen,
  UpdatedOwnerRequestsListScreen,
  MergedAddPropertyStep1Screen,
  MergedAddPropertyStep3Screen,
  FullPropertyDetailScreen,
  UpdatedTenantKYC01Screen, UpdatedOwnerKYC01Screen,
  UpdatedTenantKYC02Screen, OwnerKYC02Screen,
  UpdatedAddPropertyStep2Screen, AddPropertyVideoScreen,
  TenantForgotPasswordScreen, OwnerForgotPasswordScreen,
} from "./screens-updates";
import {
  TenantNotificationsScreen, TenantProfileScreen, TenantMyVisitsScreen,
  TenantChatListScreen, RatePropertyScreen, TenantSettingsScreen,
  SavedEmptyStateScreen, TenantChatSearchScreen, ReportSheetScreen,
  TenantSearchScreen, SearchResultsScreen, FilterSheetScreen,
  PropertyDetailScreen, PhotoGalleryScreen, PropertyMapScreen,
  BookVisitScreen, VisitConfirmedScreen, VisitDetailScreen,
  TenantChatThreadScreen, TenantChatRestrictedScreen, SavedListingsScreen,
  KYCStartScreen, KYCUploadScreen, KYCPendingScreen, KYCApprovedScreen,
  TenantSupportScreen, TenantSubmitTicketScreen, TenantOnboardingScreen,
  TenantPersonalizedHomeScreen,
} from "./screens-tenant";
import {
  OwnerProfileScreen, OwnerMoreScreen, OwnerNotificationsScreen,
  OwnerChatListScreen, PropertyRejectionDetailScreen, OwnerVisitsDashboardScreen,
  OwnerOnboardingScreen, OwnerDashboardScreen, OwnerMyListingsScreen,
  AddPropertyStep1Screen, AddPropertyStep2PhotosScreen, AddPropertyStep3PricingScreen,
  PropertySubmittedScreen, OwnerRequestsListScreen, OwnerRequestDetailScreen,
  OwnerChatThreadScreen, OwnerPropertyAnalyticsScreen, OwnerRevenueScreen,
  OwnerKYCScreen, OwnerSupportScreen, EditPropertyScreen, OwnerAvailabilityScreen,
} from "./screens-owner";
import {
  AdminDashboardScreen, AdminUsersScreen, AdminPropertiesScreen,
  AdminAnalyticsScreen, AdminSettingsScreen, AdminExecutiveDashboardScreen,
  AdminListingModerationScreen, AdminUsersFlagQueueScreen, AdminReportsTicketsScreen,
  AdminRolesManagementScreen, AdminSystemMonitorScreen, SharedNotificationWidget,
  SharedChatInboxWidget, SharedVisitRequestWidget, MissingScreensAuditScreen,
  AdminKYCQueueScreen, AdminKYCReviewDetailScreen, AdminUserProfileScreen,
  AdminBannedUsersScreen, AdminSupportConsoleScreen, AdminSupportTicketDetailScreen,
  AdminFinanceDashboardScreen, AdminTransactionLogScreen, AdminPropertyDetailViewScreen,
  AdminContentModerationScreen, AdminPushNotificationsScreen, AdminActivityLogsScreen,
} from "./screens-admin";
import {
  SplashScreen, RoleSelectScreen,
  TenantLoginScreen, TenantRegisterScreen,
  OwnerLoginScreen, OwnerRegisterScreen,
  NotifDetailScreen, NotifEmptyScreen,
  TenantEditProfileScreen, OwnerEditProfileScreen,
  SettingsPrivacyScreen, OwnerSettingsScreen,
} from "./screens-flow";
import {
  TenantChatAttachmentsSheet, TenantChatVoiceNoteState, TenantChatEmptyScreen,
  NotifSettingsScreen,
  OwnerAcceptRequestSheet, OwnerRejectRequestSheet, OwnerRequestsCalendarScreen,
  OwnerPropertyActionSheet,
  TenantAccountSummaryScreen,
  SettingsChangePasswordScreen, SettingsTermsScreen, SettingsAboutScreen,
  SettingsDeleteAccountScreen, SettingsLogoutSheet,
  SupportTicketDetailScreen,
  SharedBottomNavDemo, SharedStatusBadgesPanel, SharedPropertyMiniCards,
  SharedUserMiniCards, SharedEmptyStatesPanel, SharedLoadingSkeletons,
  SharedBottomSheetsDemo, SharedAdminTableDemo, SharedRoleChipsDemo,
} from "./screens-flow2";

// ── Palette ──────────────────────────────────────────────────────────
const TEAL  = "#0F766E";
const BLUE  = "#2563EB";
const GOLD  = "#D6A84F";
const SLATE = "#475569";
const PURP  = "#7C3AED";
const GREEN = "#16A34A";
const ROSE  = "#E11D48";
const DARK  = "#060B16";
const PANEL = "#0A1120";
const CARD  = "#0E1828";
const BDR   = "#162030";
const TJ: React.CSSProperties = { fontFamily: "Tajawal, sans-serif" };
type AppMode = "store" | "mockup" | "proto" | "flow" | "shared" | "landing" | "devices" | "logos";

// ══════════════════════════════════════════════════════════════════════
// FLOW SECTIONS DATA
// ══════════════════════════════════════════════════════════════════════
type Sc = { id: string; label: string; C: React.ComponentType; desktop?: boolean };
type Section = { n: number; id: string; label: string; ar: string; color: string; screens: Sc[] };
const SECTIONS: Section[] = [
  { n:1,id:"s1",label:"Auth — Tenant",ar:"مصادقة المستأجر",color:BLUE,screens:[{id:"SPLASH",label:"Splash",C:SplashScreen},{id:"ROLE-01",label:"Role Select",C:RoleSelectScreen},{id:"T-ONBOARD-01",label:"Onboarding",C:TenantOnboardingScreen},{id:"T-LOGIN-EMAIL",label:"Login",C:TenantLoginEmailScreen},{id:"T-FORGOT-01",label:"Forgot Password",C:TenantForgotPasswordScreen},{id:"T-OTP-01",label:"OTP Verify",C:TenantOTPScreen},{id:"T-VISITOR-01",label:"Visitor Sheet",C:VisitorRestrictedSheet},{id:"T-REG-01",label:"Register",C:TenantRegisterScreen},{id:"T-KYC-01",label:"KYC Start",C:UpdatedTenantKYC01Screen},{id:"T-KYC-02",label:"KYC Upload",C:UpdatedTenantKYC02Screen},{id:"T-KYC-03",label:"KYC Pending",C:KYCPendingScreen},{id:"T-KYC-04",label:"KYC Approved",C:KYCApprovedScreen}]},
  { n:2,id:"s2",label:"Auth — Owner",ar:"مصادقة المالك",color:GOLD,screens:[{id:"SPLASH-2",label:"Splash",C:SplashScreen},{id:"ROLE-02",label:"Role Select",C:RoleSelectScreen},{id:"O-ONBOARD-01",label:"Onboarding",C:OwnerOnboardingScreen},{id:"O-LOGIN-EMAIL",label:"Login",C:OwnerLoginEmailScreen},{id:"O-FORGOT-01",label:"Forgot Password",C:OwnerForgotPasswordScreen},{id:"O-OTP-01",label:"OTP Verify",C:OwnerOTPScreen},{id:"O-REG-01",label:"Register",C:OwnerRegisterScreen},{id:"O-KYC-01",label:"Owner KYC Start",C:UpdatedOwnerKYC01Screen},{id:"O-KYC-02",label:"Owner KYC Upload",C:OwnerKYC02Screen},{id:"T-KYC-03b",label:"KYC Pending",C:KYCPendingScreen},{id:"T-KYC-04b",label:"KYC Approved",C:KYCApprovedScreen}]},
  { n:3,id:"s3",label:"Home — Tenant",ar:"الرئيسية — مستأجر",color:TEAL,screens:[{id:"T-HOME-01",label:"Home",C:TenantPersonalizedHomeScreen},{id:"T-SEARCH-01",label:"Search",C:TenantSearchScreen},{id:"T-SEARCH-02",label:"Results",C:FullSearchResultsScreen},{id:"T-FILTER-01",label:"Filters (Full)",C:FullFilterSheetScreen},{id:"T-SHARE-01",label:"Share Sheet",C:SharePropertySheet},{id:"T-PROP-01",label:"Property Detail",C:FullPropertyDetailScreen},{id:"T-PROP-02",label:"Gallery",C:PhotoGalleryScreen},{id:"T-PROP-03",label:"Map View",C:PropertyMapScreen},{id:"T-VISIT-02",label:"Book Visit",C:BookVisitScreen},{id:"T-VISIT-03",label:"Confirmed",C:VisitConfirmedScreen},{id:"T-CHAT-02",label:"Chat Property",C:TenantChatThreadScreen}]},
  { n:4,id:"s4",label:"Home — Owner",ar:"الرئيسية — مالك",color:GOLD,screens:[{id:"O-DASH-01",label:"Dashboard",C:OwnerDashboardScreen},{id:"O-PROPS-01",label:"My Listings",C:OwnerMyListingsScreen},{id:"O-REQ-01",label:"Requests",C:OwnerRequestsListScreen},{id:"O-REQ-ICON",label:"Requests+Status+ChatIcon",C:UpdatedOwnerRequestsListScreen},{id:"O-ADD-01",label:"Add Property+Map",C:MergedAddPropertyStep1Screen},{id:"O-ADD-02",label:"Photos+Name+Desc",C:UpdatedAddPropertyStep2Screen},{id:"O-ADD-02V",label:"Video Upload",C:AddPropertyVideoScreen},{id:"O-ADD-03",label:"Pricing+RentalPeriod+Amenities",C:MergedAddPropertyStep3Screen},{id:"O-ADD-03U",label:"Details+Smoking+Ownership",C:UpdatedAddPropertyStep3Screen},{id:"O-ADD-04",label:"Submitted",C:PropertySubmittedScreen}]},
  { n:5,id:"s5",label:"Saved — Tenant",ar:"المحفوظات",color:ROSE,screens:[{id:"T-SAVED-01",label:"Saved Listings",C:SavedListingsScreen},{id:"T-SAVED-02",label:"Empty State",C:SavedEmptyStateScreen},{id:"T-FILTER-01b",label:"Sort / Filter",C:FilterSheetScreen}]},
  { n:6,id:"s6",label:"Chat — Tenant",ar:"الدردشة — مستأجر",color:TEAL,screens:[{id:"T-CHAT-01",label:"Inbox",C:TenantChatListScreen},{id:"T-CHAT-EMPTY",label:"Empty",C:TenantChatEmptyScreen},{id:"T-CHAT-04",label:"Search",C:TenantChatSearchScreen},{id:"T-CHAT-02b",label:"Thread",C:TenantChatThreadScreen},{id:"T-CHAT-VOICE",label:"Voice Note",C:TenantChatVoiceNoteState},{id:"T-CHAT-ATTACH",label:"Attachments",C:TenantChatAttachmentsSheet},{id:"T-CHAT-03",label:"Restricted",C:TenantChatRestrictedScreen},{id:"T-REPORT-01",label:"Report Sheet",C:ReportSheetScreen}]},
  { n:7,id:"s7",label:"Chat — Owner",ar:"الدردشة — مالك",color:GOLD,screens:[{id:"O-CHAT-01",label:"Inbox",C:OwnerChatListScreen},{id:"O-CHAT-02",label:"Thread",C:OwnerChatThreadScreen},{id:"T-REPORT-02",label:"Report",C:ReportSheetScreen}]},
  { n:8,id:"s8",label:"Notifications — Tenant",ar:"إشعارات المستأجر",color:BLUE,screens:[{id:"T-NOTIF-01",label:"Notifications",C:TenantNotificationsScreen},{id:"T-NOTIF-02",label:"Detail",C:NotifDetailScreen},{id:"T-NOTIF-03",label:"Empty",C:NotifEmptyScreen},{id:"T-NOTIF-SETT",label:"Settings",C:NotifSettingsScreen}]},
  { n:9,id:"s9",label:"Notifications — Owner",ar:"إشعارات المالك",color:GOLD,screens:[{id:"O-NOTIF-01",label:"Notifications",C:OwnerNotificationsScreen},{id:"O-NOTIF-02",label:"Detail",C:NotifDetailScreen},{id:"O-NOTIF-03",label:"Empty",C:NotifEmptyScreen},{id:"O-NOTIF-SETT",label:"Settings",C:NotifSettingsScreen}]},
  { n:10,id:"s10",label:"Visits — Tenant",ar:"الزيارات",color:GREEN,screens:[{id:"T-VISIT-01",label:"My Visits",C:TenantMyVisitsScreen},{id:"T-VISIT-02b",label:"Book Visit",C:BookVisitScreen},{id:"T-VISIT-03b",label:"Confirmed",C:VisitConfirmedScreen},{id:"T-VISIT-04",label:"Detail",C:VisitDetailScreen},{id:"T-RATE-01",label:"Rate",C:RatePropertyScreen}]},
  { n:11,id:"s11",label:"Requests — Owner",ar:"الطلبات",color:GOLD,screens:[{id:"O-REQ-01b",label:"Requests",C:OwnerRequestsListScreen},{id:"O-REQ-ICON-B",label:"Requests+Status+ChatIcon",C:UpdatedOwnerRequestsListScreen},{id:"O-REQ-02",label:"Detail",C:OwnerRequestDetailScreen},{id:"O-ACCEPT",label:"Accept",C:OwnerAcceptRequestSheet},{id:"O-REJECT",label:"Reject",C:OwnerRejectRequestSheet},{id:"O-CAL-01",label:"Calendar",C:OwnerRequestsCalendarScreen},{id:"O-AVAIL-01",label:"Availability",C:OwnerAvailabilityScreen}]},
  { n:12,id:"s12",label:"Properties — Owner",ar:"العقارات",color:GOLD,screens:[{id:"O-PROPS-01b",label:"My Listings",C:OwnerMyListingsScreen},{id:"O-ACTION-01",label:"Actions",C:OwnerPropertyActionSheet},{id:"O-EDIT-01",label:"Edit",C:EditPropertyScreen},{id:"O-ADD-04b",label:"Submitted",C:PropertySubmittedScreen},{id:"O-REJECT-01",label:"Rejection",C:PropertyRejectionDetailScreen},{id:"O-ANAL-01",label:"Analytics",C:OwnerPropertyAnalyticsScreen},{id:"O-REV-01",label:"Revenue",C:OwnerRevenueScreen}]},
  { n:13,id:"s13",label:"Profile — Tenant",ar:"الملف — مستأجر",color:TEAL,screens:[{id:"T-PROFILE-01",label:"Profile",C:TenantProfileScreen},{id:"T-SUMMARY-01",label:"Summary",C:TenantAccountSummaryScreen},{id:"T-EDIT-01",label:"Edit Profile",C:TenantEditProfileScreen},{id:"T-KYC-04c",label:"Verified",C:KYCApprovedScreen}]},
  { n:14,id:"s14",label:"Profile — Owner",ar:"الملف — مالك",color:GOLD,screens:[{id:"O-PROFILE-01",label:"Profile",C:OwnerProfileScreen},{id:"O-MORE-01",label:"More",C:OwnerMoreScreen},{id:"O-EDIT-P-01",label:"Edit Profile",C:OwnerEditProfileScreen},{id:"O-KYC-01b",label:"KYC Status",C:OwnerKYCScreen}]},
  { n:15,id:"s15",label:"Settings — Tenant",ar:"الإعدادات — مستأجر",color:SLATE,screens:[{id:"T-SETTINGS-01",label:"Settings",C:TenantSettingsScreen},{id:"T-PRIV-01",label:"Privacy",C:SettingsPrivacyScreen},{id:"T-PWD-01",label:"Password",C:SettingsChangePasswordScreen},{id:"T-TERMS-01",label:"Terms",C:SettingsTermsScreen},{id:"T-ABOUT-01",label:"About",C:SettingsAboutScreen},{id:"T-DELETE-01",label:"Delete",C:SettingsDeleteAccountScreen},{id:"T-LOGOUT-01",label:"Logout",C:SettingsLogoutSheet}]},
  { n:16,id:"s16",label:"Settings — Owner",ar:"الإعدادات — مالك",color:SLATE,screens:[{id:"O-SETTINGS-01",label:"Settings",C:OwnerSettingsScreen},{id:"O-PRIV-01",label:"Privacy",C:SettingsPrivacyScreen},{id:"O-PWD-01",label:"Password",C:SettingsChangePasswordScreen},{id:"O-TERMS-01",label:"Terms",C:SettingsTermsScreen},{id:"O-ABOUT-01",label:"About",C:SettingsAboutScreen},{id:"O-DELETE-01",label:"Delete",C:SettingsDeleteAccountScreen},{id:"O-LOGOUT-01",label:"Logout",C:SettingsLogoutSheet}]},
  { n:17,id:"s17",label:"Support — Tenant",ar:"الدعم — مستأجر",color:TEAL,screens:[{id:"T-SUPPORT-01",label:"Help Center",C:TenantSupportScreen},{id:"T-SUPPORT-02",label:"New Ticket",C:TenantSubmitTicketScreen},{id:"T-TICKET-01",label:"Ticket",C:SupportTicketDetailScreen}]},
  { n:18,id:"s18",label:"Support — Owner",ar:"الدعم — مالك",color:GOLD,screens:[{id:"O-SUPPORT-01",label:"Help Center",C:OwnerSupportScreen},{id:"O-SUPPORT-02",label:"New Ticket",C:TenantSubmitTicketScreen},{id:"O-TICKET-01",label:"Ticket",C:SupportTicketDetailScreen}]},
  { n:19,id:"s19",label:"Admin Dashboard",ar:"لوحة الإدارة",color:SLATE,screens:[{id:"A-DASH-01",label:"Dashboard",C:AdminDashboardScreen,desktop:true},{id:"A-DASH-02",label:"Executive",C:AdminExecutiveDashboardScreen,desktop:true},{id:"A-USERS-01",label:"Users",C:AdminUsersScreen,desktop:true},{id:"A-USERS-02",label:"Flag Queue",C:AdminUsersFlagQueueScreen,desktop:true},{id:"A-USERS-03",label:"User Profile",C:AdminUserProfileScreen,desktop:true},{id:"A-USERS-04",label:"Banned",C:AdminBannedUsersScreen,desktop:true},{id:"A-PROPS-01",label:"Properties",C:AdminPropertiesScreen,desktop:true},{id:"A-PROPS-02",label:"Moderation",C:AdminListingModerationScreen,desktop:true},{id:"A-PROPS-03",label:"Prop Detail",C:AdminPropertyDetailViewScreen,desktop:true},{id:"A-KYC-01",label:"KYC Queue",C:AdminKYCQueueScreen,desktop:true},{id:"A-KYC-02",label:"KYC Review",C:AdminKYCReviewDetailScreen,desktop:true},{id:"A-REPORTS-01",label:"Reports",C:AdminReportsTicketsScreen,desktop:true},{id:"A-SUPP-01",label:"Support",C:AdminSupportConsoleScreen,desktop:true},{id:"A-SUPP-02",label:"Ticket",C:AdminSupportTicketDetailScreen,desktop:true},{id:"A-FIN-01",label:"Finance",C:AdminFinanceDashboardScreen,desktop:true},{id:"A-FIN-02",label:"Transactions",C:AdminTransactionLogScreen,desktop:true},{id:"A-ANAL-01",label:"Analytics",C:AdminAnalyticsScreen,desktop:true},{id:"A-CONTENT-01",label:"Content",C:AdminContentModerationScreen,desktop:true},{id:"A-PUSH-01",label:"Push",C:AdminPushNotificationsScreen,desktop:true},{id:"A-LOGS-01",label:"Logs",C:AdminActivityLogsScreen,desktop:true},{id:"A-ROLES-01",label:"Roles",C:AdminRolesManagementScreen,desktop:true},{id:"A-MON-01",label:"Monitor",C:AdminSystemMonitorScreen,desktop:true},{id:"A-SETTINGS-01",label:"Settings",C:AdminSettingsScreen,desktop:true},{id:"A-AUDIT-01",label:"Audit",C:MissingScreensAuditScreen,desktop:true}]},
  { n:20,id:"s20",label:"Shared Components",ar:"مكوّنات مشتركة",color:PURP,screens:[{id:"SH-NOTIF-01",label:"Notification Widget",C:SharedNotificationWidget},{id:"SH-CHAT-01",label:"Chat Widget",C:SharedChatInboxWidget},{id:"SH-VISIT-01",label:"Visit Widget",C:SharedVisitRequestWidget},{id:"SH-NAV-01",label:"Bottom Nav",C:SharedBottomNavDemo},{id:"SH-BADGE-01",label:"Status Badges",C:SharedStatusBadgesPanel},{id:"SH-PROP-01",label:"Property Cards",C:SharedPropertyMiniCards},{id:"SH-USER-01",label:"User Cards",C:SharedUserMiniCards},{id:"SH-EMPTY-01",label:"Empty States",C:SharedEmptyStatesPanel},{id:"SH-SKEL-01",label:"Skeletons",C:SharedLoadingSkeletons},{id:"SH-SHEET-01",label:"Sheets",C:SharedBottomSheetsDemo},{id:"SH-TABLE-01",label:"Admin Table",C:SharedAdminTableDemo},{id:"SH-ROLE-01",label:"Role Chips",C:SharedRoleChipsDemo}]},
];
const TOTAL = SECTIONS.reduce((s, sec) => s + sec.screens.length, 0);

// ══════════════════════════════════════════════════════════════════════
// DEVICE FRAMES
// ══════════════════════════════════════════════════════════════════════
function IPhoneFrame({ comp: Comp, scale = 1 }: { comp: React.ComponentType; scale?: number }) {
  const SW = 390, SH = 844;
  const innerW = 172;
  const innerH = Math.round(SH * (innerW / SW));
  const sc = innerW / SW;
  const frameW = innerW + 14;
  const frameH = innerH + 56;
  return (
    <div style={{ width:frameW*scale, height:frameH*scale, background:"#111113", borderRadius:44*scale, boxShadow:`0 0 0 ${2*scale}px #3A3A3C, 0 0 0 ${3.5*scale}px #222224, 0 ${20*scale}px ${60*scale}px rgba(0,0,0,0.65)`, display:"flex", flexDirection:"column", alignItems:"center", padding:`${14*scale}px ${7*scale}px ${18*scale}px`, boxSizing:"border-box", position:"relative", overflow:"hidden", flexShrink:0 }}>
      <div style={{ position:"absolute", left:-1.5*scale, top:80*scale, width:3*scale, height:28*scale, background:"#2A2A2C", borderRadius:`0 ${2*scale}px ${2*scale}px 0` }} />
      <div style={{ position:"absolute", left:-1.5*scale, top:115*scale, width:3*scale, height:42*scale, background:"#2A2A2C", borderRadius:`0 ${2*scale}px ${2*scale}px 0` }} />
      <div style={{ position:"absolute", left:-1.5*scale, top:164*scale, width:3*scale, height:42*scale, background:"#2A2A2C", borderRadius:`0 ${2*scale}px ${2*scale}px 0` }} />
      <div style={{ position:"absolute", right:-1.5*scale, top:100*scale, width:3*scale, height:64*scale, background:"#2A2A2C", borderRadius:`${2*scale}px 0 0 ${2*scale}px` }} />
      <div style={{ width:72*scale, height:9*scale, background:"#000", borderRadius:9*scale, marginBottom:6*scale, flexShrink:0 }} />
      <div style={{ width:innerW*scale, height:innerH*scale, borderRadius:10*scale, overflow:"hidden", background:"#F8F9FA", flexShrink:0 }}>
        <div style={{ width:SW, height:SH, overflow:"hidden", transform:`scale(${sc*scale})`, transformOrigin:"top left" }}><Comp /></div>
      </div>
      <div style={{ width:64*scale, height:4*scale, background:"#3A3A3C", borderRadius:4*scale, marginTop:10*scale, flexShrink:0 }} />
    </div>
  );
}

function MacBookFrame({ comp: Comp, scale = 1 }: { comp: React.ComponentType; scale?: number }) {
  const SW = 1280, SH = 760, sc = 0.34;
  const dw = Math.round(SW*sc), dh = Math.round(SH*sc), bp = 14;
  const bezelW = (dw+bp*2)*scale;
  return (
    <div style={{ display:"flex", flexDirection:"column", alignItems:"center" }}>
      <div style={{ background:"#1C1C1E", borderRadius:`${14*scale}px ${14*scale}px 0 0`, padding:`${bp*scale}px ${bp*scale}px ${10*scale}px`, boxShadow:`0 0 0 ${1.5*scale}px #333335`, display:"flex", flexDirection:"column", alignItems:"center" }}>
        <div style={{ width:6*scale, height:6*scale, borderRadius:"50%", background:"#3A3A3C", marginBottom:8*scale }} />
        <div style={{ width:dw*scale, height:dh*scale, borderRadius:4*scale, overflow:"hidden", background:"#F8FAFC" }}>
          <div style={{ width:SW, height:SH, transform:`scale(${sc*scale})`, transformOrigin:"top left" }}><Comp /></div>
        </div>
      </div>
      <div style={{ width:bezelW, height:4*scale, background:"#2A2A2C", borderTop:`${1*scale}px solid #444` }} />
      <div style={{ width:bezelW+40*scale, height:14*scale, background:"#222224", borderRadius:`0 0 ${6*scale}px ${6*scale}px`, boxShadow:`0 ${4*scale}px ${16*scale}px rgba(0,0,0,0.5)` }} />
      <div style={{ width:bezelW+80*scale, height:4*scale, background:"#1A1A1C", borderRadius:`0 0 ${4*scale}px ${4*scale}px` }} />
    </div>
  );
}

// ══════════════════════════════════════════════════════════════════════
// STORE ASSETS VIEW
// ══════════════════════════════════════════════════════════════════════

type StoreShot = {
  num: string; headline: string; sub: string; caption: string;
  comp: React.ComponentType; bg: string; accent: string;
  type: "tenant" | "owner"; features: string[];
  platform: "both" | "ios" | "android";
};

const SHOTS: StoreShot[] = [
  { num:"T-01", headline:"دور على سكنك بسهولة", sub:"آلاف الوحدات السكنية في مكان واحد", caption:"Tenant Home / Search", comp:TenantPersonalizedHomeScreen, bg:"linear-gradient(170deg,#0D6B63 0%,#065F57 35%,#071820 100%)", accent:TEAL, type:"tenant", features:["بحث ذكي","فلترة متقدمة","عقارات قريبة"], platform:"both" },
  { num:"T-02", headline:"كل تفاصيل العقار قدامك", sub:"سعر · غرف · موقع · مرافق", caption:"Property Details", comp:PropertyDetailScreen, bg:"linear-gradient(170deg,#062F2B 0%,#0F766E 55%,#051014 100%)", accent:TEAL, type:"tenant", features:["موثّق ✓","معاينة الخريطة","معرض الصور"], platform:"both" },
  { num:"T-03", headline:"تواصل بأمان بدون إظهار رقمك", sub:"خصوصيتك محمية داخل سكون", caption:"Safe Chat & Privacy", comp:TenantChatThreadScreen, bg:"linear-gradient(170deg,#1E40AF 0%,#0F766E 65%,#060B16 100%)", accent:BLUE, type:"tenant", features:["رقمك مخفي","مالك موثّق","تشفير كامل"], platform:"both" },
  { num:"T-04", headline:"احجز زيارة في خطوات بسيطة", sub:"اختار الوقت المناسب وأرسل طلبك", caption:"Visit Booking", comp:BookVisitScreen, bg:"linear-gradient(170deg,#145A32 0%,#0F766E 60%,#060B16 100%)", accent:GREEN, type:"tenant", features:["اختيار التاريخ","فتحات زمنية","تأكيد فوري"], platform:"both" },
  { num:"T-05", headline:"احفظ اختياراتك وتابع حسابك", sub:"كل اختياراتك في مكان واحد", caption:"Saved & Profile", comp:SavedListingsScreen, bg:"linear-gradient(170deg,#0F766E 0%,#064E3B 40%,#111827 100%)", accent:TEAL, type:"tenant", features:["قائمة المحفوظات","حالة التوثيق","إعدادات الخصوصية"], platform:"both" },
  { num:"O-01", headline:"إدارة عقاراتك من مكان واحد", sub:"تابع الأداء، الزيارات، والرسائل", caption:"Owner Dashboard", comp:OwnerDashboardScreen, bg:"linear-gradient(170deg,#7C2D00 0%,#D97706 40%,#111827 100%)", accent:GOLD, type:"owner", features:["إجمالي المشاهدات","طلبات الزيارة","رسائل غير مقروءة"], platform:"both" },
  { num:"O-02", headline:"تابع حالة كل عقار", sub:"مقبول · قيد المراجعة · مخفي · تم تأجيره", caption:"My Properties", comp:OwnerMyListingsScreen, bg:"linear-gradient(170deg,#92400E 0%,#D6A84F 50%,#111827 100%)", accent:GOLD, type:"owner", features:["حالات العقار","تعديل سريع","تحليلات فورية"], platform:"both" },
  { num:"O-03", headline:"أضف عقارك وادخله للمراجعة", sub:"صور · موقع · تفاصيل · إرسال", caption:"Add / Submit Property", comp:AddPropertyStep1Screen, bg:"linear-gradient(170deg,#0F172A 0%,#1E3A5F 50%,#0F766E 100%)", accent:TEAL, type:"owner", features:["رفع الصور","تحديد الموقع","مراجعة فورية"], platform:"both" },
  { num:"O-04", headline:"اقبل أو ارفض طلبات الزيارة", sub:"تحكم كامل في جدول الزيارات", caption:"Visit Requests", comp:OwnerRequestsListScreen, bg:"linear-gradient(170deg,#7C2D00 0%,#B45309 50%,#1C1917 100%)", accent:GOLD, type:"owner", features:["قبول / رفض","مستأجر موثّق","شات مباشر"], platform:"both" },
  { num:"O-05", headline:"تواصل مع المستأجرين بأمان", sub:"خصوصيتك وخصوصية المستأجر محمية", caption:"Owner Chat & Support", comp:OwnerChatThreadScreen, bg:"linear-gradient(170deg,#0F766E 0%,#B45309 55%,#111827 100%)", accent:GOLD, type:"owner", features:["أرقام مخفية","دعم فني","إبلاغ عن مخالفة"], platform:"both" },
];

const ANDROID_INDICES = [0, 1, 2, 3, 5, 6, 7, 8]; // 4T + 4O

function SokoonLogoMark({ size = 28 }: { size?: number }) {
  return (
    <div style={{ width:size, height:size, borderRadius:size*0.25, background:TEAL, display:"flex", alignItems:"center", justifyContent:"center", flexShrink:0 }}>
      <svg width={size*0.6} height={size*0.6} viewBox="0 0 18 18" fill="none">
        <path d="M9,2 L16,8 L14,8 L14,16 L4,16 L4,8 L2,8 Z" fill="white"/>
        <rect x="5.5" y="10" width="2.5" height="2" rx="0.7" fill={TEAL}/>
        <rect x="10" y="10" width="2.5" height="2" rx="0.7" fill={TEAL}/>
        <path d="M7,16 L7,13 Q9,11.5 11,13 L11,16 Z" fill={TEAL}/>
      </svg>
    </div>
  );
}

// ── iPhone 17 Pro Max frame ────────────────────────────────────────────
// Titanium finish · Dynamic Island · Camera Control button · Ultra-thin bezels
function IPhone16Frame({ comp: Comp, scale = 1 }: { comp: React.ComponentType; scale?: number }) {
  // Keep alias for any legacy callers outside StoreView
  return <IPhone17ProFrame comp={Comp} scale={scale} />;
}
function IPhone17ProFrame({ comp: Comp, scale = 1 }: { comp: React.ComponentType; scale?: number }) {
  const SW = 390, SH = 844;
  // iPhone 17 Pro Max: ultra-thin bezels, 12px side padding each side
  const sidePad = 12, topPad = 14, bottomPad = 20;
  const innerW = 180, innerH = Math.round(SH * (innerW / SW));
  const sc = innerW / SW;
  const FW = 204, FH = innerH + topPad + bottomPad + 16; // 16 = home indicator + gap
  // Frame BR = 56 → screen BR = frameBR - sidePad - 2 = 42 (corners align)
  const frameBR = 56, screenBR = 42;
  // Dynamic Island: ~35% of screen width, proportional height
  const diW = Math.round(innerW * 0.34); // ~61px
  const diH = Math.round(innerW * 0.122); // ~22px
  const diTop = Math.round(innerW * 0.044); // ~8px from screen top
  const diR = Math.round(diH / 2);
  const btn = (style: React.CSSProperties) => <div style={style} />;
  return (
    <div style={{ width:FW*scale, height:FH*scale, borderRadius:Math.round(frameBR*scale), background:"linear-gradient(145deg,#C2C2C4 0%,#8A8A8C 15%,#626264 45%,#7A7A7C 75%,#B0B0B2 100%)", boxShadow:`0 0 0 ${1.5*scale}px #D0D0D2, inset 0 0 0 ${1*scale}px #2A2A2C, 0 36px 90px rgba(0,0,0,0.8), 0 8px 24px rgba(0,0,0,0.45)`, display:"flex", flexDirection:"column", alignItems:"center", padding:`${Math.round(topPad*scale)}px ${Math.round(sidePad*scale)}px ${Math.round(bottomPad*scale)}px`, boxSizing:"border-box", position:"relative", flexShrink:0 }}>
      {/* Action button — left, slim pill */}
      {btn({ position:"absolute", left:-Math.round(3.5*scale), top:Math.round(70*scale), width:Math.round(3.5*scale), height:Math.round(20*scale), background:"linear-gradient(180deg,#9A9A9C,#747476)", borderRadius:Math.round(2*scale) })}
      {/* Volume Up */}
      {btn({ position:"absolute", left:-Math.round(3.5*scale), top:Math.round(100*scale), width:Math.round(3.5*scale), height:Math.round(36*scale), background:"linear-gradient(180deg,#9A9A9C,#747476)", borderRadius:Math.round(2*scale) })}
      {/* Volume Down */}
      {btn({ position:"absolute", left:-Math.round(3.5*scale), top:Math.round(145*scale), width:Math.round(3.5*scale), height:Math.round(36*scale), background:"linear-gradient(180deg,#9A9A9C,#747476)", borderRadius:Math.round(2*scale) })}
      {/* Side / Power button */}
      {btn({ position:"absolute", right:-Math.round(3.5*scale), top:Math.round(106*scale), width:Math.round(3.5*scale), height:Math.round(58*scale), background:"linear-gradient(180deg,#9A9A9C,#747476)", borderRadius:Math.round(2*scale) })}
      {/* Camera Control button (iPhone 17 exclusive) */}
      {btn({ position:"absolute", right:-Math.round(3.5*scale), top:Math.round(178*scale), width:Math.round(3.5*scale), height:Math.round(28*scale), background:"linear-gradient(180deg,#808082,#5C5C5E)", borderRadius:Math.round(2*scale) })}

      {/* Screen — corners closely match frame corners via screenBR */}
      <div style={{ width:innerW*scale, height:innerH*scale, borderRadius:Math.round(screenBR*scale), overflow:"hidden", background:"#F8F9FA", flexShrink:0, position:"relative", boxShadow:`inset 0 0 0 ${0.5*scale}px rgba(0,0,0,0.08)` }}>
        <div style={{ width:SW, height:SH, overflow:"hidden", transform:`scale(${sc*scale})`, transformOrigin:"top left" }}><Comp /></div>
        {/* Dynamic Island — correctly proportioned pill */}
        <div style={{ position:"absolute", top:diTop*scale, left:"50%", transform:"translateX(-50%)", width:diW*scale, height:diH*scale, background:"#000", borderRadius:diR*scale, zIndex:10 }}>
          {/* Front camera micro-dot */}
          <div style={{ position:"absolute", right:Math.round(9*scale), top:"50%", transform:"translateY(-50%)", width:Math.round(8*scale), height:Math.round(8*scale), borderRadius:"50%", background:"radial-gradient(circle at 35% 35%,#1E1E38,#000)" }} />
        </div>
      </div>

      {/* Home indicator bar */}
      <div style={{ width:Math.round(60*scale), height:Math.round(4*scale), background:"rgba(255,255,255,0.28)", borderRadius:Math.round(2*scale), marginTop:Math.round(10*scale), flexShrink:0 }} />
    </div>
  );
}

// ── Samsung Galaxy Ultra frame ──────────────────────────────────────────
// Phantom Black finish · Centered punch-hole · Flat titanium rails · S-Pen slot
function AndroidFrame({ comp: Comp, scale = 1 }: { comp: React.ComponentType; scale?: number }) {
  // Keep alias for any legacy callers outside StoreView
  return <SamsungGalaxyFrame comp={Comp} scale={scale} />;
}
function SamsungGalaxyFrame({ comp: Comp, scale = 1 }: { comp: React.ComponentType; scale?: number }) {
  const SW = 390, SH = 844;
  // Galaxy S25 Ultra: flat titanium rails, less-rounded corners (BR=26 vs iPhone's 56)
  const sidePad = 11, topPad = 16, bottomPad = 16;
  const innerW = 178, innerH = Math.round(SH * (innerW / SW));
  const sc = innerW / SW;
  const FW = 200, FH = innerH + topPad + bottomPad + 14; // 14 = gesture bar + gap
  // Much less rounded than iPhone — Galaxy Ultra's squared silhouette
  const frameBR = 26, screenBR = 19;
  // Punch-hole: small centered circle, no island
  const phSize = Math.round(innerW * 0.062); // ~11px
  const phTop = Math.round(innerW * 0.05);   // ~9px from screen top
  const btn = (style: React.CSSProperties) => <div style={style} />;
  return (
    <div style={{ width:FW*scale, height:FH*scale, borderRadius:Math.round(frameBR*scale), background:"linear-gradient(158deg,#242426 0%,#161618 35%,#0E0E10 62%,#1C1C1E 100%)", boxShadow:`0 0 0 ${1.5*scale}px #323234, inset 0 0 0 ${0.8*scale}px #060608, 0 36px 90px rgba(0,0,0,0.9), 0 8px 24px rgba(0,0,0,0.55)`, display:"flex", flexDirection:"column", alignItems:"center", padding:`${Math.round(topPad*scale)}px ${Math.round(sidePad*scale)}px ${Math.round(bottomPad*scale)}px`, boxSizing:"border-box", position:"relative", flexShrink:0 }}>
      {/* Flat titanium rail highlight — left edge */}
      <div style={{ position:"absolute", left:0, top:Math.round(frameBR*scale*0.5), bottom:Math.round(frameBR*scale*0.5), width:1.5*scale, background:"linear-gradient(180deg,transparent,rgba(255,255,255,0.08) 30%,rgba(255,255,255,0.12) 55%,rgba(255,255,255,0.06) 80%,transparent)", pointerEvents:"none" }} />
      {/* Flat titanium rail highlight — right edge */}
      <div style={{ position:"absolute", right:0, top:Math.round(frameBR*scale*0.5), bottom:Math.round(frameBR*scale*0.5), width:1.5*scale, background:"linear-gradient(180deg,transparent,rgba(255,255,255,0.06) 30%,rgba(255,255,255,0.1) 55%,rgba(255,255,255,0.04) 80%,transparent)", pointerEvents:"none" }} />

      {/* Volume Up — left, flat no bevel */}
      {btn({ position:"absolute", left:-Math.round(3*scale), top:Math.round(90*scale), width:Math.round(3*scale), height:Math.round(38*scale), background:"#262628", borderRadius:`0 ${Math.round(1.5*scale)}px ${Math.round(1.5*scale)}px 0` })}
      {/* Volume Down — left */}
      {btn({ position:"absolute", left:-Math.round(3*scale), top:Math.round(136*scale), width:Math.round(3*scale), height:Math.round(38*scale), background:"#262628", borderRadius:`0 ${Math.round(1.5*scale)}px ${Math.round(1.5*scale)}px 0` })}
      {/* Power button — right, shorter than iPhone */}
      {btn({ position:"absolute", right:-Math.round(3*scale), top:Math.round(118*scale), width:Math.round(3*scale), height:Math.round(40*scale), background:"#262628", borderRadius:`${Math.round(1.5*scale)}px 0 0 ${Math.round(1.5*scale)}px` })}

      {/* Screen — corners match frame via screenBR */}
      <div style={{ width:innerW*scale, height:innerH*scale, borderRadius:Math.round(screenBR*scale), overflow:"hidden", background:"#F8F9FA", flexShrink:0, position:"relative", boxShadow:`inset 0 0 0 ${0.5*scale}px rgba(0,0,0,0.08)` }}>
        <div style={{ width:SW, height:SH, overflow:"hidden", transform:`scale(${sc*scale})`, transformOrigin:"top left" }}><Comp /></div>
        {/* Centered punch-hole — small precise circle */}
        <div style={{ position:"absolute", top:phTop*scale, left:"50%", transform:"translateX(-50%)", width:phSize*scale, height:phSize*scale, borderRadius:"50%", background:"radial-gradient(circle at 38% 38%,#141428,#000)", zIndex:10, boxShadow:`0 0 0 ${0.5*scale}px #0A0A0C` }} />
      </div>

      {/* Android gesture pill — narrower than iPhone's bar */}
      <div style={{ width:Math.round(40*scale), height:Math.round(3.5*scale), background:"rgba(255,255,255,0.18)", borderRadius:Math.round(2*scale), marginTop:Math.round(11*scale), flexShrink:0 }} />
    </div>
  );
}

// ── Marketing screenshot card — full visible phone, no cropping ────────
function MarketingCard({ shot, platform = "ios" }: { shot: StoreShot; platform?: "ios" | "android" }) {
  // Card fixed at 248×560 — phone at scale 0.74 (fully visible inside)
  const CARD_W = 248, CARD_H = 560, PHONE_SCALE = 0.80;
  const Frame = platform === "android" ? SamsungGalaxyFrame : IPhone17ProFrame;

  return (
    <div style={{ width:CARD_W, height:CARD_H, borderRadius:22, overflow:"hidden", position:"relative", background:shot.bg, boxShadow:"0 32px 80px rgba(0,0,0,0.65), 0 0 0 1px rgba(255,255,255,0.07)", flexShrink:0, display:"flex", flexDirection:"column" }}>
      {/* Ambient glow top-right */}
      <div style={{ position:"absolute", top:-60, right:-60, width:220, height:220, borderRadius:"50%", background:"rgba(255,255,255,0.05)", pointerEvents:"none" }} />
      {/* Ambient glow bottom-left */}
      <div style={{ position:"absolute", bottom:-40, left:-40, width:160, height:160, borderRadius:"50%", background:"rgba(255,255,255,0.03)", pointerEvents:"none" }} />

      {/* ── Text block ── */}
      <div style={{ padding:"18px 18px 0", direction:"rtl", flexShrink:0, position:"relative", zIndex:1 }}>
        {/* Logo row */}
        <div style={{ display:"flex", alignItems:"center", gap:6, marginBottom:10 }}>
          <SokoonLogoMark size={22} />
          <span style={{ fontSize:10, fontWeight:800, color:"rgba(255,255,255,0.88)", ...TJ }}>سكون</span>
          <div style={{ marginRight:"auto", display:"flex", alignItems:"center", gap:4 }}>
            {/* Platform chip */}
            <span style={{ fontSize:7, fontWeight:800, color:"rgba(255,255,255,0.5)", background:"rgba(255,255,255,0.08)", borderRadius:8, padding:"2px 6px", letterSpacing:0.3 }}>
              {platform === "ios" ? "iPhone 17 Pro Max" : "Galaxy Ultra"}
            </span>
            <span style={{ fontSize:7, fontWeight:800, color:shot.accent, background:"rgba(255,255,255,0.1)", borderRadius:8, padding:"2px 6px" }}>
              {shot.type === "tenant" ? "مستأجر" : "مالك"}
            </span>
          </div>
        </div>
        {/* Headline */}
        <div style={{ fontSize:16, fontWeight:900, color:"white", lineHeight:1.45, marginBottom:5, ...TJ }}>{shot.headline}</div>
        {/* Sub */}
        <div style={{ fontSize:10, color:"rgba(255,255,255,0.62)", lineHeight:1.5, marginBottom:9, ...TJ }}>{shot.sub}</div>
        {/* Feature pills */}
        <div style={{ display:"flex", gap:4, flexWrap:"wrap" }}>
          {shot.features.map(f => (
            <span key={f} style={{ fontSize:7.5, fontWeight:700, color:"rgba(255,255,255,0.82)", background:"rgba(255,255,255,0.11)", borderRadius:10, padding:"2px 7px", ...TJ }}>{f}</span>
          ))}
        </div>
      </div>

      {/* ── Full phone — never cropped ── */}
      <div style={{ flex:1, display:"flex", alignItems:"flex-end", justifyContent:"center", paddingBottom:12, position:"relative", zIndex:1 }}>
        {/* Subtle glow under phone */}
        <div style={{ position:"absolute", bottom:0, left:"50%", transform:"translateX(-50%)", width:160, height:60, background:`radial-gradient(ellipse,${shot.accent}30,transparent 70%)`, borderRadius:"50%" }} />
        <Frame comp={shot.comp} scale={PHONE_SCALE} />
      </div>

      {/* Shot ID */}
      <div style={{ position:"absolute", top:14, left:14, fontSize:7.5, fontWeight:900, color:"rgba(255,255,255,0.22)", letterSpacing:0.5 }}>{shot.num}</div>
    </div>
  );
}

// ── App Icon SVGs ──────────────────────────────────────────────────────
function IconHouseShield({ size = 200 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 1024 1024" style={{ display:"block" }}>
      <defs>
        <linearGradient id="ig1a" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="#0D9488"/>
          <stop offset="100%" stopColor="#0F766E"/>
        </linearGradient>
        <radialGradient id="ig1b" cx="35%" cy="30%" r="60%">
          <stop offset="0%" stopColor="rgba(255,255,255,0.18)"/>
          <stop offset="100%" stopColor="rgba(0,0,0,0)"/>
        </radialGradient>
      </defs>
      <rect width="1024" height="1024" rx="220" fill="url(#ig1a)"/>
      <rect width="1024" height="1024" rx="220" fill="url(#ig1b)"/>
      {/* House */}
      <path d="M512 180 L830 460 L760 460 L760 800 L264 800 L264 460 L194 460 Z" fill="white" opacity="0.93"/>
      {/* Door */}
      <rect x="432" y="610" width="160" height="190" rx="80" fill="#0F766E"/>
      {/* Windows */}
      <rect x="300" y="530" width="100" height="85" rx="12" fill="#0D9488" opacity="0.7"/>
      <rect x="624" y="530" width="100" height="85" rx="12" fill="#0D9488" opacity="0.7"/>
      {/* Shield */}
      <circle cx="790" cy="790" r="130" fill="#D6A84F"/>
      <circle cx="790" cy="790" r="118" fill="#C89A3F"/>
      <path d="M790 680 Q870 705 870 790 Q870 868 790 906 Q710 868 710 790 Q710 705 790 680Z" fill="white" opacity="0.95"/>
      {/* Check */}
      <path d="M755 795 L778 818 L828 762" stroke="#0F766E" strokeWidth="20" strokeLinecap="round" strokeLinejoin="round" fill="none"/>
    </svg>
  );
}

function IconSinMark({ size = 200 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 1024 1024" style={{ display:"block" }}>
      <defs>
        <linearGradient id="ig2a" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="#0F172A"/>
          <stop offset="100%" stopColor="#1E3A5F"/>
        </linearGradient>
        <radialGradient id="ig2b" cx="50%" cy="40%" r="55%">
          <stop offset="0%" stopColor="rgba(15,118,110,0.3)"/>
          <stop offset="100%" stopColor="rgba(0,0,0,0)"/>
        </radialGradient>
      </defs>
      <rect width="1024" height="1024" rx="220" fill="url(#ig2a)"/>
      <rect width="1024" height="1024" rx="220" fill="url(#ig2b)"/>
      {/* Stylized Arabic "س" — three arch bumps */}
      {/* Bottom baseline */}
      <rect x="148" y="600" width="728" height="44" rx="22" fill="#D6A84F"/>
      {/* Tooth tail on right */}
      <path d="M148 644 Q148 720 220 720 L148 720 Z" fill="#D6A84F"/>
      {/* Three arch bumps */}
      {[200, 432, 664].map((cx, i) => (
        <g key={i}>
          <path d={`M${cx} 600 Q${cx} 360 ${cx+120} 360 Q${cx+240} 360 ${cx+240} 600`} stroke="#0F766E" strokeWidth="52" fill="none" strokeLinecap="round"/>
          <path d={`M${cx} 600 Q${cx} 360 ${cx+120} 360 Q${cx+240} 360 ${cx+240} 600`} stroke="#D6A84F" strokeWidth="40" fill="none" strokeLinecap="round"/>
        </g>
      ))}
      {/* سكون wordmark hint */}
      <text x="512" y="840" textAnchor="middle" fill="rgba(255,255,255,0.4)" fontSize="72" fontFamily="Tajawal, sans-serif" fontWeight="900">سكون</text>
    </svg>
  );
}

function IconLocationHome({ size = 200 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 1024 1024" style={{ display:"block" }}>
      <defs>
        <linearGradient id="ig3a" x1="0" y1="0" x2="0.8" y2="1">
          <stop offset="0%" stopColor="#0D9488"/>
          <stop offset="50%" stopColor="#0F766E"/>
          <stop offset="100%" stopColor="#065F57"/>
        </linearGradient>
        <radialGradient id="ig3b" cx="40%" cy="30%" r="55%">
          <stop offset="0%" stopColor="rgba(255,255,255,0.2)"/>
          <stop offset="100%" stopColor="rgba(0,0,0,0)"/>
        </radialGradient>
      </defs>
      <rect width="1024" height="1024" rx="220" fill="url(#ig3a)"/>
      <rect width="1024" height="1024" rx="220" fill="url(#ig3b)"/>
      {/* Pin body */}
      <path d="M512 140 C340 140 210 270 210 442 C210 620 512 884 512 884 C512 884 814 620 814 442 C814 270 684 140 512 140Z" fill="white" opacity="0.95"/>
      {/* Pin inner circle */}
      <circle cx="512" cy="430" r="170" fill="#0F766E"/>
      {/* Tiny house inside pin */}
      <path d="M512 320 L600 395 L578 395 L578 520 L446 520 L446 395 L424 395 Z" fill="white" opacity="0.92"/>
      <rect x="476" y="438" width="72" height="82" rx="36" fill="#0F766E"/>
      {/* Drop shadow dot at pin tip */}
      <ellipse cx="512" cy="880" rx="50" ry="14" fill="rgba(0,0,0,0.18)"/>
    </svg>
  );
}

// ── Feature Graphic ────────────────────────────────────────────────────
function FeatureGraphic({ W = 580, H = 283 }: { W?: number; H?: number }) {
  const scaleX = W / 1024, scaleY = H / 500;
  const s = Math.min(scaleX, scaleY);
  const dW = 1024 * s, dH = 500 * s;
  // Phone scale inside feature graphic
  const phScale = 0.33;
  return (
    <div style={{ width:dW, height:dH, borderRadius:12, overflow:"hidden", position:"relative", background:"linear-gradient(135deg,#065F57 0%,#0F766E 40%,#0A1830 100%)", boxShadow:"0 20px 60px rgba(0,0,0,0.5)" }}>
      {/* Decorative circles */}
      <div style={{ position:"absolute", right:-60, top:-60, width:300, height:300, borderRadius:"50%", background:"rgba(255,255,255,0.04)" }} />
      <div style={{ position:"absolute", left:-40, bottom:-40, width:200, height:200, borderRadius:"50%", background:"rgba(214,168,79,0.08)" }} />
      {/* Left: text */}
      <div style={{ position:"absolute", left:0, top:0, width:"55%", height:"100%", display:"flex", flexDirection:"column", justifyContent:"center", padding:`0 ${dW*0.06}px`, direction:"rtl" }}>
        <div style={{ display:"flex", alignItems:"center", gap:8, marginBottom:14 }}>
          <SokoonLogoMark size={32} />
          <span style={{ fontSize:14, fontWeight:900, color:"rgba(255,255,255,0.85)", ...TJ }}>سكون | Sokoon</span>
        </div>
        <div style={{ fontSize:26, fontWeight:900, color:"white", lineHeight:1.35, marginBottom:10, ...TJ }}>سكون — سكن آمن وموثّق</div>
        <div style={{ fontSize:13, color:"rgba(255,255,255,0.65)", lineHeight:1.6, ...TJ }}>دور، تواصل، واحجز زيارة بثقة</div>
        <div style={{ display:"flex", gap:8, marginTop:16, flexWrap:"wrap" }}>
          {["بحث ذكي","توثيق هوية","خصوصية محمية"].map(f => (
            <span key={f} style={{ fontSize:9, fontWeight:700, color:"rgba(255,255,255,0.8)", background:"rgba(255,255,255,0.12)", borderRadius:10, padding:"3px 10px", ...TJ }}>{f}</span>
          ))}
        </div>
      </div>
      {/* Right: phone mockup */}
      <div style={{ position:"absolute", right:dW*0.04, top:"50%", transform:"translateY(-50%)" }}>
        <IPhoneFrame comp={TenantPersonalizedHomeScreen} scale={phScale} />
      </div>
      {/* Second phone peeking */}
      <div style={{ position:"absolute", right:dW*0.22, top:"60%", transform:"translateY(-50%)", opacity:0.5, filter:"blur(1px)" }}>
        <IPhoneFrame comp={OwnerDashboardScreen} scale={phScale*0.8} />
      </div>
    </div>
  );
}

// ── Export Checklist ───────────────────────────────────────────────────
const CHECKLIST = [
  { done:true,  label:"Arabic RTL layout verified",         ar:"اتجاه RTL مضبوط" },
  { done:true,  label:"Tajawal font used throughout",       ar:"خط Tajawal مستخدم" },
  { done:true,  label:"No full phone numbers shown",        ar:"لا أرقام هواتف كاملة" },
  { done:true,  label:"No private ID documents visible",    ar:"لا وثائق خاصة ظاهرة" },
  { done:true,  label:"No placeholder lorem ipsum",         ar:"لا نصوص عشوائية" },
  { done:true,  label:"No ranking or misleading claims",    ar:"لا ادعاءات مضللة" },
  { done:true,  label:"No App Store / Play badges inside screenshots", ar:"لا شارات متاجر داخل الشاشات" },
  { done:true,  label:"iOS screenshots ready — 1320×2868 · iPhone 17 Pro Max", ar:"لقطات iOS جاهزة" },
  { done:true,  label:"Android screenshots ready — 1080×1920 · Samsung Galaxy Ultra",ar:"لقطات Android جاهزة" },
  { done:true,  label:"10 master screenshots (5T + 5O)",   ar:"١٠ لقطات رئيسية" },
  { done:true,  label:"App icons — iOS 1024×1024",         ar:"أيقونة iOS جاهزة" },
  { done:true,  label:"App icons — Android 512×512",       ar:"أيقونة Android جاهزة" },
  { done:true,  label:"3 icon variations created",          ar:"٣ تصاميم للأيقونة" },
  { done:true,  label:"Feature Graphic — 1024×500",         ar:"Feature Graphic جاهز" },
];

function StoreView() {
  const [activeTab, setActiveTab] = useState<"master"|"icons"|"feature"|"checklist"|"future"|"logos">("master");
  const tenantShots = SHOTS.filter(s => s.type === "tenant");
  const ownerShots  = SHOTS.filter(s => s.type === "owner");

  return (
    <div style={{ minHeight:"100vh", background:DARK, ...TJ }}>
      {/* Page cover */}
      <div style={{ background:`linear-gradient(135deg,#071820 0%,#0A2A22 50%,#060B16 100%)`, borderBottom:`1px solid ${BDR}`, padding:"64px 56px 48px", position:"relative", overflow:"hidden" }}>
        <div style={{ position:"absolute", top:-80, right:-80, width:400, height:400, borderRadius:"50%", background:`radial-gradient(circle,${TEAL}20,transparent 70%)`, pointerEvents:"none" }} />
        <div style={{ position:"absolute", bottom:-60, left:200, width:300, height:300, borderRadius:"50%", background:`radial-gradient(circle,${GOLD}14,transparent 70%)`, pointerEvents:"none" }} />
        <div style={{ maxWidth:800, position:"relative" }}>
          <div style={{ fontSize:10, fontWeight:800, color:TEAL, letterSpacing:3, marginBottom:12, textTransform:"uppercase" }}>Store Assets — Sokoon | سكون</div>
          <h1 style={{ fontSize:40, fontWeight:900, color:"#F1F5F9", margin:"0 0 10px", lineHeight:1.2 }}>iOS App Store & Android Google Play</h1>
          <p style={{ color:"#475569", fontSize:14, margin:"0 0 28px", direction:"rtl", textAlign:"right", lineHeight:1.8, maxWidth:600 }}>
            أصول متجر كاملة — ١٠ لقطات تسويقية · أيقونات التطبيق · Feature Graphic · قائمة الجودة
          </p>
          <div style={{ display:"flex", flexWrap:"wrap", gap:10 }}>
            {[{l:"10 Master Screenshots",c:TEAL},{l:"3 Icon Variations",c:GOLD},{l:"Feature Graphic",c:BLUE},{l:"iPhone 17 Pro Max · Galaxy Ultra",c:PURP},{l:"Arabic RTL",c:GREEN}].map(b => (
              <span key={b.l} style={{ fontSize:11, fontWeight:700, color:b.c, background:b.c+"18", border:`1px solid ${b.c}33`, borderRadius:20, padding:"4px 14px" }}>{b.l}</span>
            ))}
          </div>
        </div>
        {/* Size reference badges */}
        <div style={{ position:"absolute", top:28, right:48, display:"flex", flexDirection:"column", gap:6, textAlign:"right" }}>
          {[{l:'iOS 6.9"',s:"1320×2868"},{l:"Android",s:"1080×1920"},{l:"Icon iOS",s:"1024×1024"},{l:"Feature",s:"1024×500"}].map(b => (
            <div key={b.l} style={{ display:"flex", alignItems:"center", gap:8, justifyContent:"flex-end" }}>
              <span style={{ fontSize:10, fontWeight:700, color:"#334155" }}>{b.l}</span>
              <span style={{ fontSize:9, fontWeight:800, color:TEAL, background:TEAL+"18", borderRadius:6, padding:"1px 7px" }}>{b.s}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Sub-tabs */}
      <div style={{ background:PANEL, borderBottom:`1px solid ${BDR}`, padding:"0 48px", display:"flex", gap:0 }}>
        {([
          {id:"master",    label:"Master Screenshots", count:"10"},
          {id:"icons",     label:"App Icons",          count:"3"},
          {id:"feature",   label:"Feature Graphic",    count:"1"},
          {id:"checklist", label:"Export Checklist",   count:"✓"},
          {id:"future",    label:"Future Graphics",    count:"12"},
          {id:"logos",     label:"Logo Concepts",      count:"20"},
        ] as const).map(tab => (
          <button key={tab.id} onClick={() => setActiveTab(tab.id as typeof activeTab)} style={{ display:"flex", alignItems:"center", gap:7, padding:"0 20px", border:"none", background:"transparent", borderBottom: activeTab===tab.id ? `2px solid ${TEAL}` : "2px solid transparent", color: activeTab===tab.id ? TEAL : "#475569", cursor:"pointer", fontSize:12, fontWeight: activeTab===tab.id ? 800 : 600, height:44, ...TJ, flexShrink:0 }}>
            <span>{tab.label}</span>
            <span style={{ fontSize:9, fontWeight:800, color: activeTab===tab.id ? TEAL : "#334155", background: activeTab===tab.id ? TEAL+"18" : "#162030", borderRadius:10, padding:"1px 6px" }}>{tab.count}</span>
          </button>
        ))}
      </div>

      {/* ── TAB: Master Screenshots ───────────────────────────────── */}
      {activeTab === "master" && (
        <div style={{ padding:"52px 48px 64px" }}>

          {/* ── iOS App Store ──────────────────────────────────────── */}
          <div style={{ display:"flex", alignItems:"center", gap:12, marginBottom:32 }}>
            <div style={{ width:3, height:28, borderRadius:2, background:BLUE }} />
            <div>
              <div style={{ fontSize:11, fontWeight:800, color:BLUE, letterSpacing:1, textTransform:"uppercase" }}>iOS App Store — iPhone 17 Pro Max</div>
              <div style={{ fontSize:10, color:"#334155", marginTop:1 }}>1320 × 2868 px · Titanium frame · Dynamic Island · Camera Control · Portrait</div>
            </div>
          </div>

          {/* Section A: Tenant */}
          <div style={{ marginBottom:52 }}>
            <div style={{ display:"flex", alignItems:"center", gap:10, marginBottom:24 }}>
              <span style={{ fontSize:10, fontWeight:800, color:BLUE, background:BLUE+"18", border:`1px solid ${BLUE}33`, borderRadius:20, padding:"3px 12px" }}>A. Tenant / Buyer — المستأجر</span>
              <span style={{ fontSize:10, color:"#334155" }}>Screenshots T-01 → T-05 · iPhone 17 Pro Max</span>
            </div>
            <div style={{ display:"flex", gap:22, overflowX:"auto", paddingBottom:16 }}>
              {tenantShots.map(s => (
                <div key={s.num} style={{ display:"flex", flexDirection:"column", alignItems:"center", gap:12 }}>
                  <MarketingCard shot={s} platform="ios" />
                  <div style={{ textAlign:"center" }}>
                    <div style={{ fontSize:9, fontWeight:800, color:BLUE }}>{s.num}</div>
                    <div style={{ fontSize:11, color:"#64748B", marginTop:2, ...TJ }}>{s.caption}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Section B: Owner — iOS */}
          <div style={{ marginBottom:56 }}>
            <div style={{ display:"flex", alignItems:"center", gap:10, marginBottom:24 }}>
              <span style={{ fontSize:10, fontWeight:800, color:GOLD, background:GOLD+"18", border:`1px solid ${GOLD}33`, borderRadius:20, padding:"3px 12px" }}>B. Owner / Landlord — المالك</span>
              <span style={{ fontSize:10, color:"#334155" }}>Screenshots O-01 → O-05 · iPhone 17 Pro Max</span>
            </div>
            <div style={{ display:"flex", gap:22, overflowX:"auto", paddingBottom:16 }}>
              {ownerShots.map(s => (
                <div key={s.num} style={{ display:"flex", flexDirection:"column", alignItems:"center", gap:12 }}>
                  <MarketingCard shot={s} platform="ios" />
                  <div style={{ textAlign:"center" }}>
                    <div style={{ fontSize:9, fontWeight:800, color:GOLD }}>{s.num}</div>
                    <div style={{ fontSize:11, color:"#64748B", marginTop:2, ...TJ }}>{s.caption}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Android Play row — separate frame */}
          <div style={{ borderTop:`1px solid ${BDR}`, paddingTop:44 }}>
            <div style={{ display:"flex", alignItems:"center", gap:12, marginBottom:10 }}>
              <div style={{ width:3, height:28, borderRadius:2, background:GREEN }} />
              <div>
                <div style={{ fontSize:11, fontWeight:800, color:GREEN, letterSpacing:1, textTransform:"uppercase" }}>Google Play Store — Samsung Galaxy Ultra</div>
                <div style={{ fontSize:10, color:"#334155", marginTop:1 }}>1080 × 1920 px · 8 selected (4T + 4O) · Centered punch-hole · S-Pen slot · Gesture bar</div>
              </div>
            </div>
            <div style={{ fontSize:10, color:"#334155", marginBottom:24, direction:"rtl", ...TJ }}>
              ملاحظة: T-05 و O-05 محفوظتان كـ master فقط — لا تُضمَّنان في حزمة Google Play (الحد 8 لقطات).
            </div>
            <div style={{ display:"flex", gap:22, overflowX:"auto", paddingBottom:16 }}>
              {ANDROID_INDICES.map(i => {
                const s = SHOTS[i];
                return (
                  <div key={s.num} style={{ display:"flex", flexDirection:"column", alignItems:"center", gap:12 }}>
                    <MarketingCard shot={s} platform="android" />
                    <div style={{ textAlign:"center" }}>
                      <div style={{ fontSize:9, fontWeight:800, color:GREEN }}>{s.num}</div>
                      <div style={{ fontSize:11, color:"#64748B", ...TJ }}>{s.caption}</div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}

      {/* ── TAB: App Icons ────────────────────────────────────────── */}
      {activeTab === "icons" && (
        <div style={{ padding:"52px 48px 64px" }}>
          <div style={{ marginBottom:40 }}>
            <div style={{ fontSize:11, fontWeight:800, color:TEAL, letterSpacing:1, textTransform:"uppercase", marginBottom:8 }}>App Icons</div>
            <h2 style={{ fontSize:24, fontWeight:900, color:"#E2E8F0", margin:"0 0 6px" }}>3 Icon Variations</h2>
            <p style={{ color:"#334155", fontSize:13, margin:0 }}>iOS 1024×1024 · Android 512×512 · SVG master artwork</p>
          </div>

          <div style={{ display:"flex", gap:48, flexWrap:"wrap" }}>
            {[
              { label:"Icon A — House + Shield", ar:"بيت + درع التحقق", desc:"الخيار الأساسي — يجمع بين رمز المنزل وشعار الثقة والأمان", accentColor:TEAL, Preview:() => <IconHouseShield size={200} /> },
              { label:"Icon B — Arabic \"س\" Mark", ar:"رمز حرف السين", desc:"مستوحى من حرف «س» في سكون — هوية عربية حديثة وجريئة", accentColor:GOLD, Preview:() => <IconSinMark size={200} /> },
              { label:"Icon C — Location + Home", ar:"موقع + منزل", desc:"دبوس الموقع مع منزل بداخله — مباشر ومميّز في العقارات", accentColor:TEAL, Preview:() => <IconLocationHome size={200} /> },
            ].map((icon, i) => (
              <div key={i} style={{ display:"flex", flexDirection:"column", gap:20, width:260 }}>
                {/* Main size preview */}
                <div style={{ display:"flex", flexDirection:"column", gap:8 }}>
                  <div style={{ fontSize:9, fontWeight:700, color:"#334155" }}>1024 × 1024 · iOS</div>
                  <div style={{ borderRadius:24, overflow:"hidden", width:200, height:200, boxShadow:`0 12px 40px rgba(0,0,0,0.5), 0 0 0 1px rgba(255,255,255,0.06)` }}>
                    <icon.Preview />
                  </div>
                </div>
                {/* Smaller sizes */}
                <div style={{ display:"flex", gap:10, alignItems:"flex-end" }}>
                  {[{size:100,label:"512px"},{size:60,label:"180px"},{size:40,label:"120px"},{size:28,label:"60px"}].map(sz => (
                    <div key={sz.label} style={{ display:"flex", flexDirection:"column", alignItems:"center", gap:4 }}>
                      <div style={{ borderRadius:sz.size*0.21, overflow:"hidden", width:sz.size, height:sz.size, boxShadow:`0 4px 12px rgba(0,0,0,0.4)` }}>
                        <icon.Preview />
                      </div>
                      <span style={{ fontSize:8, color:"#334155", fontWeight:600 }}>{sz.label}</span>
                    </div>
                  ))}
                </div>
                {/* Info */}
                <div>
                  <div style={{ fontSize:13, fontWeight:900, color:"#E2E8F0", marginBottom:4, ...TJ }}>{icon.label}</div>
                  <div style={{ fontSize:11, color:icon.accentColor, marginBottom:6, ...TJ }}>{icon.ar}</div>
                  <div style={{ fontSize:11, color:"#475569", lineHeight:1.6, direction:"rtl", ...TJ }}>{icon.desc}</div>
                </div>
                {/* Sizes badge */}
                <div style={{ display:"flex", gap:6 }}>
                  <span style={{ fontSize:9, fontWeight:700, color:TEAL, background:TEAL+"18", border:`1px solid ${TEAL}33`, borderRadius:8, padding:"2px 8px" }}>iOS 1024×1024</span>
                  <span style={{ fontSize:9, fontWeight:700, color:GREEN, background:GREEN+"18", border:`1px solid ${GREEN}33`, borderRadius:8, padding:"2px 8px" }}>Android 512×512</span>
                </div>
              </div>
            ))}
          </div>

          {/* Recommendation note */}
          <div style={{ marginTop:52, padding:"20px 24px", borderRadius:14, background:TEAL+"12", border:`1px solid ${TEAL}28` }}>
            <div style={{ fontSize:11, fontWeight:800, color:TEAL, marginBottom:6 }}>توصية الأيقونة</div>
            <p style={{ fontSize:12, color:"#94A3B8", margin:0, lineHeight:1.8, direction:"rtl", ...TJ }}>
              الأيقونة A (البيت + الدرع) هي الأقوى للتمييز في المتاجر — تجمع بين وضوح رمز العقار ومصداقية التوثيق.
              الأيقونة B مناسبة للتميّز في السوق العربي. الأيقونة C أكثر مألوفية في تطبيقات العقارات الدولية.
            </p>
          </div>

          {/* ── Device Preview — icon in context on corrected phone frames ── */}
          <div style={{ marginTop:56, borderTop:`1px solid ${BDR}`, paddingTop:48 }}>
            <div style={{ display:"flex", alignItems:"center", gap:12, marginBottom:32 }}>
              <div style={{ width:3, height:28, borderRadius:2, background:PURP }} />
              <div>
                <div style={{ fontSize:11, fontWeight:800, color:PURP, letterSpacing:1, textTransform:"uppercase" }}>Device Preview — Icon in Context</div>
                <div style={{ fontSize:10, color:"#334155", marginTop:1 }}>Splash screen · iPhone 17 Pro Max · Samsung Galaxy Ultra · Corrected frames</div>
              </div>
            </div>

            <div style={{ display:"flex", gap:56, flexWrap:"wrap", alignItems:"flex-start" }}>
              {/* iPhone preview */}
              <div style={{ display:"flex", flexDirection:"column", alignItems:"center", gap:16 }}>
                <div style={{ fontSize:9, fontWeight:700, color:"#475569", letterSpacing:0.5, textTransform:"uppercase" }}>iPhone 17 Pro Max</div>
                <div style={{ padding:"28px 24px 20px", borderRadius:24, background:"linear-gradient(145deg,#071820 0%,#0A2A22 55%,#060B16 100%)", boxShadow:"0 24px 60px rgba(0,0,0,0.55), 0 0 0 1px rgba(255,255,255,0.06)", display:"flex", alignItems:"center", justifyContent:"center" }}>
                  <div style={{ position:"relative" }}>
                    <div style={{ position:"absolute", bottom:-12, left:"50%", transform:"translateX(-50%)", width:120, height:40, background:`radial-gradient(ellipse,${TEAL}30,transparent 70%)`, borderRadius:"50%", pointerEvents:"none" }} />
                    <IPhone17ProFrame comp={SplashScreen} scale={0.62} />
                  </div>
                </div>
                <div style={{ display:"flex", flexDirection:"column", alignItems:"center", gap:4 }}>
                  <span style={{ fontSize:10, fontWeight:700, color:"#CBD5E1", ...TJ }}>Splash · Icon A in Titanium Frame</span>
                  <span style={{ fontSize:9, color:"#334155" }}>Dynamic Island · Ultra-thin bezels · Matched corners</span>
                </div>
              </div>

              {/* Samsung preview */}
              <div style={{ display:"flex", flexDirection:"column", alignItems:"center", gap:16 }}>
                <div style={{ fontSize:9, fontWeight:700, color:"#475569", letterSpacing:0.5, textTransform:"uppercase" }}>Samsung Galaxy Ultra</div>
                <div style={{ padding:"28px 24px 20px", borderRadius:24, background:"linear-gradient(145deg,#071820 0%,#0A2A22 55%,#060B16 100%)", boxShadow:"0 24px 60px rgba(0,0,0,0.55), 0 0 0 1px rgba(255,255,255,0.06)", display:"flex", alignItems:"center", justifyContent:"center" }}>
                  <div style={{ position:"relative" }}>
                    <div style={{ position:"absolute", bottom:-12, left:"50%", transform:"translateX(-50%)", width:120, height:40, background:`radial-gradient(ellipse,${TEAL}28,transparent 70%)`, borderRadius:"50%", pointerEvents:"none" }} />
                    <SamsungGalaxyFrame comp={SplashScreen} scale={0.62} />
                  </div>
                </div>
                <div style={{ display:"flex", flexDirection:"column", alignItems:"center", gap:4 }}>
                  <span style={{ fontSize:10, fontWeight:700, color:"#CBD5E1", ...TJ }}>Splash · Galaxy Ultra Frame</span>
                  <span style={{ fontSize:9, color:"#334155" }}>Centered punch-hole · Flat titanium rails · Squared corners</span>
                </div>
              </div>

              {/* Side-by-side comparison */}
              <div style={{ display:"flex", flexDirection:"column", alignItems:"center", gap:16 }}>
                <div style={{ fontSize:9, fontWeight:700, color:"#475569", letterSpacing:0.5, textTransform:"uppercase" }}>Side-by-Side</div>
                <div style={{ padding:"28px 28px 20px", borderRadius:24, background:"linear-gradient(145deg,#071820 0%,#0A2A22 55%,#060B16 100%)", boxShadow:"0 24px 60px rgba(0,0,0,0.55), 0 0 0 1px rgba(255,255,255,0.06)", display:"flex", alignItems:"flex-end", gap:20 }}>
                  <div style={{ position:"relative" }}>
                    <div style={{ position:"absolute", bottom:-10, left:"50%", transform:"translateX(-50%)", width:80, height:28, background:`radial-gradient(ellipse,${BLUE}28,transparent 70%)`, borderRadius:"50%", pointerEvents:"none" }} />
                    <IPhone17ProFrame comp={TenantPersonalizedHomeScreen} scale={0.48} />
                  </div>
                  <div style={{ position:"relative" }}>
                    <div style={{ position:"absolute", bottom:-10, left:"50%", transform:"translateX(-50%)", width:80, height:28, background:`radial-gradient(ellipse,${GREEN}22,transparent 70%)`, borderRadius:"50%", pointerEvents:"none" }} />
                    <SamsungGalaxyFrame comp={TenantPersonalizedHomeScreen} scale={0.48} />
                  </div>
                </div>
                <div style={{ display:"flex", flexDirection:"column", alignItems:"center", gap:4 }}>
                  <span style={{ fontSize:10, fontWeight:700, color:"#CBD5E1", ...TJ }}>iPhone vs Galaxy — Home Screen</span>
                  <span style={{ fontSize:9, color:"#334155" }}>Frame shape differences clearly visible</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ── TAB: Feature Graphic ─────────────────────────────────── */}
      {activeTab === "feature" && (
        <div style={{ padding:"52px 48px 64px" }}>
          <div style={{ marginBottom:40 }}>
            <div style={{ fontSize:11, fontWeight:800, color:TEAL, letterSpacing:1, textTransform:"uppercase", marginBottom:8 }}>Google Play Feature Graphic</div>
            <h2 style={{ fontSize:24, fontWeight:900, color:"#E2E8F0", margin:"0 0 6px" }}>1024 × 500 px</h2>
            <p style={{ color:"#334155", fontSize:13, margin:0 }}>JPEG or 24-bit PNG without alpha · Center-safe zone · Arabic headline</p>
          </div>

          {/* Main preview */}
          <div style={{ marginBottom:40 }}>
            <div style={{ fontSize:9, fontWeight:700, color:"#334155", marginBottom:10 }}>Preview at ~57% scale</div>
            <FeatureGraphic W={588} H={287} />
          </div>

          {/* Smaller preview */}
          <div style={{ display:"flex", gap:24, alignItems:"flex-start", flexWrap:"wrap", marginBottom:40 }}>
            <div>
              <div style={{ fontSize:9, fontWeight:700, color:"#334155", marginBottom:8 }}>40% scale</div>
              <FeatureGraphic W={410} H={200} />
            </div>
            <div>
              <div style={{ fontSize:9, fontWeight:700, color:"#334155", marginBottom:8 }}>25% scale</div>
              <FeatureGraphic W={256} H={125} />
            </div>
          </div>

          {/* Safe zone guide */}
          <div style={{ padding:"20px 24px", borderRadius:14, background:PANEL, border:`1px solid ${BDR}` }}>
            <div style={{ fontSize:11, fontWeight:800, color:"#94A3B8", marginBottom:12 }}>Feature Graphic Guidelines</div>
            <div style={{ display:"flex", flexDirection:"column", gap:8 }}>
              {[
                { icon:"✓", text:"Keep important content within center safe zone (924×398 px)", color:GREEN },
                { icon:"✓", text:"Headline visible at 100% scale without zoom", color:GREEN },
                { icon:"✓", text:"No Google Play badge or App Store badge included", color:GREEN },
                { icon:"✓", text:"No ranking claims (#1, Best, Top)", color:GREEN },
                { icon:"✓", text:"No \"Download now\" or \"Free\" text", color:GREEN },
                { icon:"✓", text:"JPEG or 24-bit PNG without alpha channel", color:GREEN },
                { icon:"→", text:"Export: 1024 × 500 px at 72dpi minimum", color:TEAL },
              ].map((g, i) => (
                <div key={i} style={{ display:"flex", gap:10, alignItems:"flex-start" }}>
                  <span style={{ color:g.color, fontWeight:800, fontSize:11, flexShrink:0 }}>{g.icon}</span>
                  <span style={{ fontSize:11, color:"#64748B", ...TJ }}>{g.text}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* ── TAB: Checklist ───────────────────────────────────────── */}
      {activeTab === "checklist" && (
        <div style={{ padding:"52px 48px 64px" }}>
          <div style={{ marginBottom:40 }}>
            <div style={{ fontSize:11, fontWeight:800, color:GREEN, letterSpacing:1, textTransform:"uppercase", marginBottom:8 }}>Export Checklist</div>
            <h2 style={{ fontSize:24, fontWeight:900, color:"#E2E8F0", margin:"0 0 6px" }}>Quality & Compliance</h2>
            <p style={{ color:"#334155", fontSize:13, margin:0 }}>متطلبات الجودة وقائمة التصدير — App Store & Google Play</p>
          </div>

          <div style={{ maxWidth:600 }}>
            <div style={{ display:"flex", flexDirection:"column", gap:3 }}>
              {CHECKLIST.map((item, i) => (
                <div key={i} style={{ display:"flex", alignItems:"center", gap:14, padding:"11px 16px", borderRadius:10, background: item.done ? GREEN+"0A" : "#1E2D40", border:`1px solid ${item.done ? GREEN+"28" : BDR}` }}>
                  <div style={{ width:20, height:20, borderRadius:"50%", background: item.done ? GREEN : "#1E2D40", border:`1.5px solid ${item.done ? GREEN : "#334155"}`, display:"flex", alignItems:"center", justifyContent:"center", flexShrink:0 }}>
                    {item.done && <span style={{ fontSize:10, color:"white", fontWeight:900 }}>✓</span>}
                  </div>
                  <div style={{ flex:1 }}>
                    <div style={{ fontSize:12, fontWeight:700, color: item.done ? "#CBD5E1" : "#475569" }}>{item.label}</div>
                    <div style={{ fontSize:10, color:item.done ? GREEN : "#334155", marginTop:1, direction:"rtl", textAlign:"right", ...TJ }}>{item.ar}</div>
                  </div>
                </div>
              ))}
            </div>

            {/* Summary */}
            <div style={{ marginTop:28, padding:"18px 20px", borderRadius:14, background:`linear-gradient(135deg,${GREEN}14,${TEAL}0A)`, border:`1px solid ${GREEN}28`, display:"flex", alignItems:"center", gap:16 }}>
              <div style={{ width:48, height:48, borderRadius:"50%", background:GREEN, display:"flex", alignItems:"center", justifyContent:"center", flexShrink:0 }}>
                <span style={{ fontSize:22, color:"white", fontWeight:900 }}>✓</span>
              </div>
              <div>
                <div style={{ fontSize:14, fontWeight:900, color:"#E2E8F0", ...TJ }}>جميع المتطلبات مكتملة</div>
                <div style={{ fontSize:11, color:GREEN, marginTop:2, ...TJ }}>{CHECKLIST.filter(c => c.done).length} / {CHECKLIST.length} items passed — Ready for store submission</div>
              </div>
            </div>
          </div>

          {/* Size reference table */}
          <div style={{ marginTop:48, maxWidth:600 }}>
            <div style={{ fontSize:11, fontWeight:800, color:"#334155", marginBottom:16, letterSpacing:1, textTransform:"uppercase" }}>Export Size Reference</div>
            <div style={{ borderRadius:12, overflow:"hidden", border:`1px solid ${BDR}` }}>
              {[
                { asset:"iOS Screenshot (Primary)",  size:"1320 × 2868 px", count:"10", format:"PNG", color:BLUE },
                { asset:"iOS Screenshot (Fallback)",  size:"1290/1260/1242/1284 × 2796+", count:"10×4", format:"PNG", color:BLUE },
                { asset:"Android Screenshot",         size:"1080 × 1920 px", count:"8", format:"PNG/JPEG", color:GREEN },
                { asset:"iOS App Icon",               size:"1024 × 1024 px", count:"3 var", format:"PNG", color:TEAL },
                { asset:"Android App Icon",           size:"512 × 512 px", count:"3 var", format:"PNG", color:TEAL },
                { asset:"Google Play Feature Graphic",size:"1024 × 500 px", count:"1", format:"JPEG", color:GOLD },
              ].map((row, i) => (
                <div key={i} style={{ display:"flex", alignItems:"center", padding:"10px 16px", background: i%2===0 ? PANEL : CARD, borderBottom: i<5 ? `1px solid ${BDR}` : "none" }}>
                  <div style={{ flex:2 }}>
                    <div style={{ fontSize:11, fontWeight:700, color:"#CBD5E1" }}>{row.asset}</div>
                  </div>
                  <div style={{ flex:2, fontSize:10, color:"#475569", fontFamily:"monospace" }}>{row.size}</div>
                  <div style={{ width:50, textAlign:"center" }}>
                    <span style={{ fontSize:9, fontWeight:800, color:row.color, background:row.color+"18", borderRadius:6, padding:"2px 7px" }}>{row.count}</span>
                  </div>
                  <div style={{ width:60, textAlign:"right", fontSize:9, color:"#334155" }}>{row.format}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* ── TAB: Future Graphics ──────────────────────────────────── */}
      {activeTab === "future" && <FutureGraphicsTab />}

      {/* ── TAB: Logo Concepts ───────────────────────────────────── */}
      {activeTab === "logos" && <LogoConceptsTab />}
    </div>
  );
}

// ══════════════════════════════════════════════════════════════════════
// PROTOTYPE NAVIGATION GRAPH
// ══════════════════════════════════════════════════════════════════════
type NavLink = { label: string; ar: string; to: string; color?: string };
type ProtoNode = { id: string; label: string; ar: string; C: React.ComponentType; links: NavLink[]; desktop?: boolean; section?: string };

const PROTO_NODES: ProtoNode[] = [
  { id:"splash",    label:"Splash",          ar:"الشاشة الافتتاحية", section:"AUTH",   C:SplashScreen,               links:[{label:"Start",ar:"ابدأ",to:"onboard"}] },
  { id:"onboard",   label:"Onboarding",      ar:"مرحباً بك",         section:"AUTH",   C:TenantOnboardingScreen,     links:[{label:"Continue",ar:"التالي",to:"role"}] },
  { id:"role",      label:"Role Select",     ar:"اختر دورك",         section:"AUTH",   C:RoleSelectScreen,           links:[{label:"Tenant",ar:"مستأجر",to:"t-login-email",color:BLUE},{label:"Owner",ar:"مالك",to:"o-login-email",color:GOLD}] },
  { id:"t-login-email",label:"Login",        ar:"تسجيل الدخول",      section:"T-AUTH", C:TenantLoginEmailScreen,     links:[{label:"Login",ar:"تسجيل الدخول",to:"t-home",color:TEAL},{label:"Forgot",ar:"نسيت كلمة المرور",to:"t-forgot"},{label:"Visitor",ar:"دخول كزائر",to:"t-visitor"},{label:"Register",ar:"إنشاء حساب",to:"t-reg"},{label:"Back",ar:"رجوع",to:"role"}] },
  { id:"t-forgot",  label:"Forgot Password", ar:"نسيت كلمة المرور",  section:"T-AUTH", C:TenantForgotPasswordScreen, links:[{label:"Back to Login",ar:"رجوع لتسجيل الدخول",to:"t-login-email"}] },
  { id:"t-otp",     label:"OTP / Reset",     ar:"كود التحقق",         section:"T-AUTH", C:TenantOTPScreen,            links:[{label:"Confirm",ar:"تأكيد",to:"t-home",color:TEAL},{label:"Back",ar:"تغيير البريد",to:"t-login-email"}] },
  { id:"t-visitor", label:"Visitor Sheet",   ar:"دخول كزائر",         section:"T-AUTH", C:VisitorRestrictedSheet,     links:[{label:"Login",ar:"تسجيل الدخول",to:"t-login-email"},{label:"Register",ar:"إنشاء حساب",to:"t-reg"}] },
  { id:"t-reg",     label:"Register",        ar:"إنشاء حساب",        section:"T-AUTH", C:TenantRegisterScreen,       links:[{label:"Next",ar:"التالي",to:"t-kyc-01"},{label:"Back",ar:"رجوع",to:"t-login-email"}] },
  { id:"t-kyc-01",  label:"T-KYC-01 Start",  ar:"توثيق الهوية",       section:"T-AUTH", C:UpdatedTenantKYC01Screen,   links:[{label:"Upload Docs",ar:"رفع المستندات",to:"t-kyc-02",color:TEAL},{label:"Skip",ar:"تخطي",to:"t-home"},{label:"Back",ar:"رجوع",to:"t-reg"}] },
  { id:"t-kyc-02",  label:"T-KYC-02 Upload", ar:"رفع المستندات",     section:"T-AUTH", C:UpdatedTenantKYC02Screen,   links:[{label:"Next",ar:"التالي",to:"kyc-pending",color:TEAL},{label:"Back",ar:"رجوع",to:"t-kyc-01"}] },
  { id:"kyc-pending",label:"KYC Pending",    ar:"قيد المراجعة",       section:"T-AUTH", C:KYCPendingScreen,           links:[{label:"Go Home",ar:"الرئيسية",to:"t-home"}] },
  { id:"kyc-approved",label:"KYC Approved",  ar:"تم التحقق",          section:"T-AUTH", C:KYCApprovedScreen,          links:[{label:"Go Home",ar:"الرئيسية",to:"t-home"}] },
  { id:"o-login-email",label:"Owner Login",   ar:"دخول المالك",        section:"O-AUTH", C:OwnerLoginEmailScreen,      links:[{label:"Login",ar:"تسجيل الدخول",to:"o-dash",color:GOLD},{label:"Forgot",ar:"نسيت كلمة المرور",to:"o-forgot"},{label:"Register",ar:"إنشاء حساب",to:"o-reg"},{label:"Back",ar:"رجوع",to:"role"}] },
  { id:"o-forgot",  label:"Forgot Password", ar:"نسيت كلمة المرور",  section:"O-AUTH", C:OwnerForgotPasswordScreen,  links:[{label:"Back to Login",ar:"رجوع لتسجيل الدخول",to:"o-login-email"}] },
  { id:"o-otp",     label:"Owner OTP / Reset",ar:"كود مالك",          section:"O-AUTH", C:OwnerOTPScreen,             links:[{label:"Confirm",ar:"تأكيد",to:"o-dash",color:GOLD},{label:"Back",ar:"تغيير البريد",to:"o-login-email"}] },
  { id:"o-reg",     label:"Owner Register",  ar:"تسجيل مالك",         section:"O-AUTH", C:OwnerRegisterScreen,        links:[{label:"Next",ar:"التالي",to:"o-kyc"},{label:"Back",ar:"رجوع",to:"o-login"}] },
  { id:"o-kyc",     label:"O-KYC-01 Start",  ar:"توثيق المالك",       section:"O-AUTH", C:UpdatedOwnerKYC01Screen,    links:[{label:"Upload Docs",ar:"رفع المستندات",to:"o-kyc-02",color:GOLD},{label:"Back",ar:"رجوع",to:"o-reg"}] },
  { id:"o-kyc-02",  label:"O-KYC-02 Upload", ar:"رفع مستندات المالك",section:"O-AUTH", C:OwnerKYC02Screen,           links:[{label:"Next",ar:"التالي",to:"kyc-pending",color:GOLD},{label:"Back",ar:"رجوع",to:"o-kyc"}] },
  { id:"t-home",    label:"Tenant Home",     ar:"الرئيسية",           section:"TENANT", C:TenantPersonalizedHomeScreen,links:[{label:"Property",ar:"عقار",to:"t-prop",color:TEAL},{label:"Search",ar:"البحث",to:"t-search",color:BLUE},{label:"Saved",ar:"محفوظات",to:"t-saved",color:ROSE},{label:"Chat",ar:"رسائل",to:"t-chat"},{label:"Notif",ar:"إشعارات",to:"t-notif"},{label:"Profile",ar:"حسابي",to:"t-profile"}] },
  { id:"t-search",  label:"Search",          ar:"البحث",              section:"TENANT", C:TenantSearchScreen,         links:[{label:"Results",ar:"النتائج",to:"t-results"},{label:"Filter",ar:"تصفية",to:"t-filter"},{label:"Back",ar:"رجوع",to:"t-home"}] },
  { id:"t-results", label:"Results",         ar:"نتائج البحث",        section:"TENANT", C:FullSearchResultsScreen,    links:[{label:"Property",ar:"تفاصيل",to:"t-prop"},{label:"Filter",ar:"تصفية",to:"t-filter"},{label:"Back",ar:"رجوع",to:"t-search"}] },
  { id:"t-filter",  label:"Filter (Full)",   ar:"الفلاتر الكاملة",    section:"TENANT", C:FullFilterSheetScreen,      links:[{label:"Apply",ar:"تطبيق",to:"t-results"},{label:"Close",ar:"إغلاق",to:"t-results"}] },
  { id:"t-share",   label:"Share Sheet",     ar:"مشاركة العقار",      section:"TENANT", C:SharePropertySheet,         links:[{label:"Close",ar:"إغلاق",to:"t-prop"}] },
  { id:"t-prop",    label:"Property Detail", ar:"تفاصيل العقار",      section:"TENANT", C:FullPropertyDetailScreen,   links:[{label:"Gallery",ar:"الصور",to:"t-gallery",color:TEAL},{label:"Map",ar:"الخريطة",to:"t-map"},{label:"Book",ar:"احجز زيارة",to:"t-book",color:GREEN},{label:"Share",ar:"مشاركة",to:"t-share"},{label:"Chat",ar:"تواصل",to:"t-thread"},{label:"Back",ar:"رجوع",to:"t-results"}] },
  { id:"t-gallery", label:"Gallery",         ar:"معرض الصور",         section:"TENANT", C:PhotoGalleryScreen,         links:[{label:"Back",ar:"رجوع",to:"t-prop"}] },
  { id:"t-map",     label:"Map View",        ar:"الخريطة",            section:"TENANT", C:PropertyMapScreen,          links:[{label:"Back",ar:"رجوع",to:"t-prop"}] },
  { id:"t-book",    label:"Book Visit",      ar:"احجز زيارة",         section:"TENANT", C:BookVisitScreen,            links:[{label:"Send",ar:"إرسال",to:"t-conf"},{label:"Back",ar:"رجوع",to:"t-prop"}] },
  { id:"t-conf",    label:"Confirmed",       ar:"تم الحجز",           section:"TENANT", C:VisitConfirmedScreen,       links:[{label:"My Visits",ar:"زياراتي",to:"t-visits"},{label:"Property",ar:"العقار",to:"t-prop"}] },
  { id:"t-visits",  label:"My Visits",       ar:"زياراتي",            section:"TENANT", C:TenantMyVisitsScreen,       links:[{label:"Detail",ar:"تفاصيل",to:"t-visit-det"},{label:"Home",ar:"الرئيسية",to:"t-home"}] },
  { id:"t-visit-det",label:"Visit Detail",   ar:"تفاصيل الزيارة",     section:"TENANT", C:VisitDetailScreen,          links:[{label:"Rate",ar:"تقييم",to:"t-rate"},{label:"Back",ar:"رجوع",to:"t-visits"}] },
  { id:"t-rate",    label:"Rate",            ar:"تقييم العقار",        section:"TENANT", C:RatePropertyScreen,         links:[{label:"Submit",ar:"إرسال",to:"t-visits"},{label:"Skip",ar:"تخطي",to:"t-home"}] },
  { id:"t-saved",   label:"Saved",           ar:"المحفوظات",          section:"TENANT", C:SavedListingsScreen,        links:[{label:"Property",ar:"عقار",to:"t-prop"},{label:"Filter",ar:"تصفية",to:"t-filter"},{label:"Home",ar:"الرئيسية",to:"t-home"}] },
  { id:"t-chat",    label:"Chat Inbox",      ar:"الرسائل",            section:"TENANT", C:TenantChatListScreen,       links:[{label:"Thread",ar:"محادثة",to:"t-thread"},{label:"Search",ar:"بحث",to:"t-chatsearch"},{label:"Home",ar:"الرئيسية",to:"t-home"}] },
  { id:"t-chatsearch",label:"Chat Search",   ar:"بحث الرسائل",        section:"TENANT", C:TenantChatSearchScreen,     links:[{label:"Thread",ar:"محادثة",to:"t-thread"},{label:"Back",ar:"رجوع",to:"t-chat"}] },
  { id:"t-thread",  label:"Chat Thread",     ar:"المحادثة",           section:"TENANT", C:TenantChatThreadScreen,     links:[{label:"Attach",ar:"مرفق",to:"t-attach"},{label:"Voice",ar:"صوت",to:"t-voice"},{label:"Report",ar:"بلاغ",to:"t-report"},{label:"Back",ar:"رجوع",to:"t-chat"}] },
  { id:"t-attach",  label:"Attachments",     ar:"المرفقات",           section:"TENANT", C:TenantChatAttachmentsSheet, links:[{label:"Close",ar:"إغلاق",to:"t-thread"}] },
  { id:"t-voice",   label:"Voice Note",      ar:"رسالة صوتية",        section:"TENANT", C:TenantChatVoiceNoteState,   links:[{label:"Send",ar:"إرسال",to:"t-thread"},{label:"Cancel",ar:"إلغاء",to:"t-thread"}] },
  { id:"t-report",  label:"Report",          ar:"بلاغ",               section:"TENANT", C:ReportSheetScreen,          links:[{label:"Submit",ar:"إرسال",to:"t-chat"},{label:"Cancel",ar:"إلغاء",to:"t-thread"}] },
  { id:"t-notif",   label:"Notifications",   ar:"الإشعارات",          section:"TENANT", C:TenantNotificationsScreen,  links:[{label:"Detail",ar:"تفاصيل",to:"t-notif-det"},{label:"Settings",ar:"الإعدادات",to:"t-notif-set"},{label:"Home",ar:"الرئيسية",to:"t-home"}] },
  { id:"t-notif-det",label:"Notif Detail",   ar:"تفاصيل الإشعار",     section:"TENANT", C:NotifDetailScreen,          links:[{label:"Back",ar:"رجوع",to:"t-notif"}] },
  { id:"t-notif-set",label:"Notif Settings", ar:"إعدادات الإشعارات",  section:"TENANT", C:NotifSettingsScreen,        links:[{label:"Back",ar:"رجوع",to:"t-notif"}] },
  { id:"t-profile", label:"Profile",         ar:"الملف الشخصي",       section:"TENANT", C:TenantProfileScreen,        links:[{label:"Edit",ar:"تعديل",to:"t-edit"},{label:"Settings",ar:"الإعدادات",to:"t-settings"},{label:"Support",ar:"الدعم",to:"t-support"},{label:"Summary",ar:"ملخص",to:"t-summary"}] },
  { id:"t-summary", label:"Account Summary", ar:"ملخص الحساب",        section:"TENANT", C:TenantAccountSummaryScreen, links:[{label:"Back",ar:"رجوع",to:"t-profile"}] },
  { id:"t-edit",    label:"Edit Profile",    ar:"تعديل الملف",        section:"TENANT", C:TenantEditProfileScreen,    links:[{label:"Save",ar:"حفظ",to:"t-profile"},{label:"Back",ar:"رجوع",to:"t-profile"}] },
  { id:"t-settings",label:"Settings",        ar:"الإعدادات",          section:"TENANT", C:TenantSettingsScreen,       links:[{label:"Privacy",ar:"خصوصية",to:"t-privacy"},{label:"Password",ar:"كلمة مرور",to:"t-pwd"},{label:"Terms",ar:"الشروط",to:"t-terms"},{label:"Logout",ar:"خروج",to:"t-logout"},{label:"Back",ar:"رجوع",to:"t-profile"}] },
  { id:"t-privacy", label:"Privacy",         ar:"الخصوصية",           section:"TENANT", C:SettingsPrivacyScreen,      links:[{label:"Back",ar:"رجوع",to:"t-settings"}] },
  { id:"t-pwd",     label:"Change Password", ar:"كلمة المرور",        section:"TENANT", C:SettingsChangePasswordScreen,links:[{label:"Back",ar:"رجوع",to:"t-settings"}] },
  { id:"t-terms",   label:"Terms",           ar:"الشروط",             section:"TENANT", C:SettingsTermsScreen,        links:[{label:"Back",ar:"رجوع",to:"t-settings"}] },
  { id:"t-logout",  label:"Logout",          ar:"تسجيل الخروج",       section:"TENANT", C:SettingsLogoutSheet,        links:[{label:"Confirm",ar:"تأكيد",to:"splash"},{label:"Cancel",ar:"إلغاء",to:"t-settings"}] },
  { id:"t-support", label:"Help Center",     ar:"مركز المساعدة",      section:"TENANT", C:TenantSupportScreen,        links:[{label:"New Ticket",ar:"تذكرة",to:"t-ticket"},{label:"Back",ar:"رجوع",to:"t-profile"}] },
  { id:"t-ticket",  label:"New Ticket",      ar:"تذكرة جديدة",        section:"TENANT", C:TenantSubmitTicketScreen,   links:[{label:"Submit",ar:"إرسال",to:"t-ticket-det"},{label:"Back",ar:"رجوع",to:"t-support"}] },
  { id:"t-ticket-det",label:"Ticket Detail", ar:"تفاصيل التذكرة",     section:"TENANT", C:SupportTicketDetailScreen,  links:[{label:"Back",ar:"رجوع",to:"t-support"}] },
  { id:"o-dash",    label:"Owner Dashboard", ar:"لوحة المالك",        section:"OWNER",  C:OwnerDashboardScreen,       links:[{label:"Properties",ar:"عقاراتي",to:"o-props",color:GOLD},{label:"Requests",ar:"الطلبات",to:"o-reqs-u",color:TEAL},{label:"Chat",ar:"رسائل",to:"o-chat"},{label:"Add",ar:"إضافة عقار",to:"o-add1",color:GREEN},{label:"Notif",ar:"إشعارات",to:"o-notif"},{label:"Profile",ar:"الملف",to:"o-profile"}] },
  { id:"o-props",   label:"My Properties",   ar:"عقاراتي",            section:"OWNER",  C:OwnerMyListingsScreen,      links:[{label:"Action",ar:"خيارات",to:"o-action"},{label:"Edit",ar:"تعديل",to:"o-edit"},{label:"Analytics",ar:"تحليلات",to:"o-anal"},{label:"Add",ar:"إضافة",to:"o-add1"},{label:"Back",ar:"رجوع",to:"o-dash"}] },
  { id:"o-action",  label:"Property Actions",ar:"خيارات العقار",      section:"OWNER",  C:OwnerPropertyActionSheet,   links:[{label:"Edit",ar:"تعديل",to:"o-edit"},{label:"Close",ar:"إغلاق",to:"o-props"}] },
  { id:"o-edit",    label:"Edit Property",   ar:"تعديل العقار",       section:"OWNER",  C:EditPropertyScreen,         links:[{label:"Save",ar:"حفظ",to:"o-props"},{label:"Back",ar:"رجوع",to:"o-props"}] },
  { id:"o-anal",    label:"Analytics",       ar:"التحليلات",          section:"OWNER",  C:OwnerPropertyAnalyticsScreen,links:[{label:"Revenue",ar:"الإيرادات",to:"o-rev"},{label:"Back",ar:"رجوع",to:"o-props"}] },
  { id:"o-rev",     label:"Revenue",         ar:"الإيرادات",          section:"OWNER",  C:OwnerRevenueScreen,         links:[{label:"Back",ar:"رجوع",to:"o-anal"}] },
  { id:"o-add1",    label:"Add Property+Map",ar:"إضافة عقار+موقع",   section:"OWNER",  C:MergedAddPropertyStep1Screen,links:[{label:"Next",ar:"التالي",to:"o-add2"},{label:"Back",ar:"رجوع",to:"o-dash"}] },
  { id:"o-add2",    label:"Upload Photos",   ar:"الصور",              section:"OWNER",  C:UpdatedAddPropertyStep2Screen,links:[{label:"Next",ar:"التالي",to:"o-add2v"},{label:"Back",ar:"رجوع",to:"o-add1"}] },
  { id:"o-add2v",   label:"Video Upload",    ar:"فيديو العقار",       section:"OWNER",  C:AddPropertyVideoScreen,links:[{label:"Next",ar:"التالي",to:"o-add3"},{label:"Skip",ar:"تخطي الفيديو",to:"o-add3"},{label:"Back",ar:"رجوع",to:"o-add2"}] },
  { id:"o-add3",    label:"Pricing+Amenities",ar:"التسعير+المرافق",   section:"OWNER",  C:MergedAddPropertyStep3Screen,links:[{label:"Next",ar:"التالي",to:"o-add3-u"},{label:"Back",ar:"رجوع",to:"o-add2"}] },
  { id:"o-add3-u",  label:"Details+Smoking+Ownership",ar:"تفاصيل+تدخين+ملكية",section:"OWNER",C:UpdatedAddPropertyStep3Screen,links:[{label:"Submit",ar:"إرسال",to:"o-submitted"},{label:"Back",ar:"رجوع",to:"o-add3"}] },
  { id:"o-submitted",label:"Submitted",      ar:"تم الإرسال",         section:"OWNER",  C:PropertySubmittedScreen,    links:[{label:"My Properties",ar:"عقاراتي",to:"o-props"},{label:"Add Another",ar:"إضافة آخر",to:"o-add1"}] },
  { id:"o-reqs",    label:"Requests (old)",  ar:"الطلبات القديمة",    section:"OWNER",  C:OwnerRequestsListScreen,    links:[{label:"Updated →",ar:"الإصدار الجديد",to:"o-reqs-u",color:TEAL}] },
  { id:"o-reqs-u",  label:"Requests",        ar:"طلبات الزيارة",      section:"OWNER",  C:UpdatedOwnerRequestsListScreen,links:[{label:"Chat",ar:"فتح الشات",to:"o-thread",color:TEAL},{label:"Accept",ar:"قبول",to:"o-accept"},{label:"Reject",ar:"رفض",to:"o-reject"},{label:"Calendar",ar:"التقويم",to:"o-cal"},{label:"Back",ar:"رجوع",to:"o-dash"}] },
  { id:"o-req-det", label:"Request Detail",  ar:"تفاصيل الطلب",       section:"OWNER",  C:OwnerRequestDetailScreen,   links:[{label:"Accept",ar:"قبول",to:"o-accept"},{label:"Reject",ar:"رفض",to:"o-reject"},{label:"Back",ar:"رجوع",to:"o-reqs"}] },
  { id:"o-accept",  label:"Accept Request",  ar:"قبول الطلب",         section:"OWNER",  C:OwnerAcceptRequestSheet,    links:[{label:"Confirm",ar:"تأكيد",to:"o-reqs"},{label:"Cancel",ar:"إلغاء",to:"o-req-det"}] },
  { id:"o-reject",  label:"Reject Request",  ar:"رفض الطلب",          section:"OWNER",  C:OwnerRejectRequestSheet,    links:[{label:"Confirm",ar:"تأكيد",to:"o-reqs"},{label:"Cancel",ar:"إلغاء",to:"o-req-det"}] },
  { id:"o-cal",     label:"Calendar",        ar:"التقويم",            section:"OWNER",  C:OwnerRequestsCalendarScreen,links:[{label:"Back",ar:"رجوع",to:"o-reqs"}] },
  { id:"o-chat",    label:"Owner Chat",      ar:"الرسائل",            section:"OWNER",  C:OwnerChatListScreen,        links:[{label:"Thread",ar:"محادثة",to:"o-thread"},{label:"Back",ar:"رجوع",to:"o-dash"}] },
  { id:"o-thread",  label:"Chat Thread",     ar:"المحادثة",           section:"OWNER",  C:OwnerChatThreadScreen,      links:[{label:"Report",ar:"بلاغ",to:"o-report"},{label:"Back",ar:"رجوع",to:"o-chat"}] },
  { id:"o-report",  label:"Report",          ar:"بلاغ",               section:"OWNER",  C:ReportSheetScreen,          links:[{label:"Submit",ar:"إرسال",to:"o-chat"},{label:"Cancel",ar:"إلغاء",to:"o-thread"}] },
  { id:"o-notif",   label:"Owner Notif",     ar:"الإشعارات",          section:"OWNER",  C:OwnerNotificationsScreen,   links:[{label:"Detail",ar:"تفاصيل",to:"o-notif-det"},{label:"Back",ar:"رجوع",to:"o-dash"}] },
  { id:"o-notif-det",label:"Notif Detail",   ar:"تفاصيل الإشعار",     section:"OWNER",  C:NotifDetailScreen,          links:[{label:"Back",ar:"رجوع",to:"o-notif"}] },
  { id:"o-profile", label:"Owner Profile",   ar:"الملف الشخصي",       section:"OWNER",  C:OwnerProfileScreen,         links:[{label:"More",ar:"المزيد",to:"o-more"},{label:"Edit",ar:"تعديل",to:"o-edit-p"},{label:"Settings",ar:"الإعدادات",to:"o-settings"}] },
  { id:"o-more",    label:"Owner More",      ar:"المزيد",             section:"OWNER",  C:OwnerMoreScreen,            links:[{label:"Support",ar:"الدعم",to:"o-support"},{label:"Settings",ar:"الإعدادات",to:"o-settings"},{label:"Profile",ar:"الملف",to:"o-profile"}] },
  { id:"o-edit-p",  label:"Edit Profile",    ar:"تعديل الملف",        section:"OWNER",  C:OwnerEditProfileScreen,     links:[{label:"Save",ar:"حفظ",to:"o-profile"},{label:"Back",ar:"رجوع",to:"o-profile"}] },
  { id:"o-settings",label:"Owner Settings",  ar:"الإعدادات",          section:"OWNER",  C:OwnerSettingsScreen,        links:[{label:"Logout",ar:"خروج",to:"o-logout"},{label:"Terms",ar:"الشروط",to:"o-terms"},{label:"Back",ar:"رجوع",to:"o-profile"}] },
  { id:"o-logout",  label:"Logout",          ar:"تسجيل الخروج",       section:"OWNER",  C:SettingsLogoutSheet,        links:[{label:"Confirm",ar:"تأكيد",to:"splash"},{label:"Cancel",ar:"إلغاء",to:"o-settings"}] },
  { id:"o-terms",   label:"Terms",           ar:"الشروط",             section:"OWNER",  C:SettingsTermsScreen,        links:[{label:"Back",ar:"رجوع",to:"o-settings"}] },
  { id:"o-support", label:"Owner Support",   ar:"الدعم",              section:"OWNER",  C:OwnerSupportScreen,         links:[{label:"New Ticket",ar:"تذكرة",to:"o-ticket"},{label:"Back",ar:"رجوع",to:"o-more"}] },
  { id:"o-ticket",  label:"New Ticket",      ar:"تذكرة جديدة",        section:"OWNER",  C:TenantSubmitTicketScreen,   links:[{label:"Submit",ar:"إرسال",to:"o-ticket-det"},{label:"Back",ar:"رجوع",to:"o-support"}] },
  { id:"o-ticket-det",label:"Ticket Detail", ar:"تفاصيل التذكرة",     section:"OWNER",  C:SupportTicketDetailScreen,  links:[{label:"Back",ar:"رجوع",to:"o-support"}] },
  { id:"a-dash",    label:"Admin Dashboard", ar:"لوحة الإدارة",       section:"ADMIN",  desktop:true, C:AdminDashboardScreen,       links:[{label:"Users",ar:"المستخدمون",to:"a-users",color:BLUE},{label:"Listings",ar:"العقارات",to:"a-props",color:TEAL},{label:"Reports",ar:"التقارير",to:"a-reports"},{label:"Finance",ar:"المالية",to:"a-fin",color:GOLD}] },
  { id:"a-users",   label:"Users",           ar:"المستخدمون",         section:"ADMIN",  desktop:true, C:AdminUsersScreen,           links:[{label:"Profile",ar:"ملف",to:"a-user-p"},{label:"Back",ar:"رجوع",to:"a-dash"}] },
  { id:"a-user-p",  label:"User Profile",    ar:"ملف المستخدم",       section:"ADMIN",  desktop:true, C:AdminUserProfileScreen,     links:[{label:"Back",ar:"رجوع",to:"a-users"}] },
  { id:"a-props",   label:"Listings",        ar:"العقارات",           section:"ADMIN",  desktop:true, C:AdminPropertiesScreen,      links:[{label:"Moderation",ar:"المراجعة",to:"a-mod"},{label:"Back",ar:"رجوع",to:"a-dash"}] },
  { id:"a-mod",     label:"Moderation",      ar:"مراجعة العقارات",    section:"ADMIN",  desktop:true, C:AdminListingModerationScreen,links:[{label:"Back",ar:"رجوع",to:"a-props"}] },
  { id:"a-reports", label:"Reports",         ar:"التقارير",           section:"ADMIN",  desktop:true, C:AdminReportsTicketsScreen,  links:[{label:"Back",ar:"رجوع",to:"a-dash"}] },
  { id:"a-fin",     label:"Finance",         ar:"المالية",            section:"ADMIN",  desktop:true, C:AdminFinanceDashboardScreen,links:[{label:"Transactions",ar:"المعاملات",to:"a-tx"},{label:"Back",ar:"رجوع",to:"a-dash"}] },
  { id:"a-tx",      label:"Transactions",    ar:"سجل المعاملات",      section:"ADMIN",  desktop:true, C:AdminTransactionLogScreen,  links:[{label:"Back",ar:"رجوع",to:"a-fin"}] },
];
const PROTO_MAP: Record<string, ProtoNode> = Object.fromEntries(PROTO_NODES.map(n => [n.id, n]));
const SEC_COLOR: Record<string, string> = { AUTH:BLUE, "T-AUTH":BLUE, "O-AUTH":GOLD, TENANT:TEAL, OWNER:GOLD, ADMIN:SLATE };

// ══════════════════════════════════════════════════════════════════════
// PROTOTYPE VIEW
// ══════════════════════════════════════════════════════════════════════
function ProtoView() {
  const [current, setCurrent] = useState("splash");
  const [history, setHistory] = useState<string[]>([]);
  const node = PROTO_MAP[current] ?? PROTO_MAP["splash"];
  const isD = !!node.desktop;
  const secColor = SEC_COLOR[node.section ?? "AUTH"] ?? TEAL;
  function goTo(id: string) { if (PROTO_MAP[id]) { setHistory(h => [...h, current]); setCurrent(id); } }
  function goBack() { setHistory(h => { const p = h[h.length-1]; if (p) setCurrent(p); return h.slice(0,-1); }); }
  function reset(id: string) { setHistory([]); setCurrent(id); }
  return (
    <div style={{ minHeight:"100vh", background:DARK, ...TJ }}>
      <div style={{ background:PANEL, borderBottom:`1px solid ${BDR}`, padding:"10px 28px", display:"flex", alignItems:"center", gap:12, flexWrap:"wrap" }}>
        {[{label:"Full App",ar:"الكامل",id:"splash"},{label:"Tenant",ar:"مستأجر",id:"t-home"},{label:"Owner",ar:"مالك",id:"o-dash"},{label:"Admin",ar:"إدارة",id:"a-dash"}].map(sp => (
          <button key={sp.id} onClick={() => reset(sp.id)} style={{ fontSize:11, fontWeight:700, padding:"5px 12px", borderRadius:8, border:`1px solid ${current===sp.id ? TEAL : BDR}`, background: current===sp.id ? TEAL+"28" : "transparent", color: current===sp.id ? TEAL : "#64748B", cursor:"pointer", ...TJ }}>
            {sp.label} · {sp.ar}
          </button>
        ))}
        <div style={{ flex:1 }} />
        {history.length > 0 && <button onClick={goBack} style={{ fontSize:11, fontWeight:700, padding:"5px 14px", borderRadius:8, border:`1px solid ${BDR}`, background:CARD, color:"#94A3B8", cursor:"pointer", ...TJ }}>← رجوع</button>}
      </div>
      <div style={{ display:"flex", minHeight:"calc(100vh - 52px)" }}>
        <div style={{ flex:1, display:"flex", flexDirection:"column", alignItems:"center", justifyContent:"center", padding:"40px 24px", gap:24 }}>
          <div style={{ display:"flex", alignItems:"center", gap:6, flexWrap:"wrap", justifyContent:"center" }}>
            {history.slice(-3).map((h, i) => (<React.Fragment key={i}><span style={{ fontSize:10, color:"#334155" }}>{PROTO_MAP[h]?.label}</span><span style={{ fontSize:10, color:"#1E2D40" }}>›</span></React.Fragment>))}
            <span style={{ fontSize:10, fontWeight:800, color:secColor }}>{node.label}</span>
          </div>
          {isD ? <MacBookFrame comp={node.C} scale={0.9} /> : <IPhoneFrame comp={node.C} scale={1} />}
          <div style={{ textAlign:"center" }}>
            <div style={{ fontSize:15, fontWeight:900, color:"#E2E8F0" }}>{node.label}</div>
            <div style={{ fontSize:12, color:secColor, marginTop:2 }}>{node.ar}</div>
          </div>
        </div>
        <div style={{ width:255, background:PANEL, borderLeft:`1px solid ${BDR}`, padding:"24px 16px", display:"flex", flexDirection:"column", gap:10, overflowY:"auto" }}>
          <div style={{ fontSize:10, fontWeight:800, color:"#334155", letterSpacing:1, textTransform:"uppercase" }}>Actions</div>
          {node.links.map((link, i) => (
            <button key={i} onClick={() => goTo(link.to)} disabled={!PROTO_MAP[link.to]} style={{ display:"flex", alignItems:"center", justifyContent:"space-between", padding:"9px 12px", borderRadius:10, border:`1px solid ${(link.color??secColor)+"44"}`, background:(link.color??secColor)+"12", color:link.color??secColor, cursor:PROTO_MAP[link.to]?"pointer":"default", opacity:PROTO_MAP[link.to]?1:0.4, textAlign:"right", ...TJ, width:"100%" }}>
              <span style={{ fontSize:10, color:"#334155" }}>→ {link.to}</span>
              <div style={{ textAlign:"right" }}><div style={{ fontSize:12, fontWeight:800 }}>{link.ar}</div><div style={{ fontSize:10, opacity:0.7 }}>{link.label}</div></div>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

// ══════════════════════════════════════════════════════════════════════
// MOCKUP PRESENTATION VIEW
// ══════════════════════════════════════════════════════════════════════
const MOBILE_MOCKUPS = [
  { comp:SplashScreen,               caption:"اكتشف سكنك المثالي",          label:"Welcome",       color:BLUE },
  { comp:TenantPersonalizedHomeScreen,caption:"دور على سكنك بسهولة",         label:"Tenant Home",   color:TEAL },
  { comp:PropertyDetailScreen,       caption:"تفاصيل واضحة قبل ما تختار",   label:"Property",      color:TEAL },
  { comp:TenantChatThreadScreen,     caption:"تواصل بأمان داخل سكون",        label:"Chat",          color:BLUE },
  { comp:BookVisitScreen,            caption:"احجز زيارة في خطوات بسيطة",   label:"Book Visit",    color:GREEN },
  { comp:SavedListingsScreen,        caption:"حفظ اللي يعجبك",              label:"Saved",         color:ROSE },
  { comp:TenantProfileScreen,        caption:"حسابك في مكان واحد",          label:"Profile",       color:TEAL },
  { comp:OwnerDashboardScreen,       caption:"إدارة عقاراتك من مكان واحد",  label:"Owner Home",    color:GOLD },
  { comp:OwnerMyListingsScreen,      caption:"عقاراتك دايماً تحت إيدك",     label:"My Properties", color:GOLD },
  { comp:OwnerRequestDetailScreen,   caption:"تابع طلبات الزيارة",          label:"Requests",      color:GOLD },
];
const DESKTOP_MOCKUPS = [
  { comp:AdminDashboardScreen,       caption:"لوحة إدارة كاملة للمنصة",     label:"Admin Dashboard",color:SLATE },
  { comp:AdminUsersScreen,           caption:"إدارة المستخدمين احترافياً",   label:"User Mgmt",     color:BLUE },
  { comp:AdminListingModerationScreen,caption:"مراجعة واعتماد العقارات",     label:"Listing Review", color:TEAL },
  { comp:AdminReportsTicketsScreen,  caption:"التقارير والشكاوى",            label:"Reports",       color:ROSE },
];
function MockupView() {
  return (
    <div style={{ minHeight:"100vh", background:DARK, ...TJ }}>
      <div style={{ padding:"80px 60px 60px", background:`linear-gradient(135deg,#08111F,#0A1830,#060B16)`, borderBottom:`1px solid ${BDR}`, textAlign:"center", position:"relative", overflow:"hidden" }}>
        <div style={{ position:"absolute", top:-60, left:"50%", transform:"translateX(-50%)", width:600, height:300, background:`radial-gradient(ellipse at center,${TEAL}22,transparent 70%)`, pointerEvents:"none" }} />
        <div style={{ fontSize:10, fontWeight:800, color:TEAL, letterSpacing:3, marginBottom:16, textTransform:"uppercase", position:"relative" }}>Sokoon · سكون</div>
        <h1 style={{ fontSize:42, fontWeight:900, color:"#F1F5F9", margin:"0 0 12px", lineHeight:1.15, position:"relative" }}>Mockup Presentation</h1>
        <p style={{ fontSize:14, color:"#475569", margin:"0 auto 32px", maxWidth:500, lineHeight:1.8, direction:"rtl", position:"relative" }}>عرض تقديمي جاهز للعميل — تصميم نظيف وعملي</p>
        <div style={{ display:"flex", justifyContent:"center", gap:10, flexWrap:"wrap", position:"relative" }}>
          {[{l:"10 Mobile",c:TEAL},{l:"4 Desktop",c:SLATE},{l:"Arabic RTL",c:BLUE},{l:"Premium",c:GOLD}].map(b => (
            <span key={b.l} style={{ fontSize:11, fontWeight:700, color:b.c, background:b.c+"18", border:`1px solid ${b.c}33`, borderRadius:20, padding:"4px 14px" }}>{b.l}</span>
          ))}
        </div>
      </div>
      <div style={{ padding:"64px 48px 48px" }}>
        <div style={{ marginBottom:36 }}>
          <div style={{ fontSize:10, fontWeight:800, color:TEAL, letterSpacing:2, textTransform:"uppercase", marginBottom:8 }}>Mobile App</div>
          <h2 style={{ fontSize:24, fontWeight:900, color:"#E2E8F0", margin:0 }}>تجربة المستخدم على الجوال</h2>
        </div>
        <div style={{ display:"flex", gap:28, justifyContent:"center", flexWrap:"wrap", marginBottom:40 }}>
          {MOBILE_MOCKUPS.slice(0,5).map((m, i) => (
            <div key={i} style={{ display:"flex", flexDirection:"column", alignItems:"center", gap:14 }}>
              <IPhoneFrame comp={m.comp} scale={0.78} />
              <div style={{ textAlign:"center", maxWidth:120 }}>
                <div style={{ fontSize:9, fontWeight:800, color:m.color }}>{m.label}</div>
                <div style={{ fontSize:11, color:"#94A3B8", lineHeight:1.5, direction:"rtl", ...TJ }}>{m.caption}</div>
              </div>
            </div>
          ))}
        </div>
        <div style={{ display:"flex", gap:28, justifyContent:"center", flexWrap:"wrap" }}>
          {MOBILE_MOCKUPS.slice(5).map((m, i) => (
            <div key={i} style={{ display:"flex", flexDirection:"column", alignItems:"center", gap:14 }}>
              <IPhoneFrame comp={m.comp} scale={0.78} />
              <div style={{ textAlign:"center", maxWidth:120 }}>
                <div style={{ fontSize:9, fontWeight:800, color:m.color }}>{m.label}</div>
                <div style={{ fontSize:11, color:"#94A3B8", lineHeight:1.5, direction:"rtl", ...TJ }}>{m.caption}</div>
              </div>
            </div>
          ))}
        </div>
      </div>
      <div style={{ margin:"0 48px", height:1, background:BDR }} />
      <div style={{ padding:"64px 48px 80px" }}>
        <div style={{ marginBottom:44 }}>
          <div style={{ fontSize:10, fontWeight:800, color:SLATE, letterSpacing:2, textTransform:"uppercase", marginBottom:8 }}>Admin Panel</div>
          <h2 style={{ fontSize:24, fontWeight:900, color:"#E2E8F0", margin:0 }}>لوحة الإدارة على الحاسب</h2>
        </div>
        <div style={{ display:"flex", gap:36, justifyContent:"center", flexWrap:"wrap" }}>
          {DESKTOP_MOCKUPS.map((m, i) => (
            <div key={i} style={{ display:"flex", flexDirection:"column", alignItems:"center", gap:14 }}>
              <MacBookFrame comp={m.comp} scale={0.95} />
              <div style={{ textAlign:"center" }}>
                <div style={{ fontSize:9, fontWeight:800, color:m.color }}>{m.label}</div>
                <div style={{ fontSize:11, color:"#94A3B8", direction:"rtl", ...TJ }}>{m.caption}</div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// ══════════════════════════════════════════════════════════════════════
// FLOW OVERVIEW HELPERS
// ══════════════════════════════════════════════════════════════════════
function Arrow({ color }: { color: string }) {
  return (
    <div style={{ display:"flex", alignItems:"center", padding:"0 4px 36px", flexShrink:0 }}>
      <svg width="26" height="18" viewBox="0 0 26 18" fill="none">
        <path d="M2,9 L20,9" stroke={color} strokeWidth="1.5" strokeLinecap="round"/>
        <path d="M13,3 L20,9 L13,15" stroke={color} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" fill="none"/>
      </svg>
    </div>
  );
}
function MiniScreen({ sc, color }: { sc: Sc; color: string }) {
  const isD = !!sc.desktop;
  const NW = isD ? 1280 : 390, NH = isD ? 760 : 844;
  const SCALE = isD ? 0.21 : 0.295;
  const dw = NW*SCALE, dh = NH*SCALE;
  return (
    <div style={{ display:"flex", flexDirection:"column", alignItems:"center", gap:8, flexShrink:0 }}>
      <div style={{ width:dw, height:dh, overflow:"hidden", borderRadius: isD ? 6 : 12, border:`1.5px solid ${color}44`, background:"#FAFAF8", flexShrink:0, boxShadow:`0 4px 20px rgba(0,0,0,0.3)` }}>
        <div style={{ width:NW, height:NH, transform:`scale(${SCALE})`, transformOrigin:"top left" }}><sc.C /></div>
      </div>
      <div style={{ textAlign:"center", maxWidth:dw+10 }}>
        <div style={{ fontSize:8.5, fontWeight:800, color, letterSpacing:0.4, lineHeight:1.2, ...TJ }}>{sc.id}</div>
        <div style={{ fontSize:10, color:"#64748B", lineHeight:1.2, marginTop:1, ...TJ }}>{sc.label}</div>
      </div>
    </div>
  );
}
function FlowSection({ sec }: { sec: Section }) {
  return (
    <div id={sec.id} style={{ borderBottom:`1px solid ${BDR}` }}>
      <div style={{ padding:"28px 40px 14px", display:"flex", alignItems:"center", gap:14 }}>
        <div style={{ width:36, height:36, borderRadius:10, background:sec.color+"22", border:`1px solid ${sec.color}44`, display:"flex", alignItems:"center", justifyContent:"center", flexShrink:0 }}>
          <span style={{ fontSize:12, fontWeight:900, color:sec.color }}>{String(sec.n).padStart(2,"0")}</span>
        </div>
        <div>
          <h2 style={{ fontSize:15, fontWeight:900, color:"#E2E8F0", margin:0, ...TJ }}>{sec.label}</h2>
          <p style={{ fontSize:11, color:sec.color, margin:"2px 0 0", fontWeight:600, ...TJ }}>{sec.ar} · {sec.screens.length}</p>
        </div>
        <div style={{ flex:1, height:1, background:sec.color+"28" }} />
        <span style={{ fontSize:10, fontWeight:700, color:sec.color, background:sec.color+"18", border:`1px solid ${sec.color}33`, borderRadius:20, padding:"3px 10px" }}>{sec.screens.length}</span>
      </div>
      <div style={{ overflowX:"auto", padding:"4px 40px 28px" }}>
        <div style={{ display:"flex", alignItems:"flex-end", gap:0, width:"max-content" }}>
          {sec.screens.map((sc, i) => (
            <React.Fragment key={sc.id}>
              <MiniScreen sc={sc} color={sec.color} />
              {i < sec.screens.length-1 && <Arrow color={sec.color} />}
            </React.Fragment>
          ))}
        </div>
      </div>
    </div>
  );
}
function TOC({ onClose }: { onClose: () => void }) {
  return (
    <div style={{ position:"fixed", inset:0, zIndex:200, background:"rgba(6,11,22,0.85)", backdropFilter:"blur(8px)", display:"flex", alignItems:"center", justifyContent:"center" }} onClick={onClose}>
      <div onClick={e => e.stopPropagation()} style={{ background:CARD, borderRadius:20, border:`1px solid ${BDR}`, padding:"24px 28px", width:520, maxHeight:"82vh", overflowY:"auto", boxShadow:"0 40px 80px rgba(0,0,0,0.6)" }}>
        <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center", marginBottom:16 }}>
          <h3 style={{ color:"#F1F5F9", fontSize:15, fontWeight:900, margin:0, ...TJ }}>جدول المحتويات — {TOTAL} شاشة</h3>
          <button onClick={onClose} style={{ background:"none", border:"none", color:"#64748B", cursor:"pointer", fontSize:20 }}>×</button>
        </div>
        {SECTIONS.map(sec => (
          <a key={sec.id} href={`#${sec.id}`} onClick={onClose} style={{ display:"flex", alignItems:"center", gap:10, padding:"8px 10px", borderRadius:9, textDecoration:"none" }}
            onMouseEnter={e => (e.currentTarget.style.background=sec.color+"18")}
            onMouseLeave={e => (e.currentTarget.style.background="transparent")}>
            <span style={{ fontSize:10, fontWeight:800, color:sec.color, width:22, textAlign:"center" }}>{String(sec.n).padStart(2,"0")}</span>
            <div style={{ width:3, height:14, borderRadius:2, background:sec.color, flexShrink:0 }} />
            <span style={{ fontSize:12, fontWeight:700, color:"#CBD5E1", flex:1, ...TJ }}>{sec.label}</span>
            <span style={{ fontSize:9, color:sec.color, background:sec.color+"18", borderRadius:10, padding:"2px 7px" }}>{sec.screens.length}</span>
          </a>
        ))}
      </div>
    </div>
  );
}
function FlowView() {
  return (
    <div>
      <div style={{ padding:"40px 40px 32px", background:`linear-gradient(135deg,${PANEL},#0A1830)`, borderBottom:`1px solid ${BDR}` }}>
        <div style={{ fontSize:10, fontWeight:800, color:TEAL, letterSpacing:2, marginBottom:10 }}>SOKOON · سكون</div>
        <h1 style={{ color:"#F1F5F9", fontSize:28, fontWeight:900, margin:"0 0 8px" }}>App Flow Overview</h1>
        <p style={{ color:"#475569", fontSize:13, margin:"0 0 16px", direction:"rtl", textAlign:"right" }}>نظرة شاملة — {TOTAL} شاشة في {SECTIONS.length} قسماً</p>
        <div style={{ display:"flex", flexWrap:"wrap", gap:8 }}>
          {[{l:`${TOTAL} Screens`,c:TEAL},{l:"20 Sections",c:BLUE},{l:"3 Roles",c:GOLD}].map(b => (
            <span key={b.l} style={{ fontSize:11, fontWeight:700, color:b.c, background:b.c+"18", border:`1px solid ${b.c}33`, borderRadius:8, padding:"4px 12px" }}>{b.l}</span>
          ))}
        </div>
      </div>
      {SECTIONS.map(sec => <FlowSection key={sec.id} sec={sec} />)}
      <div style={{ padding:"28px 40px 44px", borderTop:`1px solid ${BDR}`, textAlign:"center" }}>
        <p style={{ color:"#1E2D40", fontSize:11, margin:0 }}>Sokoon · سكون · {TOTAL} screens · {SECTIONS.length} sections</p>
      </div>
    </div>
  );
}

// ══════════════════════════════════════════════════════════════════════
// DEVICE MOCKUPS VIEW
// ══════════════════════════════════════════════════════════════════════
const DEVICE_SCREENS = [
  { label:"Home",          comp:TenantPersonalizedHomeScreen, accent:TEAL  },
  { label:"Property",      comp:FullPropertyDetailScreen,     accent:TEAL  },
  { label:"Chat",          comp:TenantChatThreadScreen,       accent:BLUE  },
  { label:"Book Visit",    comp:BookVisitScreen,              accent:GREEN },
  { label:"Owner Dash",    comp:OwnerDashboardScreen,         accent:GOLD  },
  { label:"Add Property",  comp:MergedAddPropertyStep1Screen, accent:GOLD  },
  { label:"Splash",        comp:SplashScreen,                 accent:TEAL  },
  { label:"Profile",       comp:TenantProfileScreen,          accent:ROSE  },
];

function DeviceMockupsView() {
  const [activeIdx, setActiveIdx] = React.useState(0);
  const screen = DEVICE_SCREENS[activeIdx];
  const Comp = screen.comp;

  return (
    <div style={{ minHeight:"100vh", background:DARK, fontFamily:"Tajawal, sans-serif" }}>

      {/* Header */}
      <div style={{ background:"linear-gradient(135deg,#071820 0%,#0A2030 55%,#060B16 100%)", borderBottom:`1px solid ${BDR}`, padding:"48px 56px 40px", position:"relative", overflow:"hidden" }}>
        <div style={{ position:"absolute", top:-80, right:-80, width:360, height:360, borderRadius:"50%", background:`radial-gradient(circle,${PURP}18,transparent 70%)`, pointerEvents:"none" }} />
        <div style={{ position:"relative" }}>
          <div style={{ fontSize:10, fontWeight:800, color:PURP, letterSpacing:3, marginBottom:10, textTransform:"uppercase" }}>Device Mockups — Sokoon</div>
          <h1 style={{ fontSize:34, fontWeight:900, color:"#F1F5F9", margin:"0 0 10px" }}>iPhone 17 Pro Max · Samsung Galaxy Ultra</h1>
          <p style={{ color:"#475569", fontSize:13, margin:"0 0 22px" }}>Corrected screen fitting · matched corner radii · Dynamic Island · flat titanium rails</p>
          <div style={{ display:"flex", gap:8, flexWrap:"wrap" }}>
            {[{l:"iPhone 17 Pro Max",c:BLUE},{l:"Samsung Galaxy Ultra",c:GREEN},{l:"Dynamic Island fixed",c:PURP},{l:"Corners matched",c:TEAL}].map(b=>(
              <span key={b.l} style={{ fontSize:11, fontWeight:700, color:b.c, background:b.c+"18", border:`1px solid ${b.c}33`, borderRadius:20, padding:"4px 14px" }}>{b.l}</span>
            ))}
          </div>
        </div>
      </div>

      {/* Screen selector tabs */}
      <div style={{ background:PANEL, borderBottom:`1px solid ${BDR}`, padding:"0 48px", display:"flex", overflowX:"auto" }}>
        {DEVICE_SCREENS.map((s,i)=>(
          <button key={i} onClick={()=>setActiveIdx(i)} style={{ padding:"0 18px", border:"none", background:"transparent", borderBottom: activeIdx===i ? `2px solid ${PURP}` : "2px solid transparent", color: activeIdx===i ? PURP : "#475569", cursor:"pointer", fontSize:11, fontWeight: activeIdx===i ? 800 : 600, height:44, flexShrink:0, fontFamily:"Tajawal, sans-serif", whiteSpace:"nowrap" }}>
            {s.label}
          </button>
        ))}
      </div>

      {/* Main side-by-side showcase */}
      <div style={{ padding:"56px 56px 48px", display:"flex", gap:80, alignItems:"center", justifyContent:"center", flexWrap:"wrap" }}>

        {/* iPhone */}
        <div style={{ display:"flex", flexDirection:"column", alignItems:"center", gap:18 }}>
          <span style={{ fontSize:11, fontWeight:800, color:BLUE, letterSpacing:0.5 }}>iPhone 17 Pro Max</span>
          <div style={{ position:"relative" }}>
            <div style={{ position:"absolute", bottom:-28, left:"50%", transform:"translateX(-50%)", width:180, height:70, background:`radial-gradient(ellipse,${screen.accent}28,transparent 70%)`, borderRadius:"50%", pointerEvents:"none" }} />
            <IPhone17ProFrame comp={Comp} scale={0.92} />
          </div>
          <div style={{ display:"flex", gap:5, flexWrap:"wrap", justifyContent:"center", maxWidth:200 }}>
            {["Titanium frame","Dynamic Island","Matched corners","Camera Control btn"].map(f=>(
              <span key={f} style={{ fontSize:8, fontWeight:700, color:"#475569", background:CARD, borderRadius:6, padding:"2px 7px" }}>{f}</span>
            ))}
          </div>
        </div>

        {/* Samsung */}
        <div style={{ display:"flex", flexDirection:"column", alignItems:"center", gap:18 }}>
          <span style={{ fontSize:11, fontWeight:800, color:GREEN, letterSpacing:0.5 }}>Samsung Galaxy Ultra</span>
          <div style={{ position:"relative" }}>
            <div style={{ position:"absolute", bottom:-28, left:"50%", transform:"translateX(-50%)", width:180, height:70, background:`radial-gradient(ellipse,${screen.accent}22,transparent 70%)`, borderRadius:"50%", pointerEvents:"none" }} />
            <SamsungGalaxyFrame comp={Comp} scale={0.92} />
          </div>
          <div style={{ display:"flex", gap:5, flexWrap:"wrap", justifyContent:"center", maxWidth:200 }}>
            {["Phantom Black","Punch-hole cam","Flat rails","Squared corners"].map(f=>(
              <span key={f} style={{ fontSize:8, fontWeight:700, color:"#475569", background:CARD, borderRadius:6, padding:"2px 7px" }}>{f}</span>
            ))}
          </div>
        </div>
      </div>

      {/* Thumbnail strip — iOS */}
      <div style={{ borderTop:`1px solid ${BDR}`, padding:"40px 56px 16px" }}>
        <div style={{ fontSize:10, fontWeight:800, color:BLUE, marginBottom:16, letterSpacing:0.5 }}>iPhone 17 Pro Max — All Screens</div>
        <div style={{ display:"flex", gap:16, overflowX:"auto", paddingBottom:16 }}>
          {DEVICE_SCREENS.map((s,i)=>(
            <div key={i} onClick={()=>setActiveIdx(i)} style={{ display:"flex", flexDirection:"column", alignItems:"center", gap:6, cursor:"pointer", flexShrink:0 }}>
              <div style={{ outline: activeIdx===i ? `2px solid ${BLUE}` : "2px solid transparent", borderRadius:22, padding:2 }}>
                <IPhone17ProFrame comp={s.comp} scale={0.36} />
              </div>
              <span style={{ fontSize:8.5, fontWeight: activeIdx===i ? 800 : 500, color: activeIdx===i ? BLUE : "#475569" }}>{s.label}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Thumbnail strip — Android */}
      <div style={{ padding:"24px 56px 64px" }}>
        <div style={{ fontSize:10, fontWeight:800, color:GREEN, marginBottom:16, letterSpacing:0.5 }}>Samsung Galaxy Ultra — All Screens</div>
        <div style={{ display:"flex", gap:16, overflowX:"auto", paddingBottom:16 }}>
          {DEVICE_SCREENS.map((s,i)=>(
            <div key={i} onClick={()=>setActiveIdx(i)} style={{ display:"flex", flexDirection:"column", alignItems:"center", gap:6, cursor:"pointer", flexShrink:0 }}>
              <div style={{ outline: activeIdx===i ? `2px solid ${GREEN}` : "2px solid transparent", borderRadius:12, padding:2 }}>
                <SamsungGalaxyFrame comp={s.comp} scale={0.36} />
              </div>
              <span style={{ fontSize:8.5, fontWeight: activeIdx===i ? 800 : 500, color: activeIdx===i ? GREEN : "#475569" }}>{s.label}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// ══════════════════════════════════════════════════════════════════════
// ROOT APP
// ══════════════════════════════════════════════════════════════════════
export default function App() {
  const [mode, setMode] = useState<AppMode>("store");
  const [toc, setToc] = useState(false);
  const TABS: { id: AppMode; label: string; icon: string; color: string }[] = [
    { id:"store",  label:"Store Assets",          icon:"📦", color:GOLD  },
    { id:"mockup", label:"Mockup Presentation",   icon:"📱", color:TEAL  },
    { id:"proto",  label:"Interactive Prototype", icon:"▶",  color:BLUE  },
    { id:"flow",   label:"Flow Overview",          icon:"⬡",  color:PURP  },
    { id:"shared", label:"Shared Components",      icon:"⚙",  color:TEAL  },
    { id:"landing",label:"Landing Page",           icon:"🌐", color:GREEN },
    { id:"devices",label:"Device Mockups",         icon:"📲", color:PURP  },
    { id:"logos",  label:"App Logos & Brand",      icon:"✦",  color:GOLD  },
  ];
  return (
    <div style={{ ...TJ, background:DARK, minHeight:"100vh" }}>
      {toc && mode==="flow" && <TOC onClose={() => setToc(false)} />}
      {/* Global nav */}
      <div style={{ position:"sticky", top:0, zIndex:100, background:PANEL, borderBottom:`1px solid ${BDR}`, padding:"0 24px", display:"flex", alignItems:"stretch" }}>
        <div style={{ display:"flex", alignItems:"center", gap:9, paddingRight:18, borderRight:`1px solid ${BDR}`, marginRight:6 }}>
          <SokoonLogoMark size={30} />
          <div style={{ lineHeight:1.1 }}>
            <div style={{ color:"#F1F5F9", fontSize:12, fontWeight:900 }}>Sokoon · سكون</div>
            <div style={{ color:"#334155", fontSize:9 }}>{TOTAL} screens</div>
          </div>
        </div>
        {TABS.map(tab => (
          <button key={tab.id} onClick={() => setMode(tab.id)} style={{ display:"flex", alignItems:"center", gap:6, padding:"0 16px", border:"none", background:"transparent", borderBottom: mode===tab.id ? `2px solid ${tab.color}` : "2px solid transparent", color: mode===tab.id ? tab.color : "#475569", cursor:"pointer", fontSize:11, fontWeight: mode===tab.id ? 800 : 600, height:46, flexShrink:0, ...TJ }}>
            <span style={{ fontSize:13 }}>{tab.icon}</span><span>{tab.label}</span>
          </button>
        ))}
        <div style={{ flex:1 }} />
        {mode==="flow" && (
          <>
            <button onClick={() => setToc(true)} style={{ display:"flex", alignItems:"center", gap:6, fontSize:11, fontWeight:700, padding:"10px 12px", border:`1px solid ${BDR}`, borderRadius:8, margin:"8px 6px", background:CARD, color:"#94A3B8", cursor:"pointer", ...TJ }}>☰ TOC</button>
            <div style={{ display:"flex", gap:4, alignItems:"center" }}>
              {[{l:"Auth",h:"s1",c:BLUE},{l:"Home",h:"s3",c:TEAL},{l:"Admin",h:"s19",c:SLATE}].map(g => (
                <a key={g.l} href={`#${g.h}`} style={{ fontSize:10, fontWeight:700, textDecoration:"none", color:g.c, background:g.c+"18", border:`1px solid ${g.c}33`, borderRadius:6, padding:"3px 9px", whiteSpace:"nowrap" }}>{g.l}</a>
              ))}
            </div>
          </>
        )}
      </div>
      {mode==="store"  && <StoreView />}
      {mode==="mockup" && <MockupView />}
      {mode==="proto"  && <ProtoView />}
      {mode==="flow"   && <FlowView />}
      {mode==="shared"  && <SharedView />}
      {mode==="landing" && (
        <div style={{ height: "calc(100vh - 46px)", overflow: "hidden" }}>
          <LandingPage />
        </div>
      )}
      {mode==="devices" && <DeviceMockupsView />}
      {mode==="logos" && (
        <div style={{ minHeight:"100vh", background:DARK }}>
          <div style={{ background:`linear-gradient(135deg,#0A1020 0%,#0E1C10 55%,#060B16 100%)`, borderBottom:`1px solid ${BDR}`, padding:"48px 56px 40px", position:"relative", overflow:"hidden" }}>
            <div style={{ position:"absolute", top:-60, right:-60, width:320, height:320, borderRadius:"50%", background:`radial-gradient(circle,${GOLD}18,transparent 70%)`, pointerEvents:"none" }} />
            <div style={{ position:"relative" }}>
              <div style={{ fontSize:10, fontWeight:800, color:GOLD, letterSpacing:3, marginBottom:10, textTransform:"uppercase" as const }}>App Logos & Brand Identity — Sokoon | سكون</div>
              <h1 style={{ fontSize:34, fontWeight:900, color:"#F1F5F9", margin:"0 0 10px", ...TJ }}>20 Logo Concepts · 12 Feature Graphics</h1>
              <p style={{ color:"#475569", fontSize:13, margin:"0 0 22px", direction:"rtl", textAlign:"right", lineHeight:1.8, maxWidth:560, ...TJ }}>هوية بصرية كاملة — شعارات عربية، ثنائية اللغة، رموز تطبيق، أختام، ولوحات تسويقية</p>
              <div style={{ display:"flex", gap:8, flexWrap:"wrap" as const }}>
                {[{l:"20 Logo Concepts",c:GOLD},{l:"6 Categories",c:TEAL},{l:"Arabic Wordmark",c:GREEN},{l:"App Icons",c:BLUE},{l:"Feature Graphics ×12",c:PURP}].map(b=>(
                  <span key={b.l} style={{ fontSize:11, fontWeight:700, color:b.c, background:b.c+"18", border:`1px solid ${b.c}33`, borderRadius:20, padding:"4px 14px" }}>{b.l}</span>
                ))}
              </div>
            </div>
          </div>
          <LogoConceptsTab />
          <div style={{ borderTop:`1px solid ${BDR}`, padding:"40px 56px 32px" }}>
            <div style={{ fontSize:10, fontWeight:800, color:"#334155", letterSpacing:2, textTransform:"uppercase" as const, marginBottom:32 }}>Feature Graphics — 12 Concepts</div>
            <FutureGraphicsTab />
          </div>
        </div>
      )}
    </div>
  );
}
