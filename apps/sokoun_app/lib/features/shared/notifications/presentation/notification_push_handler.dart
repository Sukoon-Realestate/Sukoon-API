import 'package:melos_core/core/helpers/user_type/user_enum.dart';
import 'package:melos_core/core/helpers/user_type/user_type_helper.dart';
import 'package:melos_core/core/navigation/navigator.dart';

import '../data/enums/app_notification_kind.dart';
import '../data/enums/notification_role.dart';
import '../data/models/app_notification_content.dart';
import 'notification_navigation.dart';
import 'screens/notification_detail_screen.dart';
import 'screens/notifications_screen.dart';

abstract final class NotificationPushHandler {
  static Future<void> handle(Map<String, dynamic> payload) async {
    final NotificationRole role =
        UserTypeHelper.instance.currentUserType.isOwner
        ? NotificationRole.owner
        : NotificationRole.tenant;
    final AppNotificationContent notification =
        AppNotificationContent.fromPushPayload(payload);

    if (notification.primaryActionType.isNotEmpty ||
        notification.kind != AppNotificationKind.unknown) {
      await NotificationNavigation.open(notification: notification, role: role);
      return;
    }

    if (notification.id.isNotEmpty) {
      await Go.to<void>(
        NotificationDetailScreen(role: role, notification: notification),
      );
      return;
    }

    await Go.to<void>(NotificationsScreen(role: role));
  }
}
