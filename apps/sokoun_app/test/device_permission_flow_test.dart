import 'package:melos_core/core/network/network_request.dart';
import 'dart:async';
import 'dart:convert';

import 'package:easy_localization/easy_localization.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/helpers/cache_service.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/core/widgets/location_permission_view.dart';
import 'package:melos_core/core/widgets/notification_permission_view.dart';
import 'package:melos_core/core/widgets/permissions/permission_actions.dart';
import 'package:sokoun_app/features/shared/notifications/data/notification_device_data.dart';
import 'package:sokoun_app/features/shared/notifications/presentation/widgets/device_notification_permission_tile.dart';
import 'package:sokoun_app/features/shared/permissions/data/device_permission_data.dart';
import 'package:sokoun_app/features/shared/permissions/data/enums/device_permission.dart';
import 'package:sokoun_app/features/shared/permissions/presentation/device_permission_flow.dart';
import 'package:sokoun_app/features/shared/permissions/presentation/widgets/permission_settings_dialog.dart';
import 'package:sokoun_app/features/tenant/home/data/current_location_data.dart';
import 'package:sokoun_app/features/tenant/home/data/models/current_location_area.dart';
import 'package:sokoun_app/features/tenant/home/presentation/widgets/tenant_search/use_current_location_button.dart';

import 'package:pagify/helpers/data_and_pagination_data.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_search_model.dart';
import 'package:sokoun_app/features/tenant/home/data/property_search_data.dart';
import 'package:sokoun_app/features/tenant/home/presentation/screens/tenant_search_screen.dart';
import 'package:sokoun_app/features/tenant/home/presentation/screens/tenant_search_results_screen.dart';

import 'helpers/home_page_test_dependencies.dart';

