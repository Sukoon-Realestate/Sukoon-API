import 'dart:convert';
import '../../config/language/languages.dart';

class ReadCachePolicy {
  const ReadCachePolicy({
    this.persist = true,
    this.publicContent = false,
    this.maxAge = const Duration(days: 7),
  });
  final bool persist;
  final bool publicContent;
  final Duration maxAge;
  static const privateMemory = ReadCachePolicy(persist: false);
  static const publicListing = ReadCachePolicy(publicContent: true);
  static const catalog = ReadCachePolicy(
    publicContent: true,
    maxAge: Duration(days: 30),
  );
}

abstract final class ReadCacheContext {
  static String environment = 'unconfigured';
  static String get scope =>
      jsonEncode([environment, Languages.currentLanguage.locale.languageCode]);
}
