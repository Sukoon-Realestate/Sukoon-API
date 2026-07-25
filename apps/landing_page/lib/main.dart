import 'package:easy_localization/easy_localization.dart';
import 'package:flutter/material.dart';
import 'package:melos_core/config/language/languages.dart';

import 'app.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await EasyLocalization.ensureInitialized();

  runApp(
    EasyLocalization(
      supportedLocales: Languages.supportedLocales,
      path: Languages.translationsPath,
      saveLocale: true,
      startLocale: Languages.arabic.locale,
      fallbackLocale: Languages.arabic.locale,
      child: const LandingPageApp(),
    ),
  );
}