late Map<String, dynamic> _translations;

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  const preferences = MethodChannel('plugins.flutter.io/shared_preferences');
  late _PermissionSource permissions;
  late _LocationSource location;
  late _NotificationDeviceSource notifications;

  setUpAll(() async {
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(
          preferences,
          (call) async => call.method == 'getAll' ? <String, Object>{} : true,
        );
    await EasyLocalization.ensureInitialized();
    await CacheStorage.init();
    _translations =
        jsonDecode(
              await rootBundle.loadString(
                'packages/melos_core/assets/translations/en.json',
              ),
            )
            as Map<String, dynamic>;
  });

  setUp(() async {
    await injector.reset();
    permissions = _PermissionSource();
    location = _LocationSource();
    notifications = _NotificationDeviceSource();
    injector.registerSingleton<DevicePermissionDataSource>(permissions);
    injector.registerSingleton<CurrentLocationDataSource>(location);
    injector.registerSingleton<NotificationDeviceDataSource>(notifications);
  });

  tearDown(() async => injector.reset());

  tearDownAll(() {
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(preferences, null);
  });

  test('notification prompt history survives data source recreation', () async {
    await CacheStorage.delete(
      NativeDevicePermissionDataSource.notificationPromptKey,
    );
    const first = NativeDevicePermissionDataSource();
    expect(first.hasSeenNotificationPrompt, isFalse);
    await first.markNotificationPromptSeen();
    const recreated = NativeDevicePermissionDataSource();
    expect(recreated.hasSeenNotificationPrompt, isTrue);
    await CacheStorage.delete(
      NativeDevicePermissionDataSource.notificationPromptKey,
    );
  });

  testWidgets('not now suppresses automatic prompts but settings can retry', (
    tester,
  ) async {
    await _pump(tester);
    final context = tester.element(find.byType(Scaffold));
    final first = DevicePermissionFlow.ensureGranted(
      context,
      DevicePermission.notifications,
      promptOnce: true,
    );
    await tester.pumpAndSettle();
    expect(permissions.requests, 0);
    await tester.ensureVisible(_actions.last);
    await tester.tap(_actions.last);
    await tester.pumpAndSettle();
    expect(await first, isFalse);
    expect(permissions.seen, isTrue);
    expect(permissions.requests, 0);

    expect(
      await DevicePermissionFlow.ensureGranted(
        context,
        DevicePermission.notifications,
        promptOnce: true,
      ),
      isFalse,
    );
    await tester.pumpAndSettle();
    expect(find.byType(NotificationPermissionView), findsNothing);

    final retry = DevicePermissionFlow.ensureGranted(
      context,
      DevicePermission.notifications,
    );
    await tester.pumpAndSettle();
    expect(find.byType(NotificationPermissionView), findsOneWidget);
    await tester.ensureVisible(_actions.first);
    await tester.tap(_actions.first);
    await tester.pumpAndSettle();
    expect(await retry, isTrue);
    expect(permissions.requests, 1);
    expect(notifications.registrations, 1);
  });

  testWidgets('barrier dismissal never requests the native permission', (
    tester,
  ) async {
    await _pump(tester);
    final result = DevicePermissionFlow.ensureGranted(
      tester.element(find.byType(Scaffold)),
      DevicePermission.notifications,
      promptOnce: true,
    );
    await tester.pumpAndSettle();
    await tester.tapAt(const Offset(10, 10));
    await tester.pumpAndSettle();
    expect(await result, isFalse);
    expect(permissions.requests, 0);
    expect(permissions.seen, isTrue);
  });

  for (final permission in DevicePermission.values) {
    testWidgets(
      'already granted $permission skips explanation and OS request',
      (tester) async {
        permissions.current = DevicePermissionStatus.granted;
        await _pump(tester);
        expect(
          await DevicePermissionFlow.ensureGranted(
            tester.element(find.byType(Scaffold)),
            permission,
          ),
          isTrue,
        );
        expect(permissions.requests, 0);
        expect(find.byType(PermissionActions), findsNothing);
      },
    );
  }

  testWidgets('OS denial does not register push or report success', (
    tester,
  ) async {
    permissions.requestResult = DevicePermissionStatus.denied;
    await _pump(tester);
    final result = DevicePermissionFlow.ensureGranted(
      tester.element(find.byType(Scaffold)),
      DevicePermission.notifications,
    );
    await tester.pumpAndSettle();
    await tester.ensureVisible(_actions.first);
    await tester.tap(_actions.first);
    await tester.pumpAndSettle();
    expect(await result, isFalse);
    expect(permissions.requests, 1);
    expect(notifications.registrations, 0);
    await tester.pump(const Duration(seconds: 5));
    await tester.pumpAndSettle();
  });

  testWidgets(
    'blocked permission opens settings only after explicit confirmation',
    (tester) async {
      permissions.current = DevicePermissionStatus.blocked;
      await _pump(tester);
      final result = DevicePermissionFlow.ensureGranted(
        tester.element(find.byType(Scaffold)),
        DevicePermission.notifications,
      );
      await tester.pumpAndSettle();
      expect(find.byType(PermissionSettingsDialog), findsOneWidget);
      expect(permissions.settingsOpened, 0);
      await tester.tap(find.text(LocaleKeys.permissionOpenSettings));
      await tester.pumpAndSettle();
      expect(await result, isFalse);
      expect(permissions.settingsOpened, 1);
      expect(permissions.requests, 0);
    },
  );

  testWidgets('blocked automatic prompts do not interrupt home', (
    tester,
  ) async {
    permissions.current = DevicePermissionStatus.blocked;
    await _pump(tester);
    expect(
      await DevicePermissionFlow.ensureGranted(
        tester.element(find.byType(Scaffold)),
        DevicePermission.notifications,
        promptOnce: true,
      ),
      isFalse,
    );
    expect(find.byType(PermissionSettingsDialog), findsNothing);
    expect(permissions.settingsOpened, 0);
  });

  testWidgets('concurrent requests share one visible permission prompt', (
    tester,
  ) async {
    await _pump(tester);
    final context = tester.element(find.byType(Scaffold));
    final first = DevicePermissionFlow.ensureGranted(
      context,
      DevicePermission.location,
    );
    final second = DevicePermissionFlow.ensureGranted(
      context,
      DevicePermission.location,
    );
    await tester.pumpAndSettle();
    expect(find.byType(LocationPermissionView), findsOneWidget);
    expect(await second, isFalse);
    await tester.ensureVisible(_actions.last);
    await tester.tap(_actions.last);
    await tester.pumpAndSettle();
    expect(await first, isFalse);
    expect(permissions.requests, 0);
  });

  testWidgets('leaving a screen during status lookup does not show a prompt', (
    tester,
  ) async {
    permissions.pendingStatus = Completer<DevicePermissionStatus>();
    await _pump(tester);
    final result = DevicePermissionFlow.ensureGranted(
      tester.element(find.byType(Scaffold)),
      DevicePermission.location,
    );
    await tester.pumpWidget(const SizedBox.shrink());
    permissions.pendingStatus!.complete(DevicePermissionStatus.denied);
    await tester.pumpAndSettle();
    expect(await result, isFalse);
    expect(permissions.requests, 0);
    expect(tester.takeException(), isNull);
  });

  testWidgets(
    'notification settings refresh actual access after returning from settings',
    (tester) async {
      permissions.current = DevicePermissionStatus.blocked;
      await _pump(tester, child: const DeviceNotificationPermissionTile());
      expect(find.text(LocaleKeys.permissionOpenSettings), findsOneWidget);
      permissions.current = DevicePermissionStatus.granted;
      tester.binding.handleAppLifecycleStateChanged(AppLifecycleState.paused);
      tester.binding.handleAppLifecycleStateChanged(AppLifecycleState.resumed);
      await tester.pumpAndSettle();
      expect(find.text(LocaleKeys.deviceNotificationsEnabled), findsOneWidget);
      expect(find.text(LocaleKeys.permissionOpenSettings), findsNothing);
      expect(notifications.registrations, 1);
    },
  );

  testWidgets('search screen submits the resolved area to property results', (
    tester,
  ) async {
    registerHomePageTestDependencies();
    final search = _PropertySearchSource();
    injector.registerSingleton<PropertySearchDataSource>(search);
    const connectivity = MethodChannel(
      'dev.fluttercommunity.plus/connectivity',
    );
    const connectivityStatus = MethodChannel(
      'dev.fluttercommunity.plus/connectivity_status',
    );
    final messenger =
        TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger;
    messenger.setMockMethodCallHandler(
      connectivity,
      (_) async => <String>['wifi'],
    );
    messenger.setMockMethodCallHandler(connectivityStatus, (_) async => null);
    addTearDown(() {
      messenger.setMockMethodCallHandler(connectivity, null);
      messenger.setMockMethodCallHandler(connectivityStatus, null);
    });
    await _pump(tester, child: const TenantSearchScreen());
    await tester.tap(find.text(LocaleKeys.useMyLocation));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 400));
    await tester.ensureVisible(_actions.first);
    await tester.tap(_actions.first);
    for (var frame = 0; frame < 12; frame++) {
      await tester.pump(const Duration(milliseconds: 100));
    }
    expect(find.byType(TenantSearchResultsScreen), findsOneWidget);
    expect(search.request?.search, 'Nasr City Cairo');
    expect(search.request?.page, 1);
    expect(permissions.requests, 1);
    expect(tester.takeException(), isNull);
    await tester.pumpWidget(const SizedBox.shrink());
    await tester.pumpAndSettle();
  });

  testWidgets('location skip never reads position or changes the search area', (
    tester,
  ) async {
    CurrentLocationArea? selected;
    await _pump(
      tester,
      child: UseCurrentLocationButton(
        onAreaResolved: (area) => selected = area,
      ),
    );
    await tester.tap(find.text(LocaleKeys.useMyLocation));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 400));
    expect(find.byType(LocationPermissionView), findsOneWidget);
    expect(location.lookups, 0);
    await tester.ensureVisible(_actions.last);
    await tester.tap(_actions.last);
    await tester.pumpAndSettle();
    expect(permissions.requests, 0);
    expect(location.lookups, 0);
    expect(selected, isNull);
  });

  testWidgets(
    'location consent resolves area only after the OS grants access',
    (tester) async {
      CurrentLocationArea? selected;
      await _pump(
        tester,
        child: UseCurrentLocationButton(
          onAreaResolved: (area) => selected = area,
        ),
      );
      await tester.tap(find.text(LocaleKeys.useMyLocation));
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 400));
      expect(location.lookups, 0);
      await tester.ensureVisible(_actions.first);
      await tester.tap(_actions.first);
      await tester.pumpAndSettle();
      expect(permissions.requests, 1);
      expect(location.lookups, 1);
      expect(selected?.searchQuery, 'Nasr City Cairo');
    },
  );

  testWidgets('location denial never resolves an area', (tester) async {
    permissions.requestResult = DevicePermissionStatus.denied;
    await _pump(
      tester,
      child: UseCurrentLocationButton(
        onAreaResolved: (_) => fail('Must not resolve an area'),
      ),
    );
    await tester.tap(find.text(LocaleKeys.useMyLocation));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 400));
    await tester.ensureVisible(_actions.first);
    await tester.tap(_actions.first);
    await tester.pumpAndSettle();
    expect(location.lookups, 0);
    await tester.pump(const Duration(seconds: 5));
    await tester.pumpAndSettle();
  });

  testWidgets(
    'disabled location services provide settings recovery without requesting access',
    (tester) async {
      location.enabled = false;
      await _pump(
        tester,
        child: UseCurrentLocationButton(
          onAreaResolved: (_) => fail('Must not resolve an area'),
        ),
      );
      await tester.tap(find.text(LocaleKeys.useMyLocation));
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 400));
      expect(find.text(LocaleKeys.locationServicesDisabled), findsOneWidget);
      await tester.tap(find.text(LocaleKeys.permissionOpenSettings));
      await tester.pumpAndSettle();
      expect(location.settingsOpened, 1);
      expect(location.lookups, 0);
      expect(permissions.requests, 0);
    },
  );

  testWidgets(
    'location failure leaves manual search available and permits retry',
    (tester) async {
      permissions.current = DevicePermissionStatus.granted;
      location.failLookup = true;
      CurrentLocationArea? selected;
      await _pump(
        tester,
        child: UseCurrentLocationButton(
          onAreaResolved: (area) => selected = area,
        ),
      );
      await tester.tap(find.text(LocaleKeys.useMyLocation));
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 400));
      expect(selected, isNull);
      expect(find.text(LocaleKeys.useMyLocation), findsOneWidget);
      await tester.pump(const Duration(seconds: 5));
      await tester.pumpAndSettle();
      location.failLookup = false;
      await tester.tap(find.text(LocaleKeys.useMyLocation));
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 400));
      expect(selected, isNotNull);
      expect(tester.takeException(), isNull);
    },
  );
}

