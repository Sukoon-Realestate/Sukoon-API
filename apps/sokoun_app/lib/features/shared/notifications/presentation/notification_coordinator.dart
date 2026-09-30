import 'dart:async';
import 'dart:developer' show log;

import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/notification/notification_service.dart';

import '../data/notification_device_data.dart';
import '../data/foreground_notification_bus.dart';
import 'notification_push_handler.dart';

abstract final class NotificationCoordinator {
  static Future<void>? _pushSetup;

  static Future<void> start() async {
    // Registration may wait on the API; it must not delay launch dialogs.
    unawaited(NotificationDeviceData.start());
    await (_pushSetup ??= _setupPushNotifications());
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
          ForegroundNotificationBus.receive(
            message.data,
            deliveryId: message.messageId,
          );
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
