import 'package:equatable/equatable.dart';

import 'app_notification_content.dart';

class NotificationsResponse extends Equatable {
  const NotificationsResponse({
    required this.perPage,
    required this.totalPages,
    required this.unreadCount,
    required this.results,
  });

  const NotificationsResponse.initial()
    : perPage = 20,
      totalPages = 1,
      unreadCount = 0,
      results = const [];

  factory NotificationsResponse.fromJson(Map<String, dynamic> json) {
    final List<dynamic> rawResults = json['results'] as List? ?? const [];
    return NotificationsResponse(
      perPage: (json['per_page'] as num?)?.toInt() ?? 20,
      totalPages: (json['total_pages'] as num?)?.toInt() ?? 1,
      unreadCount: (json['unread_count'] as num?)?.toInt() ?? 0,
      results: rawResults
          .whereType<Map>()
          .map(
            (item) => AppNotificationContent.fromJson(
              Map<String, dynamic>.from(item),
            ),
          )
          .toList(growable: false),
    );
  }

  final int perPage;
  final int totalPages;
  final int unreadCount;
  final List<AppNotificationContent> results;

  Map<String, dynamic> toJson() => {
    'per_page': perPage,
    'total_pages': totalPages,
    'unread_count': unreadCount,
    'results': results.map((item) => item.toJson()).toList(growable: false),
  };

  NotificationsResponse copyWith({
    int? perPage,
    int? totalPages,
    int? unreadCount,
    List<AppNotificationContent>? results,
  }) {
    return NotificationsResponse(
      perPage: perPage ?? this.perPage,
      totalPages: totalPages ?? this.totalPages,
      unreadCount: unreadCount ?? this.unreadCount,
      results: results ?? this.results,
    );
  }

  @override
  List<Object?> get props => [perPage, totalPages, unreadCount, results];
}
