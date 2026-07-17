# Sokoun Design System

This document captures the current visual direction of the Sokoun app based on
the Flutter theme, shared tokens, and existing screens.

## Source Of Truth

- Colors: `packages/core/lib/config/res/color_manager.dart`
- Typography and constants: `packages/core/lib/config/res/constants_manager.dart`
- Spacing, sizing, radius, font sizes: `packages/core/lib/config/res/app_sizes.dart`
- App theme bootstrap: `lib/app.dart`
- Shared app widgets: `lib/shared_widgets/`
- Shared core widgets: `packages/core/lib/core/widgets/`

Use the token names in code. Do not duplicate raw color values or hardcoded
sizes in feature widgets unless the value is genuinely one-off.

## Brand Direction

Sokoun is a real-estate app with two main modes: tenant and owner. The UI should
feel calm, trustworthy, private, and practical. Screens should prioritize clear
decision making, readable property information, and low-friction form flows.

The current visual language is:

- Clean white cards on a warm off-white scaffold.
- Deep navy text for confidence and readability.
- Teal as the primary action and tenant accent.
- Gold as the owner/role accent and premium highlight.
- Soft borders and pale color fills instead of heavy shadows.
- Compact, rounded controls with strong Arabic readability.

## Color Tokens

### Core Brand

| Token | Hex | Use |
| --- | --- | --- |
| `AppColors.sokoonTeal` / `AppColors.primary` | `#0F766E` | Primary actions, selected controls, tenant accent, active icons |
| `AppColors.sokoonGold` | `#D6A84F` | Owner accent, premium highlights, secondary brand moments |
| `AppColors.sokoonNavy` | `#111827` | Main text, titles, important icons |
| `AppColors.scaffoldBackground` | `#FAFAF8` | Default page background |
| `AppColors.white` | `#FFFFFF` | Cards, fields, app bars, sheets |

### Neutrals

| Token | Hex | Use |
| --- | --- | --- |
| `AppColors.sokoonGray` / `AppColors.gray` | `#6B7280` | Secondary text, loading button background, muted icons |
| `AppColors.sokoonMuted` / `AppColors.grayLight` | `#9CA3AF` | Hints, placeholders, disabled secondary text |
| `AppColors.graySoft` | `#D1D5DB` | Stronger neutral dividers |
| `AppColors.grayPale` | `#E5E7EB` | Light dividers and inactive borders |
| `AppColors.sokoonBorder` / `AppColors.grayMist` | `#EEF0F3` | Default component borders |
| `AppColors.grayBackground` | `#F3F4F6` | Neutral chips and subtle grouped backgrounds |
| `AppColors.grayOffWhite` | `#F9FAFB` | Light card interiors and empty areas |

### Semantic And Support

| Token | Hex | Use |
| --- | --- | --- |
| `AppColors.sokoonRose` / `AppColors.rose` | `#E11D48` | Errors, destructive actions, validation states |
| `AppColors.red` | `#EF4444` | Error foregrounds and critical badges |
| `AppColors.redPale` | `#FFF1F1` | Error backgrounds |
| `AppColors.green` | `#16A34A` | Success states and confirmations |
| `AppColors.emerald` | `#22C55E` | Positive status badges |
| `AppColors.greenPale` | `#EAFBF1` | Success backgrounds |
| `AppColors.mintLight` | `#E0F2F1` | Teal icon wells and soft positive surfaces |
| `AppColors.mintPale` | `#E8F4F0` | Informational teal surfaces |
| `AppColors.amber` | `#F59E0B` | Ratings, warnings, pending statuses |
| `AppColors.amberPale` | `#FFFBEB` | Warning backgrounds |
| `AppColors.blue` | `#2563EB` | Informational status accents |
| `AppColors.bluePale` | `#EEF5FF` | Informational status backgrounds |

### Role-Aware Color

Use these helpers for UI that changes by selected user type:

- `AppColors.tealOrGoldBasedRole`
- `AppColors.tealOrGoldAlphaBasedRole`

