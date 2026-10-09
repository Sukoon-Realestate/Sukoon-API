import 'package:flutter_test/flutter_test.dart';
import 'package:melos_core/config/res/config_imports.dart' show injector;
import 'package:melos_core/core/base_crud/code/domain/base_domain_imports.dart';
import 'package:melos_core/core/base_crud/code/domain/usecases/pagination_response.dart';
import 'package:melos_core/core/error/failure.dart';
import 'package:melos_core/core/network/api_endpoints.dart';
import 'package:melos_core/core/network/network_request.dart';
import 'package:melos_core/core/network/network_service.dart';
import 'package:multiple_result/multiple_result.dart';
import 'package:sokoun_app/features/shared/notifications/data/enums/app_notification_kind.dart';
import 'package:sokoun_app/features/shared/notifications/data/models/app_notification_content.dart';
import 'package:sokoun_app/features/shared/notifications/data/notification_device_data.dart';
import 'package:sokoun_app/features/shared/notifications/data/notifications_data.dart';
import 'package:sokoun_app/features/shared/notifications/presentation/cubits/notification_detail_cubit.dart';
import 'package:sokoun_app/features/shared/notifications/presentation/cubits/notification_settings_cubit.dart';
import 'package:sokoun_app/features/shared/notifications/presentation/cubits/notifications_cubit.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  late _FakeNetworkService networkService;
  late _RecordingBaseRepository repository;

  setUp(() async {
    await injector.reset();
    networkService = _FakeNetworkService();
    repository = _RecordingBaseRepository();
    injector
      ..registerSingleton<NetworkService>(networkService)
      ..registerSingleton<BaseCrudUseCase>(
        BaseCrudUseCase(repository: repository),
      );
  });

  tearDown(() => injector.reset());

  test('loads the documented paginated notifications response', () async {
    int? unreadCount;
    final (
      notifications,
      pagination,
    ) = await NotificationsData.getNotificationsPage(
      page: 2,
      onUnreadCount: (count) => unreadCount = count,
    );

    expect(networkService.lastRequest.path, ApiConstants.notifications);
    expect(networkService.lastRequest.method, RequestMethod.get);
    expect(networkService.lastRequest.queryParameters, {
      'page': 2,
      'page_size': 20,
    });
    expect(pagination.perPage, 20);
    expect(pagination.totalPages, 3);
    expect(unreadCount, 2);
    expect(notifications, hasLength(1));
    expect(notifications.single.kind, AppNotificationKind.visitRequest);
    expect(notifications.single.payload.visitId, 'visit-id');
    expect(notifications.single.isUnread, isTrue);
  });

  test(
    'registers an authenticated FCM device with the documented body',
    () async {
      networkService.hasSession = true;
      await NotificationDeviceData.registerToken('fcm-token');

      expect(networkService.lastRequest.path, ApiConstants.notificationDevices);
      expect(networkService.lastRequest.method, RequestMethod.post);
      expect(
        networkService.lastRequest.body,
        containsPair('token', 'fcm-token'),
      );
      expect(networkService.lastRequest.body, contains('device_type'));
      expect(networkService.lastRequest.body, contains('device_name'));
    },
  );

  test('maps detail appointment and action data symmetrically', () {
    final AppNotificationContent notification = AppNotificationContent.fromJson(
      _notificationJson,
    );
    final AppNotificationContent restored = AppNotificationContent.fromJson(
      notification.toJson(),
    );

    expect(notification.detailLabel, 'تفاصيل الموعد');
    expect(notification.detailDate, 'الثلاثاء 14 يناير، 3:00 م');
    expect(notification.primaryActionType, 'view_request');
    expect(notification.primaryTargetId, 'visit-id');
    expect(notification.payload.tenantName, 'سارة أحمد');
    expect(notification.payload.viewsCount, 50);
    expect(restored, notification);
  });

  test('uses the documented read and mark-all endpoints', () async {
    final NotificationsCubit cubit = NotificationsCubit();
    addTearDown(cubit.close);
    cubit.setUnreadCount(2);

    expect(await cubit.markAsRead('notification-id'), isTrue);
    expect(repository.lastParams.api, 'notifications/notification-id/read/');
    expect(repository.lastParams.httpRequestType, HttpRequestType.patch);
    expect(cubit.data.unreadCount, 1);

    expect(await cubit.markAllAsRead(), isTrue);
    expect(repository.lastParams.api, ApiConstants.markAllNotificationsRead);
    expect(repository.lastParams.httpRequestType, HttpRequestType.post);
    expect(cubit.data.unreadCount, 0);
  });

  test(
    'loads private details and notification settings then patches a key',
    () async {
      final NotificationDetailCubit detailCubit = NotificationDetailCubit();
      final NotificationSettingsCubit settingsCubit =
          NotificationSettingsCubit();
      final NotificationSettingUpdateCubit updateCubit =
          NotificationSettingUpdateCubit();
      addTearDown(detailCubit.close);
      addTearDown(settingsCubit.close);
      addTearDown(updateCubit.close);

      await detailCubit.load(notificationId: 'notification-id');
      expect(repository.lastParams.api, 'notifications/notification-id/');
      expect(
        repository.lastParams.cacheKey,
        'notification_details_notification-id',
      );
      expect(detailCubit.data.id, 'notification-id');
      expect(repository.lastParams.cachePolicy?.persist, isFalse);

      await settingsCubit.loadSettings();
      expect(repository.lastParams.api, ApiConstants.notificationSettings);
      expect(repository.lastParams.cacheKey, 'notification_settings');
      expect(settingsCubit.data.items, hasLength(5));
      expect(repository.lastParams.cachePolicy?.persist, isFalse);

      expect(
        await updateCubit.updateSetting(key: 'property_updates', value: true),
        isTrue,
      );
      expect(repository.lastParams.httpRequestType, HttpRequestType.patch);
      expect(repository.lastParams.body, {'property_updates': true});
    },
  );
}

