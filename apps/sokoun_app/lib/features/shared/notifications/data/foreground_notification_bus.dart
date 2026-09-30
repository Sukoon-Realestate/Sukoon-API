import 'dart:async';

import 'package:melos_core/core/network/account_session.dart';
import 'package:melos_core/core/shared/models/user_models/user_model.dart';

import 'models/app_notification_content.dart';

/// Foreground deliveries update badges locally; read actions use the refresh bus.
abstract final class ForegroundNotificationBus {
  static final StreamController<AppNotificationContent> _controller =
      StreamController<AppNotificationContent>.broadcast(sync: true);
  static final Set<String> _receivedIds = {};
  static int _sessionGeneration = AccountSession.generation;

  static Stream<AppNotificationContent> get stream => _controller.stream;

  static void receive(Map<String, dynamic> payload, {String? deliveryId}) {
    if (!UserModel.isAuthenticated) return;
    if (_sessionGeneration != AccountSession.generation) {
      _sessionGeneration = AccountSession.generation;
      _receivedIds.clear();
    }
    final AppNotificationContent notification =
        AppNotificationContent.fromPushPayload(payload);
    final String id = notification.id.isNotEmpty
        ? 'notification:${notification.id}'
        : deliveryId == null
        ? ''
        : 'delivery:$deliveryId';
    if (id.isNotEmpty) {
      if (!_receivedIds.add(id)) return;
      if (_receivedIds.length > 200) _receivedIds.remove(_receivedIds.first);
    }
    _controller.add(notification);
  }
}
