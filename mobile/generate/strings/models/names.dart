import '../../utils/exceptions.dart';
import '../../utils/names_helper.dart';

class Names {
  String original;
  String camelCase;
  String snakeCase;
  String classCase;

  Names({
    required this.original,
    required this.camelCase,
    required this.snakeCase,
    required this.classCase,
  });

  factory Names.fromString(String input) {
    String original = input.trim();

    String snakeCase = '';
    if (NamesHelper.shortKey.hasMatch(input)) {
      snakeCase = NamesHelper.toSnakeCase(original.split('#\$').first.trim());
      original = original.split('#\$').last.trim();
    } else {
      snakeCase = NamesHelper.toSnakeCase(original);
    }
    if (!NamesHelper.validCharactersPattern.hasMatch(original) ||
        original.isEmpty) {
      throw NamesException('Invalid name: "$input"');
    }

    try {
      final String camelCase =
          NamesHelper.snakeToCamelCase(NamesHelper.toSnakeCase(original));
      final String classCase = NamesHelper.camelToClassCase(camelCase);

      return Names(
        original: original,
        snakeCase: snakeCase,
        camelCase: camelCase,
        classCase: classCase,
      );
    } catch (e) {
      throw NamesException('Invalid name: "$input"');
    }
  }
}
