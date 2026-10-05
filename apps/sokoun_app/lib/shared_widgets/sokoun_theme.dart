import 'package:flutter/material.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/helpers/text_style_manager.dart';
import 'package:melos_core/core/widgets/buttons/app_control_theme.dart';
import 'package:melos_core/core/widgets/pull_refresher_theme.dart';

import 'sokoun_refresh_indicator.dart';

abstract final class SokounTheme {
  static final ThemeData light = _build(Brightness.light);
  static final ThemeData dark = _build(Brightness.dark);

  static final AppColorTheme _darkColors = AppColorTheme(
    foreground: {
      AppColors.navy: AppColors.sokoonDarkText,
      AppColors.black: AppColors.sokoonDarkText,
      AppColors.charcoal: AppColors.sokoonDarkText,
      AppColors.slateGray: AppColors.blueGrayPale,
      AppColors.gray: AppColors.sokoonDarkSecondary,
      AppColors.grayLight: AppColors.sokoonDarkMuted,
      AppColors.blueGray: AppColors.sokoonDarkSecondary,
      AppColors.graySoft: AppColors.blueGray,
      AppColors.grayPale: AppColors.sokoonDarkBorder,
      AppColors.grayBluePale: AppColors.sokoonDarkBorder,
      AppColors.grayMist: AppColors.sokoonDarkBorder,
      AppColors.teal: AppColors.sokoonDarkTeal,
      AppColors.green: AppColors.sokoonDarkSuccess,
      AppColors.greenStrong: AppColors.sokoonDarkSuccess,
      AppColors.rose: AppColors.sokoonDarkError,
      AppColors.red: AppColors.sokoonDarkError,
      AppColors.blue: AppColors.sokoonDarkInfo,
      AppColors.brown: AppColors.sokoonDarkWarning,
      AppColors.amber: AppColors.sokoonDarkWarning,
    },
    surfaces: {
      AppColors.offWhite: AppColors.sokoonDarkCanvas,
      AppColors.white: AppColors.sokoonDarkSurface,
      AppColors.grayOffWhite: AppColors.sokoonDarkRaised,
      AppColors.grayBackground: AppColors.sokoonDarkRaised,
      AppColors.graySoft: AppColors.sokoonDarkBorder,
      AppColors.grayPale: AppColors.sokoonDarkBorder,
      AppColors.grayBluePale: AppColors.sokoonDarkBorder,
      AppColors.grayMist: AppColors.sokoonDarkBorder,
      AppColors.mintLight: AppColors.sokoonDarkTealSurface,
      AppColors.mintPale: AppColors.sokoonDarkTealSurface,
      AppColors.mint: AppColors.sokoonDarkSuccessSurface,
      AppColors.greenPale: AppColors.sokoonDarkSuccessSurface,
      AppColors.redPale: AppColors.sokoonDarkErrorSurface,
      AppColors.bluePale: AppColors.sokoonDarkInfoSurface,
      AppColors.goldPale: AppColors.sokoonDarkGoldSurface,
      AppColors.amberPale: AppColors.sokoonDarkWarningSurface,
      AppColors.orangePale: AppColors.sokoonDarkWarningSurface,
      AppColors.yellowPale: AppColors.sokoonDarkWarningSurface,
    },
  );