const Map<String, dynamic> _notificationJson = {
  'id': 'notification-id',
  'notification_type': 'visit_request',
  'title': 'طلب زيارة جديد!',
  'body': 'مستأجر يطلب زيارة العقار',
  'category': 'حجز زيارة',
  'icon_type': 'calendar',
  'is_read': false,
  'created_at': '2026-09-13T01:25:00Z',
  'time_ago': 'منذ 5 دقائق',
  'appointment_details': {
    'title': 'تفاصيل الموعد',
    'datetime_label': 'الثلاثاء 14 يناير، 3:00 م',
    'location_label': 'مدينة نصر',
  },
  'actions': {
    'primary': {
      'label': 'عرض الزيارة',
      'action_type': 'view_request',
      'target_id': 'visit-id',
    },
  },
  'data': {
    'visit_id': 'visit-id',
    'property_id': 'property-id',
    'tenant_name': 'سارة أحمد',
    'views_count': 50,
  },
};

class _FakeNetworkService implements NetworkService {
  late NetworkRequest lastRequest;
  bool hasSession = false;

  @override
  Future<BaseModel<Model>> callApi<Model>(
    NetworkRequest networkRequest, {
    Model Function(dynamic json)? mapper,
  }) async {
    lastRequest = networkRequest;
    final Model data = mapper!({
      'per_page': 20,
      'total_pages': 3,
      'unread_count': 2,
      'results': [_notificationJson],
    });
    return BaseModel<Model>(key: '', msg: '', data: data);
  }

  @override
  Future<void> clearSessionCookies() async {}

  @override
  Future<bool> hasSessionCookies() async => hasSession;

  @override
  Future<void> updateBaseUrl() async {}
}

class _RecordingBaseRepository implements BaseRepository {
  late CrudBaseParmas<dynamic> lastParams;

  @override
  Future<Result<BaseModel<T>, Failure>> crudCall<T>(
    CrudBaseParmas<T> params,
  ) async {
    lastParams = params;
    final dynamic response = switch (params.api) {
      ApiConstants.notificationSettings => _settingsJson,
      ApiConstants.unreadNotificationCount => const {'unread_count': 2},
      _ when params.api.endsWith('/read/') => const {
        'id': 'notification-id',
        'is_read': true,
      },
      _ when params.api == 'notifications/notification-id/' =>
        _notificationJson,
      _ => const <String, dynamic>{},
    };
    final T data = params.mapper == null
        ? response as T
        : params.mapper!(response);
    return Success(BaseModel<T>(key: '', msg: '', data: data));
  }

  @override
  Future<Result<List<T>, Failure>> getBaseIdAndNameEntity<T extends BaseEntity>(
    GetBaseEntityParams? param,
  ) => throw UnimplementedError();
}

const Map<String, dynamic> _settingsJson = {
  'id': 'settings-id',
  'visit_notifications': true,
  'owner_messages': true,
  'property_updates': false,
  'security_alerts': true,
  'promotions_and_updates': false,
  'sections': {
    'notifications': {
      'items': [
        {
          'key': 'visit_notifications',
          'title': 'طلبات الزيارات',
          'subtitle': 'قبول ورفض مواعيد الزيارة',
          'value': true,
          'enabled': true,
        },
        {
          'key': 'owner_messages',
          'title': 'الرسائل الجديدة',
          'subtitle': 'إشعار عند وصول رسالة',
          'value': true,
          'enabled': true,
        },
        {
          'key': 'property_updates',
          'title': 'تحديثات العقارات',
          'subtitle': 'تغيير السعر أو الحالة',
          'value': false,
          'enabled': true,
        },
        {
          'key': 'security_alerts',
          'title': 'التنبيهات الأمنية',
          'subtitle': 'دخول جديد وتغيير كلمة المرور',
          'value': true,
          'enabled': true,
        },
        {
          'key': 'promotions_and_updates',
          'title': 'العروض الترويجية',
          'subtitle': 'أخبار وعروض سكون',
          'value': false,
          'enabled': true,
        },
      ],
      'footer_note': 'يمكنك إدارة الإشعارات من إعدادات الهاتف.',
    },
  },
};
