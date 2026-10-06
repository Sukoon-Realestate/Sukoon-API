Map<String, dynamic> supportMap(Object? value) =>
    value is Map ? Map<String, dynamic>.from(value) : const {};

List<T> supportList<T>(
  Object? value,
  T Function(Map<String, dynamic>) mapper,
) => value is List
    ? List.unmodifiable(
        value.whereType<Map>().map((item) => mapper(supportMap(item))),
      )
    : const [];

int supportInt(Object? value, {int fallback = 0}) =>
    (value is num ? value.toInt() : int.tryParse('$value')) ?? fallback;
