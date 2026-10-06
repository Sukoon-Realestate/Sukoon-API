import 'package:flutter/material.dart';

abstract final class LandingColors {
  static const teal = Color(0xFF0C6254);
  static const tealDark = Color(0xFF084B40);
  static const tealLight = Color(0xFFEDFDF3);
  static const navy = Color(0xFF152E29);
  static const gold = Color(0xFFD6A84F);
  static const blue = Color(0xFF2563EB);
  static const green = Color(0xFF22C55E);
  static const rose = Color(0xFFE11D48);
  static const background = Color(0xFFFAFBF8);
  static const border = Color(0xFFE3EBE5);
  static const subtext = Color(0xFF6B7280);
  static const softSurface = Color(0xFFF3F4F6);
}

abstract final class LandingBreakpoints {
  static const mobile = 680.0;
  static const tablet = 960.0;
  static const contentMaxWidth = 1200.0;

  static bool isMobile(double width) => width < mobile;
  static bool isTablet(double width) => width >= mobile && width < tablet;
}

abstract final class LandingTheme {
  static ThemeData get theme {
    final colorScheme = ColorScheme.fromSeed(
      seedColor: LandingColors.teal,
      brightness: Brightness.light,
      surface: LandingColors.background,
    );

    return ThemeData(
      useMaterial3: true,
      colorScheme: colorScheme,
      scaffoldBackgroundColor: LandingColors.background,
      fontFamily: 'packages/melos_core/Tajawal',
      textSelectionTheme: const TextSelectionThemeData(
        cursorColor: LandingColors.teal,
        selectionColor: LandingColors.tealLight,
      ),
      focusColor: LandingColors.teal.withValues(alpha: 0.12),
      hoverColor: LandingColors.teal.withValues(alpha: 0.06),
      splashColor: LandingColors.teal.withValues(alpha: 0.08),
    );
  }
}
