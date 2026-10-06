import 'dart:math' as math;

import 'package:equatable/equatable.dart';

class ChatPageResponse<T> extends Equatable {
  const ChatPageResponse({
    required this.count,
    required this.next,
    required this.previous,
    required this.results,
    required this.page,
    required this.pageSize,
  });

  factory ChatPageResponse.fromJson(
    Map<String, dynamic> json, {
    required T Function(Map<String, dynamic> json) itemFromJson,
    required int page,
    required int pageSize,
  }) {
    final List<T> results = (json['results'] as List? ?? const [])
        .whereType<Map>()
        .map((item) => itemFromJson(Map<String, dynamic>.from(item)))
        .toList(growable: false);
    return ChatPageResponse<T>(
      count: (json['count'] as num?)?.toInt() ?? results.length,
      next: json['next']?.toString(),
      previous: json['previous']?.toString(),
      results: results,
      page: page,
      pageSize: pageSize,
    );
  }

  final int count;
  final String? next;
  final String? previous;
  final List<T> results;
  final int page;
  final int pageSize;

  ChatPageResponse<T> copyWith({
    int? count,
    String? next,
    String? previous,
    List<T>? results,
    int? page,
    int? pageSize,
  }) {
    return ChatPageResponse<T>(
      count: count ?? this.count,
      next: next ?? this.next,
      previous: previous ?? this.previous,
      results: results ?? this.results,
      page: page ?? this.page,
      pageSize: pageSize ?? this.pageSize,
    );
  }

  Map<String, dynamic> toJson(
    Map<String, dynamic> Function(T item) itemToJson,
  ) => {
    'count': count,
    'next': next,
    'previous': previous,
    'results': results.map(itemToJson).toList(growable: false),
  };

  int get totalPages {
    if (count > 0) return math.max(1, (count / pageSize).ceil());
    return next == null ? math.max(1, page) : page + 1;
  }

  @override
  List<Object?> get props => [count, next, previous, results, page, pageSize];
}
