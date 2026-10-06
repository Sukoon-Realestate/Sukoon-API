import '../data/models/app_notification_content.dart';
import 'notification_navigation.dart';

abstract final class NotificationPushHandler {
  static Future<void> handle(Map<String, dynamic> payload) async {
    final AppNotificationContent notification =
        AppNotificationContent.fromPushPayload(payload);

    await NotificationNavigation.open(notification: notification);
  }
}
