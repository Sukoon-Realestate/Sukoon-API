# Sokoun App Design System

This is the implementation reference for Sokoun's phone and tablet design
language. It is derived from the Flutter tokens, shared widgets, and the
authentication, KYC, tenant, owner, search, property, and visit flows already
in the repository.

The app is Arabic-first, calm, and utility-led. New UI should look like it
belongs to the existing product before introducing a new visual pattern.

## Source of Truth

- Colors: `packages/core/lib/config/res/color_manager.dart`
- Font families and shared constants:
  `packages/core/lib/config/res/constants_manager.dart`
- Text styles: `packages/core/lib/core/helpers/text_style_manager.dart`
- Spacing, sizing, radii, and font sizes:
  `packages/core/lib/config/res/app_sizes.dart`
- App theme: `apps/sokoun_app/lib/shared_widgets/sokoun_theme.dart`
- Responsive layout: `apps/sokoun_app/lib/shared_widgets/sokoun_layout.dart`
- Motion policy: `apps/sokoun_app/lib/shared_widgets/sokoun_motion.dart`
- Sokoun-specific widgets: `apps/sokoun_app/lib/shared_widgets/`
- Feature UI: `apps/sokoun_app/lib/features/`
- Cross-app widgets: `packages/core/lib/core/widgets/`
- Localized content: `packages/core/assets/translations/lang.json`

Use token names in code. Do not duplicate raw color values or hardcode sizes
unless a value is genuinely one-off.

`SokounTheme.light` sets Tajawal, the semantic color scheme, typography,
fields, buttons, sheets, and feedback surfaces. `AppControlTheme` opts Sokoun
into natural-height controls with a minimum 48-pixel target and 12-pixel
corners; other apps retain their existing control sizing.

## Brand Direction

Sokoun is a real-estate app with tenant and owner modes. The experience should
feel calm, trustworthy, private, and practical. Screens should favor clear
decisions, readable property information, and low-friction task flows.

The visual language is:

- Clean white cards on a warm off-white canvas.
- Deep navy text for confidence and readability.
- Teal for universal actions, active navigation, and tenant identity.
- Gold for owner identity, verification, and premium highlights.
- Pale semantic fills and soft borders instead of heavy shadows.
- Compact rounded controls with strong Arabic readability.

### Product principles

1. **Clarity before decoration.** Property facts, price, status, and the next
   action should be immediately scannable.
2. **Trust through restraint.** Use quiet surfaces and explicit privacy or
   verification cues instead of dramatic effects.
3. **Role-aware, not fragmented.** Tenant and owner experiences share one
   system. Gold adds owner identity; teal remains the product action color.
4. **Arabic-first by construction.** RTL layout, alignment, icon direction,
   copy length, and truncation must work from the start.
5. **State must be visible.** Selected, loading, disabled, empty, success,
   warning, and error states need more than a text change.

## Color System

### Core brand

| Token | Hex | Primary use |
| --- | --- | --- |
| `AppColors.sokoonTeal` / `AppColors.primary` | `#0F766E` | Primary actions, active navigation, selected controls, tenant identity |
| `AppColors.sokoonGold` | `#D6A84F` | Owner identity, verification, premium highlights |
| `AppColors.sokoonNavy` | `#111827` | Titles, body text, and important icons |
| `AppColors.scaffoldBackground` | `#FAFAF8` | Default page canvas |
| `AppColors.white` | `#FFFFFF` | Cards, fields, app bars, and sheets |
| `AppColors.splash` / `AppColors.amber` | `#F59E0B` | Splash and focused warning moments |

### Neutrals

| Token | Hex | Primary use |
| --- | --- | --- |
| `AppColors.sokoonGray` / `AppColors.gray` | `#6B7280` | Secondary text and muted icons |
| `AppColors.sokoonMuted` / `AppColors.grayLight` | `#9CA3AF` | Hints, placeholders, and disabled content |
| `AppColors.graySoft` | `#D1D5DB` | Strong neutral dividers |
| `AppColors.grayPale` | `#E5E7EB` | Light dividers and inactive borders |
| `AppColors.sokoonBorder` / `AppColors.grayMist` | `#EEF0F3` | Default component border |
| `AppColors.grayBackground` | `#F3F4F6` | Neutral chips and grouped backgrounds |
| `AppColors.grayOffWhite` | `#F9FAFB` | Subtle card interiors and empty areas |

