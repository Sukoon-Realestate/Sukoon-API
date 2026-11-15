import 'dart:io';
import 'dart:ui' as ui;
import 'package:sokoun_app/shared_widgets/app_scaffold.dart';
import 'package:sokoun_app/features/shared/rental_offers/data/models/rental_selection.dart';
import 'package:sokoun_app/features/shared/rental_offers/data/models/rental_terms.dart';
import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:sokoun_app/features/tenant/visits/imports.dart';
import 'package:sokoun_app/features/shared/visit_decisions/presentation/widgets/viewing_arrival_entry.dart';
import 'package:sokoun_app/features/shared/visit_decisions/presentation/widgets/viewing_times_entry.dart';
import 'package:sokoun_app/features/shared/visit_decisions/presentation/screens/viewing_times_screen.dart';
import 'helpers/feature_tools_test_dependencies.dart';

const visit = TenantVisitContent(
  id: 'clean-visit',
  propertyId: 'clean-property',
  propertyTitle: 'منزل عائلي بمدخل مستقل في منطقة الاستاد - طنطا',
  day: '',
  time: '',
  status: TenantVisitStatus.pending,
  statusText: '',
  ownerName: 'Cycle QA owner_b',
  rentalSelection: RentalSelection(
    propertyId: 'clean-property',
    offerId: 'entire',
    scopeValue: 'entire_property',
    name: 'إيجار الوحدة بالكامل',
    terms: RentalTerms(
      price: '10000',
      pricePeriod: 'monthly',
      minimumMonths: 12,
    ),
  ),
);

void main() {
  setUpAll(initializeFeatureTestEnvironment);
  setUp(() async {
    final repository = FeatureTestRepository();
    repository.replies['features/v1/experience/capabilities/'] = const FeatureTestReply(data: {'features': ['sync']});
    await registerFeatureTestDependencies(repository);
  });
  for (final width in [320.0, 390.0]) {
  for (final locale in ['ar', 'en']) {
    for (final dark in [false, true]) {
      for (final scale in [1.0, 2.0]) {
        for (final reduced in [false, true]) {
          testWidgets(
            'visit details $locale width=$width dark=$dark scale=$scale reduced=$reduced',
            (tester) async {
              tester.view.physicalSize = Size(width, 844);
              tester.view.devicePixelRatio = 1;
              addTearDown(tester.view.reset);
              final boundary = GlobalKey();
              await tester.pumpWidget(
                featureTestHost(
                  RepaintBoundary(
                    key: boundary,
                    child: AppScaffold(
                      title: LocaleKeys.tenantVisitDetailsTitle,
                      showBackButton: true,
                      body: VisitDetailsContent(visit: visit, fresh: true),
                    ),
                  ),
                  locale: locale,
                  dark: dark,
                  scale: scale,
                  reducedMotion: reduced,
                ),
              );
              await tester.pumpAndSettle();
              expect(find.byType(ViewingArrivalEntry), findsOneWidget);
              expect(find.byType(ViewingTimesEntry), findsOneWidget);
              final status = tester.getRect(find.byType(VisitStatusHeader));
              final property = tester.getRect(find.text(visit.propertyTitle));
              final tools = tester.getRect(find.text(LocaleKeys.toolsTitle));
              expect(status.bottom, lessThan(property.top));
              expect(property.bottom, lessThan(tools.top));
              expect(property.left, greaterThanOrEqualTo(20));
              expect(property.right, lessThanOrEqualTo(width - 20));
              expect(
                find.text(LocaleKeys.tenantVisitSummaryStatus),
                findsNothing,
              );
              if (scale == 1) {
                final arrival = find.descendant(
                  of: find.byType(ViewingArrivalEntry),
                  matching: find.byType(TextButton),
                );
                expect(
                  tester.getSize(arrival).height,
                  greaterThanOrEqualTo(48),
                );
              }
              expect(tester.takeException(), isNull);
              if (width == 390 && locale == 'ar' && !dark && scale == 1 && reduced) {
                await tester.runAsync(() async {
                  final render =
                      boundary.currentContext!.findRenderObject()!
                          as RenderRepaintBoundary;
                  final image = await render.toImage(pixelRatio: 2);
                  final bytes = await image.toByteData(
                    format: ui.ImageByteFormat.png,
                  );
                  await File(
                    '/tmp/visit-details-clean-ar.png',
                  ).writeAsBytes(bytes!.buffer.asUint8List());
                  image.dispose();
                });
              }
            },
          );
        }
      }
    }
  }
  }
  testWidgets('appointment tool navigates and refreshes on return', (
    tester,
  ) async {
    var refreshes = 0;
    await tester.pumpWidget(
      featureTestHost(
        Scaffold(
          body: VisitDetailsContent(
            visit: visit,
            fresh: true,
            onRefresh: () async {
              refreshes++;
            },
          ),
        ),
        reducedMotion: false,
      ),
    );
    await tester.pumpAndSettle();
    final action = find.byType(ViewingTimesEntry);
    await tester.ensureVisible(action);
    await tester.tap(action);
    await tester.pumpAndSettle();
    expect(find.byType(ViewingTimesScreen), findsOneWidget);
    await tester.tap(find.byIcon(Icons.arrow_back_ios_new_rounded));
    await tester.pumpAndSettle();
    expect(refreshes, 1);
    expect(find.text(visit.propertyTitle), findsOneWidget);
    expect(tester.takeException(), isNull);
  });
}
