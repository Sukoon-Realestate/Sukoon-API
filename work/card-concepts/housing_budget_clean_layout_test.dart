import 'dart:io';
import 'dart:ui' as ui;
import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:sokoun_app/features/tenant/decision_tools/presentation/widgets/housing_budget_form.dart';
import 'package:sokoun_app/features/tenant/decision_tools/data/models/housing_budget.dart';
import 'package:sokoun_app/features/tenant/decision_tools/data/models/property_cost_breakdown.dart';
import 'helpers/feature_tools_test_dependencies.dart';

void main() {
  setUpAll(initializeFeatureTestEnvironment);
  for (final locale in ['ar', 'en']) {
    for (final dark in [false, true]) {
      for (final width in [320.0, 390.0]) {
        for (final scale in [1.0, 2.0]) {
          testWidgets('budget $locale dark=$dark width=$width scale=$scale', (tester) async {
            tester.view.physicalSize = Size(width, 900);
            tester.view.devicePixelRatio = 1;
            addTearDown(tester.view.reset);
            final boundary = GlobalKey();
            HousingBudget? saved;
            await tester.pumpWidget(featureTestHost(Scaffold(body: Align(
              alignment: Alignment.bottomCenter,
              child: RepaintBoundary(key: boundary, child: HousingBudgetForm(
                value: const HousingBudget(),
                cost: const PropertyCostBreakdown(rent: 10000, deposit: 10000, period: 'monthly'),
                fingerprint: 'fixture', busy: false, failed: false,
                onSave: (value) async { saved = value; return true; },
              )),
            )), locale: locale, dark: dark, scale: scale));
            await tester.pumpAndSettle();
            expect(tester.takeException(), isNull);
            final field = find.byType(TextFormField).first;
            await tester.ensureVisible(field);
            await tester.pumpAndSettle();
            await tester.enterText(field, '500');
            tester.testTextInput.hide();
            await tester.pumpAndSettle();
            final firstPeriod = find.byType(DropdownButtonFormField<BudgetPeriod>).first;
            expect(tester.getRect(firstPeriod).top - tester.getRect(field).bottom, greaterThanOrEqualTo(10));
            if (locale == 'ar' && !dark && width == 390 && scale == 1) {
              await tester.drag(find.byType(SingleChildScrollView).first, const Offset(0, 1000));
              await tester.pumpAndSettle();
              await tester.runAsync(() async {
                final render = boundary.currentContext!.findRenderObject()! as RenderRepaintBoundary;
                final image = await render.toImage(pixelRatio: 2);
                final bytes = await image.toByteData(format: ui.ImageByteFormat.png);
                await File('/tmp/housing-budget-clean-ar.png').writeAsBytes(bytes!.buffer.asUint8List());
                image.dispose();
              });
            }
            final save = find.text(LocaleKeys.exSaveCalculate);
            await tester.scrollUntilVisible(save, 250, scrollable: find.byType(Scrollable).first);
            await tester.tap(save);
            await tester.pumpAndSettle();
            expect(saved!.estimates['utilities']!.minor, 50000);
            expect(saved!.estimates['internet']!.minor, isNull);
            expect(find.text(LocaleKeys.exBudgetSaved), findsOneWidget);
            expect(tester.takeException(), isNull);
          });
        }
      }
    }
  }
}
