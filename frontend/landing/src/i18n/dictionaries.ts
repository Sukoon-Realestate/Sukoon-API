import type { Locale } from "./config";
import { featuresAr, featuresEn } from "./features";

const ar = {
  features: featuresAr,
  meta: {
    title: "سكون – سكنك القادم من المالك مباشرة",
    description:
      "سكون يجمع المالك والمستأجر مباشرة. مراجعة الهوية مستقلة عن مراجعة العقار. عمولة التأجير على المالك 10% من إيجار الفترة الأولى، وعمولة التجديد 0%، ورسوم خدمة المستأجر صفر.",
    ogAlt: "سكون: سكنك القادم من المالك مباشرة، تواصل مباشر وسياسة رسوم واضحة.",
  },
  loading: "جارٍ التحميل…",
  header: {
    switchLanguage: "English",
    getApp: "حمّل التطبيق",
    adminDashboard: "لوحة الإدارة",
    homeLabel: "سكون – الصفحة الرئيسية",
    toggleTheme: "تبديل الوضع الليلي",
  },
  nav: {
    label: "أقسام الصفحة",
    features: "داخل سكون",
    howItWorks: "كيف يعمل",
    why: "لماذا سكون",
    faq: "أسئلة شائعة",
    download: "حمّل التطبيق",
  },
  store: {
    comingSoon: "قريبًا على",
    appStore: "App Store",
    googlePlay: "Google Play",
  },
  hero: {
    badge: "قريبًا على App Store و Google Play",
    titleLead: "سكنك القادم،",
    titleHighlight: "من المالك مباشرة.",
    subtitle:
      "سكون يجمع المالك والمستأجر مباشرة. مراجعة الهوية مستقلة عن مراجعة العقار. عمولة التأجير على المالك 10% من إيجار الفترة الأولى، وعمولة التجديد 0%، ورسوم خدمة المستأجر صفر.",
    tenantPrompt: "تبحث عن سكن؟",
    tenantLink: "كيف تستأجر",
    ownerPrompt: "لديك عقار للإيجار؟",
    ownerLink: "كيف تعرض عقارك",
  },
  trust: {
    label: "سكون باختصار",
    items: [
      { title: "رسوم واضحة", body: "لا سمسار ولا وسيط" },
      { title: "حالة مراجعة واضحة", body: "راجع حالة العقار قبل المتابعة" },
      { title: "حسابات موثّقة", body: "تعرف مع من تتعامل" },
      { title: "شات وحجز معاينة", body: "من داخل التطبيق" },
    ],
  },
  phone: {
    locationLabel: "موقعك",
    location: "القاهرة",
    avatar: "أ",
    title: "ابحث عن سكنك",
    search: "ابحث بالمنطقة أو المدينة",
    filters: ["الكل", "شقق", "استوديو", "فيلا"],
    reviewed: "تمت المراجعة",
    listings: [
      { title: "شقة 3 غرف", price: "18,000 ج.م", location: "التجمع الخامس، القاهرة", period: "شهريًا" },
      { title: "استوديو مفروش", price: "9,500 ج.م", location: "المعادي، القاهرة", period: "شهريًا" },
    ],
    tabs: ["الرئيسية", "المحفوظة", "الرسائل", "حسابي"],
    verifiedOwner: { title: "مالك موثّق", subtitle: "تم التحقق من بياناته" },
    viewingBooked: { title: "تم حجز المعاينة", subtitle: "الخميس · 6:00 مساءً" },
  },
  howItWorks: {
    eyebrow: "كيف يعمل سكون",
    title: "خطوات بسيطة للطرفين",
    subtitle: "سواء كنت تبحث عن سكن أو تعرض عقارك، الطريق واضح من أول خطوة.",
    tenant: {
      label: "للمستأجر",
      title: "تبحث عن سكن؟",
      steps: [
        { title: "أنشئ حسابك ووثّقه", body: "سجّل ببياناتك الشخصية مرة واحدة." },
        { title: "تصفّح العقارات وحالة مراجعتها", body: "ظهور العقار في البحث لا يعني اعتماده؛ راجع حالة المراجعة والتفاصيل قبل المتابعة." },
        { title: "تكلّم مع المالك واحجز معاينة", body: "اسأل عن أي تفصيلة في الشات، واختر الموعد المناسب لك." },
        { title: "اتفق مع المالك مباشرة", body: "اتفاق مباشر وفق شروط الرسوم المعروضة." },
      ],
    },
    owner: {
      label: "للمالك",
      title: "لديك عقار للإيجار؟",
      steps: [
        { title: "وثّق حسابك", body: "ببياناتك الشخصية، ليعرف المستأجر مع من يتعامل." },
        { title: "أضف عقارك بكل تفاصيله", body: "كل ما يحتاج المستأجر أن يعرفه، في مكان واحد." },
        { title: "نراجعه قبل النشر", body: "نتأكد من تفاصيل العقار وبياناته قبل أن يظهر للمستأجرين." },
        { title: "استقبل طلبات المعاينة", body: "وردّ على المستأجرين من الشات، بدون إزعاج." },
      ],
    },
  },
  why: {
    eyebrow: "لماذا سكون",
    titleLines: ["اسم على مسمّى"],
    subtitle:
      "اسمنا يعني الهدوء وراحة البال، وكل ميزة في التطبيق موجودة لتجعل الإيجار أوضح وأسهل للطرفين.",
    commission: {
      // Display the supported rental policy rather than an unimplemented launch promise.
      badge: "سياسة التأجير",
      titleLines: ["بدون سمسار،", "رسوم واضحة"],
      body: "عمولة التأجير على المالك 10% من إيجار الفترة الأولى، وعمولة التجديد 0%. لا توجد رسوم خدمة على المستأجر.",
      stat: "10%",
      statLabel: "عمولة المالك على إيجار الفترة الأولى",
    },
    verified: {
      initial: "م",
      name: "محمد عادل",
      role: "مالك عقار",
      badge: "موثّق",
      title: "حسابات موثّقة",
      body: "تظهر حالة التحقق بعد مراجعة مستندات الهوية؛ إنشاء الحساب وحده لا يعني توثيقه.",
    },
    review: {
      checks: ["تفاصيل العقار", "بيانات العقار"],
      status: "جاهز للنشر",
      title: "مراجعة بيانات العقار",
      body: "الإعلان وموافقة المراجعة خطوتان مختلفتان. راجع حالة العقار وتفاصيله قبل الاتفاق.",
    },
    chat: {
      question: "هل الشقة متاحة للمعاينة هذا الأسبوع؟",
      answer: "نعم، اختر الموعد المناسب لك من التطبيق.",
      title: "شات داخل التطبيق",
      body: "تواصل مع المالك أو المستأجر مباشرة من داخل التطبيق.",
    },
    booking: {
      days: ["السبت", "الأحد", "الإثنين"],
      times: ["5:00 مساءً", "6:30 مساءً"],
      confirm: "تأكيد الموعد",
      title: "حجز معاينة بسهولة",
      body: "اختر موعد المعاينة في خطوات بسيطة، بدون إزعاج.",
    },
  },
  faq: {
    eyebrow: "أسئلة شائعة",
    title: "لديك سؤال؟",
    subtitle: "إجابات سريعة عن أكثر ما يسأل عنه الناس.",
    items: [
      { question: "هل يأخذ سكون عمولة؟", answer: "نعم، في مسار التأجير المدعوم يدفع المالك 10% من إيجار الفترة الأولى. عمولة التجديد 0% ورسوم خدمة المستأجر صفر. راجع الشروط قبل الموافقة." },
      { question: "كيف تتأكدون من العقارات؟", answer: "تخضع بيانات العقار للمراجعة، لكن ظهور الإعلان في البحث لا يعني اعتماده. راجع حالة المراجعة وتحقق من التفاصيل قبل الاتفاق." },
      { question: "لماذا أوثّق حسابي؟", answer: "حتى يعرف كل طرف مع من يتعامل. يتم التوثيق بمعلوماتك الشخصية." },
      { question: "متى ينزل التطبيق؟", answer: "قريبًا على App Store و Google Play." },
    ],
  },
  finalCta: {
    title: "الإيجار، بكل سكون.",
    subtitle: "التطبيق قادم قريبًا على App Store و Google Play",
  },
  footer: {
    unavailable: "غير متاح",
    unavailableHelp: "غير متاح حتى إعداد وجهة عامة معتمدة.",
    privacy: "الخصوصية",
    terms: "الشروط",
    contact: "تواصل معنا",
    linksLabel: "روابط",
    socialLabel: "تابعنا على مواقع التواصل الاجتماعي",
    copyright: "© 2026 سكون. جميع الحقوق محفوظة.",
  },
  notFound: {
    title: "الصفحة غير موجودة",
    body: "الرابط الذي فتحته غير موجود أو تم نقله.",
    cta: "العودة إلى الصفحة الرئيسية",
  },
};