### Semantic colors

| Meaning | Foreground | Background/support |
| --- | --- | --- |
| Destructive | `AppColors.sokoonRose` (`#E11D48`) | `AppColors.roseAlpha07` |
| Error | `AppColors.red` (`#EF4444`) | `AppColors.redPale` |
| Success | `AppColors.green` (`#16A34A`) | `AppColors.greenPale` |
| Positive badge | `AppColors.emerald` (`#22C55E`) | `AppColors.mint` |
| Warning/pending | `AppColors.amber` (`#F59E0B`) | `AppColors.amberPale` or `AppColors.orangePale` |
| Information | `AppColors.blue` (`#2563EB`) | `AppColors.bluePale` |
| Teal information | `AppColors.sokoonTeal` | `AppColors.mintLight` or `AppColors.mintPale` |

Use a pale background with a strong matching foreground. Do not use gold as a
generic warning color; use amber/orange. Do not use teal for a specifically
semantic success state; use green.

### Role-aware color

Use these helpers when a control changes with the selected user type:

- `AppColors.tealOrGoldBasedRole`
- `AppColors.tealOrGoldAlphaBasedRole`

Tenant flows lean teal. Owner flows use gold for identity, verification, and
premium moments. Primary actions and active bottom navigation remain teal
unless a role-selection flow explicitly uses the role-aware helpers.

## Typography

The primary typeface is Tajawal:

- `ConstantManager.fontFamily = packages/melos_core/Tajawal`
- Riyal-specific text can use `ConstantManager.riyalFontFamily`
- The app-wide family is set in `apps/sokoun_app/lib/app.dart`

Use `AppText` for display text when possible, with `style` from
`AppTextStyles` in `packages/core/lib/core/helpers/text_style_manager.dart`.
Use the same styles for fields, spans, and theme typography, and pass them to
shared buttons through `textStyle`. Customize colors, responsive sizes, and
line heights with `copyWith` or the core text-style extensions. Weight-only
styles preserve inherited sizes in dialogs and nested spans.

| Purpose | Size | Weight | Color |
| --- | --- | --- | --- |
| Screen title | `20.sp` to `22.sp` | `w700` | `AppColors.sokoonNavy` |
| App bar title | `16.sp` | `w600` to `w700` | `AppColors.sokoonNavy` |
| Hero/property title | `18.sp` to `20.sp` | `w700` | `AppColors.sokoonNavy` |
| Card title | `14.sp` to `16.sp` | `w600` to `w700` | `AppColors.sokoonNavy` |
| Body | `13.sp` to `15.sp` | `w500` to `w600` | `AppColors.sokoonNavy` |
| Secondary | `12.sp` to `13.sp` | `w400` to `w500` | `AppColors.sokoonGray` |
| Button | `14.sp` | `w700` | White or navy |
| Metadata | `11.sp` to `12.sp` | `w400` | `AppColors.sokoonGray` |

Use weight and color before adding more sizes. Use `w700` for headings and reserve `w800` for short
prices and metrics. Avoid making every label equally heavy. Body copy
uses a line height around `1.4` to `1.5`.

Wrap explanatory content. Use `maxLines` and `TextOverflow.ellipsis` for
dynamic content in cards, app bars, chips, navigation labels, and constrained
rows. Do not shrink content with `FittedBox` when a flexible layout or wrapping
can preserve readability and text scaling.

## Responsive Layout

The app keeps `flutter_screenutil` units for existing tokens, with viewport
scaling disabled in `app.dart`. Logical dimensions stay consistent across
phones and tablets; the system `TextScaler` still enlarges text.

- Reference size: `360 × 690`; `.w`, `.h`, `.r`, and `.sp` resolve without
  multiplying spacing or font sizes by tablet width.
