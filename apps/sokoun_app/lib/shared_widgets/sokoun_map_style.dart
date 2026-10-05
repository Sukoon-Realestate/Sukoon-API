import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'sokoun_theme.dart';

/// Quiet land and roads, readable navy labels and teal water; transit stays
/// visible because proximity to transport matters when choosing a property.
abstract final class SokounMapStyle {
  static final String light = _build(const AppColorTheme());
  static final String dark = _build(
    SokounTheme.dark.extension<AppColorTheme>()!,
  );

  static String of(BuildContext context) =>
      Theme.of(context).brightness == Brightness.dark ? dark : light;

  static String _build(AppColorTheme palette) => jsonEncode([
    _rule(
      'all',
      'geometry',
      palette.resolve(AppColors.scaffoldBackground, surface: true),
    ),
    _rule('all', 'labels.text.fill', palette.resolve(AppColors.sokoonNavy)),
    _rule(
      'all',
      'labels.text.stroke',
      palette.resolve(AppColors.white, surface: true),
    ),
    _rule('road', 'geometry', palette.resolve(AppColors.white, surface: true)),
    _rule('road', 'geometry.stroke', palette.resolve(AppColors.grayPale)),
    _rule(
      'road.highway',
      'geometry',
      palette.resolve(AppColors.goldPale, surface: true),
    ),
    _rule(
      'water',
      'geometry',
      palette.resolve(AppColors.mintLight, surface: true),
    ),
    _rule('water', 'labels.text.fill', palette.resolve(AppColors.sokoonTeal)),
    _rule(
      'poi.park',
      'geometry',
      palette.resolve(AppColors.mintPale, surface: true),
    ),
    {
      'featureType': 'poi.business',
      'stylers': [
        {'visibility': 'off'},
      ],
    },
    {
      'featureType': 'poi',
      'elementType': 'labels.icon',
      'stylers': [
        {'visibility': 'off'},
      ],
    },
  ]);

  static Map<String, dynamic> _rule(
    String feature,
    String element,
    Color color,
  ) => {
    'featureType': feature,
    'elementType': element,
    'stylers': [
      {
        'color':
            '#${(color.toARGB32() & 0xffffff).toRadixString(16).padLeft(6, '0')}',
      },
    ],
  };
}
