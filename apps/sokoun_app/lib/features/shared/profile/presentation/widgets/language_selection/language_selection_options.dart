part of '../../../imports.dart';

class LanguageSelectionOptions extends StatelessWidget {
  const LanguageSelectionOptions({
    super.key,
    required this.selectedLanguage,
    required this.onLanguageSelected,
  });

  final Languages selectedLanguage;
  final ValueChanged<Languages> onLanguageSelected;

  @override
  Widget build(BuildContext context) {
    return Column(
      spacing: 12.h,
      children: [
        LanguageOptionCard(
          title: LocaleKeys.languageArabicName,
          subtitle: LocaleKeys.languageArabicTranslation,
          flag: '🇸🇦',
          selected: selectedLanguage == Languages.arabic,
          onSelected: () => onLanguageSelected(Languages.arabic),
        ),
        LanguageOptionCard(
          title: LocaleKeys.languageEnglishNativeName,
          subtitle: LocaleKeys.languageEnglishTranslation,
          flag: '🇬🇧',
          selected: selectedLanguage == Languages.english,
          onSelected: () => onLanguageSelected(Languages.english),
        ),
      ],
    );
  }
}
