"use client";

import Link from "next/link";
import { useParams } from "next/navigation";

export default function PublicPageError({ retry }: { error: Error & { digest?: string }; retry: () => void }) {
  const { lang } = useParams<{ lang: string }>();
  const arabic = lang === "ar";
  const locale = arabic ? "ar" : "en";
  return <main className="mx-auto max-w-3xl space-y-5 px-5 py-12 text-fg sm:px-8">
    <h1 className="text-3xl font-bold leading-snug">{arabic ? "تعذر تحميل الصفحة" : "This page could not be loaded"}</h1>
    <p className="leading-8 text-muted">{arabic ? "تعذر الوصول إلى المحتوى المنشور الآن. أعد المحاولة أو تواصل معنا للمساعدة." : "The published content is unavailable right now. Please try again or contact us for help."}</p>
    <div className="flex flex-wrap gap-4">
      <button type="button" onClick={() => retry()} className="min-h-11 rounded-xl bg-fg px-5 py-3 font-semibold text-sand focus-visible:outline-2 focus-visible:outline-offset-4">{arabic ? "إعادة المحاولة" : "Try again"}</button>
      <Link href={`/${locale}/support`} className="inline-flex min-h-11 items-center text-accent underline underline-offset-4">{arabic ? "التواصل مع الدعم" : "Contact support"}</Link>
      <Link href={`/${locale}/delete-account`} className="inline-flex min-h-11 items-center text-accent underline underline-offset-4">{arabic ? "طلب حذف الحساب" : "Request account deletion"}</Link>
    </div>
  </main>;
}
