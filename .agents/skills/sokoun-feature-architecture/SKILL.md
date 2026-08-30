---
name: sokoun-feature-architecture
description: Build or refactor features in apps/sokoun_app using the repository's data/presentation separation, Cubit lifecycle, thin screens, and extracted widgets. Use for substantial Sokoun feature or screen work; do not invoke for core-package-only utilities or trivial visual edits that need no architectural change.
---

# Sokoun Feature Architecture

Apply the existing Sokoun feature structure to the requested work. Preserve behavior and user scope; this skill determines organization, not product requirements.

## Inspect Before Editing

1. Read the applicable repository instructions, especially `apps/sokoun_app/AGENTS.md`.
2. Inspect the target feature and the closest implemented feature with the same behavior. Prefer current repository patterns over generic Flutter boilerplate.
3. Inventory existing models, endpoints, shared widgets, translation keys, asset constants, and navigation targets before creating files.
4. State the proposed file split in a concise commentary update, then implement it. Do not stop for confirmation when the split follows these rules and does not change product behavior.

## Feature Layout

Use only the folders the feature needs, following this shape:

```text
features/<feature_name>/
  imports.dart                         # optional barrel for a large part-based feature
  data/
    enums/
    models/
    <feature_name>_data.dart           # optional API/data helper
  presentation/
    cubits/
    screens/
    widgets/
      shared/
      <screen_or_flow_name>/
```

- Put JSON mapping, request/response models, filters, enums, and data-source helpers under `data/`.
- Put state management, screens, and UI components under `presentation/`.
- Keep one main responsibility per file. A screen file owns the scaffold and flow orchestration; each distinct visual section belongs in its own widget file.
- Use a feature-level `imports.dart` with `part`/`part of` only when the feature already uses that convention or has enough files to benefit. Otherwise use direct imports.
- Never place API calls, JSON parsing, or reusable visual sections directly in a screen.

## Cubit Boundary

Create a Cubit when the work calls an API or local database, consumes realtime events, or exposes state shared by multiple widgets/screens. Keep local tab indices, toggles, controllers, animation state, and other single-screen UI state in a `StatefulWidget`.

For remote state:

- Extend `AsyncCubit<T>` and initialize it with meaningful non-null data, normally `const Model.initial()`.
- Keep the constructor side-effect free. Inject dependencies there if needed, but trigger loading from the screen's `initState`.
- Put endpoint selection, request bodies, query parameters, mapping, pagination merging, and async state transitions in the Cubit or a `data/` helper—not in widgets.
- Prefer `baseCrudUseCase` with `CrudBaseParmas<T>` for ordinary requests. Use `NetworkService` only through a data-layer helper when the feature's pagination or response shape needs it.
- Always await `executeAsyncWithBaseModel`, enable the internet interceptor where appropriate, and keep navigation/snackbars in the presentation layer.
- Dispose screen-owned Cubits and cancel Cubit subscriptions.

### Offline-First Remote Reads

Use the core cache pipeline for cacheable GET requests instead of adding mock-data or local-content branches to screens. Supply the complete cache contract on `CrudBaseParmas<T>`:

```dart
CrudBaseParmas<MyModel>(
  api: ApiConstants.itemDetails(id),
  httpRequestType: HttpRequestType.get,
  cacheKey: 'item_details_$id',
  mapper: (json) => MyModel.fromJson(json),
  fromCacheJson: MyModel.fromJson,
  toJson: (model) => model.toJson(),
)
```

- Include every resource identity or query dimension in `cacheKey`; detail screens must not share one key across IDs.
- Keep `fromJson` and `toJson` structurally symmetric so cached models deserialize exactly like API models.
- The core repository requests fresh data first, persists successful responses, and restores cached data as a success when the request fails. `StatusBuilder` therefore renders cached content automatically; its exception view appears only when the request fails and no valid cache exists.
- Do not add a mock fallback branch to hide request failures, and do not start a second request from `build`.
- Do not cache POST, PUT, PATCH, or DELETE operations through this read-cache contract.
- For `AppPagify`, provide `cacheKey`, `cacheToJson`, and `cacheFromJson` together. Use the same three arguments on API-backed `AppDropinity` widgets. Omit the entire cache configuration when any serializer is unavailable.

### API Empty States

Every API-backed screen whose successful response can contain no items must use a feature-specific Lottie empty-state widget instead of the generic `NotContainData`. Treat an empty response as a valid success state, distinct from loading, an error without cache, or offline content restored from cache.