Tenant-facing flows should lean teal. Owner-facing flows may use gold for
selection, premium, and property management moments, while retaining navy text
and the off-white page background.

## Typography

The app uses Tajawal:

- `ConstantManager.fontFamily = packages/melos_core/Tajawal`
- Riyal-specific text can use `ConstantManager.riyalFontFamily`
- The global `ThemeData` sets the font family in `lib/app.dart`

Use `AppText` for display text when possible.

| Purpose | Size | Weight | Color |
| --- | --- | --- | --- |
| Screen title | `20.sp` to `22.sp` | `FontWeight.w900` | `AppColors.sokoonNavy` |
| App bar title | `16.sp` | `FontWeight.w800` | `AppColors.sokoonNavy` |
| Card title | `14.sp` to `18.sp` | `FontWeight.w800` / `w900` | `AppColors.sokoonNavy` |
| Body text | `13.sp` to `15.sp` | `FontWeight.w500` / `w600` | `AppColors.sokoonNavy` |
| Secondary text | `12.sp` to `13.sp` | `FontWeight.w400` / `w500` | `AppColors.sokoonGray` |
| Button text | `14.sp` | `FontWeight.w700` / `bold` | `AppColors.white` or `sokoonNavy` |
| Metadata | `11.sp` to `12.sp` | `FontWeight.w400` | `AppColors.sokoonGray` |

Keep text compact and readable. Use `maxLines` and `TextOverflow.ellipsis` in
cards, buttons, app bars, chips, and rows that can receive dynamic content.

## Sizing And Layout

The app is built with `flutter_screenutil`.

- Design size: `360 x 690`
- Use `.w`, `.h`, `.r`, and `.sp`
- Prefer shared constants from `AppSize`, `AppPadding`, `AppMargin`,
  `FontSize`, and `AppCircular`
- Avoid raw pixel values in app UI

Common spacing:

- `4.h`: tight label/detail spacing
- `8.h`: compact vertical grouping
- `10.w` / `10.h`: row and section rhythm
- `12.h`: header-to-copy spacing
- `16.w` / `16.h`: default card and screen content padding
- `20.w` to `24.w`: large screen section padding

## Radius And Shape

Use rounded but practical shapes:

- Small controls: `10.r` to `12.r`
- Text fields: `12.r`
- Icon wells: `12.r` to `16.r`
- Cards: `16.r` to `20.r`
- Circular buttons and avatars: equal width/height with `.r`
- Primary app loading buttons: `ConstantManager.buttonBorderRadiusNumber`

Do not over-round dense operational controls. Use larger radii only for cards,
profile elements, and friendly auth/empty-state surfaces.

## Surfaces

Default screen composition:

- `Scaffold.backgroundColor`: `AppColors.scaffoldBackground`
- App bars are flat, same color as the screen, no elevation
- Primary content appears in `AppColors.white` cards
- Borders use `AppColors.sokoonBorder` or `AppColors.grayPale`
- Shadows should be rare and subtle, usually `AppColors.shadowBlack04`

Cards should be readable and structured:

- White fill
- 1px light border
- `16.r` to `20.r` radius
- Padding around `16.w`
- Only use stronger color fills for selected, status, or informational blocks

## Buttons

### Primary Button

- Background: `AppColors.sokoonTeal` or `AppColors.tealOrGoldBasedRole`
- Text: `AppColors.white`
- Height: usually `45.h` to `48.h`
- Radius: `10.r` to `12.r`
- Loading state: `AppColors.gray`

### Secondary Button

- Background: `AppColors.white`
- Border: `AppColors.sokoonBorder`
- Text: `AppColors.sokoonNavy`
- Use for social sign-in, cancel, back, and alternate actions

### Destructive Button

- Foreground: `AppColors.sokoonRose`
- Border or pale background: `AppColors.sokoonRose`, `AppColors.roseAlpha07`,
  or `AppColors.redPale`
- Avoid using full red backgrounds unless the action is critical

### Disabled State

