Map<String, dynamic> ownerVisitJsonMap(Object? value) {
  return value is Map ? value.cast<String, dynamic>() : const {};
}

String ownerVisitString(Object? value) => value?.toString().trim() ?? '';
