part of 'imports_constants.dart';

extension RouterExtension on BuildContext {
  Object? get arg => ModalRoute.of(this)?.settings.arguments;
  Map<String, dynamic>? get arguments =>
      ModalRoute.of(this)?.settings.arguments as Map<String, dynamic>?;
}
