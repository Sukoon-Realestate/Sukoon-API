import 'dart:convert';
import 'dart:ui';
import 'package:melos_core/config/res/config_imports.dart';

/// Quiet land and roads, readable navy labels and teal water; transit stays
/// visible because proximity to transport matters when choosing a property.
abstract final class SokounMapStyle {
  static String get light => jsonEncode([
    _rule('all', 'geometry', AppColors.scaffoldBackground),
    _rule('all', 'labels.text.fill', AppColors.sokoonNavy),
    _rule('all', 'labels.text.stroke', AppColors.white),
    _rule('road', 'geometry', AppColors.white),
    _rule('road', 'geometry.stroke', AppColors.grayPale),
    _rule('road.highway', 'geometry', AppColors.goldPale),
    _rule('water', 'geometry', AppColors.mintLight),
    _rule('water', 'labels.text.fill', AppColors.sokoonTeal),
    _rule('poi.park', 'geometry', AppColors.mintPale),
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
