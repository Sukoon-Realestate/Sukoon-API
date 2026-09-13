import 'package:easy_localization/easy_localization.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:sokoun_app/features/owner/home/presentation/screens/owner_home_screen.dart';
import 'package:sokoun_app/features/tenant/home/presentation/screens/tenant_home_screen.dart';
import 'package:sokoun_app/features/shared/notifications/data/enums/notification_role.dart';
import 'package:sokoun_app/features/shared/notifications/data/models/app_notification_content.dart';
import 'package:sokoun_app/features/shared/notifications/presentation/screens/notification_detail_screen.dart';
import 'package:sokoun_app/features/shared/notifications/presentation/screens/notification_settings_screen.dart';
import 'package:sokoun_app/features/shared/notifications/presentation/screens/notifications_empty_screen.dart';
import 'package:sokoun_app/features/shared/notifications/presentation/screens/notifications_screen.dart';
import 'package:sokoun_app/features/shared/notifications/presentation/widgets/notification_card.dart';

import 'helpers/home_page_test_dependencies.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  const MethodChannel sharedPreferencesChannel = MethodChannel(
    'plugins.flutter.io/shared_preferences',
  );

  setUpAll(() async {
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(sharedPreferencesChannel, (call) async {
          return call.method == 'getAll' ? <String, Object>{} : true;
        });
    await EasyLocalization.ensureInitialized();
    registerHomePageTestDependencies();
  });

  tearDownAll(() {
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(sharedPreferencesChannel, null);
  });

  Widget buildScreen(Widget screen) {
    return EasyLocalization(
      supportedLocales: const [Locale('ar')],
      path: 'unused',
      assetLoader: const _NotificationTestAssetLoader(),
      startLocale: const Locale('ar'),
      fallbackLocale: const Locale('ar'),
      child: ScreenUtilInit(
        designSize: Size(ScreenSizes.width, ScreenSizes.height),
        builder: (context, _) {
          return MaterialApp(
            navigatorKey: Go.navigatorKey,
            localizationsDelegates: context.localizationDelegates,
            supportedLocales: context.supportedLocales,
            locale: context.locale,
            home: screen,
          );
        },
      ),
    );
  }

  void configurePhoneViewport(WidgetTester tester) {
    tester.view.physicalSize = const Size(360, 690);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.reset);
  }

  testWidgets('runs the tenant list detail settings and read-state flow', (
    tester,
  ) async {
    configurePhoneViewport(tester);

    await tester.pumpWidget(
      buildScreen(
        NotificationsScreen(
          role: NotificationRole.tenant,
          initialNotifications: _tenantNotifications,
        ),
      ),
    );
    await tester.pumpAndSettle();

    expect(_tenantNotifications, hasLength(2));
    expect(find.byType(NotificationCard), findsWidgets);
    expect(
      tester
          .widget<NotificationCard>(
            find.byKey(const ValueKey('tenant-visit-accepted')),
          )
          .notification
          .isUnread,
      isTrue,
    );
    expect(tester.takeException(), isNull);

    await tester.tap(find.byKey(const ValueKey('tenant-visit-accepted')));
    await tester.pumpAndSettle();

    expect(find.byType(NotificationDetailScreen), findsOneWidget);
    expect(find.text('تم قبول طلب زيارتك'), findsOneWidget);
    expect(tester.takeException(), isNull);

    await tester.tap(find.byIcon(Icons.arrow_back_ios_new_rounded));
    await tester.pumpAndSettle();

    expect(
      tester
          .widget<NotificationCard>(
            find.byKey(const ValueKey('tenant-visit-accepted')),
          )
          .notification
          .isUnread,
      isFalse,
    );
    expect(tester.takeException(), isNull);

    await tester.tap(find.byIcon(Icons.settings_outlined));
    await tester.pumpAndSettle();

    expect(find.byType(NotificationSettingsScreen), findsOneWidget);
    expect(tester.takeException(), isNull);
    await tester.tap(find.byKey(const ValueKey('property_updates')));
    await tester.pump();
    expect(tester.takeException(), isNull);

    await tester.tap(find.byIcon(Icons.arrow_back_ios_new_rounded));
    await tester.pumpAndSettle();
    await tester.tap(find.text('تحديد الكل كمقروء'));
    await tester.pump();

    expect(
      tester
          .widget<NotificationCard>(
            find.byKey(const ValueKey('tenant-new-property')),
          )
          .notification
          .isUnread,
      isFalse,
    );
    expect(tester.takeException(), isNull);
  });

  testWidgets('renders the owner dataset and owner detail flow', (
    tester,
  ) async {
    configurePhoneViewport(tester);

    await tester.pumpWidget(
      buildScreen(
        NotificationsScreen(
          role: NotificationRole.owner,
          initialNotifications: _ownerNotifications,
        ),
      ),
    );
    await tester.pumpAndSettle();

    expect(_ownerNotifications, hasLength(1));
    expect(find.byType(NotificationCard), findsWidgets);
    expect(find.text('طلب زيارة جديد!'), findsOneWidget);

    await tester.tap(find.byKey(const ValueKey('owner-visit-request')));
    await tester.pumpAndSettle();

    expect(find.byType(NotificationDetailScreen), findsOneWidget);
    expect(find.text('تفاصيل الطلب'), findsOneWidget);
    expect(find.text('عرض الطلب'), findsOneWidget);

    await tester.tap(find.byIcon(Icons.arrow_back_ios_new_rounded));
    await tester.pumpAndSettle();
    await tester.tap(find.byIcon(Icons.settings_outlined));
    await tester.pumpAndSettle();

    expect(find.byType(NotificationSettingsScreen), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('shows the notification empty frame', (tester) async {
    configurePhoneViewport(tester);

    await tester.pumpWidget(
      buildScreen(
        const NotificationsScreen(
          role: NotificationRole.tenant,
          initialNotifications: [],
        ),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.byType(NotificationsEmptyScreen), findsNothing);
    expect(find.text('لا إشعارات حالياً'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('tenant and owner home bells open their notification roles', (
    tester,
  ) async {
    configurePhoneViewport(tester);

    await tester.pumpWidget(buildScreen(const TenantHomeScreen()));
    await tester.pumpAndSettle();
    await tester.tap(find.byIcon(Icons.notifications_none_rounded));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 200));

    expect(find.byType(NotificationsScreen), findsOneWidget);
    expect(
      tester.widget<NotificationsScreen>(find.byType(NotificationsScreen)).role,
      NotificationRole.tenant,
    );

    await tester.pumpWidget(const SizedBox.shrink());
    await tester.pump();
    await tester.pumpWidget(buildScreen(const OwnerHomeScreen()));
    await tester.pumpAndSettle();
    await tester.tap(find.byIcon(Icons.notifications_none_rounded));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 200));

    expect(find.byType(NotificationsScreen), findsOneWidget);
    expect(
      tester.widget<NotificationsScreen>(find.byType(NotificationsScreen)).role,
      NotificationRole.owner,
    );
    expect(tester.takeException(), isNull);
  });
}

class _NotificationTestAssetLoader extends AssetLoader {
  const _NotificationTestAssetLoader();

  @override
  Future<Map<String, dynamic>> load(String path, Locale locale) async {
    return {
      'home': 'الرئيسية',
      'favorites_navigation_saved': 'المحفوظات',
      'chats': 'الشات',
      'notifications': 'الإشعارات',
      'favorites_navigation_account': 'الحساب',
      'notifications_flow_title': 'الإشعارات',
      'notifications_mark_all_read': 'تحديد الكل كمقروء',
      'notifications_mark_all': 'تحديد الكل',
      'notification_details_title': 'تفاصيل الإشعار',
      'notifications_empty_title': 'لا إشعارات حالياً',
      'notifications_empty_description':
          'ستظهر هنا إشعاراتك عند وجود تحديثات على طلباتك أو عقاراتك',
      'notifications_explore_properties': 'استكشف العقارات',
      'notifications_owner_add_property': 'إضافة عقار',
      'notification_view_visit': 'عرض الزيارة',
      'notification_view_request': 'عرض الطلب',
      'notification_open_related': 'عرض التفاصيل',
      'notification_dismiss': 'تجاهل',
      'notification_settings_title': 'إعدادات الإشعارات',
      'notification_setting_visit_requests': 'طلبات الزيارة',
      'notification_setting_visit_requests_description':
          'قبول ورفض مواعيد الزيارة',
      'notification_setting_new_messages': 'الرسائل الجديدة',
      'notification_setting_new_messages_description': 'إشعار عند وصول رسالة',
      'notification_setting_property_updates': 'تحديثات العقارات',
      'notification_setting_property_updates_description':
          'تغيير السعر أو الحالة',
      'notification_setting_security_alerts': 'التنبيهات الأمنية',
      'notification_setting_security_alerts_description':
          'دخول جديد وتغيير كلمة المرور',
      'notification_setting_promotions': 'العروض الترويجية',
      'notification_setting_promotions_description': 'أخبار وعروض سكون',
      'notification_settings_info':
          'يمكنك أيضاً إدارة إشعارات التطبيق من إعدادات هاتفك مباشرةً.',
      'notifications_owner_properties_navigation': 'عقاراتي',
      'notifications_owner_requests_navigation': 'الطلبات',
      'notifications_owner_more_navigation': 'المزيد',
    };
  }
}

final List<AppNotificationContent> _tenantNotifications = [
  AppNotificationContent.fromJson({
    'id': 'tenant-visit-accepted',
    'notification_type': 'visit_accepted',
    'icon_type': 'check_circle',
    'title': 'تم قبول طلب زيارتك',
    'body': 'المالك أحمد محمد وافق على موعد الزيارة',
    'time_ago': 'منذ 5 دقائق',
    'category': 'حجز زيارة',
    'is_read': false,
    'appointment_details': {
      'title': 'تفاصيل الموعد',
      'datetime_label': 'الثلاثاء 14 يناير · 3:00 م',
      'location_label': 'مدينة نصر — شارع عباس العقاد',
    },
    'actions': {
      'primary': {
        'label': 'عرض الزيارة',
        'action_type': 'view_visit',
        'target_id': 'visit-1',
      },
    },
  }),
  AppNotificationContent.fromJson({
    'id': 'tenant-new-property',
    'notification_type': 'new_property',
    'icon_type': 'bell',
    'title': 'عقار جديد في منطقتك',
    'body': 'شقة مفروشة 3 غرف',
    'time_ago': 'منذ ساعة',
    'category': 'عقار جديد',
    'is_read': false,
  }),
];

final List<AppNotificationContent> _ownerNotifications = [
  AppNotificationContent.fromJson({
    'id': 'owner-visit-request',
    'notification_type': 'visit_request',
    'icon_type': 'calendar',
    'title': 'طلب زيارة جديد!',
    'body': 'سارة أحمد تطلب زيارة شقة مدينة نصر',
    'time_ago': 'منذ 5 دقائق',
    'category': 'طلب زيارة',
    'is_read': false,
    'appointment_details': {
      'title': 'تفاصيل الطلب',
      'datetime_label': 'النهارده · 3:00 م',
      'location_label': 'شقة مدينة نصر — شارع عباس العقاد',
    },
    'actions': {
      'primary': {
        'label': 'عرض الطلب',
        'action_type': 'view_request',
        'target_id': 'request-1',
      },
    },
  }),
];
