import 'package:equatable/equatable.dart';

class UnreadNotificationsContent extends Equatable {
  const UnreadNotificationsContent({required this.count});

  const UnreadNotificationsContent.initial() : count = 0;

  factory UnreadNotificationsContent.fromJson(Map<String, dynamic> json) {
    return UnreadNotificationsContent(
      count:
          ((json['unread_notifications_count'] ?? json['unread_count']) as num?)
              ?.toInt() ??
          0,
    );
  }

  final int count;

  Map<String, dynamic> toJson() => {'unread_count': count};

  UnreadNotificationsContent copyWith({int? count}) {
    return UnreadNotificationsContent(count: count ?? this.count);
  }

  @override
  List<Object?> get props => [count];
}
