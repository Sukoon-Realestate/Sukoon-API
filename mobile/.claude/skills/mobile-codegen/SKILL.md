---
name: mobile-codegen
description: "Run code generation for Flutter/Dart models (injectable, json_serializable, objectbox) and regenerate translation keys from lang.json."
---

# Mobile Code Generation Skill

Use this skill when modifying dependency injection annotations, JSON serializable models, or adding new translation keys.

## 1. Running Build Runner
To regenerate code for all packages and apps in the Melos monorepo:

```bash
cd mobile && melos exec -- dart run build_runner build -d
```

For a specific package or app:
```bash
cd mobile/packages/core && dart run build_runner build -d
# or
cd mobile/apps/sokoun_app && dart run build_runner build -d
```

## 2. Generating Localization Strings
When new strings are added to `mobile/packages/core/assets/translations/lang.json`:

```bash
cd mobile && dart run generate/strings/main.dart
```

To watch for changes during development:
```bash
cd mobile && dart run generate/strings/main.dart --watch
```

## Verification
After code generation, verify with:
```bash
cd mobile && melos exec -- dart analyze .
```
