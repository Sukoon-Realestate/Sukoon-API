abstract class GenerateConstants {
  //print_colors
  static const String blueColorCode = '\x1B[34m';
  static const String orangeColorCode = '\x1B[33m';
  static const String redColorCode = '\x1B[31m';
  static const String greenColorCode = '\x1B[32m';
  static const String resetColorCode = '\x1B[0m';
  //generate_strings
  static const List<String> translationPackageRoots = [
    'packages/core',
    'apps/aait_flutter_app',
    'apps/dashboard',
  ];

  static Iterable<TranslationTarget> get translationTargets =>
      translationPackageRoots.map(TranslationTarget.new);

  static const String langJsonAssetFilePath =
      'packages/core/assets/translations/lang.json';
  static const String langEnJsonAssetFilePath =
      'packages/core/assets/translations/en.json';
  static const String langArJsonAssetFilePath =
      'packages/core/assets/translations/ar.json';
  static const String outputStringsFilePath =
      'packages/core/lib/config/language/locale_keys.g.dart';
  //generate_features
  static const String projectFeaturesPath = 'lib/src/features';
  static const String requestsAssetsPath = 'assets/requests';
}

class TranslationTarget {
  final String packageRoot;

  const TranslationTarget(this.packageRoot);

  String get langJsonAssetFilePath =>
      '$packageRoot/assets/translations/lang.json';

  String get langEnJsonAssetFilePath =>
      '$packageRoot/assets/translations/en.json';

  String get langArJsonAssetFilePath =>
      '$packageRoot/assets/translations/ar.json';

  String get outputStringsFilePath =>
      '$packageRoot/lib/config/language/locale_keys.g.dart';
}