- Use `LayoutBuilder` constraints to change composition.
- `SokounContentWidth.form`: max 520; `readable`: max 720; `wide`: max 1200.
- The root shell switches from bottom navigation to a 104-pixel side rail at
  600 logical pixels, retaining tab instances and selected workspace state.
- Property collections use `AppPagify` with `Ranking.adaptiveGrid`: one to
  three natural-height columns, a 320-pixel minimum card width, and 16-pixel
  gaps. Larger text increases the minimum column width.
- Bounded collections use `SokounAdaptiveGrid`; dashboard metrics use up to
  four columns. Never force text cards into a fixed aspect ratio.
- Property details use gallery/content columns at 960 available pixels when
  text scaling permits; otherwise they remain in reading order vertically.
- Tablet displays permit rotation. Phone orientation remains portrait.
- Check widths 320, 390, 600, 768, 1024, and 1366 with Arabic/English and text
  scales 1, 1.3, and 2. Test keyboard insets and state preservation on resize.

### Spacing rhythm

- `4`: tight label-to-detail spacing
- `8`: compact internal grouping
- `10` to `12`: row gaps and related component rhythm
- `16`: default card padding and compact screen padding
- `18` to `20`: standard screen padding and section gaps
- `24`: major section separation and auth horizontal padding

### Layout standards

- Auth screens use `24.w` horizontal padding through `AuthScaffold`.
- Home and dashboard screens commonly use `20.w`.
- Detail and dense task screens commonly use `16.w` to `18.w`.
- Card grids use consistent gutters, normally `10.w` to `12.w`.
- Bottom-fixed actions sit in a white safe-area surface with a top border and
  `20.w` horizontal padding through `SokounActionFooter`.
- Protect essential content from system safe areas and the keyboard.
- Avoid fixed-width text containers. Use `Expanded`, `Flexible`, `Wrap`, or a
  scrollable row where Arabic or translated content can grow.

## Radius and Shape

- Small controls and fields: `10.r` to `12.r`
- Icon wells: `12.r` to `16.r`
- Cards: `16.r` to `20.r`
- Bottom sheets: `24.r` top corners
- Pills and status badges: `999.r`
- Circular actions and avatars: equal width and height using `.r`
- Loading buttons: `ConstantManager.buttonBorderRadiusNumber`

The cross-app `DefaultButton` falls back to `AppCircular.r5`. Sokoun opts into
a 12-pixel default radius through `AppControlTheme`; flow-specific overrides
remain available. Reserve `20.r` for large selection cards and
friendly empty-state surfaces.

## Surfaces

Default composition:

- Canvas: `AppColors.scaffoldBackground`
- Primary surface: `AppColors.white`
- Grouped surface: `AppColors.grayOffWhite` or `AppColors.grayBackground`
- Borders: `AppColors.sokoonBorder` or `AppColors.grayPale`
- Shadow: rare and subtle, normally `AppColors.shadowBlack04`
- Media: clipped consistently; inset square thumbnails in compact discovery
  rows, stable aspect ratios in larger result and saved-property cards
- Photo counts and thumbnail controls appear only for actual media

Standard cards use a white fill, a 1-pixel light border, `16.r` to `20.r`
corners, and `14.w` to `16.w` internal padding. Strong fills are reserved for
selection, status, or information.

Use borders to define most cards. Add a subtle shadow only when a selectable or
floating surface needs separation; avoid combining a strong border with a
heavy shadow.

## Screen Composition

### Authentication and KYC

- Use `AuthScaffold`.
- Center the main message and keep forms full-width.
- Separate the title, supporting copy, form, and CTA with clear rhythm.
- Use the role-aware accent for auth actions after a role is known.
- Multi-step KYC flows show progress near the top and keep the primary action
  fixed at the bottom when possible.
- Privacy, verification, and document requirements use pale informational
  cards with an icon, short title, and concise explanation.

### Tenant discovery

- Compose screens from a greeting/header, prominent search entry point,
  contextual banner, section header, and property cards.
- Property cards prioritize image, title, location, metrics, tags, rating, and
  price in that order.
- Price is high-emphasis teal; supporting metadata remains gray.
- Results, filters, and details should preserve search context.

### Owner operations

