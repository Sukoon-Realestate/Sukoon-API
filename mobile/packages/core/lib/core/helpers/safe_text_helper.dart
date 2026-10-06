import 'package:safe_text/safe_text.dart';
import '../../config/language/locale_keys.g.dart';

class SafeTextHelper {
  static const List<String> allowedWords = ['الله'];

  static Future<void> init() async {
    await SafeTextFilter.init(languages: [Language.english, Language.arabic]);
  }

  static Future<bool> containsBadWord(String text) =>
      SafeTextFilter.containsBadWord(text: text, excludedWords: allowedWords);

  static String filterText(String text) => SafeTextFilter.filterText(
        text: text,
        excludedWords: allowedWords,
        strategy: MaskStrategy.custom(replacement: '[${LocaleKeys.dissenter}]'),
      );
}