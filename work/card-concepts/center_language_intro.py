from pathlib import Path
p=Path('/Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/lib/features/shared/profile/presentation/widgets/language_selection/language_selection_intro.dart')
p.write_text('''part of '../../../imports.dart';

class LanguageSelectionIntro extends StatelessWidget {
  const LanguageSelectionIntro({super.key});
  @override
  Widget build(BuildContext context) => Column(
    mainAxisSize: MainAxisSize.min,
    crossAxisAlignment: CrossAxisAlignment.stretch,
    children: [
      AppText(
        LocaleKeys.uiLanguageTitle,
        textAlign: TextAlign.center,
        style: Theme.of(context).textTheme.titleLarge,
      ),
      const SizedBox(height: 8),
      AppText(
        LocaleKeys.languageSelectionSubtitle,
        textAlign: TextAlign.center,
        style: Theme.of(context).textTheme.bodyMedium?.copyWith(
          color: Theme.of(context).colorScheme.onSurfaceVariant,
          height: 1.5,
        ),
      ),
    ],
  );
}
''')