- Use gold in the owner avatar, verification badges, and identity moments.
- Keep operational actions teal and state feedback semantic.
- Dashboard cards prioritize counts and pending work.
- Request and listing cards place status near the title and group accept,
  reject, edit, or view actions consistently.

### Detail and task flows

- Use a clear top bar or media hero, followed by grouped information sections.
- Keep one obvious primary task, such as booking a visit or continuing a form.
- Long flows use segmented progress, scrollable content, and a fixed CTA
  footer.
- Full-screen media viewers may use `AppColors.slate` with high-contrast
  controls.

## Buttons and Actions

### Primary

- Teal or role-aware background
- White text
- Minimum 48 logical pixels; grow vertically with larger or wrapped labels
- `8.r` to `12.r` corners
- Full width for final auth and multi-step actions

### Secondary

- White background
- `AppColors.sokoonBorder` border
- Navy text
- Used for alternate, back, cancel, and social sign-in actions

### Destructive

- Rose foreground and border or a pale red/rose background
- Usually secondary to the safe action
- A solid red fill is reserved for critical confirmation

### Disabled and loading

- Disabled fill: `AppColors.grayPale` or a comparable light gray
- Disabled content: `AppColors.sokoonMuted`
- Loading preserves the button footprint and prevents duplicate submission

Use `DefaultButton` for standard synchronous actions and `AppLoadingButton` for
async submissions. Icon-only actions need a semantic label and a touch target
of at least 48 logical pixels even when the glyph is smaller.

## Forms

Sokoun fields use:

- White fill
- `12.r` corners
- `16.w` horizontal and `14.h` vertical content padding
- Tajawal input text at `15.sp`, `w600`, in navy
- Short field labels above the control
- Default border: `AppColors.sokoonBorder`
- Focused or filled border: teal or the current role accent
- Error border: rose/red

Use the Sokoun field wrappers from `apps/sokoun_app/lib/shared_widgets/`
before styling `DefaultTextField` directly. Preserve keyboard type, autofill
hints, input actions, formatters, and password visibility controls. Error text
must explain how to fix the value and must not rely on border color alone.

## Chips, Badges, and Status

Use a soft fill with a strong foreground:

- Selected: `AppColors.tealAlpha07` fill,
  `AppColors.tealAlpha19` border, teal content
- Warning: amber/orange pale fill with amber or brown content
- Success: `AppColors.greenPale` fill with green content
- Error: `AppColors.redPale` fill with red or rose content
- Neutral: `AppColors.grayBackground` fill with gray content

Pill badges generally use `9.w` horizontal and `5.h` vertical padding with
`12.sp` high-emphasis text. Keep badges compact and visually below primary
actions.

## Icons and Media

Use the rounded Material icon language already established in the app:

- `14.r` to `16.r`: metadata
- `18.r` to `20.r`: buttons and row actions
- `22.r`: bottom navigation
- `24.r` to `28.r`: headers and empty states

Icon wells pair a pale background with a strong foreground:

- Teal: `AppColors.mintLight` + `AppColors.sokoonTeal`
- Gold: `AppColors.goldPale` + `AppColors.sokoonGold`
- Warning: `AppColors.orangePale` + `AppColors.amber`
- Error: `AppColors.redPale` + `AppColors.sokoonRose`

Mirror directional arrows for RTL where appropriate. Do not mirror universal
symbols such as search, favorite, camera, or close. Property media should keep
a stable aspect ratio, use clipped rounded corners, and include a deliberate
loading/error placeholder.

## Navigation and App Bars

Use `AppScaffold` for ordinary screens, including custom-header screens with
`showBackButton: false`. `AuthScaffold` composes it with the form width cap.
Full-screen media and the root navigation shell keep specialized scaffolds. App bars are flat, have no
elevation or surface tint, share the canvas color, and use a centered navy
`16.sp` title. Use `SokoonBackButton` for the standard back action.

Home navigation uses:

- White surface with a top `AppColors.sokoonBorder` divider
- Minimum 76 logical pixels plus the device safe area; labels can grow
- Five evenly distributed items
- `22.r` icons and `11.sp` labels
- Teal active pill and legible gray inactive state
- A scrollable side rail on tablets and split views at least 600 pixels wide
- Stable item order within each role