- Background: `AppColors.grayPale` or `Colors.grey[300]`
- Text/icon: `AppColors.sokoonMuted`
- Keep disabled controls visually present but clearly inactive

## Forms

Current Sokoun fields use:

- White fill
- `12.r` radius
- `16.w` horizontal and `14.h` vertical padding
- Navy input text
- Border changes by state:
  - Empty/default: `AppColors.sokoonBorder`
  - Focused or filled: role/accent color, usually `AppColors.sokoonTeal`
  - Error: `AppColors.sokoonRose`

Field text should use Tajawal, `15.sp`, and `FontWeight.w600`.

## Chips, Badges, And Status

Use soft fill plus colored foreground:

- Selected teal chip: `AppColors.tealAlpha07` fill,
  `AppColors.tealAlpha19` border, `AppColors.sokoonTeal` text/icon
- Warning chip: `AppColors.amberPale` or `AppColors.orangePale` fill,
  `AppColors.amber` or `AppColors.brown` foreground
- Success chip: `AppColors.greenPale` fill, `AppColors.green` foreground
- Error chip: `AppColors.redPale` fill, `AppColors.red` or
  `AppColors.sokoonRose` foreground
- Neutral chip: `AppColors.grayBackground` fill, `AppColors.sokoonGray`
  foreground

Badges should stay compact and not compete with primary actions.

## Icons

Use Material icons already present in the app. Icon sizing should generally be:

- `14.r` to `16.r`: metadata icons
- `18.r` to `20.r`: buttons and row actions
- `24.r` to `28.r`: header marks and empty-state icons

Icon wells should use a pale background and a strong foreground:

- Teal icon well: `AppColors.mintLight` + `AppColors.sokoonTeal`
- Gold icon well: `AppColors.goldPale` + `AppColors.sokoonGold`
- Warning icon well: `AppColors.orangePale` + `AppColors.amber`
- Error icon well: `AppColors.redPale` + `AppColors.sokoonRose`

## Navigation And App Bars

Use `AppScaffold` for standard screens.

App bars should be:

- Flat, no elevation
- Center-titled when a title exists
- `AppColors.sokoonNavy` title at `16.sp`, `FontWeight.w800`
- Same background as the scaffold
- Back button from `SokoonBackButton`

Do not use `Navigator` directly. Use the shared `Go` navigation helper.

## Motion

Motion should be subtle and functional:

- Selection cards: about `180ms`
- Loading buttons: use the shared loading button animation
- Avoid decorative animation in form and dashboard flows
- Use animation to clarify state changes, not to add visual noise

## Content And Localization

- Use `LocaleKeys.*` for user-facing text.
- Do not hardcode production strings in widgets.
- Keep Arabic text concise and layout-aware.
- Use `TextAlign.right` or directional alignment where content is explicitly
  Arabic.
- Prefer `AlignmentDirectional` and padding helpers for RTL-safe layouts.

## Component Rules

- Prefer shared widgets from `packages/core/lib/core/widgets` and
  `lib/shared_widgets` before creating new controls.
- Put reusable components in their own files.
- Keep screen files thin and compose them from named section widgets.
- Parent widgets own selected values; picker/selector children receive callbacks.
- Use `StatelessWidget` unless local mutable UI state is needed.
- Use `StatefulWidget` for controllers, focus nodes, animation controllers,
  `initState`, `dispose`, or local toggles.

## Implementation Checklist

Before finishing a UI change:

- Uses `AppColors` tokens, not duplicated hex values.
- Uses ScreenUtil sizing: `.w`, `.h`, `.r`, `.sp`.
- Uses `AppText` or Tajawal text styles.
- Uses `LocaleKeys` for user-facing text.
- Handles long text with wrapping or ellipsis.
- Keeps cards white with light borders unless status/selection requires color.
- Uses teal for primary action and role-aware helpers where needed.
- Uses gold only for owner, premium, role, or highlight moments.
- Keeps destructive states rose/red and visually secondary unless critical.
- Reuses shared buttons, fields, scaffolds, and auth widgets where possible.
