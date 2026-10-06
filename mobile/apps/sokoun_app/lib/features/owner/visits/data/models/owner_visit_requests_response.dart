import 'package:equatable/equatable.dart';

import 'owner_visit_request_content.dart';

class OwnerVisitRequestsResponse extends Equatable {
  const OwnerVisitRequestsResponse({
    required this.count,
    required this.results,
    this.next,
    this.tabs = const {},
  });

  const OwnerVisitRequestsResponse.initial()
    : count = 0,
      next = null,
      results = const [],
      tabs = const {};

  factory OwnerVisitRequestsResponse.fromJson(dynamic json) {
    final Map<String, dynamic> data = json is Map<String, dynamic>
        ? json
        : const {};
    final List<OwnerVisitRequestContent> results =
        OwnerVisitRequestContent.listFromResponse(json);
    final Object? rawTabs = data['tabs'];
    return OwnerVisitRequestsResponse(
      count: (data['count'] as num?)?.toInt() ?? results.length,
      next: data['next'] as String?,
      results: results,
      tabs: rawTabs is Map
          ? {
              for (final entry in rawTabs.entries)
                if (entry.value is num)
                  entry.key.toString(): (entry.value as num).toInt(),
            }
          : const {},
    );
  }

  final int count;
  final String? next;
  final List<OwnerVisitRequestContent> results;
  final Map<String, int> tabs;

  Map<String, dynamic> toJson() => {
    'count': count,
    'next': next,
    'results': results
        .map((request) => request.toJson())
        .toList(growable: false),
    'tabs': tabs,
  };

  OwnerVisitRequestsResponse copyWith({
    int? count,
    String? next,
    List<OwnerVisitRequestContent>? results,
    Map<String, int>? tabs,
  }) => OwnerVisitRequestsResponse(
    count: count ?? this.count,
    next: next ?? this.next,
    results: results ?? this.results,
    tabs: tabs ?? this.tabs,
  );

  @override
  List<Object?> get props => [count, next, results, tabs];
}
