import Image from "next/image";
import {
  ArrowLeft,
  Bell,
  CalendarDays,
  ChevronDown,
  Heart,
  House,
  MapPin,
  MessageCircle,
  Plus,
  Search,
  Send,
  ShieldCheck,
  SlidersHorizontal,
  Star,
  User,
} from "lucide-react";
import type { Locale } from "@/i18n/config";

const copy = {
  ar: {
    titles: [
      "ابحث عن سكنك",
      "العقارات المحفوظة",
      "احجز معاينة",
      "أهلًا وليد",
      "المحادثات",
      "الإشعارات",
      "قيّم تجربتك",
      "كيف نقدر نساعدك؟",
    ],
    tabs: ["الرئيسية", "المحفوظة", "الرسائل", "حسابي"],
    location: "القاهرة",
    search: "ابحث بالمنطقة أو المدينة",
    filters: "فلاتر البحث",
    area: "المنطقة",
    district: "المعادي، القاهرة",
    type: "نوع العقار",
    types: ["الكل", "شقة", "استوديو", "فيلا"],
    price: "الإيجار الشهري",
    range: "٥٬٠٠٠ – ٢٠٬٠٠٠ ج.م",
    rooms: "عدد الغرف",
    amenities: "المرافق",
    facilities: ["تكييف", "واي فاي", "جراج"],
    results: "عرض العقارات",
    apartment: "شقة ٣ غرف",
    studio: "استوديو مفروش",
    rent: "١٨٬٠٠٠ ج.م / شهر",
    studioRent: "٩٬٥٠٠ ج.م / شهر",
    reviewed: "تمت المراجعة",
    compare: "قارن اختياراتك",
    saved: "عقاراتك المفضلة في مكان واحد",
    day: "اختر اليوم المناسب",
    days: ["السبت", "الأحد", "الإثنين"],
    time: "المواعيد المتاحة",
    confirm: "إرسال طلب المعاينة",
    notice: "سيتم تأكيد الموعد بعد موافقة المالك",
    stats: ["عقاراتي", "طلبات المعاينة", "المشاهدات"],
    manage: "إدارة عقاراتك",
    requests: "طلبات المعاينة",
    tenant: "أحمد محمد",
    request: "طلب معاينة · شقة المعادي",
    accept: "قبول",
    decline: "رفض",
    owner: "وليد الوهيدي",
    online: "مالك العقار",
    messages: [
      "أهلًا، هل الشقة متاحة للمعاينة؟",
      "أهلًا بك! نعم، اختر الموعد المناسب من التطبيق.",
      "شكرًا، سأرسل طلب المعاينة الآن.",
    ],
    write: "اكتب رسالتك…",
    updates: [
      "تم تأكيد موعد المعاينة",
      "لديك رسالة جديدة من المالك",
      "تم تحديث حالة عقارك",
    ],
    details: [
      "شقة المعادي · الخميس، ٦:٠٠ مساءً",
      "اضغط للاطّلاع على المحادثة",
      "يمكنك متابعة التفاصيل من حسابك",
    ],
    today: "اليوم",
    review: "كيف كانت المعاينة؟",
    criteria: ["النظافة", "دقة بيانات الإعلان", "تعامل المالك"],
    comment: "أضف تعليقًا عن تجربتك…",
    submit: "إرسال التقييم",
    ticket: "تذكرة دعم جديدة",
    subject: "الموضوع",
    subjectText: "استفسار عن موعد معاينة",
    description: "تفاصيل المشكلة",
    descriptionText: "اكتب التفاصيل لمساعدة فريق الدعم…",
    attach: "إرفاق صورة",
    send: "إرسال التذكرة",
    help: "نحن هنا لمساعدتك",
    helpText: "أرسل استفسارك وتابع الردود في مكان واحد",
  },
  en: {
    titles: [
      "Find your place",
      "Saved properties",
      "Book a viewing",
      "Hello, Walid",
      "Conversations",
      "Notifications",
      "Rate your experience",
      "How can we help?",
    ],
    tabs: ["Home", "Saved", "Messages", "Profile"],
    location: "Cairo",
    search: "Search by area or city",
    filters: "Search filters",
    area: "Location",
    district: "Maadi, Cairo",
    type: "Property type",
    types: ["All", "Flat", "Studio", "Villa"],
    price: "Monthly rent",
    range: "EGP 5,000 – 20,000",
    rooms: "Bedrooms",
    amenities: "Amenities",
    facilities: ["Air conditioning", "Wi-Fi", "Parking"],
    results: "Show properties",
    apartment: "3-bedroom apartment",
    studio: "Furnished studio",
    rent: "EGP 18,000 / month",
    studioRent: "EGP 9,500 / month",
    reviewed: "Reviewed",
    compare: "Compare your shortlist",
    saved: "Your favourite homes in one place",
    day: "Choose a day",
    days: ["Saturday", "Sunday", "Monday"],
    time: "Available times",
    confirm: "Request a viewing",
    notice: "The owner will confirm your viewing request",
    stats: ["Properties", "Viewing requests", "Views"],
    manage: "Manage your properties",
    requests: "Viewing requests",
    tenant: "Ahmed Mohamed",
    request: "Viewing request · Maadi apartment",
    accept: "Accept",
    decline: "Decline",
    owner: "Walid Al-Wahaidi",
    online: "Property owner",
    messages: [
      "Hi, is the apartment available for a viewing?",
      "Welcome! Yes, choose a time that suits you in the app.",
      "Thanks, I’ll send a viewing request now.",
    ],
    write: "Write a message…",
    updates: [
      "Your viewing is confirmed",
      "New message from the owner",
      "Your property status was updated",
    ],
    details: [
      "Maadi apartment · Thursday, 6:00 PM",
      "Open your conversation to read more",
      "Check your account for details",
    ],
    today: "Today",
    review: "How was your viewing?",
    criteria: ["Cleanliness", "Listing accuracy", "Owner interaction"],
    comment: "Tell us about your experience…",
    submit: "Submit review",
    ticket: "New support ticket",
    subject: "Subject",
    subjectText: "Question about a viewing",
    description: "Issue details",
    descriptionText: "Share details to help our support team…",
    attach: "Attach a photo",
    send: "Send ticket",
    help: "We’re here to help",
    helpText: "Send your question and follow replies in one place",
  },
};

