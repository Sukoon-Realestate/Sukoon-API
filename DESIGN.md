---
name: Sukoon Admin
description: Arabic administration workspace using the Sukoon landing identity.
colors:
  background: "#f6f2e9"
  foreground: "#173923"
  text-muted: "#566151"
  text-subtle: "#67715f"
  card-bg: "#fcfbf7"
  card-border: "#e3dccb"
  sidebar-bg: "#f0ede3"
  primary: "#0a5c18"
  primary-hover: "#084b14"
  primary-subtle: "#e1f0e2"
  chart-bar: "#c3d5bc"
  chart-active: "#1d4a2c"
typography:
  headline:
    fontFamily: "Readex Pro, IBM Plex Sans Arabic, sans-serif"
    fontSize: "1.625rem"
    fontWeight: 500
    lineHeight: 1.55
  body:
    fontFamily: "IBM Plex Sans Arabic, sans-serif"
    fontSize: "0.875rem"
  label:
    fontFamily: "IBM Plex Sans Arabic, sans-serif"
    fontSize: "0.75rem"
    fontWeight: 500
rounded:
  control: "0.5rem"
  metric: "0.75rem"
  panel: "0.875rem"
  dialog: "1rem"
spacing:
  compact: "0.5rem"
  group: "1rem"
  panel: "1.5rem"
  page: "2rem"
components:
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "#ffffff"
    rounded: "{rounded.control}"
    padding: "0.55rem 0.85rem"
  button-secondary:
    backgroundColor: "{colors.card-bg}"
    textColor: "{colors.foreground}"
    rounded: "{rounded.control}"
  panel:
    backgroundColor: "{colors.card-bg}"
    rounded: "{rounded.panel}"
---

# Design System: Sukoon Admin

## Overview

This system applies to the Arabic admin workspace in `frontend/landing/src/app/(admin)` and its shared admin components. Public landing and mobile interfaces retain their own authority. The user confirmed a balanced overview of operations and business performance, retaining the landing page's cream and forest-green identity.

**Key Characteristics:**

- RTL reading and right-side workflow navigation.
- Warm canvas, cream panels, forest selection, restrained sage data graphics.
- Compact controls, clear data hierarchy, accessible mobile and keyboard interactions.

## Colors

Use the frontmatter's source values through the CSS semantic properties in `admin.css`. Forest marks selected navigation; primary green marks actions. Cream separates panels from the warm canvas. Status colors carry status, while role tags use neutral surfaces.

Dark mode is a semantic translation, not an inversion: canvas `#0b140f`, panel `#111e16`, foreground `#eaf0e4`, border `#293c2d`, action `#2c7039`, accent text `#a8d99d`. The complete implemented dark-role map is recorded in the sidecar.

## Typography

IBM Plex Sans Arabic carries controls, tables, and body text. Readex Pro is reserved for page headings. Desktop headings are 1.625rem/500; mobile headings are 1.375rem. Typical labels are 0.75rem; table headers are 0.6875rem. Use tabular numerals for comparable metrics. Arabic letter spacing stays zero.

## Layout

The desktop sidebar is 16.25rem wide, expanding to 17.5rem at 1600px. The utility bar is 4.5rem high. Content is bounded at 88rem with 2rem inline padding, reducing to 1.5rem below 1280px and 1rem below 768px. The sidebar becomes a native modal drawer below 1024px. Overview panels stack below 768px.

Six workflow groups organize overview, properties, users/verification, safety/support, finance/communication, and platform management. Long tables scroll in their own focusable, labeled regions; mobile shows a scrolling instruction.

## Elevation & Depth

Panels use a single border and no shadow. Tonal surfaces establish hierarchy. Overlays use `0 20px 65px -20px #0c2a1840`; native dialog backdrops use `#07160db3`.

## Shapes

Controls use 0.5rem corners, metrics 0.75rem, panels 0.875rem, and dialogs 1rem. Small tags may use tighter radii; avatars remain circular. Table borders and dividers follow semantic border roles.

## Components

Buttons use consistent padding and visible focus outlines. Primary actions use green with white text; secondary actions use cream and a neutral border. Disabled buttons reduce opacity and reject interaction.

Inputs use the input surface and border roles. Focus uses the accent role with a 2px outline and 3px offset. Page headers separate the section title from the utility bar.

Navigation has one active destination, determined by the most specific matching route. Groups expand to reveal related work. Ctrl/Cmd+K opens section search; arrows reveal the selected result and Enter navigates. Dialogs use native focus management and Escape behavior.

Metrics, queues, charts, and activity distinguish loading, unavailable, and empty states. Unavailable source counts must not become zeros or complete-looking totals. Demonstration mode is labeled.

## Do's and Don'ts

- Do use semantic CSS properties for theme-aware surfaces and text.
- Do preserve RTL layouts, correct `/admin` destinations, and visible keyboard focus.
- Do keep each table's overflow inside its labeled scrolling region.
- Do retain truthful loading and failure states alongside real API values.
- Don't add a decorative welcome banner ahead of actionable overview content.
- Don't inherit product-wide rules from legacy screen-specific styling.
- Don't treat demonstration data as live platform activity.

Source authority: `frontend/landing/src/app/(admin)/admin.css`; `components/layout/{Sidebar,Header,CommandMenu}.tsx`; `components/ui/{TableScroll,MetricCard,ConfirmModal}.tsx`; `lib/admin-navigation.ts`. The direction and review scope are recorded in `frontend/landing/docs/admin-design.md`.
