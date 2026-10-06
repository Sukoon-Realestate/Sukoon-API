part of 'notification_service.dart';

/// Normalized notification data from either an API response or an FCM message.
///
/// API responses put action fields inside `data`, while [RemoteMessage.data]
/// exposes those fields directly. This model accepts both representations.
class NotificationPayload {
  NotificationPayload._({
    required this.notificationType,
    required this.actionType,
    required this.iconType,
    required this.title,
    required this.body,
    required this.category,
    required this.actionLabel,
    required this.visitId,
    required this.propertyId,
    required this.chatId,
    required this.senderId,
    required this.senderName,
    required this.tenantName,
    required this.visitDate,
    required this.visitTime,
    required this.appointmentDate,
    required this.appointmentTime,
    required this.address,
    required this.viewsCount,
    required this.promoUrl,
    required this.data,
  });

  factory NotificationPayload.fromMap(Map<String, dynamic> payload) {
    final Map<String, dynamic> root = Map<String, dynamic>.from(payload);
    final Map<String, dynamic> nestedData = _notificationMap(root['data']);
    final Map<String, dynamic> notification = _notificationMap(
      root['notification'],
    );
    final Map<String, dynamic> data = <String, dynamic>{...root, ...nestedData}
      ..remove('data');

    final NotificationType notificationType = NotificationType.fromValue(
      data['notification_type'] ?? data['type'],
    );
    final NotificationActionType parsedAction =
        NotificationActionType.fromValue(data['action_type']);
    final NotificationIconType parsedIcon = NotificationIconType.fromValue(
      data['icon_type'],
    );

    return NotificationPayload._(
      notificationType: notificationType,
      actionType: parsedAction == NotificationActionType.unknown
          ? notificationType.actionType
          : parsedAction,
      iconType: parsedIcon == NotificationIconType.unknown
          ? notificationType.iconType
          : parsedIcon,
      title: _notificationString(data['title'] ?? notification['title']),
      body: _notificationString(
        data['body'] ?? data['description'] ?? notification['body'],
      ),
      category: _notificationString(data['category']).isEmpty
          ? notificationType.category
          : _notificationString(data['category']),
      actionLabel: _notificationString(data['action_label']),
      visitId: _notificationString(data['visit_id']),
      propertyId: _notificationString(data['property_id']),
      chatId: _notificationString(data['conversation_id'] ?? data['chat_id']),
      senderId: _notificationString(data['sender_id']),
      senderName: _notificationString(data['sender_name']),
      tenantName: _notificationString(data['tenant_name']),
      visitDate: _notificationString(data['visit_date']),
      visitTime: _notificationString(data['visit_time']),
      appointmentDate: _notificationString(data['appointment_date']),
      appointmentTime: _notificationString(data['appointment_time']),
      address: _notificationString(data['address']),
      viewsCount: _notificationInt(data['views_count']),
      promoUrl: _notificationString(data['promo_url']),
      data: Map<String, dynamic>.unmodifiable(data),
    );
  }

  factory NotificationPayload.fromRemoteMessage(RemoteMessage message) {
    return NotificationPayload.fromMap(<String, dynamic>{
      ...message.data,
      if (message.notification?.title != null)
        'title': message.notification!.title,
      if (message.notification?.body != null)
        'body': message.notification!.body,
    });
  }

  final NotificationType notificationType;
  final NotificationActionType actionType;
  final NotificationIconType iconType;
  final String title;
  final String body;
  final String category;
  final String actionLabel;
  final String visitId;
  final String propertyId;
  final String chatId;
  final String senderId;
  final String senderName;
  final String tenantName;
  final String visitDate;
  final String visitTime;
  final String appointmentDate;
  final String appointmentTime;
  final String address;
  final int viewsCount;
  final String promoUrl;

  /// The flattened source data, with nested `data` values taking precedence.
  final Map<String, dynamic> data;

  bool get isKnown => notificationType != NotificationType.unknown;

  Map<String, dynamic> toDataMap() => <String, dynamic>{
    ...data,
    'notification_type': notificationType.id,
    'action_type': actionType.id,
    'icon_type': iconType.id,
    if (title.isNotEmpty) 'title': title,
    if (body.isNotEmpty) 'body': body,
    if (category.isNotEmpty) 'category': category,
    if (actionLabel.isNotEmpty) 'action_label': actionLabel,
    if (visitId.isNotEmpty) 'visit_id': visitId,
    if (propertyId.isNotEmpty) 'property_id': propertyId,
    if (chatId.isNotEmpty) 'chat_id': chatId,
    if (senderId.isNotEmpty) 'sender_id': senderId,
    if (senderName.isNotEmpty) 'sender_name': senderName,
    if (tenantName.isNotEmpty) 'tenant_name': tenantName,
    if (visitDate.isNotEmpty) 'visit_date': visitDate,
    if (visitTime.isNotEmpty) 'visit_time': visitTime,
    if (appointmentDate.isNotEmpty) 'appointment_date': appointmentDate,
    if (appointmentTime.isNotEmpty) 'appointment_time': appointmentTime,
    if (address.isNotEmpty) 'address': address,
    if (viewsCount > 0) 'views_count': viewsCount,
    if (promoUrl.isNotEmpty) 'promo_url': promoUrl,
  };
}

Map<String, dynamic> _notificationMap(Object? value) {
  if (value is Map) {
    return value.map(
      (Object? key, Object? value) => MapEntry(key.toString(), value),
    );
  }
  if (value is String && value.trim().isNotEmpty) {
    try {
      final Object? decoded = jsonDecode(value);
      if (decoded is Map) {
        return decoded.map(
          (Object? key, Object? value) => MapEntry(key.toString(), value),
        );
      }
    } on FormatException {
      return const <String, dynamic>{};
    }
  }
  return const <String, dynamic>{};
}

String _notificationString(Object? value) => value?.toString().trim() ?? '';

int _notificationInt(Object? value) {
  if (value is num) return value.toInt();
  return int.tryParse(_notificationString(value)) ?? 0;
}
