import 'package:flutter/material.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:melos_core/core/network/account_session.dart';
import 'package:sokoun_app/features/tenant/decision_tools/data/discovery_memory_data.dart';
import 'package:sokoun_app/features/tenant/decision_tools/data/models/discovery_memory.dart';
import 'package:sokoun_app/features/tenant/decision_tools/presentation/widgets/property_memory_badge.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  setUp(() {
    FlutterSecureStorage.setMockInitialValues({});
    AccountSession.begin('spacing-test');
  });
  tearDown(() async {
    AccountSession.end();
    await AccountSession.finishCleanup();
  });
  for (final direction in TextDirection.values) {
    testWidgets('seen badge has image gap and card gutters in $direction', (tester) async {
      await DiscoveryMemoryData.store().update((value) => value.viewed(
        PropertyBookmark(propertyId: 'seen', title: 'Home', at: DateTime.now()),
      ));
      await tester.pumpWidget(MaterialApp(home: Scaffold(body: Directionality(
        textDirection: direction,
        child: SizedBox(width: 320, child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            const SizedBox(key: ValueKey('image'), height: 180),
            const PropertyMemoryBadge(
              propertyId: 'seen',
              contentPadding: EdgeInsetsDirectional.fromSTEB(12, 12, 12, 0),
            ),
          ],
        )),
      ))));
      await tester.pumpAndSettle();
      final image = tester.getRect(find.byKey(const ValueKey('image')));
      final chip = tester.getRect(find.byType(Chip));
      expect(chip.top - image.bottom, greaterThanOrEqualTo(12));
      expect(chip.left, greaterThanOrEqualTo(12));
      expect(chip.right, lessThanOrEqualTo(308));
      expect(tester.takeException(), isNull);
    });
  }
  testWidgets('unseen badge reserves no blank margin', (tester) async {
    await tester.pumpWidget(const MaterialApp(home: Scaffold(body: Column(
      children: [PropertyMemoryBadge(
        key: ValueKey('memory'), propertyId: 'unseen',
        contentPadding: EdgeInsets.all(12),
      )],
    ))));
    await tester.pumpAndSettle();
    expect(tester.getSize(find.byKey(const ValueKey('memory'))).height, 0);
    expect(find.byType(Chip), findsNothing);
  });
}
