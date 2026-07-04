abstract class NamesHelper {
  static final RegExp validCharactersPattern = RegExp(r"^[A-Za-z0-9_\s\?'']+$");
  static final RegExp shortKey = RegExp(r'#\$');

  static String toSnakeCase(String input) {
    // Replace all non-alphanumeric characters (except underscore) with underscores

    String snakeCase =
        input.replaceAll(RegExp(r'[^\w\s]'), '').replaceAll(' ', '_');
    // Check if input String needs to be converted to snake case
    if (!snakeCase.contains('_')) {
      final String snakeWithoutUnderscore = snakeCase;
      if (isCamelCase(snakeWithoutUnderscore)) {
        snakeCase = camelToSnakeCase(snakeWithoutUnderscore);
      }
      if (isClassCase(snakeWithoutUnderscore)) {
        snakeCase = classToSnakeCase(snakeWithoutUnderscore);
      }
    }

    // Remove leading and trailing underscores
    return snakeCase.trim().replaceAll(RegExp(r'\s+'), '_').toLowerCase();
  }

  static bool isSnakeCase(String input) {
    return RegExp(r'^[a-z]+(?:_[a-z0-9]+)*$').hasMatch(input);
  }

  static bool isCamelCase(String input) {
    return RegExp(r'^[a-z]+(?:[A-Z][a-z0-9]*)*$').hasMatch(input);
  }

  static bool isClassCase(String input) {
    return RegExp(r'^[A-Z][a-zA-Z0-9]*$').hasMatch(input);
  }

  static String snakeToCamelCase(String input) {
    final List<String> parts = input.replaceAll('?', '').split('_');
    String camelCase = parts[0];
    for (int i = 1; i < parts.length; i++) {
      camelCase += parts[i][0].toUpperCase() + parts[i].substring(1);
    }

    return camelCase;
  }

  static String snakeToClassCase(String input) {
    return camelToClassCase(snakeToCamelCase(input));
  }

  static String camelToSnakeCase(String input) {
    String snakeCase = '';
    for (int i = 0; i < input.length; i++) {
      final String currentChar = input[i];
      if (currentChar == currentChar.toUpperCase()) {
        if (i != 0) {
          snakeCase += '_';
        }
        snakeCase += currentChar.toLowerCase();
      } else {
        snakeCase += currentChar;
      }
    }
    return snakeCase;
  }

  static String camelToClassCase(String input) {
    return input[0].toUpperCase() + input.substring(1);
  }

  static String classToCamelCase(String input) {
    return input[0].toLowerCase() + input.substring(1);
  }

  static String classToSnakeCase(String input) {
    return camelToSnakeCase(classToCamelCase(input));
  }
}
