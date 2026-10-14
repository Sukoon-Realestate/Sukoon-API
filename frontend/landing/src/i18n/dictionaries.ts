import type { Locale } from "./config";

const ar = {
  meta: {
    title: "سكون – سكنك القادم من المالك مباشرة",
    description:
      "سكون يجمع المالك والمستأجر في مكان واحد، بدون سمسار وبدون عمولة. نراجع كل عقار قبل نشره، وكل الحسابات موثّقة.",
    ogAlt: "سكون: سكنك القادم من المالك مباشرة، بدون سمسار وبدون عمولة.",
  },
  header: {
    switchLanguage: "English",
    getApp: "حمّل التطبيق",
    homeLabel: "سكون – الصفحة الرئيسية",
  },
  nav: {
    label: "أقسام الصفحة",
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
      "سكون يجمع المالك والمستأجر في مكان واحد، بدون سمسار وبدون عمولة. نراجع كل عقار قبل نشره، وكل الحسابات موثّقة.",
    tenantPrompt: "تبحث عن سكن؟",
    tenantLink: "كيف تستأجر",
    ownerPrompt: "لديك عقار للإيجار؟",
    ownerLink: "كيف تعرض عقارك",
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
        { title: "تصفّح عقارات تمت مراجعتها", body: "كل عقار تراه في سكون راجعناه قبل نشره." },
        { title: "تكلّم مع المالك واحجز معاينة", body: "اسأل عن أي تفصيلة في الشات، واختر الموعد المناسب لك." },
        { title: "اتفق مع المالك مباشرة", body: "بدون سمسار، وبدون عمولة." },
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
      // ? Copied verbatim from the design; the EN equivalent reads "Non-profit at launch".
      badge: "سكون بدون سمسار او عموله",
      titleLines: ["بدون سمسار،", "بدون عمولة"],
      body: "لا وسيط بينك وبين الطرف الآخر، ولا عمولة تدفعها لأحد.",
      stat: "0%",
      statLabel: "عمولة",
    },
    verified: {
      initial: "م",
      name: "محمد عادل",
      role: "مالك عقار",
      badge: "موثّق",
      title: "حسابات موثّقة",
      body: "يوثّق كل مستخدم حسابه بمعلوماته الشخصية، فتعرف دائمًا مع من تتعامل.",
    },
    review: {
      checks: ["تفاصيل العقار", "بيانات العقار"],
      status: "جاهز للنشر",
      title: "مراجعة كاملة لكل عقار",
      body: "قبل نشر أي عقار، نراجع تفاصيله وبياناته بالكامل.",
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
      { question: "هل يأخذ سكون عمولة؟", answer: "لا. لا يوجد سمسار ولا وسيط ولا عمولة، وسكون غير ربحي في بدايته." },
      { question: "كيف تتأكدون من العقارات؟", answer: "نراجع تفاصيل وبيانات كل عقار بالكامل قبل نشره على التطبيق." },
      { question: "لماذا أوثّق حسابي؟", answer: "حتى يعرف كل طرف مع من يتعامل. يتم التوثيق بمعلوماتك الشخصية." },
      { question: "متى ينزل التطبيق؟", answer: "قريبًا على App Store و Google Play." },
    ],
  },
  finalCta: {
    title: "الإيجار، بكل سكون.",
    subtitle: "التطبيق قادم قريبًا على App Store و Google Play",
  },
  footer: {
    privacy: "الخصوصية",
    terms: "الشروط",
    contact: "تواصل معنا",
    linksLabel: "روابط",
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
  meta: {
    title: "Sukoon – Your next home, straight from the owner",
    description:
      "Sukoon brings owners and tenants together in one place, with no broker and no commission. We review every property before it goes live, and every account is verified.",
    ogAlt: "Sukoon: your next home, straight from the owner, with no broker and no commission.",
  },
  header: {
    switchLanguage: "العربية",
    getApp: "Get the app",
    homeLabel: "Sukoon – Home",
  },
  nav: {
    label: "Page sections",
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
      "Sukoon brings owners and tenants together in one place, with no broker and no commission. We review every property before it goes live, and every account is verified.",
    tenantPrompt: "Looking for a place?",
    tenantLink: "How renting works",
    ownerPrompt: "Have a property to rent?",
    ownerLink: "How listing works",
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
        { title: "Browse reviewed listings", body: "Every property on Sukoon was checked before it went live." },
        { title: "Chat and book a viewing", body: "Ask the owner anything, then pick a time that suits you." },
        { title: "Agree with the owner directly", body: "No broker. No commission." },
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
      badge: "Non-profit at launch",
      titleLines: ["No broker.", "No commission."],
      body: "Nobody in the middle, and no commission to pay anyone.",
      stat: "0%",
      statLabel: "commission",
    },
    verified: {
      initial: "M",
      name: "Mohamed Adel",
      role: "Property owner",
      badge: "Verified",
      title: "Verified accounts",
      body: "Every user verifies their account with personal details, so you always know who you’re dealing with.",
    },
    review: {
      checks: ["Property details", "Property information"],
      status: "Ready to publish",
      title: "Every property, fully reviewed",
      body: "Before any property goes live, we review all of its details and information.",
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
        answer: "No. There’s no broker, no middleman and no commission, and Sukoon is non-profit at launch.",
      },
      {
        question: "How do you check properties?",
        answer: "We fully review every property’s details and information before it’s published in the app.",
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
    privacy: "Privacy",
    terms: "Terms",
    contact: "Contact us",
    linksLabel: "Links",
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
