import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:melos_core/core/helpers/cache_service.dart';
import 'package:melos_core/core/network/account_session.dart';
import 'package:sokoun_app/features/shared/contact/presentation/widgets/visit_contact_refresh.dart';
import 'package:sokoun_app/features/shared/notifications/data/foreground_notification_bus.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  const channel = MethodChannel('plugins.flutter.io/shared_preferences');

  setUpAll(() async {
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(
          channel,
          (call) async => call.method == 'getAll' ? <String, Object>{} : true,
        );
    await CacheStorage.init();
  });

  setUp(() async {
    AccountSession.begin('account');
    await CacheStorage.write('user', {'id': 'account', 'is_verified': true});
  });

  tearDown(() async {
    AccountSession.end();
    await CacheStorage.delete('user');
  });

  tearDownAll(() {
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(channel, null);
  });

  testWidgets('collections refresh for any acceptance and app resume', (
    tester,
  ) async {
    int refreshes = 0;
    await tester.pumpWidget(
      MaterialApp(
        home: VisitContactRefresh(
          onRefresh: () async => refreshes++,
          child: const SizedBox.shrink(),
        ),
      ),
    );
    _notify('visit_accepted', 'one', visitId: 'visit');
    _notify('visit_rejected', 'two', visitId: 'visit');
    await tester.pump();
    expect(refreshes, 1);
    tester.binding.handleAppLifecycleStateChanged(AppLifecycleState.resumed);
    await tester.pump();
    expect(refreshes, 2);

    await tester.pumpWidget(const SizedBox.shrink());
    _notify('visit_accepted', 'three', visitId: 'visit');
    expect(refreshes, 2);
  });

  testWidgets('details refresh only for the requested visit or property', (
    tester,
  ) async {
    int refreshes = 0;
    await tester.pumpWidget(
      MaterialApp(
        home: VisitContactRefresh(
          visitId: 'target-visit',
          propertyId: 'target-property',
          onRefresh: () async => refreshes++,
          child: const SizedBox.shrink(),
        ),
      ),
    );
    _notify('visit_accepted', 'one', visitId: 'unrelated');
    expect(refreshes, 0);
    _notify('visit_accepted', 'two', visitId: 'target-visit');
    _notify('visit_accepted', 'three', propertyId: 'target-property');
    expect(refreshes, 2);
  });

  testWidgets('account replacement prevents old screens from refreshing', (
    tester,
  ) async {
    int refreshes = 0;
    await tester.pumpWidget(
      MaterialApp(
        home: VisitContactRefresh(
          onRefresh: () async => refreshes++,
          child: const SizedBox.shrink(),
        ),
      ),
    );
    AccountSession.begin('new-account');
    _notify('visit_accepted', 'one');
    tester.binding.handleAppLifecycleStateChanged(AppLifecycleState.resumed);
    await tester.pump();
    expect(refreshes, 0);
  });
}

void _notify(
  String kind,
  String id, {
  String visitId = '',
  String propertyId = '',
}) {
  ForegroundNotificationBus.receive({
    'notification_type': kind,
    'notification_id': id,
    'visit_id': visitId,
    'property_id': propertyId,
  });
}
