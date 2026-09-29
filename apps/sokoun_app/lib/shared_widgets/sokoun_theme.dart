import 'package:flutter/material.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/widgets/buttons/app_control_theme.dart';

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
    TextStyle text(double size, FontWeight weight, {Color? color}) => TextStyle(
      fontFamily: ConstantManager.fontFamily,
      fontSize: size,
      fontWeight: weight,
      height: 1.45,
      color: color ?? AppColors.sokoonNavy,
    );
    return ThemeData(
      useMaterial3: true,
      fontFamily: ConstantManager.fontFamily,
      colorScheme: colors,
      scaffoldBackgroundColor: AppColors.scaffoldBackground,
      visualDensity: VisualDensity.standard,
      materialTapTargetSize: MaterialTapTargetSize.padded,
      extensions: const [AppControlTheme()],
      textTheme: TextTheme(
        headlineSmall: text(24, FontWeight.w700),
        titleLarge: text(22, FontWeight.w700),
        titleMedium: text(18, FontWeight.w700),
        titleSmall: text(16, FontWeight.w700),
        bodyLarge: text(16, FontWeight.w400),
        bodyMedium: text(14, FontWeight.w400),
        bodySmall: text(12, FontWeight.w400, color: AppColors.sokoonGray),
        labelLarge: text(14, FontWeight.w700),
        labelMedium: text(13, FontWeight.w500),
        labelSmall: text(12, FontWeight.w500),
      ),
      appBarTheme: AppBarTheme(
        backgroundColor: AppColors.scaffoldBackground,
        foregroundColor: AppColors.sokoonNavy,
        surfaceTintColor: Colors.transparent,
        elevation: 0,
        scrolledUnderElevation: 0,
        centerTitle: true,
        titleTextStyle: text(18, FontWeight.w700),
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
      snackBarTheme: SnackBarThemeData(
        backgroundColor: AppColors.sokoonNavy,
        behavior: SnackBarBehavior.floating,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      ),
    );
  }
}