Use the shared `Go` navigation helper instead of calling `Navigator` directly.

## Bottom Sheets and Overlays

- Use a transparent route background and a white surface with `24.r` top
  corners.
- Add a centered `42.w × 4.h` gray drag handle for draggable/action sheets.
- Use `20.w` side padding and protect the bottom safe area.
- Put the title first, followed by clear full-width action rows.
- Destructive actions use rose/red; dismiss actions remain secondary.
- Keyboard-driven sheets must remain scrollable and keep controls visible.

## Motion and Feedback

- Selection cards: approximately `180ms`
- Other selection, expansion, and state feedback: `150ms` to `250ms`
- Use `SokounReveal` for a one-time `320ms` fade and short slide on coherent
  content sections; stagger neighboring sections by at most `160ms` total.
  Do not replay entrances when a field changes or animate every scrolling row.
- Long property descriptions and changing history sections expand/collapse in
  `260ms`; active filters and inline validation resize in `240ms`.
- Async actions: use the shared loading button behavior
- Use motion to explain a state change, not as decoration
- Use `SokounMotion.duration(context)` for app-owned transitions; duration is
  zero for reduced motion or accessible navigation
- Disable inactive tab tickers through `TickerMode`

Reuse the state widgets and Lottie assets under
`packages/core/assets/lottie/` for loading, empty, error, no-connection, and
success feedback.

## Content, Localization, and RTL

- Use `LocaleKeys.*` for user-facing production text.
- Do not hardcode production strings in widgets.
- Keep Arabic copy concise and layout-aware.
- Prefer `TextAlign.start`, `AlignmentDirectional`, and
  `EdgeInsetsDirectional` over fixed left/right assumptions.
- Use an explicit `TextAlign.right` only for a deliberately Arabic-only
  composition.
- Let the active locale provide directionality. Add `Directionality` only for
  isolated previews or deliberate mixed-direction content.
- Keep numbers, prices, phone numbers, dates, and units readable in RTL text.
- Do not put essential meaning in emoji or iconography alone.

## Accessibility

- Target at least 48 logical pixels for touch interactions.
- Keep normal text contrast at or above 4.5:1 and large text at or above 3:1.
- Pair status color with a label, icon, border, or shape.
- Add `Semantics` labels to icon-only buttons, media actions, progress
  indicators, and non-text status marks.
- Preserve logical focus order and visible keyboard focus.
- Support text scaling without clipping primary content or actions.
- Give meaningful images a description and exclude decorative images from
  semantics.
- Announce loading feedback and avoid layout jumps.

## Component Rules

- Check `apps/sokoun_app/lib/shared_widgets/` and
  `packages/core/lib/core/widgets/` before creating a control.
- Put reusable components in their own files.
- Keep screen files thin and compose them from named section widgets.
- Parent widgets own selected values; selector children receive callbacks.
- Prefer `StatelessWidget`; use `StatefulWidget` for controllers, focus nodes,
  animation controllers, lifecycle work, or local mutable state.

Preferred reuse order:

1. Existing Sokoun-specific component
2. Existing core component configured with Sokoun tokens
3. New feature-local component
4. New shared component after a pattern repeats across features

## UI Review Checklist

- Uses `AppColors` rather than duplicated hex values.
- Uses ScreenUtil units and shared size tokens.
- Uses `AppTextStyles` for text, fields, spans, buttons, and theme typography.
- Uses `LocaleKeys` for production copy.
- Handles long and scaled text with wrapping or ellipsis.
- Works in RTL without accidental fixed left/right assumptions.
- Handles the keyboard, system safe areas, and fluid widths.
- Gives icon-only actions semantic labels and usable touch targets.
- Uses white bordered cards unless status or selection needs color.
- Uses teal for actions/navigation and gold for owner identity moments.
- Uses semantic green, amber, blue, and red/rose consistently.
- Includes loading, disabled, empty, error, and success states as applicable.
- Reuses shared buttons, fields, scaffolds, and auth components where possible.
