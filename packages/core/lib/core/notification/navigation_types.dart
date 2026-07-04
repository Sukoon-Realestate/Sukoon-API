part of 'notification_service.dart';

enum NotificationType{
  none("0", NoNavigation());

  final String id;
  final NotificationNavigation navigation;

  const NotificationType(this.id, this.navigation);
}