Finder get _actions => find.descendant(
  of: find.byType(PermissionActions),
  matching: find.byType(ElevatedButton),
);

Future<void> _pump(
  WidgetTester tester, {
  Widget child = const SizedBox.shrink(),
}) async {
  tester.view.physicalSize = const Size(390, 844);
  tester.view.devicePixelRatio = 1;
  addTearDown(tester.view.reset);
  await tester.pumpWidget(
    EasyLocalization(
      supportedLocales: const [Locale('en')],
      startLocale: const Locale('en'),
      path: 'unused',
      assetLoader: const _Translations(),
      child: ScreenUtilInit(
        designSize: const Size(390, 844),
        builder: (context, _) => MaterialApp(
          navigatorKey: Go.navigatorKey,
          localizationsDelegates: context.localizationDelegates,
          supportedLocales: context.supportedLocales,
          locale: context.locale,
          builder: (context, child) =>
              Overlay(initialEntries: [OverlayEntry(builder: (_) => child!)]),
          home: Scaffold(body: Center(child: child)),
        ),
      ),
    ),
  );
  await tester.pumpAndSettle();
}

class _Translations extends AssetLoader {
  const _Translations();
  @override
  Future<Map<String, dynamic>> load(String path, Locale locale) async =>
      _translations;
}

