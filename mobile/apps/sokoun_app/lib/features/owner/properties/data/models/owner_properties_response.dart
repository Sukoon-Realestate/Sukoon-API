import 'owner_property_content.dart';
import '../owner_property_json.dart';
import 'package:equatable/equatable.dart';

class OwnerPropertiesResponse extends Equatable {
  const OwnerPropertiesResponse({
    required this.count,
    required this.results,
    this.perPage = defaultPerPage,
    this.totalPages = 1,
    this.next,
    this.previous,
  });

  const OwnerPropertiesResponse.initial()
    : count = 0,
      perPage = defaultPerPage,
      totalPages = 1,
      results = const [],
      next = null,
      previous = null;

  factory OwnerPropertiesResponse.fromJson(Map<String, dynamic> json) {
    final int count = ownerPropertyNumber(json['count']).toInt();
    final int parsedPerPage = ownerPropertyNumber(json['per_page']).toInt();
    final int perPage = parsedPerPage > 0 ? parsedPerPage : defaultPerPage;
    final int parsedTotalPages = ownerPropertyNumber(
      json['total_pages'],
    ).toInt();
    return OwnerPropertiesResponse(
      count: count,
      perPage: perPage,
      totalPages: parsedTotalPages > 0
          ? parsedTotalPages
          : count > 0
          ? (count + perPage - 1) ~/ perPage
          : 1,
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

  static const int defaultPerPage = 10;

  final int count;
  final int perPage;
  final int totalPages;
  final String? next;
  final String? previous;
  final List<OwnerPropertyContent> results;

  Map<String, dynamic> toJson() => {
    'count': count,
    'per_page': perPage,
    'total_pages': totalPages,
    'next': next,
    'previous': previous,
    'results': results.map((property) => property.toJson()).toList(),
  };

  OwnerPropertiesResponse copyWith({
    int? count,
    int? perPage,
    int? totalPages,
    String? next,
    String? previous,
    List<OwnerPropertyContent>? results,
  }) {
    return OwnerPropertiesResponse(
      count: count ?? this.count,
      perPage: perPage ?? this.perPage,
      totalPages: totalPages ?? this.totalPages,
      next: next ?? this.next,
      previous: previous ?? this.previous,
      results: results ?? this.results,
    );
  }

  @override
  List<Object?> get props => [
    count,
    perPage,
    totalPages,
    next,
    previous,
    results,
  ];
}
