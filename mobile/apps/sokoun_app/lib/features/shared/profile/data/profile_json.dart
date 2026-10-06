Map<String, dynamic> profileJsonMap(Object? value) {
  if (value is Map<String, dynamic>) return value;
  if (value is Map) return Map<String, dynamic>.from(value);
  return const {};
}

String profileString(Object? value) => value?.toString().trim() ?? '';

String? profileNullableString(Object? value) {
  final String normalized = profileString(value);
  return normalized.isEmpty ? null : normalized;
}

int profileInt(Object? value) =>
    value is num ? value.toInt() : int.tryParse(profileString(value)) ?? 0;

double profileDouble(Object? value) => value is num
    ? value.toDouble()
    : double.tryParse(profileString(value)) ?? 0;
