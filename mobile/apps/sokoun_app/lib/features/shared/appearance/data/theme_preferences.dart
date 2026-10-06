import 'package:flutter/material.dart';
import 'package:melos_core/core/helpers/cache_service.dart';
import 'package:sokoun_app/shared_widgets/sokoun_theme_config.dart';

abstract final class ThemePreferences {
  static ThemeMode read() {
    final Object? value = CacheStorage.read(SokounThemeConfig.preferenceKey);
    return ThemeMode.values.firstWhere(
      (mode) => mode.name == value,
      orElse: () => SokounThemeConfig.defaultMode,
    );
  }

  static Future<void> write(ThemeMode mode) =>
      CacheStorage.write(SokounThemeConfig.preferenceKey, mode.name);
}
