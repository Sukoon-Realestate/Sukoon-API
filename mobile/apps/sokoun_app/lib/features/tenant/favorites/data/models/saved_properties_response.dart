import 'package:equatable/equatable.dart';
import 'package:sokoun_app/features/tenant/favorites/data/models/favorites_content.dart';

class SavedPropertiesResponse extends Equatable {
  const SavedPropertiesResponse({
    required this.count,
    required this.perPage,
    required this.totalPages,
    required this.results,
  });

  const SavedPropertiesResponse.initial()
    : count = 0,
      perPage = 9,
      totalPages = 1,
      results = const [];

  factory SavedPropertiesResponse.fromJson(Map<String, dynamic> json) {
    final List<dynamic> rawResults = json['results'] as List? ?? const [];
    return SavedPropertiesResponse(
      count: (json['count'] as num?)?.toInt() ?? 0,
      perPage: (json['per_page'] as num?)?.toInt() ?? 9,
      totalPages: (json['total_pages'] as num?)?.toInt() ?? 1,
      results: rawResults
          .whereType<Map>()
          .map(
            (item) => FavoritePropertyContent.fromJson(
              Map<String, dynamic>.from(item),
            ),
          )
          .toList(growable: false),
    );
  }

  final int count;
  final int perPage;
  final int totalPages;
  final List<FavoritePropertyContent> results;

  Map<String, dynamic> toJson() => {
    'count': count,
    'per_page': perPage,
    'total_pages': totalPages,
    'results': results.map((item) => item.toJson()).toList(growable: false),
  };

  SavedPropertiesResponse copyWith({
    int? count,
    int? perPage,
    int? totalPages,
    List<FavoritePropertyContent>? results,
  }) {
    return SavedPropertiesResponse(
      count: count ?? this.count,
      perPage: perPage ?? this.perPage,
      totalPages: totalPages ?? this.totalPages,
      results: results ?? this.results,
    );
  }

  @override
  List<Object?> get props => [count, perPage, totalPages, results];
}