- Before designing the state, read `design.md`, inspect the screen's purpose and retained controls, and inspect the closest feature empty state. Preserve useful context such as the app bar, search query, filters, or tabs; replace only the data region that is empty.
- Put the widget in the feature's presentation widgets folder and name it for the screen or collection, such as `SearchResultsEmptyState` or `VisitsEmptyState`. Reuse an existing feature widget only when its meaning, copy, action, and role styling match.
- Select the closest semantic generated asset from `Assets.lottie`, normally `noData`, `emptyBox`, or `notFound1`/`notFound2`; reserve `emptyCart` for cart-like flows. Render it through the generated `.lottie(...)` API, not a raw asset path, and never use error or no-internet animations for a successful empty response.
- Follow `design.md`: use the scaffold canvas, restrained teal or role-aware accents, ScreenUtil sizing, a centered and scroll-safe layout, a short navy high-emphasis title, and concise gray supporting copy. Keep the animation subordinate to the message and avoid decorative cards or shadows that do not help comprehension.
- Use `LocaleKeys` for the title, description, and optional CTA. Add one CTA only when the user has a useful recovery or next action, such as clearing filters, browsing properties, adding a listing, or retrying a different search; do not add a dead-end or unrelated action.
- Respect reduced-motion settings for nonessential animation, and make the empty state accessible. When the adjacent title already explains the state, treat the Lottie as decorative rather than announcing duplicate content.
- `StatusBuilder` automatically detects emptiness only when `T` itself is a `List`. Pass the custom widget through `emptyView` for list state. For wrapped responses, check the domain collection such as `data.results.isEmpty` inside the success builder and render the empty widget there. For `AppPagify`, pass it through `emptyListView`.
- Test that an empty API success renders the custom empty state and its action, while an error with no valid cache still renders the exception view and non-empty cached/API data renders the normal content.

## Models and Data

- Use typed immutable models rather than loose maps in presentation code.
- Response/state models normally extend `Equatable` and provide a const constructor, resilient `fromJson`, `toJson` when serialized, `copyWith`, `initial`, and complete `props`.
- Use meaningful empty values in `initial()` so shimmer rendering is safe. Avoid force-unwrapping API fields.
- For request bodies with more than two fields, create a typed body model and build the request map only in `toJson()`.
- Add or reuse endpoint constants; do not scatter raw endpoint strings across screens.

## Screen Lifecycle and Composition

For an `AsyncCubit` screen, follow this lifecycle:

1. Create the Cubit and store the single request `Future<void>` in `initState`.
2. Provide the Cubit with `BlocProvider.value` when the screen owns it.
3. Render with `StatusBuilder<Cubit, Model>.withShimmer`, passing `Model.initial()` and the same stored request future.
4. Delegate successful data rendering to a small body method or extracted widgets.
5. Close the Cubit and dispose controllers/focus nodes in `dispose`.

Use the role-aware navigation approach from `home_screen.dart` only for tab containers: build typed destination/screen pairs, select the role-specific list once, render screens with `IndexedStack`, and keep the bottom-navigation widget separate. Do not apply tab-container structure to ordinary screens.

## Project Conventions

- Navigate through `Go`; do not introduce direct `Navigator` calls.
- Use `LocaleKeys` for user-facing text and update `packages/core/assets/translations/lang.json` when a key is missing.
- Reuse `packages/core/lib/core/widgets` and existing feature widgets before creating new components.
- Reference generated asset constants such as `Assets.*`; render SVG assets through `SvgPic` rather than hardcoded paths.
- Use `AppColors`, `AppText`, ScreenUtil units, and existing spacing/extensions.
- Preserve unrelated working-tree changes and avoid editing generated outputs unless the repository's established generator owns the change.

## Completion Check

Before handing off:

1. Confirm data code does not import presentation code and widgets do not import screens.
2. Confirm async requests are not started from `build` or a Cubit constructor.
3. Confirm cacheable GETs use a stable key plus both serializers, and that screens rely on the cache result instead of mock fallback data.
4. Confirm successful empty API data renders a contextual Lottie empty state without hiding the screen's useful controls.
5. Confirm the screen is orchestration-focused and visual sections are separated.
6. Run Dart formatting, focused analysis, relevant tests, and `git diff --check`.
7. Summarize the resulting file structure and verification. Mention any intentionally omitted layer or unavailable backend/profile screen instead of adding a misleading placeholder.
