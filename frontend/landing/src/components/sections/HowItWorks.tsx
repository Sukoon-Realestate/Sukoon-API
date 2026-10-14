import { Building2, KeyRound } from "lucide-react";
import clsx from "clsx";
import type { Dictionary } from "@/i18n/dictionaries";
import { Container } from "@/components/ui/Container";
import { SectionHeading } from "@/components/ui/SectionHeading";
import { ContourLines } from "@/components/ui/Decor";
import { SECTION_IDS } from "@/lib/sections";

type Journey = Dictionary["howItWorks"]["tenant"];

function JourneyCard({
  id,
  journey,
  icon,
  tone,
}: {
  id: string;
  journey: Journey;
  icon: React.ReactNode;
  tone: "light" | "dark";
}) {
  const dark = tone === "dark";
  const lastIndex = journey.steps.length - 1;

  return (
    <article
      id={id}
      className={clsx(
        "scroll-mt-8 rounded-3xl p-6 sm:p-8",
        dark ? "bg-forest text-white" : "border border-black/8 bg-white text-heading",
      )}
    >
      <header className="flex items-center gap-3.5">
        <span
          className={clsx(
            "grid size-11 shrink-0 place-items-center rounded-xl",
            dark ? "bg-brand text-heading" : "bg-mint-strong text-brand-deep",
          )}
        >
          {icon}
        </span>
        <div>
          <p className={clsx("text-xs", dark ? "text-white/60" : "text-body")}>{journey.label}</p>
          <h3 className="text-xl font-bold">{journey.title}</h3>
        </div>
      </header>

      <ol className="mt-7 space-y-5">
        {journey.steps.map((step, index) => (
          <li key={step.title} className="flex gap-3.5">
            <span
              className={clsx(
                "grid size-7 shrink-0 place-items-center rounded-full text-xs font-bold",
                index === lastIndex
                  ? "bg-brand text-heading"
                  : dark
                    ? "bg-white/8 text-brand-soft"
                    : "bg-mint-strong text-brand-deep",
              )}
            >
              {index + 1}
            </span>
            <div>
              <p className="font-semibold">{step.title}</p>
              <p className={clsx("mt-0.5 text-sm leading-6", dark ? "text-white/60" : "text-body")}>{step.body}</p>
            </div>
          </li>
        ))}
      </ol>
    </article>
  );
}

export function HowItWorks({ dict }: { dict: Dictionary }) {
  const section = dict.howItWorks;

  return (
    <section id={SECTION_IDS.howItWorks} className="relative overflow-hidden bg-mint py-20 sm:py-24">
      <ContourLines className="inset-x-0 bottom-0 h-48 w-full" />

      <Container className="relative">
        <SectionHeading eyebrow={section.eyebrow} titleLines={[section.title]} subtitle={section.subtitle} />

        <div className="mt-12 grid gap-5 md:grid-cols-2">
          <JourneyCard
            id="tenants"
            journey={section.tenant}
            tone="light"
            icon={<KeyRound className="size-5" aria-hidden />}
          />
          <JourneyCard
            id="owners"
            journey={section.owner}
            tone="dark"
            icon={<Building2 className="size-5" aria-hidden />}
          />
        </div>
      </Container>
    </section>
  );
}
