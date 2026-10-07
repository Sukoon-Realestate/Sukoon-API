import 'dart:convert';

Map<String, dynamic> rentalMap(Object? value) {
  if (value is Map) return Map<String, dynamic>.from(value);
  if (value is String) {
    try {
      final decoded = jsonDecode(value);
      if (decoded is Map) return Map<String, dynamic>.from(decoded);
    } on FormatException {
      return const {};
    }
  }
  return const {};
}

List<Map<String, dynamic>> rentalMaps(Object? value) => value is List
    ? value.whereType<Map>().map(rentalMap).toList(growable: false)
    : const [];

List<String> rentalStrings(Object? value) => value is List
    ? value.whereType<String>().toList(growable: false)
    : const [];

int rentalInt(Object? value) => int.tryParse('$value') ?? 0;
