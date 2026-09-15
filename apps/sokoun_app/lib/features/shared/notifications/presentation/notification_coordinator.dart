import 'dart:async';
import 'dart:developer' show log;

import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/notification/notification_service.dart';

import '../data/notification_device_data.dart';
import '../data/notification_refresh_bus.dart';
import '../../chat/data/chat_unread_refresh_bus.dart';
import 'notification_push_handler.dart';

abstract final class NotificationCoordinator {
  static Future<void>? _pushSetup;

  static Future<void> start() async {
    await Future.wait([
      _pushSetup ??= _setupPushNotifications(),
      NotificationDeviceData.start(),
    ]);
  }

  static Future<void> _setupPushNotifications() async {
    try {
      final NotificationService notificationService =
          injector<NotificationService>();
      NotificationNavigator(
        onRoutingMessage: (message) {
          unawaited(
            NotificationPushHandler.handle({
              ...message.data,
              'title': message.notification?.title,
              'body': message.notification?.body,
            }),
          );
        },
        onNoInitialMessage: () {},
      );
      await notificationService.setupNotifications(
        onForegroundMessage: (message) {
          NotificationRefreshBus.requestRefresh();
          final String type =
              message.data['notification_type']?.toString() ?? '';
          final String category = message.data['category']?.toString() ?? '';
          if (type == 'new_message' || category == 'chat') {
            ChatUnreadRefreshBus.requestRefresh();
          }
        },
      );
    } catch (error, stackTrace) {
      log(
        'Unable to initialize push notifications.',
        error: error,
        stackTrace: stackTrace,
      );
      _pushSetup = null;
    }
  }
}
