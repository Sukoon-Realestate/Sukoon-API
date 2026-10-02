import 'package:easy_localization/easy_localization.dart';
import 'package:flutter/material.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/core/navigation/navigator.dart';

import 'landing/pages/landing_page.dart';
import 'landing/theme/landing_theme.dart';

class LandingPageApp extends StatelessWidget {
  const LandingPageApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      navigatorKey: Go.navigatorKey,
      debugShowCheckedModeBanner: false,
      onGenerateTitle: (_) => LocaleKeys.landingAppTitle,
      localizationsDelegates: context.localizationDelegates,
      supportedLocales: context.supportedLocales,
      locale: context.locale,
      theme: LandingTheme.theme,
      // LocaleKeys resolves strings outside BuildContext; remount cached sections
      // so a language change also refreshes const widgets and header delegates.
      home: LandingPage(key: ValueKey(context.locale.languageCode)),
    );
  }
}
