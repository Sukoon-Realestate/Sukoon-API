import type { Locale } from "./config";
import { featuresAr, featuresEn } from "./features";

const ar = {
  features: featuresAr,
  meta: {
    title: "سكون – سكنك القادم من المالك مباشرة",
    description:
      "سكون يجمع المالك والمستأجر مباشرة، بدون عمولات على التأجير أو التجديد لأي من الطرفين. تصفّح العقارات وتواصل مع المالك واحجز معاينة من داخل التطبيق.",
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
    appStore: "App Store",
    googlePlay: "Google Play",
  },
  hero: {
    badge: "متاح على App Store و Google Play",
    titleLead: "سكنك القادم،",
    titleHighlight: "من المالك مباشرة.",
    subtitle:
      "سكون يجمع المالك والمستأجر في مكان واحد لتجربة إيجار أسهل وأوضح. تصفّح العقارات، وتعرّف على تفاصيلها وحالة مراجعتها، وتواصل مع المالك مباشرة واحجز موعد المعاينة من داخل التطبيق. وإذا كنت مالكًا، اعرض عقارك بتفاصيله وصوره، وتابع رسائل المستأجرين وطلبات المعاينة بكل سهولة.",
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
        { title: "اتفق مع المالك مباشرة", body: "اتفاق مباشر مع المالك، بدون عمولة لسكون." },
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
      badge: "بدون عمولات",
      titleLines: ["بدون سمسار،", "بدون عمولات"],
      body: "سكون لا يأخذ أي عمولة من المالك أو المستأجر، سواء عند التأجير أو التجديد. تواصل واتفق مباشرة، بدون وسيط.",
      stat: "0%",
      statLabel: "عمولة على المالك والمستأجر",
    },
    verified: {
      initial: "و",
      name: "وليد الوهيدي",
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
      { question: "هل يأخذ سكون عمولة؟", answer: "لا، سكون لا يأخذ أي عمولة من المالك أو المستأجر، سواء عند التأجير أو تجديد الإيجار. تتواصل وتتفق مع الطرف الآخر مباشرة من خلال التطبيق، بدون وسيط." },
      { question: "كيف تتأكدون من العقارات؟", answer: "تخضع بيانات العقار للمراجعة، لكن ظهور الإعلان في البحث لا يعني اعتماده. راجع حالة المراجعة وتحقق من التفاصيل قبل الاتفاق." },
      { question: "لماذا أوثّق حسابي؟", answer: "حتى يعرف كل طرف مع من يتعامل. يتم التوثيق بمعلوماتك الشخصية." },
      { question: "أين يمكنني تحميل التطبيق؟", answer: "متاح على App Store و Google Play." },
    ],
  },
  finalCta: {
    title: "الإيجار، بكل سكون.",
    subtitle: "App Store و Google Play",
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
      "Sukoon connects owners and tenants directly, with no rental or renewal commissions for either side. Browse properties, chat with owners, and book viewings in the app.",
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
    appStore: "App Store",
    googlePlay: "Google Play",
  },
  hero: {
    badge: "Available on the App Store and Google Play",
    titleLead: "Your next home,",
    titleHighlight: "straight from the owner.",
    subtitle:
      "Sukoon brings owners and tenants together for a simpler, clearer rental experience. Browse properties, explore their details and review status, chat directly with owners, and book viewings in the app. If you’re an owner, list your property with photos and details, then manage tenant messages and viewing requests in one place.",
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
        { title: "Agree with the owner directly", body: "Agree directly with the owner, with no commission to Sukoon." },
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
      badge: "No commissions",
      titleLines: ["No broker.", "No commissions."],
      body: "Sukoon takes no commission from owners or tenants, whether renting or renewing. Connect and agree directly, without a middleman.",
      stat: "0%",
      statLabel: "commission for owners and tenants",
    },
    verified: {
      initial: "W",
      name: "Walid Al-Wahaidi",
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
        answer: "No. Sukoon takes no commission from owners or tenants, whether renting or renewing a lease. Connect and agree directly through the app, without a middleman.",
      },
      {
        question: "How do you check properties?",
        answer: "Property information is subject to review, but appearing in search does not establish approval. Check the review status and confirm the details before agreeing.",
      },
      {
        question: "Why do I need to verify my account?",
        answer: "So both sides know who they’re dealing with. You verify with your personal details.",
      },
      { question: "Where can I download the app?", answer: "The app is available on the App Store and Google Play." },
    ],
  },
  finalCta: {
    title: "Renting, made calm.",
    subtitle: "App Store and Google Play",
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