  static ThemeData _build(Brightness brightness) {
    final bool isDark = brightness == Brightness.dark;
    final AppColorTheme palette = isDark ? _darkColors : const AppColorTheme();
    Color ink(Color color) => palette.resolve(color);
    Color surface(Color color) => palette.resolve(color, surface: true);
    final Color canvas = surface(AppColors.scaffoldBackground);
    final Color card = surface(AppColors.white);
    final Color textColor = ink(AppColors.sokoonNavy);
    final Color secondary = ink(AppColors.sokoonGray);
    final Color accent = ink(AppColors.sokoonTeal);
    final Color outline = ink(AppColors.sokoonBorder);
    final ColorScheme colors =
        ColorScheme.fromSeed(
          seedColor: AppColors.sokoonTeal,
          brightness: brightness,
        ).copyWith(
          primary: accent,
          onPrimary: isDark ? AppColors.slate : AppColors.white,
          primaryContainer: surface(AppColors.mintLight),
          onPrimaryContainer: accent,
          secondary: AppColors.sokoonGold,
          onSecondary: AppColors.sokoonNavy,
          secondaryContainer: surface(AppColors.goldPale),
          onSecondaryContainer: isDark ? AppColors.sokoonGold : textColor,
          surface: card,
          surfaceContainerLowest: canvas,
          surfaceContainerLow: card,
          surfaceContainer: surface(AppColors.grayOffWhite),
          surfaceContainerHigh: surface(AppColors.grayBackground),
          surfaceContainerHighest: surface(AppColors.grayBackground),
          onSurface: textColor,
          onSurfaceVariant: secondary,
          outline: ink(AppColors.grayPale),
          outlineVariant: outline,
          error: ink(AppColors.sokoonRose),
          onError: isDark ? AppColors.slate : AppColors.white,
          errorContainer: surface(AppColors.redPale),
          onErrorContainer: ink(AppColors.sokoonRose),
        );
    TextStyle text(TextStyle style, {double? size, Color? color}) =>
        style.copyWith(fontSize: size, height: 1.45, color: color ?? textColor);
    return ThemeData(
      useMaterial3: true,
      brightness: brightness,
      fontFamily: AppTextStyles.base.fontFamily,
      colorScheme: colors,
      scaffoldBackgroundColor: canvas,
      canvasColor: card,
      cardColor: card,
      disabledColor: ink(AppColors.sokoonMuted),
      iconTheme: IconThemeData(color: textColor),
      visualDensity: VisualDensity.standard,
      materialTapTargetSize: MaterialTapTargetSize.padded,
      extensions: [
        palette,
        const AppControlTheme(),
        const PullRefresherTheme(
          indicatorBuilder: SokounRefreshIndicator.builder,
        ),
      ],
      textTheme: TextTheme(
        headlineSmall: text(AppTextStyles.bold, size: 24),
        titleLarge: text(AppTextStyles.bold, size: 22),
        titleMedium: text(AppTextStyles.bold, size: 18),
        titleSmall: text(AppTextStyles.bold16),
        bodyLarge: text(AppTextStyles.regular16),
        bodyMedium: text(AppTextStyles.regular14),
        bodySmall: text(AppTextStyles.regular12, color: secondary),
        labelLarge: text(AppTextStyles.bold14),
        labelMedium: text(AppTextStyles.medium13),
        labelSmall: text(AppTextStyles.medium12),
      ),
      appBarTheme: AppBarTheme(
        backgroundColor: canvas,
        foregroundColor: textColor,
        surfaceTintColor: Colors.transparent,
        elevation: 0,
        scrolledUnderElevation: 0,
        centerTitle: true,
        titleTextStyle: text(AppTextStyles.bold, size: 18),
      ),
      dividerTheme: DividerThemeData(color: outline, thickness: 1),
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: AppColors.sokoonTeal,
          foregroundColor: AppColors.white,
          minimumSize: const Size(48, 48),
          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
          elevation: 0,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(12),
          ),
        ),
      ),
      textButtonTheme: TextButtonThemeData(
        style: TextButton.styleFrom(
          minimumSize: const Size(48, 48),
          foregroundColor: accent,
        ),
      ),
      iconButtonTheme: IconButtonThemeData(
        style: IconButton.styleFrom(
          minimumSize: const Size(48, 48),
          foregroundColor: textColor,
        ),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: card,
        hintStyle: text(
          AppTextStyles.regular14,
          color: ink(AppColors.sokoonMuted),
        ),
        contentPadding: const EdgeInsets.symmetric(
          horizontal: 16,
          vertical: 16,
        ),
        border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: BorderSide(color: outline),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: BorderSide(color: accent, width: 1.5),
        ),
        errorMaxLines: 3,
      ),
      bottomSheetTheme: BottomSheetThemeData(
        backgroundColor: card,
        surfaceTintColor: Colors.transparent,
        constraints: BoxConstraints(maxWidth: 640),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
        ),
      ),
      dialogTheme: DialogThemeData(
        backgroundColor: card,
        surfaceTintColor: Colors.transparent,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
      ),
      navigationRailTheme: NavigationRailThemeData(
        backgroundColor: card,
        indicatorColor: surface(AppColors.mintLight),
        selectedIconTheme: IconThemeData(color: accent),
        unselectedIconTheme: IconThemeData(color: secondary),
        useIndicator: true,
      ),
      snackBarTheme: SnackBarThemeData(
        backgroundColor: isDark
            ? AppColors.sokoonDarkRaised
            : AppColors.sokoonNavy,
        contentTextStyle: text(AppTextStyles.regular14, color: AppColors.white),
        actionTextColor: isDark ? accent : AppColors.sokoonGold,
      ),
      progressIndicatorTheme: ProgressIndicatorThemeData(color: accent),
    );
  }
}
