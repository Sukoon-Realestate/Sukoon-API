import 'package:equatable/equatable.dart';
import 'tenant_visit_content.dart';

class TenantVisitsResponse extends Equatable {
  const TenantVisitsResponse({
    required this.totalPages,
    required this.perPage,
    required this.results,
  });

  const TenantVisitsResponse.initial()
    : totalPages = 1,
      perPage = 20,
      results = const [];

  factory TenantVisitsResponse.fromJson(Map<String, dynamic> json) {
    final List<dynamic> rawResults = json['results'] as List? ?? const [];
    return TenantVisitsResponse(
      totalPages: (json['total_pages'] as num?)?.toInt() ?? 1,
      perPage: (json['per_page'] as num?)?.toInt() ?? 20,
      results: rawResults
          .whereType<Map>()
          .map(
            (item) =>
                TenantVisitContent.fromJson(Map<String, dynamic>.from(item)),
          )
          .toList(growable: false),
    );
  }

  final int totalPages;
  final int perPage;
  final List<TenantVisitContent> results;

  Map<String, dynamic> toJson() => {
    'total_pages': totalPages,
    'per_page': perPage,
    'results': results.map((item) => item.toJson()).toList(growable: false),
  };

  TenantVisitsResponse copyWith({
    int? totalPages,
    int? perPage,
    List<TenantVisitContent>? results,
  }) {
    return TenantVisitsResponse(
      totalPages: totalPages ?? this.totalPages,
      perPage: perPage ?? this.perPage,
      results: results ?? this.results,
    );
  }

  @override
  List<Object?> get props => [totalPages, perPage, results];
}
