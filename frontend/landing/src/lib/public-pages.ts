import type { Locale } from "@/i18n/config";
import { BUSINESS } from "@/lib/site";

export const publicPages = {
  privacy: {
    title: { en: "Privacy policy", ar: "سياسة الخصوصية" },
    description: {
      en: "How Sukoon handles personal information, permissions and privacy requests.",
      ar: "كيف يتعامل سكون مع البيانات الشخصية والأذونات وطلبات الخصوصية.",
    },
  },
  terms: {
    title: { en: "Terms of use", ar: "شروط الاستخدام" },
    description: {
      en: "Read the terms for using Sukoon accounts, listings and rental services.",
      ar: "اقرأ شروط استخدام حسابات سكون والإعلانات وخدمات الإيجار.",
    },
  },
  "delete-account": {
    title: { en: "Delete your Sukoon account", ar: "حذف حسابك في سكون" },
    description: {
      en: "Request deletion of your Sukoon account and associated personal data, with or without the app.",
      ar: "اطلب حذف حسابك في سكون والبيانات الشخصية المرتبطة به، حتى إذا لم يعد التطبيق على جهازك.",
    },
  },
  support: {
    title: { en: "Support & contact", ar: "الدعم والتواصل" },
    description: {
      en: "Contact Sukoon about account access, app issues, privacy or account deletion.",
      ar: "تواصل مع سكون بشأن الدخول لحسابك أو مشكلات التطبيق أو الخصوصية أو حذف الحساب.",
    },
  },
} as const;

export type PublicPage = keyof typeof publicPages;
export const publicPageKeys = Object.keys(publicPages) as PublicPage[];

// Only prepares an email. The visitor reviews and sends it in their own mail app.
export function contactMailto(subject: string, body?: string) {
  const query = new URLSearchParams({ subject });
  if (body) query.set("body", body);
  return `mailto:${BUSINESS.email}?${query.toString().replace(/\+/g, "%20")}`;
}

export function deletionMailto(lang: Locale) {
  return contactMailto(
    lang === "ar" ? "طلب حذف حساب سكون" : "Sukoon account deletion request",
    lang === "ar"
      ? "أطلب حذف حسابي في سكون والبيانات الشخصية المرتبطة به.\n\nالبريد الإلكتروني المرتبط بالحساب: \n\nيرجى توضيح الخطوات التالية وأي بيانات يجب الاحتفاظ بها وسبب ومدة الاحتفاظ."
      : "Please delete my Sukoon account and associated personal data.\n\nAccount email: \n\nPlease explain the next steps and any data that must be retained, including the reason and retention period.",
  );
}
