part of 'notification_service.dart';

typedef NotificationRouteHandler =
    void Function(NotificationRoute route, NotificationPayload payload);

/// A destination emitted by a concrete [NotificationNavigation].
class NotificationRoute {
  const NotificationRoute._({
    required this.location,
    required this.notificationType,
    required this.actionType,
    this.isExternal = false,
  });

  final String location;
  final NotificationType notificationType;
  final NotificationActionType actionType;
  final bool isExternal;
}

class NotificationRoutes {
  static NotificationRouteHandler? _handler;

  /// Registers the app-level executor that opens screens or external URLs.
  ///
  /// Core cannot import screens from `sokoun_app`, so concrete notification
  /// navigation classes emit a route through this handler.
  static void registerHandler(NotificationRouteHandler handler) {
    _handler = handler;
  }

  static void clearHandler() {
    _handler = null;
  }

  static void navigateByType(Map<String, dynamic> data) {
    final NotificationPayload payload = NotificationPayload.fromMap(data);
    final String type = payload.notificationType.type;
    log('Notification type: $type');

    final NotificationType notificationType = type.getType;
    notificationType.navigation.navigate(data: payload.toDataMap());
  }

  static void _navigate(
    String? location, {
    required Map<String, dynamic> data,
    bool isExternal = false,
  }) {
    if (location == null || location.isEmpty || _handler == null) return;

    final NotificationPayload payload = NotificationPayload.fromMap(data);
    _handler!(
      NotificationRoute._(
        location: location,
        notificationType: payload.notificationType,
        actionType: payload.actionType,
        isExternal: isExternal,
      ),
      payload,
    );
  }
}

extension GetNotificationTypeById on String {
  NotificationType get getType {
    return NotificationType.values.firstWhere(
      (NotificationType element) => element.type == trim().toLowerCase(),
      orElse: () => NotificationType.unknown,
    );
  }
}

abstract interface class NotificationNavigation {
  void navigate({required Map<String, dynamic> data});
}

// ----------------- Visits -----------------

class VisitNavigation implements NotificationNavigation {
  const VisitNavigation();

  @override
  void navigate({required Map<String, dynamic> data}) {
    final NotificationPayload payload = NotificationPayload.fromMap(data);
    NotificationRoutes._navigate(
      _notificationRouteWithId('/visits', payload.visitId),
      data: data,
    );
  }
}

class VisitReviewNavigation implements NotificationNavigation {
  const VisitReviewNavigation();

  @override
  void navigate({required Map<String, dynamic> data}) {
    final NotificationPayload payload = NotificationPayload.fromMap(data);
    final String? route = payload.visitId.isNotEmpty
        ? _notificationRouteWithId('/visits', payload.visitId, suffix: 'review')
        : _notificationRouteWithId(
            '/properties',
            payload.propertyId,
            suffix: 'review',
          );
    NotificationRoutes._navigate(route, data: data);
  }
}

// ----------------- Chat -----------------

class ChatNavigation implements NotificationNavigation {
  const ChatNavigation();

  @override
  void navigate({required Map<String, dynamic> data}) {
    final NotificationPayload payload = NotificationPayload.fromMap(data);
    NotificationRoutes._navigate(
      _notificationRouteWithId('/chat', payload.chatId),
      data: data,
    );
  }
}

// ----------------- Properties -----------------

class PropertyNavigation implements NotificationNavigation {
  const PropertyNavigation();

  @override
  void navigate({required Map<String, dynamic> data}) {
    final NotificationPayload payload = NotificationPayload.fromMap(data);
    NotificationRoutes._navigate(
      '${_notificationRouteWithId('/properties', payload.propertyId)}${payload.offerId.isEmpty ? '' : '?offer_id=${Uri.encodeQueryComponent(payload.offerId)}'}',
      data: data,
    );
  }
}

class OwnerPropertyNavigation implements NotificationNavigation {
  const OwnerPropertyNavigation();

  @override
  void navigate({required Map<String, dynamic> data}) {
    final NotificationPayload payload = NotificationPayload.fromMap(data);
    NotificationRoutes._navigate(
      _notificationRouteWithId('/my-properties', payload.propertyId),
      data: data,
    );
  }
}

class PropertyStatsNavigation implements NotificationNavigation {
  const PropertyStatsNavigation();

  @override
  void navigate({required Map<String, dynamic> data}) {
    final NotificationPayload payload = NotificationPayload.fromMap(data);
    NotificationRoutes._navigate(
      _notificationRouteWithId(
        '/my-properties',
        payload.propertyId,
        suffix: 'analytics',
      ),
      data: data,
    );
  }
}

class MyPropertiesNavigation implements NotificationNavigation {
  const MyPropertiesNavigation();

  @override
  void navigate({required Map<String, dynamic> data}) {
    NotificationRoutes._navigate('/my-properties', data: data);
  }
}

// ----------------- Account -----------------

class AccountVerificationNavigation implements NotificationNavigation {
  const AccountVerificationNavigation();

  @override
  void navigate({required Map<String, dynamic> data}) {
    NotificationRoutes._navigate('/profile/kyc', data: data);
  }
}

class SecurityNavigation implements NotificationNavigation {
  const SecurityNavigation();

  @override
  void navigate({required Map<String, dynamic> data}) {
    NotificationRoutes._navigate('/profile/security', data: data);
  }
}

// ----------------- Promotion / General -----------------

class PromotionNavigation implements NotificationNavigation {
  const PromotionNavigation();

  @override
  void navigate({required Map<String, dynamic> data}) {
    final NotificationPayload payload = NotificationPayload.fromMap(data);
    NotificationRoutes._navigate(
      _safeNotificationUrl(payload.promoUrl),
      data: data,
      isExternal: true,
    );
  }
}

class NotificationsNavigation implements NotificationNavigation {
  const NotificationsNavigation();

  @override
  void navigate({required Map<String, dynamic> data}) {
    NotificationRoutes._navigate('/notifications', data: data);
  }
}

class NoNavigation implements NotificationNavigation {
  const NoNavigation();

  @override
  void navigate({required Map<String, dynamic> data}) {}
}

String? _notificationRouteWithId(String basePath, String id, {String? suffix}) {
  final String normalizedId = id.trim();
  if (normalizedId.isEmpty) return null;
  final String route = '$basePath/${Uri.encodeComponent(normalizedId)}';
  return suffix == null ? route : '$route/$suffix';
}

String? _safeNotificationUrl(String value) {
  final Uri? uri = Uri.tryParse(value.trim());
  if (uri == null || !uri.hasAuthority) return null;
  if (uri.scheme != 'https' && uri.scheme != 'http') return null;
  return uri.toString();
}
