import 'package:flutter/material.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/helpers/text_style_manager.dart';
import 'package:melos_core/core/widgets/buttons/app_control_theme.dart';
import 'package:melos_core/core/widgets/pull_refresher_theme.dart';

import 'sokoun_refresh_indicator.dart';

abstract final class SokounTheme {
  static ThemeData get light {
    final ColorScheme colors =
        ColorScheme.fromSeed(
          seedColor: AppColors.sokoonTeal,
          brightness: Brightness.light,
        ).copyWith(
          primary: AppColors.sokoonTeal,
          onPrimary: AppColors.white,
          surface: AppColors.white,
          onSurface: AppColors.sokoonNavy,
          onSurfaceVariant: AppColors.sokoonGray,
          outline: AppColors.grayPale,
          error: AppColors.sokoonRose,
        );
    TextStyle text(TextStyle style, {double? size, Color? color}) =>
        style.copyWith(
          fontSize: size,
          height: 1.45,
          color: color ?? AppColors.sokoonNavy,
        );
    return ThemeData(
      useMaterial3: true,
      fontFamily: AppTextStyles.base.fontFamily,
      colorScheme: colors,
      scaffoldBackgroundColor: AppColors.scaffoldBackground,
      visualDensity: VisualDensity.standard,
      materialTapTargetSize: MaterialTapTargetSize.padded,
      extensions: const [
        AppControlTheme(),
        PullRefresherTheme(indicatorBuilder: SokounRefreshIndicator.builder),
      ],
      textTheme: TextTheme(
        headlineSmall: text(AppTextStyles.bold, size: 24),
        titleLarge: text(AppTextStyles.bold, size: 22),
        titleMedium: text(AppTextStyles.bold, size: 18),
        titleSmall: text(AppTextStyles.bold16),
        bodyLarge: text(AppTextStyles.regular16),
        bodyMedium: text(AppTextStyles.regular14),
        bodySmall: text(AppTextStyles.regular12, color: AppColors.sokoonGray),
        labelLarge: text(AppTextStyles.bold14),
        labelMedium: text(AppTextStyles.medium13),
        labelSmall: text(AppTextStyles.medium12),
      ),
      appBarTheme: AppBarTheme(
        backgroundColor: AppColors.scaffoldBackground,
        foregroundColor: AppColors.sokoonNavy,
        surfaceTintColor: Colors.transparent,
        elevation: 0,
        scrolledUnderElevation: 0,
        centerTitle: true,
        titleTextStyle: text(AppTextStyles.bold, size: 18),
      ),
      dividerTheme: const DividerThemeData(
        color: AppColors.sokoonBorder,
        thickness: 1,
      ),
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
          foregroundColor: AppColors.sokoonTeal,
        ),
      ),
      iconButtonTheme: IconButtonThemeData(
        style: IconButton.styleFrom(
          minimumSize: const Size(48, 48),
          foregroundColor: AppColors.sokoonNavy,
        ),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: AppColors.white,
        contentPadding: const EdgeInsets.symmetric(
          horizontal: 16,
          vertical: 16,
        ),
        border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: AppColors.sokoonBorder),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: AppColors.sokoonTeal, width: 1.5),
        ),
        errorMaxLines: 3,
      ),
      bottomSheetTheme: const BottomSheetThemeData(
        backgroundColor: AppColors.white,
        surfaceTintColor: Colors.transparent,
        constraints: BoxConstraints(maxWidth: 640),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
        ),
      ),
      dialogTheme: DialogThemeData(
        backgroundColor: AppColors.white,
        surfaceTintColor: Colors.transparent,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
      ),
      navigationRailTheme: const NavigationRailThemeData(
        backgroundColor: AppColors.white,
        indicatorColor: AppColors.mintLight,
        selectedIconTheme: IconThemeData(color: AppColors.sokoonTeal),
        unselectedIconTheme: IconThemeData(color: AppColors.sokoonGray),
        useIndicator: true,
      ),
    );
  }
}
