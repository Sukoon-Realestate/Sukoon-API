import 'package:equatable/equatable.dart';

import '../enums/app_notification_icon_kind.dart';
import '../enums/app_notification_kind.dart';
import 'notification_action_content.dart';
import 'notification_appointment_content.dart';
import 'notification_payload_content.dart';

class AppNotificationContent extends Equatable {
  const AppNotificationContent({
    required this.id,
    required this.kind,
    required this.iconType,
    required this.title,
    required this.description,
    required this.time,
    required this.category,
    required this.isRead,
    required this.createdAt,
    required this.formattedTime,
    required this.payload,
    required this.actions,
    this.appointmentDetails,
    this.readAt = '',
  });

  const AppNotificationContent.initial()
    : id = '',
      kind = AppNotificationKind.unknown,
      iconType = AppNotificationIconKind.unknown,
      title = '',
      description = '',
      time = '',
      category = '',
      isRead = false,
      createdAt = '',
      readAt = '',
      formattedTime = '',
      payload = const NotificationPayloadContent.initial(),
      actions = const NotificationActionsContent.initial(),
      appointmentDetails = null;

  factory AppNotificationContent.fromJson(Map<String, dynamic> json) {
    final Map<String, dynamic> payload = _jsonMap(json['data']);
    final Map<String, dynamic> actions = _jsonMap(json['actions']);
    final Map<String, dynamic> appointment = _jsonMap(
      json['appointment_details'],
    );
    final String notificationType =
        json['notification_type']?.toString() ?? json['kind']?.toString() ?? '';

    return AppNotificationContent(
      id: json['id']?.toString() ?? '',
      kind: AppNotificationKind.fromApiValue(notificationType),
      iconType: AppNotificationIconKind.fromApiValue(json['icon_type']),
      title: json['title']?.toString() ?? '',
      description:
          json['body']?.toString() ?? json['description']?.toString() ?? '',
      time: json['time_ago']?.toString() ?? json['time']?.toString() ?? '',
      category: json['category']?.toString() ?? '',
      isRead:
          _boolFromJson(json['is_read']) ||
          (json.containsKey('is_unread') && !_boolFromJson(json['is_unread'])),
      createdAt: json['created_at']?.toString() ?? '',
      readAt: json['read_at']?.toString() ?? '',
      formattedTime: json['formatted_time']?.toString() ?? '',
      payload: NotificationPayloadContent.fromJson(payload),
      actions: NotificationActionsContent.fromJson(actions),
      appointmentDetails: appointment.isEmpty
          ? null
          : NotificationAppointmentContent.fromJson(appointment),
    );
  }

  factory AppNotificationContent.fromPushPayload(Map<String, dynamic> json) {
    return AppNotificationContent(
      id: json['notification_id']?.toString() ?? '',
      kind: AppNotificationKind.fromApiValue(json['notification_type']),
      iconType: AppNotificationIconKind.fromApiValue(json['icon_type']),
      title: json['title']?.toString() ?? '',
      description: json['body']?.toString() ?? '',
      time: '',
      category: json['category']?.toString() ?? '',
      isRead: false,
      createdAt: '',
      formattedTime: '',
      payload: NotificationPayloadContent.fromJson(json),
      actions: NotificationActionsContent(
        primary: NotificationActionContent(
          label: json['action_label']?.toString() ?? '',
          actionType: json['action_type']?.toString() ?? '',
          targetId: json['target_id']?.toString() ?? '',
        ),
      ),
    );
  }

  final String id;
  final AppNotificationKind kind;
  final AppNotificationIconKind iconType;
  final String title;
  final String description;
  final String time;
  final String category;
  final bool isRead;
  final String createdAt;
  final String readAt;
  final String formattedTime;
  final NotificationPayloadContent payload;
  final NotificationActionsContent actions;
  final NotificationAppointmentContent? appointmentDetails;

  bool get isUnread => !isRead;

