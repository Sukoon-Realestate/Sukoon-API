import type { Locale } from "@/i18n/config";
import { Container } from "@/components/ui/Container";
import { SECTION_IDS } from "@/lib/sections";

export function TestSubscription({ lang }: { lang: Locale }) {
  const ar = lang === "ar";
  const apiUrl = (process.env.NEXT_PUBLIC_API_URL || "https://api.sukoon.rent").replace(/\/$/, "");
  const inputClass = "mt-2 min-h-12 w-full rounded-xl border border-line bg-sand px-4 text-fg outline-none focus:border-accent focus:ring-2 focus:ring-accent/20";

  return (
    <section id={SECTION_IDS.testSubscription} className="scroll-mt-24 bg-sand py-16 sm:py-24" aria-labelledby="test-subscription-title">
      <Container>
        <div className="mx-auto grid max-w-4xl gap-10 rounded-[2rem] border border-line bg-paper p-6 sm:p-10 md:grid-cols-2">
          <div>
            <span className="inline-flex rounded-full bg-chip px-3 py-1 text-xs font-semibold text-accent">
              {ar ? "للتجربة فقط" : "Test mode only"}
            </span>
            <h2 id="test-subscription-title" className="mt-5 font-display text-3xl font-semibold tracking-tight text-fg sm:text-4xl">
              {ar ? "اشتراك تجريبي" : "Test subscription"}
            </h2>
            <p className="mt-4 text-muted leading-7">
              {ar ? "جرّب خطوة الدفع مع سكون. لن يتم خصم أي أموال حقيقية." : "Try the payment experience with Sukoon. No real money will be charged."}
            </p>
            <p className="mt-8 text-fg">
              <span className="font-display text-5xl font-semibold">{ar ? "١٠" : "10"}</span>
              <span className="ms-2 text-lg">{ar ? "جنيه مصري" : "EGP"}</span>
            </p>
            <p className="mt-3 text-sm leading-7 text-muted">
              {ar ? "دفعة تجريبية واحدة، بدون تجديد تلقائي أو تفعيل مزايا على حسابك. استخدم بيانات كارت اختبار فقط." : "One test payment, with no automatic renewal or account benefits. Use test card details only."}
            </p>
          </div>
          <form action={`${apiUrl}/api/v1/payments/paymob/test-checkout/`} method="post" className="space-y-4">
            <input type="hidden" name="language" value={lang} />
            <div className="grid grid-cols-2 gap-3">
              <label className="block text-sm font-medium text-fg">
                {ar ? "الاسم الأول" : "First name"}
                <input className={inputClass} name="first_name" autoComplete="given-name" required maxLength={100} />
              </label>
              <label className="block text-sm font-medium text-fg">
                {ar ? "اسم العائلة" : "Last name"}
                <input className={inputClass} name="last_name" autoComplete="family-name" required maxLength={100} />
              </label>
            </div>
            <label className="block text-sm font-medium text-fg">
              {ar ? "البريد الإلكتروني" : "Email"}
              <input className={inputClass} name="email" type="email" autoComplete="email" dir="ltr" required maxLength={254} />
            </label>
            <label className="block text-sm font-medium text-fg">
              {ar ? "رقم الموبايل" : "Mobile number"}
              <input className={inputClass} name="phone_number" type="tel" autoComplete="tel" dir="ltr" placeholder="+201012345678" pattern="\+?20[0-9]{10}" maxLength={14} required aria-describedby="test-phone-help" />
              <span id="test-phone-help" className="mt-1 block text-xs text-muted">{ar ? "رقم مصري بكود الدولة +20" : "Egyptian number with country code +20"}</span>
            </label>
            <button type="submit" className="min-h-12 w-full rounded-full bg-pine px-5 py-3 font-semibold text-white transition-colors hover:bg-moss focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-accent dark:bg-brand dark:hover:bg-brand-hover">
              {ar ? "تجربة الدفع بـ١٠ جنيه" : "Try checkout · EGP 10"}
            </button>
            <p className="text-center text-xs leading-6 text-muted">{ar ? "ستنتقل إلى صفحة الدفع الآمنة من Paymob." : "Continue to Paymob’s secure payment page."}</p>
          </form>
        </div>
      </Container>
    </section>
  );
}
