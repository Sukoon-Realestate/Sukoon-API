part of '../../imports.dart';

class OwnerPropertiesResponse {
  const OwnerPropertiesResponse({
    required this.count,
    required this.results,
    this.next,
    this.previous,
  });

  factory OwnerPropertiesResponse.fromJson(Map<String, dynamic> json) {
    return OwnerPropertiesResponse(
      count: (json['count'] as num?)?.toInt() ?? 0,
      next: json['next'] as String?,
      previous: json['previous'] as String?,
      results:
          (json['results'] as List?)
              ?.whereType<Map<String, dynamic>>()
              .map(OwnerPropertyContent.fromJson)
              .toList(growable: false) ??
          const [],
    );
  }

  final int count;
  final String? next;
  final String? previous;
  final List<OwnerPropertyContent> results;
}
