import 'package:flutter_test/flutter_test.dart';
import 'package:melos_core/core/notification/notification_service.dart';

void main() {
  group('NotificationType', () {
    test('implements all notification types from the contract', () {
      expect(
        NotificationType.values
            .where((NotificationType type) => type != NotificationType.unknown)
            .map((NotificationType type) => type.id),
        <String>[
          'visit_request',
          'visit_accepted',
          'visit_rejected',
          'visit_review',
          'new_message',
          'property_verified',
          'property_views',
          'daily_bump',
          'new_property',
          'property_update',
          'account_verification',
          'security_alert',
          'promotion',
          'general',
        ],
      );
    });

    test('unknown values do not throw', () {
      expect(
        NotificationType.fromValue('future_type'),
        NotificationType.unknown,
      );
      expect('future_type'.getType, NotificationType.unknown);
    });
  });

  group('NotificationPayload', () {
    test('normalizes an API payload with nested data', () {
      final NotificationPayload payload = NotificationPayload.fromMap(
        <String, dynamic>{
          'notification_type': 'visit_request',
          'title': 'طلب زيارة جديد!',
          'body': 'سارة أحمد تطلب زيارة العقار',
          'data': <String, dynamic>{
            'notification_type': 'visit_request',
            'visit_id': 'visit-1',
            'property_id': 'property-1',
            'tenant_name': 'سارة أحمد',
            'visit_date': '2026-09-20',
            'visit_time': '16:00:00',
            'action_type': 'view_visit',
          },
        },
      );

      expect(payload.notificationType, NotificationType.visitRequest);
      expect(payload.actionType, NotificationActionType.viewVisit);
      expect(payload.iconType, NotificationIconType.calendar);
      expect(payload.category, 'حجز زيارة');
      expect(payload.visitId, 'visit-1');
      expect(payload.propertyId, 'property-1');
      expect(payload.tenantName, 'سارة أحمد');
    });

    test('normalizes an FCM envelope and string-encoded data', () {
      final NotificationPayload payload = NotificationPayload.fromMap(
        <String, dynamic>{
          'notification': <String, dynamic>{
            'title': 'رسالة جديدة',
            'body': 'مرحباً',
          },
          'data':
              '{"notification_type":"new_message",'
              '"conversation_id":"chat-1","sender_name":"أحمد"}',
        },
      );

      expect(payload.notificationType, NotificationType.newMessage);
      expect(payload.actionType, NotificationActionType.openChat);
      expect(payload.title, 'رسالة جديدة');
      expect(payload.body, 'مرحباً');
      expect(payload.chatId, 'chat-1');
      expect(payload.senderName, 'أحمد');
    });

    test('parses numeric string fields', () {
      final NotificationPayload payload =
          NotificationPayload.fromMap(<String, dynamic>{
            'notification_type': 'property_views',
            'property_id': 'property-1',
            'views_count': '50',
          });

      expect(payload.viewsCount, 50);
      expect(payload.actionType, NotificationActionType.viewPropertyStats);
      expect(payload.iconType, NotificationIconType.eye);
    });
  });

  group('NotificationRoutes', () {
    NotificationRoute? handledRoute;
    NotificationPayload? handledPayload;

    setUp(() {
      handledRoute = null;
      handledPayload = null;
      NotificationRoutes.registerHandler((
        NotificationRoute route,
        NotificationPayload payload,
      ) {
        handledRoute = route;
        handledPayload = payload;
      });
    });

    tearDown(NotificationRoutes.clearHandler);

    final Map<String, String> expectedRoutes = <String, String>{
      'visit_request': '/visits/visit-1',
      'visit_accepted': '/visits/visit-1',
      'visit_rejected': '/properties/property-1',
      'visit_review': '/visits/visit-1/review',
      'new_message': '/chat/chat-1',
      'property_verified': '/my-properties/property-1',
      'property_views': '/my-properties/property-1/analytics',
      'daily_bump': '/my-properties',
      'new_property': '/properties/property-1',
      'property_update': '/properties/property-1',
      'account_verification': '/profile/kyc',
      'security_alert': '/profile/security',
      'promotion': 'https://sukoon.app/promotions/summer-offer',
      'general': '/notifications',
    };

    for (final MapEntry<String, String> entry in expectedRoutes.entries) {
      test('resolves ${entry.key}', () {
        NotificationRoutes.navigateByType(<String, dynamic>{
          'notification_type': entry.key,
          'visit_id': 'visit-1',
          'property_id': 'property-1',
          'chat_id': 'chat-1',
          'promo_url': 'https://sukoon.app/promotions/summer-offer',
        });

        expect(handledRoute?.location, entry.value);
      });
    }

    test('each type owns its concrete navigation strategy', () {
      expect(NotificationType.visitRequest.navigation, isA<VisitNavigation>());
      expect(NotificationType.newMessage.navigation, isA<ChatNavigation>());
      expect(
        NotificationType.propertyVerified.navigation,
        isA<OwnerPropertyNavigation>(),
      );
      expect(
        NotificationType.accountVerification.navigation,
        isA<AccountVerificationNavigation>(),
      );
      expect(NotificationType.unknown.navigation, isA<NoNavigation>());
    });

    test('supports direct navigation through the enum strategy', () {
      NotificationType.newProperty.navigation.navigate(
        data: <String, dynamic>{
          'notification_type': 'new_property',
          'property_id': 'property with spaces',
        },
      );

      expect(handledRoute?.location, '/properties/property%20with%20spaces');
    });

    test('does not resolve routes missing a required id', () {
      NotificationRoutes.navigateByType(<String, dynamic>{
        'notification_type': 'new_message',
      });

      expect(handledRoute, isNull);
    });

    test('rejects unsafe promotion URLs', () {
      NotificationRoutes.navigateByType(<String, dynamic>{
        'notification_type': 'promotion',
        'promo_url': 'javascript:alert(1)',
      });

      expect(handledRoute, isNull);
    });

    test('dispatches through the registered app handler', () {
      NotificationRoutes.navigateByType(<String, dynamic>{
        'notification_type': 'general',
        'action_type': 'open_general',
      });

      expect(handledRoute?.location, '/notifications');
      expect(handledPayload?.notificationType, NotificationType.general);
    });
  });
}