export function FeaturePhoneScreen({
  index,
  lang,
}: {
  index: number;
  lang: Locale;
}) {
  const c = copy[lang];
  const card = "rounded-2xl border border-line bg-paper p-3";
  const field =
    "mt-2 flex items-center justify-between rounded-xl border border-line bg-paper p-3 text-[10px] text-muted";
  const action = (label: string) => (
    <div className="mt-4 rounded-xl bg-brand-deep px-3 py-3 text-center text-[11px] font-semibold text-white">
      {label}
    </div>
  );
  const label = (text: string) => (
    <p className="mb-2 mt-4 text-[11px] font-semibold">{text}</p>
  );
  const property = (studio = false) => (
    <div className="overflow-hidden rounded-2xl border border-line bg-paper">
      <div className="relative h-24">
        <Image
          unoptimized
          src={`/images/listings/${studio ? "studio" : "apartment"}.jpg`}
          alt=""
          fill
          className="object-cover"
        />
        <span className="absolute start-2 top-2 rounded-full bg-paper px-2 py-1 text-[8px] text-accent">
          ✓ {c.reviewed}
        </span>
        <Heart className="absolute end-2 top-2 size-5 rounded-full bg-paper p-1 text-accent" />
      </div>
      <div className="space-y-1 p-3">
        <p className="text-[11px] font-bold">
          {studio ? c.studio : c.apartment}
        </p>
        <p className="text-[10px] font-bold text-accent">
          {studio ? c.studioRent : c.rent}
        </p>
        <p className="flex items-center gap-1 text-[9px] text-muted">
          <MapPin className="size-3" />
          {c.district}
        </p>
      </div>
    </div>
  );
  const icons = [House, Heart, MessageCircle, User];

  return (
    <div
      dir={lang === "ar" ? "rtl" : "ltr"}
      aria-hidden
      className="relative flex aspect-[390/844] flex-col overflow-hidden bg-[#f6f8f6] text-start text-fg dark:bg-ink-raised"
    >
      <div className="relative flex h-10 shrink-0 items-center justify-between px-5 text-[9px] font-bold">
        <span dir="ltr">9:41</span>
        <span className="absolute left-1/2 top-2 h-4 w-20 -translate-x-1/2 rounded-full bg-black" />
        <span dir="ltr">▮▮▮ ▰</span>
      </div>
      <div className="flex min-h-0 flex-1 flex-col overflow-hidden px-4 pb-3">
        <div className="mb-4 flex items-center justify-between gap-2">
          <h4 className="text-base font-bold leading-snug">
            {c.titles[index]}
          </h4>
          {index === 3 ? (
            <Plus className="size-6 rounded-full bg-brand-deep p-1 text-white" />
          ) : (
            <ArrowLeft className="size-4 shrink-0 rtl:rotate-180" />
          )}
        </div>
        {index === 0 && (
          <>
            <div className="flex items-center gap-2 rounded-full border border-line bg-paper p-2 text-[9px] text-muted">
              <Search className="size-3" />
              {c.search}
              <SlidersHorizontal className="ms-auto size-3" />
            </div>
            {label(c.filters)}
            <div className={card}>
              {label(c.area)}
              <div className={field}>
                {c.district}
                <ChevronDown className="size-3" />
              </div>
              {label(c.type)}
              <div className="flex gap-1">
                {c.types.map((t, i) => (
                  <span
                    key={t}
                    className={`rounded-full px-2 py-1 text-[9px] ${i === 0 ? "bg-brand-deep text-white" : "bg-chip text-accent"}`}
                  >
                    {t}
                  </span>
                ))}
              </div>
              {label(c.price)}
              <p className="text-[10px] text-muted">{c.range}</p>
              <div className="my-3 h-1 rounded bg-brand">
                <div className="mx-4 -translate-y-1 border-x-8 border-brand-deep h-3" />
              </div>
              {label(c.rooms)}
              <div className="flex gap-2" dir="ltr">
                {[1, 2, 3, "4+"].map((n) => (
                  <span
                    key={n}
                    className="rounded-lg bg-chip px-3 py-1 text-[10px] text-accent"
                  >
                    {n}
                  </span>
                ))}
              </div>
              {label(c.amenities)}
              <div className="flex flex-wrap gap-1">
                {c.facilities.map((t) => (
                  <span
                    key={t}
                    className="rounded-md bg-chip px-2 py-1 text-[8px] text-accent"
                  >
                    ✓ {t}
                  </span>
                ))}
              </div>
            </div>
            {action(c.results)}
          </>
        )}
        {index === 1 && (
          <>
            <p className="mb-3 text-[10px] text-muted">{c.saved}</p>
            <div className="space-y-3">
              {property()}
              {property(true)}
            </div>
            {action(c.compare)}
          </>
        )}
        {index === 2 && (
          <>
            {property()}
            {label(c.day)}
            <div className="grid grid-cols-3 gap-2">
              {c.days.map((d, i) => (
                <div
                  key={d}
                  className={`${card} text-center text-[9px] ${i === 0 ? "ring-1 ring-brand" : ""}`}
                >
                  {d}
                  <b className="mt-1 block text-lg">{24 + i}</b>
                </div>
              ))}
            </div>
            {label(c.time)}
            <div dir="ltr" className="flex gap-2">
              {["5:00 PM", "6:30 PM"].map((t) => (
                <span
                  key={t}
                  className="rounded-xl bg-chip px-3 py-2 text-[10px] text-accent"
                >
                  {t}
                </span>
              ))}
            </div>
            {action(c.confirm)}
            <p className="mt-3 text-center text-[9px] text-muted">{c.notice}</p>
          </>
        )}
        {index === 3 && (
          <>
            <div className="grid grid-cols-3 gap-2">
              {c.stats.map((t, i) => (
                <div key={t} className={`${card} text-center`}>
                  <b className="text-xl text-accent">{[3, 8, 124][i]}</b>
                  <p className="mt-1 text-[8px] text-muted">{t}</p>
                </div>
              ))}
            </div>
            {label(c.manage)}
            {property()}
            {label(c.requests)}
            <div className={card}>
              <p className="text-[11px] font-bold">{c.tenant}</p>
              <p className="mt-1 text-[9px] text-muted">{c.request}</p>
              <div className="mt-3 flex gap-2">
                <span className="rounded-lg bg-brand-deep px-5 py-2 text-[10px] text-white">
                  {c.accept}
                </span>
                <span className="rounded-lg border border-line px-5 py-2 text-[10px]">
                  {c.decline}
                </span>
              </div>
            </div>
          </>
        )}
        {index === 4 && (
          <>
            <div className={`${card} flex items-center gap-2`}>
              <User className="size-9 rounded-full bg-chip p-2 text-accent" />
              <div>
                <p className="text-[11px] font-bold">{c.owner}</p>
                <p className="text-[9px] text-muted">{c.online}</p>
              </div>
              <ShieldCheck className="ms-auto size-4 text-accent" />
            </div>
            <p className="my-5 text-center text-[9px] text-muted">{c.today}</p>
            <div className="space-y-5">
              {c.messages.map((t, i) => (
                <div
                  key={t}
                  className={`max-w-[90%] rounded-2xl p-3 text-[11px] leading-6 ${i === 1 ? "me-auto bg-paper border border-line" : "ms-auto bg-chip text-accent"}`}
                >
                  {t}
                  <p className="text-end text-[8px] opacity-60">10:0{i} ✓✓</p>
                </div>
              ))}
            </div>
            <div className={`${field} mt-auto!`}>
              {c.write}
              <Send className="size-4 text-accent rtl:-scale-x-100" />
            </div>
          </>
        )}
        {index === 5 && (
          <>
            {label(c.today)}
            <div className="space-y-3">
              {c.updates.map((t, i) => (
                <div key={t} className={`${card} flex items-start gap-2`}>
                  <span className="rounded-xl bg-chip p-2 text-accent">
                    {i === 0 ? (
                      <CalendarDays className="size-4" />
                    ) : i === 1 ? (
                      <MessageCircle className="size-4" />
                    ) : (
                      <Bell className="size-4" />
                    )}
                  </span>
                  <div>
                    <p className="text-[11px] font-semibold leading-5">{t}</p>
                    <p className="mt-1 text-[9px] leading-5 text-muted">
                      {c.details[i]}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </>
        )}
        {index === 6 && (
          <>
            {property()}
            <p className="mb-2 mt-4 text-center text-sm font-bold">
              {c.review}
            </p>
            <div className={card}>
              {c.criteria.map((t) => (
                <div key={t} className="mb-4">
                  <p className="mb-2 text-[10px]">{t}</p>
                  <div className="flex gap-2">
                    {[1, 2, 3, 4, 5].map((n) => (
                      <Star key={n} className="size-5 fill-brand text-brand" />
                    ))}
                  </div>
                </div>
              ))}
            </div>
            <div className={`${field} min-h-16 items-start!`}>{c.comment}</div>
            {action(c.submit)}
          </>
        )}
        {index === 7 && (
          <>
            <div className="rounded-2xl bg-chip p-4 text-accent">
              <MessageCircle className="mb-2 size-6" />
              <p className="text-[12px] font-bold">{c.help}</p>
              <p className="mt-2 text-[10px] leading-5">{c.helpText}</p>
            </div>
            {label(c.ticket)}
            {label(c.subject)}
            <div className={field}>{c.subjectText}</div>
            {label(c.description)}
            <div className={`${field} min-h-28 items-start!`}>
              {c.descriptionText}
            </div>
            <div className="mt-3 flex items-center gap-2 rounded-xl border border-dashed border-line p-3 text-[10px] text-muted">
              <Plus className="size-4" />
              {c.attach}
            </div>
            {action(c.send)}
          </>
        )}
      </div>
      <div className="relative grid shrink-0 grid-cols-4 border-t border-line bg-paper px-2 pb-5 pt-2">
        {c.tabs.map((t, i) => {
          const Icon = icons[i];
          return (
            <span
              key={t}
              className={`flex flex-col items-center gap-1 text-[8px] ${i === (index === 1 ? 1 : index === 4 ? 2 : 0) ? "text-accent" : "text-muted"}`}
            >
              <Icon className="size-3.5" />
              {t}
            </span>
          );
        })}
        <span className="absolute bottom-1.5 left-1/2 h-1 w-[36%] -translate-x-1/2 rounded-full bg-fg/85" />
      </div>
    </div>
  );
}
