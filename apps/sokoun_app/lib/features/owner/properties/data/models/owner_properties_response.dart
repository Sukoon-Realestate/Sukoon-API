part of '../../imports.dart';

class OwnerPropertiesResponse extends Equatable {
  const OwnerPropertiesResponse({
    required this.count,
    required this.results,
    this.next,
    this.previous,
  });

  const OwnerPropertiesResponse.initial()
    : count = 0,
      results = const [],
      next = null,
      previous = null;

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

  Map<String, dynamic> toJson() => {
    'count': count,
    'next': next,
    'previous': previous,
    'results': results.map((property) => property.toJson()).toList(),
  };

  OwnerPropertiesResponse copyWith({
    int? count,
    String? next,
    String? previous,
    List<OwnerPropertyContent>? results,
  }) {
    return OwnerPropertiesResponse(
      count: count ?? this.count,
      next: next ?? this.next,
      previous: previous ?? this.previous,
      results: results ?? this.results,
    );
  }

  @override
  List<Object?> get props => [count, next, previous, results];
}
