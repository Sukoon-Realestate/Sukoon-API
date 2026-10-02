import 'package:easy_localization/easy_localization.dart';
import 'package:flutter/material.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';

import '../../theme/landing_theme.dart';

class LanguageButton extends StatelessWidget {
  const LanguageButton({super.key});

  @override
  Widget build(BuildContext context) {
    final localization = EasyLocalization.of(context);
    if (localization == null) return const SizedBox.shrink();
    final arabic = localization.locale.languageCode == 'ar';
    return Tooltip(
      message: LocaleKeys.changeLanguage,
      child: TextButton(
        onPressed: () => context.setLocale(Locale(arabic ? 'en' : 'ar')),
        style: TextButton.styleFrom(foregroundColor: LandingColors.teal),
        child: Text(
          arabic
              ? LocaleKeys.languageEnglishNativeName
              : LocaleKeys.languageArabicName,
        ),
      ),
    );
  }
}