export type Dictionary = typeof ar;

const en: Dictionary = {
  features: featuresEn,
  meta: {
    title: "Sukoon – Your next home, straight from the owner",
    description:
      "Sukoon connects owners and tenants directly. Identity and listing review are separate. Owners pay 10% of first-period base rent, with 0% renewal commission and no tenant service fee.",
    ogAlt: "Sukoon: your next home, straight from the owner, with direct communication and clear rental fees.",
  },
  loading: "Loading…",
  header: {
    switchLanguage: "العربية",
    getApp: "Get the app",
    adminDashboard: "Admin dashboard",
    homeLabel: "Sukoon – Home",
    toggleTheme: "Toggle dark mode",
  },
  nav: {
    label: "Page sections",
    features: "Inside Sukoon",
    howItWorks: "How it works",
    why: "Why Sukoon",
    faq: "FAQ",
    download: "Get the app",
  },
  store: {
    comingSoon: "Coming soon on",
    appStore: "App Store",
    googlePlay: "Google Play",
  },
  hero: {
    badge: "Coming soon to the App Store and Google Play",
    titleLead: "Your next home,",
    titleHighlight: "straight from the owner.",
    subtitle:
      "Sukoon connects owners and tenants directly. Identity and listing review are separate. Owners pay 10% of first-period base rent, with 0% renewal commission and no tenant service fee.",
    tenantPrompt: "Looking for a place?",
    tenantLink: "How renting works",
    ownerPrompt: "Have a property to rent?",
    ownerLink: "How listing works",
  },
  trust: {
    label: "Sukoon at a glance",
    items: [
      { title: "Clear fees", body: "No broker, no middleman" },
      { title: "Visible review status", body: "Check the listing status before continuing" },
      { title: "Verified accounts", body: "Know who you’re dealing with" },
      { title: "Chat & book viewings", body: "Right inside the app" },
    ],
  },
  phone: {
    locationLabel: "Your location",
    location: "Cairo",
    avatar: "A",
    title: "Find your place",
    search: "Search by area or city",
    filters: ["All", "Flats", "Studios", "Villas"],
    reviewed: "Reviewed",
    listings: [
      { title: "3-bed apartment", price: "EGP 18,000", location: "New Cairo, Cairo", period: "per month" },
      { title: "Furnished studio", price: "EGP 9,500", location: "Maadi, Cairo", period: "per month" },
    ],
    tabs: ["Home", "Saved", "Messages", "Profile"],
    verifiedOwner: { title: "Verified owner", subtitle: "Personal details checked" },
    viewingBooked: { title: "Viewing booked", subtitle: "Thu · 6:00 PM" },
  },
  howItWorks: {
    eyebrow: "How Sukoon works",
    title: "Simple steps for both sides",
    subtitle: "Whether you’re looking for a place or renting one out, the path is clear from the first step.",
    tenant: {
      label: "For tenants",
      title: "Looking for a place?",
      steps: [
        { title: "Create and verify your account", body: "Sign up once with your personal details." },
        { title: "Browse listings and their review status", body: "Appearing in search does not establish approval. Check the review status and property details before continuing." },
        { title: "Chat and book a viewing", body: "Ask the owner anything, then pick a time that suits you." },
        { title: "Agree with the owner directly", body: "Agree directly under the displayed fee policy." },
      ],
    },
    owner: {
      label: "For owners",
      title: "Have a property to rent?",
      steps: [
        { title: "Verify your account", body: "With your personal details, so tenants know who they’re dealing with." },
        { title: "Add your property with all its details", body: "Everything a tenant needs to know, in one place." },
        { title: "We review it before it goes live", body: "We check the property’s details and information before tenants see it." },
        { title: "Get viewing requests", body: "And reply to tenants in the chat, without the hassle." },
      ],
    },
  },
  why: {
    eyebrow: "Why Sukoon",
    titleLines: ["Calm by name.", "Calm by design."],
    subtitle:
      "Sukoon means calm in Arabic, and every feature in the app is there to make renting clearer and easier for both sides.",
    commission: {
      badge: "Rental fee policy",
      titleLines: ["No broker.", "Clear fees."],
      body: "The owner pays 10% of first-period base rent. Renewal commission is 0%; the tenant service fee is zero.",
      stat: "10%",
      statLabel: "owner commission on first-period rent",
    },
    verified: {
      initial: "M",
      name: "Mohamed Adel",
      role: "Property owner",
      badge: "Verified",
      title: "Verified accounts",
      body: "Identity status reflects document review. Creating an account alone does not establish identity verification.",
    },
    review: {
      checks: ["Property details", "Property information"],
      status: "Ready to publish",
      title: "Property information review",
      body: "Listing a property and approving its information are separate steps. Check the review status and details before agreeing.",
    },
    chat: {
      question: "Is the apartment free to view this week?",
      answer: "Yes, pick whatever time suits you in the app.",
      title: "In-app chat",
      body: "Talk to the owner or tenant directly, right inside the app.",
    },
    booking: {
      days: ["Sat", "Sun", "Mon"],
      times: ["5:00 PM", "6:30 PM"],
      confirm: "Confirm viewing",
      title: "Easy viewing bookings",
      body: "Book a viewing in a few simple steps, without the hassle.",
    },
  },
  faq: {
    eyebrow: "FAQ",
    title: "Got a question?",
    subtitle: "Quick answers to what people ask most.",
    items: [
      {
        question: "Does Sukoon take a commission?",
        answer: "For the supported rental flow, the owner pays 10% of first-period base rent. Renewal commission is 0% and the tenant service fee is zero. Review the agreement before accepting.",
      },
      {
        question: "How do you check properties?",
        answer: "Property information is subject to review, but appearing in search does not establish approval. Check the review status and confirm the details before agreeing.",
      },
      {
        question: "Why do I need to verify my account?",
        answer: "So both sides know who they’re dealing with. You verify with your personal details.",
      },
      { question: "When is the app coming out?", answer: "Soon, on the App Store and Google Play." },
    ],
  },
  finalCta: {
    title: "Renting, made calm.",
    subtitle: "The app is coming soon to the App Store and Google Play.",
  },
  footer: {
    unavailable: "Unavailable",
    unavailableHelp: "Unavailable until an approved public destination is configured.",
    privacy: "Privacy",
    terms: "Terms",
    contact: "Contact us",
    linksLabel: "Links",
    socialLabel: "Follow us on social media",
    copyright: "© 2026 Sukoon. All rights reserved.",
  },
  notFound: {
    title: "Page not found",
    body: "The link you followed doesn’t exist or has moved.",
    cta: "Back to the homepage",
  },
};

const dictionaries: Record<Locale, Dictionary> = { ar, en };

export const getDictionary = (locale: Locale) => dictionaries[locale];
