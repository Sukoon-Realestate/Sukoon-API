import 'package:melos_core/core/navigation/navigator.dart';
import '../data/enums/notification_role.dart';
import '../data/models/app_notification_content.dart';
import '../../destinations/data/destination_resolver.dart';
import '../../destinations/presentation/destination_navigation.dart';

abstract final class NotificationNavigation {
  static Future<void> open({
    required AppNotificationContent notification,
    NotificationRole? role,
  }) async {
    if (notification.primaryActionType == 'dismiss') {
      Go.back();
      return;
    }
    await DestinationNavigation.open(
      DestinationResolver.notification(notification),
      notification: notification,
    );
  }
}
