import { getDictionary } from "@/i18n/dictionaries";
import { SITE_NAME, SITE_NAME_AR, absoluteUrl } from "@/lib/site";

export const dynamic = "force-static";

// https://llmstxt.org — a plain-Markdown summary of the site for LLMs,
// built from the same dictionaries as the page so the two never drift.
export function GET() {
  const en = getDictionary("en");
  const { tenant, owner } = en.howItWorks;
  const steps = (items: { title: string; body: string }[]) =>
    items.map((step, index) => `${index + 1}. ${step.title}: ${step.body}`).join("\n");

  const body = `# ${SITE_NAME} (${SITE_NAME_AR})

> ${en.meta.description}

${en.why.subtitle} ${en.hero.badge}.

## Pages

- [${SITE_NAME} in English](${absoluteUrl("/en")}): ${en.meta.title}
- [${SITE_NAME} in Arabic](${absoluteUrl("/ar")}): ${getDictionary("ar").meta.title}

## How it works

### ${tenant.label}

${steps(tenant.steps)}

### ${owner.label}

${steps(owner.steps)}

## ${en.features.eyebrow}

${en.features.items.map((item) => `### ${item.title}\n\n${item.body}\n\n${item.points.map((point) => `- ${point}`).join("\n")}`).join("\n\n")}

## FAQ

${en.faq.items.map((item) => `### ${item.question}\n\n${item.answer}`).join("\n\n")}
`;

  return new Response(body, {
    headers: { "Content-Type": "text/plain; charset=utf-8" },
  });
}
