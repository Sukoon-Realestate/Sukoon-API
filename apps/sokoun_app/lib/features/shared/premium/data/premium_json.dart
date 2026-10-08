import 'dart:convert';
import 'package:melos_core/config/language/languages.dart';

Map<String, dynamic> premiumMap(Object? value) =>
    value is Map ? Map<String, dynamic>.from(value) : const {};
String premiumString(Object? value) =>
    value is String || value is num ? value.toString() : '';
int? premiumInt(Object? value) => value is int
    ? value
    : value is String
    ? int.tryParse(value)
    : null;
DateTime? premiumDate(Object? value) {
  final text = premiumString(value);
  final match = RegExp(r'^(\d{4})-(\d{2})-(\d{2})(?:T.*)?$').firstMatch(text);
  if (match == null) return null;
  final year = int.parse(match[1]!),
      month = int.parse(match[2]!),
      day = int.parse(match[3]!);
  final calendar = DateTime.utc(year, month, day);
  if (calendar.year != year || calendar.month != month || calendar.day != day) {
    return null;
  }
  return DateTime.tryParse(text);
}

List<Map<String, dynamic>> premiumMaps(Object? value) => value is List
    ? value.whereType<Map>().map(premiumMap).toList(growable: false)
    : const [];
String premiumCacheKey(String name, Iterable<Object?> dimensions) =>
    'features_v1_${name}_${base64Url.encode(utf8.encode(jsonEncode([Languages.currentLanguage.locale.languageCode, ...dimensions])))}';
