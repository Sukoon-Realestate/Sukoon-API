import 'package:flutter/material.dart';

/// Shared defaults for startup, persistence, and appearance transitions.
abstract final class SokounThemeConfig {
  static const ThemeMode defaultMode = ThemeMode.system;
  static const String preferenceKey = 'sokoun_theme_mode_v1';
  static const int transitionMilliseconds = 320;
  static const Curve transitionCurve = Curves.easeInOutCubic;
}