class _PermissionSource implements DevicePermissionDataSource {
  DevicePermissionStatus current = DevicePermissionStatus.denied;
  DevicePermissionStatus requestResult = DevicePermissionStatus.granted;
  Completer<DevicePermissionStatus>? pendingStatus;
  bool seen = false;
  int requests = 0;
  int settingsOpened = 0;
  @override
  bool get hasSeenNotificationPrompt => seen;
  @override
  Future<void> markNotificationPromptSeen() async => seen = true;
  @override
  Future<bool> openSettings() async {
    settingsOpened++;
    return true;
  }

  @override
  Future<DevicePermissionStatus> status(DevicePermission permission) async =>
      pendingStatus == null ? current : await pendingStatus!.future;
  @override
  Future<DevicePermissionStatus> request(DevicePermission permission) async {
    requests++;
    return current = requestResult;
  }
}

class _LocationSource implements CurrentLocationDataSource {
  bool enabled = true;
  bool failLookup = false;
  int lookups = 0;
  int settingsOpened = 0;
  @override
  Future<bool> isServiceEnabled() async => enabled;
  @override
  Future<bool> openLocationSettings() async {
    settingsOpened++;
    return true;
  }

  @override
  Future<CurrentLocationArea> resolveArea({
    required String languageCode,
  }) async {
    lookups++;
    if (failLookup) throw TimeoutException('Location lookup timed out');
    return const CurrentLocationArea(city: 'Cairo', district: 'Nasr City');
  }
}

class _NotificationDeviceSource implements NotificationDeviceDataSource {
  int registrations = 0;
  @override
  Future<void> start() async {}
  @override
  Future<void> registerCurrentDevice() async {
    registrations++;
  }

  @override
  Future<void> registerToken(String token) async {}
  @override
  Future<void> unregisterCurrentDevice() async {}
}

class _PropertySearchSource implements PropertySearchDataSource {
  PropertySearchFilters? request;
  @override
  String cacheKeyFor(PropertySearchFilters filters) => filters.cacheKey;
  @override
  Future<(PropertySearchResponseModel, PaginationData)> getPropertiesPage(
    PropertySearchFilters filters, {
    CancelToken? cancelToken,
  }) async {
    request = filters;
    return (
      PropertySearchResponseModel.fromJson(const {'count': 0, 'results': []}),
      PaginationData(perPage: 20, totalPages: 1),
    );
  }
}