  AppNotificationIconKind get resolvedIconType {
    if (iconType != AppNotificationIconKind.unknown) return iconType;
    return switch (kind) {
      AppNotificationKind.visitRequest => AppNotificationIconKind.calendar,
      AppNotificationKind.visitAccepted => AppNotificationIconKind.checkCircle,
      AppNotificationKind.visitRejected => AppNotificationIconKind.cancel,
      AppNotificationKind.visitReview ||
      AppNotificationKind.promotion => AppNotificationIconKind.star,
      AppNotificationKind.newMessage => AppNotificationIconKind.chat,
      AppNotificationKind.propertyVerified => AppNotificationIconKind.verified,
      AppNotificationKind.propertyViews => AppNotificationIconKind.eye,
      AppNotificationKind.dailyBump ||
      AppNotificationKind.accountVerification =>
        AppNotificationIconKind.warning,
      AppNotificationKind.newProperty => AppNotificationIconKind.bell,
      AppNotificationKind.propertyUpdate => AppNotificationIconKind.refresh,
      AppNotificationKind.securityAlert => AppNotificationIconKind.shield,
      AppNotificationKind.unknown => AppNotificationIconKind.unknown,
    };
  }

  bool get hasDetailCard =>
      appointmentDetails?.isEmpty == false ||
      payload.appointmentDateTime.isNotEmpty ||
      payload.address.isNotEmpty;

  String get detailLabel => appointmentDetails?.title ?? '';

  String get detailDate => appointmentDetails?.dateTimeLabel.isNotEmpty == true
      ? appointmentDetails!.dateTimeLabel
      : payload.appointmentDateTime;

  String get detailLocation =>
      appointmentDetails?.locationLabel.isNotEmpty == true
      ? appointmentDetails!.locationLabel
      : payload.address;

  String get primaryActionType => actions.primary?.actionType.isNotEmpty == true
      ? actions.primary!.actionType
      : payload.actionType;

  String get primaryTargetId {
    if (actions.primary?.targetId.isNotEmpty == true) {
      return actions.primary!.targetId;
    }
    if (payload.visitId.isNotEmpty) return payload.visitId;
    if (payload.chatId.isNotEmpty) return payload.chatId;
    return payload.propertyId;
  }

  Map<String, dynamic> toJson() => {
    'id': id,
    'notification_type': kind.apiValue,
    'icon_type': resolvedIconType.apiValue,
    'title': title,
    'body': description,
    'time_ago': time,
    'category': category,
    'is_read': isRead,
    'created_at': createdAt,
    'read_at': readAt,
    'formatted_time': formattedTime,
    'data': payload.toJson(),
    'actions': actions.toJson(),
    if (appointmentDetails != null)
      'appointment_details': appointmentDetails!.toJson(),
  };

  AppNotificationContent copyWith({
    String? id,
    AppNotificationKind? kind,
    AppNotificationIconKind? iconType,
    String? title,
    String? description,
    String? time,
    String? category,
    bool? isRead,
    String? createdAt,
    String? readAt,
    String? formattedTime,
    NotificationPayloadContent? payload,
    NotificationActionsContent? actions,
    NotificationAppointmentContent? appointmentDetails,
  }) {
    return AppNotificationContent(
      id: id ?? this.id,
      kind: kind ?? this.kind,
      iconType: iconType ?? this.iconType,
      title: title ?? this.title,
      description: description ?? this.description,
      time: time ?? this.time,
      category: category ?? this.category,
      isRead: isRead ?? this.isRead,
      createdAt: createdAt ?? this.createdAt,
      readAt: readAt ?? this.readAt,
      formattedTime: formattedTime ?? this.formattedTime,
      payload: payload ?? this.payload,
      actions: actions ?? this.actions,
      appointmentDetails: appointmentDetails ?? this.appointmentDetails,
    );
  }

  @override
  List<Object?> get props => [
    id,
    kind,
    iconType,
    title,
    description,
    time,
    category,
    isRead,
    createdAt,
    readAt,
    formattedTime,
    payload,
    actions,
    appointmentDetails,
  ];
}

Map<String, dynamic> _jsonMap(Object? value) {
  if (value is! Map) return const {};
  return Map<String, dynamic>.from(value);
}

bool _boolFromJson(Object? value) {
  if (value is bool) return value;
  if (value is num) return value != 0;
  return value?.toString().toLowerCase() == 'true';
}
