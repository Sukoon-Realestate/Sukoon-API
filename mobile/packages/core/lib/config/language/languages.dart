import 'package:easy_localization/easy_localization.dart';
import 'package:flutter/material.dart';

import '../../core/navigation/navigator.dart';
import 'locale_keys.g.dart';

enum Languages {
  english(Locale('en'), 'English', 'en'),
  arabic(Locale('ar'), 'Arabic', 'ar');

  static const String translationsPath =
      'packages/melos_core/assets/translations';

  final Locale locale;
  final String title;
  final String languageCode;

  const Languages(this.locale, this.title, this.languageCode);

  static List<Locale> get supportedLocales =>
      Languages.values.map((e) => e.locale).toList();

  static List<Locale> get suppoerLocales => supportedLocales;

  static List<String> get titles =>
      Languages.values.map((e) => e.title).toList();

  static void setLocale(Languages lang) {
    Go.navigatorKey.currentContext!.setLocale(lang.locale);
  }

  static void setLocaleWithContext(BuildContext context, Languages lang) {
    context.setLocale(lang.locale);
  }

  static String getLanguageCode(Languages language) {
    return language.locale.languageCode;
  }

  /// Get device locale from platform without context
  static Languages getDeviceLocaleFromPlatform() {
    final platformLocale = WidgetsBinding.instance.platformDispatcher.locale;
    return platformLocale.languageCode == 'ar'
        ? Languages.arabic
        : Languages.english;
  }

  /// Get device locale using EasyLocalization context
  static Languages get deviceLocale {
    return EasyLocalization.of(
              Go.navigatorKey.currentContext!,
            )?.locale.languageCode ==
            'ar'
        ? Languages.arabic
        : Languages.english;
  }

  static bool get currentIsArabic => currentLanguage == Languages.arabic;
  static bool get currentIsEnglish => currentLanguage == Languages.english;

  static Languages get currentLanguage {
    final currentLocale = EasyLocalization.of(
      Go.navigatorKey.currentContext!,
    )!.locale;
    return Languages.values.firstWhere(
      (element) => element.locale == currentLocale,
    );
  }
}

extension LanguagesExtension on Languages {
  String toFullTitle() {
    if (this == Languages.arabic) {
      return LocaleKeys.arabic;
    } else if (this == Languages.english) {
      return LocaleKeys.english;
    }

    return '';
  }
}
