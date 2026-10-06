Map<String, dynamic> visitJsonMap(Object? value) =>
    value is Map ? Map<String, dynamic>.from(value) : const {};
