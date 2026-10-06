# CLAUDE.md — Sukoon Mobile App

Flutter 3.9+ + Dart + Melos 8 Monorepo workspace.
Includes `packages/core` (shared logic, widgets, networking, caching), `apps/sokoun_app` (main tenant/owner app), and `apps/landing_page`.
Clean Architecture with BLoC/Cubit (`AsyncCubit`), `GetIt` dependency injection, and `Go` router.

---

## CORE RULE — Auto-route every mobile task

**Before answering directly, check the routing table below.** If a prompt matches the keywords of an agent or skill, **invoke it automatically** — do not wait for the user to name it. If several match, pick the most specific. Only answer inline when nothing fits (simple questions, quick edits, conversation).

---

## WORKSPACE COMMANDS (Run from `mobile/`)

```bash
# Melos workspace analyze
melos exec -- dart analyze .

# Run test suite across all packages and apps
melos exec -- flutter test

# Code generation (injectable, json_serializable, objectbox)
melos exec -- dart run build_runner build -d

# Generate localization strings from lang.json
dart run generate/strings/main.dart

# Watch and generate localization strings
dart run generate/strings/main.dart --watch

# Clean all packages
melos exec -- flutter clean

# Run specific app
cd apps/sokoun_app && flutter run
```

---

## SKILLS (invoke with the Skill tool)

### `/sokoun-feature-architecture`
Build or refactor features in `apps/sokoun_app` following the strict presentation/data layer separation, Cubit lifecycle, thin screens, and extracted widgets.
**Trigger words:** feature, screen, scaffold, build screen, new screen, refactor screen, cubit, async cubit, status builder, app pagify, pagination, empty state, lottie, clean architecture.

### `/feature-readiness`
Validate feature readiness, run comprehensive mobile verification checklists, and produce handoff reports.
**Trigger words:** readiness, feature readiness, verify feature, mobile checklist, validate screen, audit feature, handoff review.

### `/mobile-codegen`
Run Melos build runner codegen or regenerate string localization assets.
**Trigger words:** codegen, build_runner, build runner, generate strings, translations, lang.json, locale keys, objectbox gen.

---

## AGENTS (spawn with the Agent tool — `subagent_type`)

### flutter-developer
Deep Flutter UI development, complex screens, widget trees, animations, ScreenUtil responsiveness, and platform adaptations.
**Trigger words:** flutter, widget, screen, ui, animation, screenutil, dialog, bottom sheet, scaffold, theme, lottie, custom painter.

### mobile-architect
Monorepo structuring, clean architecture boundaries, Melos package management, state management patterns, and offline-first data caching.
**Trigger words:** mobile architecture, state management, bloc, cubit, get_it, dependency injection, offline first, caching, melos, package split.

### dart-pro
Deep Dart language tasks, type system, models, immutability, generics, async/await, streams, and performance optimization.
**Trigger words:** dart, equatable, json_serializable, model, serializer, parsing, extension, stream, isolates, dart pro.

### mobile-qa
Mobile test automation, widget testing, unit tests, Cubit testing, and integration verification.
**Trigger words:** flutter test, widget test, unit test mobile, mockito, bloc test, test coverage mobile.

### code-reviewer
Review mobile pull requests and working diffs for Flutter/Dart best practices, architecture compliance, memory leaks, and UI guidelines.
**Trigger words:** mobile code review, review flutter, audit dart, check mobile code, pr review mobile.

---

## Project Conventions (ALWAYS HONOR)

1. **Navigation — `Go` Class Only**:
   - MUST use `Go.to(...)`, `Go.off(...)`, `Go.offAll(...)`, `Go.toNamed(...)`, `Go.back(...)`.
   - NEVER use `Navigator.push(...)` or `Navigator.of(context)` directly.

2. **Clean Architecture & Folder Structure**:
   ```text
   features/<feature_name>/
     data/
       enums/
       models/
       <feature_name>_data.dart
     presentation/
       cubits/
       screens/
       widgets/
         shared/
         <screen_or_flow_name>/
   ```
   - Screens are thin flow orchestrators. NEVER put API calls, raw JSON parsing, or large widget trees directly in screen files.
   - Separate distinct visual sections into extracted widget files.

3. **State Management & Cubit Lifecycle**:
   - Extend `AsyncCubit<T>`, initialize with `const Model.initial()`.
   - Cubit constructor must be side-effect free (trigger request from screen's `initState`).
   - Use `StatusBuilder<Cubit, Model>.withShimmer` to render states.
   - For local UI changes, prefer `ValueNotifier<T>` + `ValueListenableBuilder<T>` over `setState`.

4. **Paginated Lists**:
   - MUST use `AppPagify` from `packages/core/lib/core/widgets/app_pagify.dart`.
   - Never build custom scroll listeners or pagination cubits when `AppPagify` handles it.

5. **Empty States**:
   - Every API-backed screen must use a contextual Lottie animation (`Assets.lottie.*`) for empty states rather than generic text.

6. **Localization**:
   - NO hardcoded text strings in UI.
   - Add strings to `packages/core/assets/translations/lang.json`.
   - Access via `LocaleKeys.<key>`.
   - Run `dart run generate/strings/main.dart` after updating.

7. **Design System & Aesthetics**:
   - Arabic-first, Tajawal font, primary Navy `#0F172A`, accent Teal `#0D9488`, Gold `#D97706`.
   - Reuse components from `packages/core/lib/core/widgets` before creating new ones.
   - SVGs rendered via `SvgPic`, not raw paths.
