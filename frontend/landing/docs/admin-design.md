# Admin redesign direction

Confirmed brief: balanced business and operational overview; cream and forest green from the landing page; regroup all existing admin categories.

Mode: Operate. Code-first. Existing Arabic RTL product and API behavior remain authoritative.

Palette: paper #fcfbf7, canvas #f6f2e9, forest #0c2a18, green #0a5c18, sage #e1f0e2, line #e3dccb. Dark mode translates these roles to green-black surfaces and lighter sage text.

Typography: IBM Plex Sans Arabic for controls and data; Readex Pro reserved for page headings. Fixed rem sizes, no heavy all-bold interface, tabular numbers, no Arabic tracking.

Layout: quiet navigation rail with six workflow groups; compact utility bar; right-aligned title and supporting text; bounded content column. Home combines a metric strip, wide growth chart, operational queue, user composition, and recent activity. Tables remain tables on desktop and retain existing mobile presentations.

Alternatives considered: business-report-first; review-inbox-first; split overview; full-width activity feed; balanced workbench; role-specific home; compact index. The balanced workbench is used to honor the user's confirmed priorities. The skills' optional concept selection has been resolved by that explicit brief instead of adding a second approval step.

First viewport: the administrator can see the core performance metrics and find property review, identity verification, and support without scrolling through a decorative welcome panel. The signature interaction is a grouped, searchable navigation system with keyboard section search (Ctrl/Cmd+K), route-aware active states, and a responsive drawer.

State rules: real API values; explicit demonstration-mode label; unavailable counts shown as a dash; loading skeletons and recoverable errors; no fabricated online indicator or action-success toast. Quiet hover and focus feedback only.

Scope: every page under /admin via shared shell, page containers, panels, controls, tables, badges, pagination, overlays, login, and a rebuilt overview. Public landing content and legacy standalone admin code are not the target of this pass.

## Direction contract

THESIS: Sukoon administration balances the work awaiting staff with the health of the business. It replaces the decorative welcome banner with directly actionable information.

OWN-WORLD: warm paper canvas, cream panels, deep forest selected navigation, restrained sage data graphics. Plex Arabic controls and data; Readex page headings. Quiet 8px controls and 12–16px panels.

STORY: understand performance, inspect pending work, move into property/user/support tasks, and review business detail without losing section context.

FIRST VIEWPORT: right-side grouped navigation; compact top utility bar; page title; four performance summaries; broad user-growth chart beside a three-row review queue. Mobile stacks the panels and exposes a modal navigation drawer.

FORM: balanced workbench, candidate five. Explicit user choice resolves the composition: balanced overview and retention of the landing identity. Seed reference was unavailable in the recorded output.

FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance
