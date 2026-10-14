import { Building2, KeyRound } from "lucide-react";
import clsx from "clsx";
import type { Dictionary } from "@/i18n/dictionaries";
import { Container } from "@/components/ui/Container";
import { SectionHeading } from "@/components/ui/SectionHeading";
import { ArchLines } from "@/components/ui/Decor";
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
        "reveal relative scroll-mt-24 overflow-hidden rounded-[2rem] p-7 sm:p-10",
        dark ? "bg-pine text-white dark:ring-1 dark:ring-white/10" : "border border-line bg-sand text-fg",
      )}
    >
      <ArchLines
        count={4}
        className={clsx("-end-16 -top-10 size-64", dark ? "text-white/8" : "text-accent/10")}
      />

      <header className="relative flex items-center gap-4">
        <span
          className={clsx(
            "grid size-12 shrink-0 place-items-center rounded-2xl",
            dark ? "bg-brand text-white" : "bg-pine text-white dark:bg-brand",
          )}
        >
          {icon}
        </span>
        <div>
          <p className={clsx("text-sm font-medium", dark ? "text-brand-soft" : "text-accent")}>{journey.label}</p>
          <h3 className="font-display text-2xl font-semibold">{journey.title}</h3>
        </div>
      </header>

      <ol className="relative mt-9">
        {journey.steps.map((step, index) => {
          const last = index === lastIndex;
          return (
            <li key={step.title} className="relative flex gap-4 pb-7 last:pb-0">
              {!last && (
                <span
                  aria-hidden
                  className={clsx(
                    "absolute start-4 top-9 bottom-1 w-px -translate-x-1/2 rtl:translate-x-1/2",
                    dark ? "bg-white/15" : "bg-line",
                  )}
                />
              )}
              <span
                className={clsx(
                  "relative grid size-8 shrink-0 place-items-center rounded-full font-display text-sm font-semibold",
                  last
                    ? "bg-brand text-white shadow-[0_0_0_5px_rgba(4,164,23,0.18)]"
                    : dark
                      ? "bg-white/10 text-brand-soft ring-1 ring-white/15"
                      : "bg-paper text-accent ring-1 ring-line",
                )}
              >
                {index + 1}
              </span>
              <div className="pt-1">
                <p className="font-semibold">{step.title}</p>
                <p className={clsx("mt-1 text-sm leading-6", dark ? "text-white/60" : "text-muted")}>{step.body}</p>
              </div>
            </li>
          );
        })}
      </ol>
    </article>
  );
}

export function HowItWorks({ dict }: { dict: Dictionary }) {
  const section = dict.howItWorks;

  return (
    <section id={SECTION_IDS.howItWorks} className="scroll-mt-16 bg-paper py-24 sm:py-32">
      <Container>
        <SectionHeading
          eyebrow={section.eyebrow}
          titleLines={[section.title]}
          subtitle={section.subtitle}
          align="center"
        />

        <div className="mt-14 grid gap-5 md:grid-cols-2 lg:gap-6">
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
