import 'package:easy_localization/easy_localization.dart';
import 'package:flutter/material.dart';

import 'locale_keys.g.dart';

enum Languages {
  english(Locale('en'), 'English', 'en'),
  arabic(Locale('ar'), 'Arabic', 'ar');

  static const String translationsPath = 'assets/translations';
  static final GlobalKey<NavigatorState> navigatorKey =
      GlobalKey<NavigatorState>();

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
    final context = navigatorKey.currentContext;
    if (context != null) {
      context.setLocale(lang.locale);
    }
  }

  static void setLocaleWithContext(BuildContext context, Languages lang) {
    context.setLocale(lang.locale);
  }

  static String getLanguageCode(Languages language) {
    return language.locale.languageCode;
  }

  static Languages getDeviceLocaleFromPlatform() {
    final platformLocale = WidgetsBinding.instance.platformDispatcher.locale;
    return platformLocale.languageCode == 'ar'
        ? Languages.arabic
        : Languages.english;
  }

  static Languages get deviceLocale {
    final context = navigatorKey.currentContext;
    final locale = context == null
        ? WidgetsBinding.instance.platformDispatcher.locale
        : EasyLocalization.of(context)?.locale;
    return locale?.languageCode == 'ar' ? Languages.arabic : Languages.english;
  }

  static bool get currentIsArabic => currentLanguage == Languages.arabic;
  static bool get currentIsEnglish => currentLanguage == Languages.english;

  static Languages get currentLanguage {
    final context = navigatorKey.currentContext;
    final locale = context == null
        ? WidgetsBinding.instance.platformDispatcher.locale
        : EasyLocalization.of(context)?.locale;
    return Languages.values.firstWhere(
      (element) => element.locale.languageCode == locale?.languageCode,
      orElse: () => Languages.english,
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
