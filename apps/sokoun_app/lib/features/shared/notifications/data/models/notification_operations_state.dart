import 'package:equatable/equatable.dart';

class NotificationOperationsState extends Equatable {
  const NotificationOperationsState({
    required this.unreadCount,
    required this.pendingNotificationIds,
    required this.isMarkingAll,
  });

  const NotificationOperationsState.initial()
    : unreadCount = 0,
      pendingNotificationIds = const {},
      isMarkingAll = false;

  factory NotificationOperationsState.fromJson(Map<String, dynamic> json) {
    return NotificationOperationsState(
      unreadCount: (json['unread_count'] as num?)?.toInt() ?? 0,
      pendingNotificationIds:
          (json['pending_notification_ids'] as List? ?? const [])
              .map((id) => id.toString())
              .toSet(),
      isMarkingAll: json['is_marking_all'] == true,
    );
  }

  final int unreadCount;
  final Set<String> pendingNotificationIds;
  final bool isMarkingAll;

  NotificationOperationsState copyWith({
    int? unreadCount,
    Set<String>? pendingNotificationIds,
    bool? isMarkingAll,
  }) {
    return NotificationOperationsState(
      unreadCount: unreadCount ?? this.unreadCount,
      pendingNotificationIds:
          pendingNotificationIds ?? this.pendingNotificationIds,
      isMarkingAll: isMarkingAll ?? this.isMarkingAll,
    );
  }

  Map<String, dynamic> toJson() => {
    'unread_count': unreadCount,
    'pending_notification_ids': pendingNotificationIds.toList(growable: false),
    'is_marking_all': isMarkingAll,
  };

  @override
  List<Object?> get props => [
    unreadCount,
    pendingNotificationIds,
    isMarkingAll,
  ];
}
