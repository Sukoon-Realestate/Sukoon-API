import 'dart:io';
import 'dart:ui' as ui;
import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:sokoun_app/features/shared/rental_offers/data/models/rental_selection.dart';
import 'package:sokoun_app/features/shared/rental_offers/data/models/rental_terms.dart';
import 'package:sokoun_app/features/shared/rental_offers/presentation/widgets/rental_selection_panel.dart';
import 'helpers/feature_tools_test_dependencies.dart';

const description = 'منزل عائلي بمدخل مستقل بمساحة 180 متر مربع في منطقة الاستاد، طنطا. يضم 3 غرف نوم و2 حمام، معيشة مضيئة ومطبخ مجهز ومساحات تخزين. مفروش ومجهز بالأجهزة الأساسية، بالقرب من الخدمات والمواصلات. الإيجار الشهري 10,000 جنيه مصري، التأمين شهر واحد ومدة العقد 12 شهرًا. مرافق الكهرباء والمياه حسب الاستهلاك. المعاينة بحجز موعد مسبق.';
const selection = RentalSelection(
  propertyId: 'readability', offerId: 'entire', scopeValue: 'entire_property',
  name: 'إيجار الوحدة بالكامل', availability: 'available',
  terms: RentalTerms(price: '10000', pricePeriod: 'monthly', minimumMonths: 12,
    deposit: '10000', suitableFor: 'families', description: description,
    smokingAllowed: false,
    rules: ['المعاينة بموعد مسبق', 'المرافق حسب الاستهلاك', 'احترام هدوء المبنى'],
  ),
);

void main() {
  setUpAll(initializeFeatureTestEnvironment);
  for (final locale in ['ar', 'en']) {
    for (final dark in [false, true]) {
      for (final width in [320.0, 390.0]) {
        for (final scale in [1.0, 2.0]) {
          testWidgets('rental details $locale dark=$dark width=$width scale=$scale', (tester) async {
            tester.view.physicalSize = Size(width, 844);
            tester.view.devicePixelRatio = 1;
            addTearDown(tester.view.reset);
            final boundary = GlobalKey();
            await tester.pumpWidget(featureTestHost(
              Scaffold(body: SingleChildScrollView(child: Padding(
                padding: const EdgeInsets.all(12),
                child: RepaintBoundary(key: boundary, child: const RentalSelectionPanel(selection: selection)),
              ))), locale: locale, dark: dark, scale: scale,
            ));
            await tester.pumpAndSettle();
            expect(find.text(description), findsOneWidget);
            expect(find.text(LocaleKeys.rentalOfferDescription), findsOneWidget);
            expect(find.text(LocaleKeys.rentalRules), findsOneWidget);
            expect(find.text('احترام هدوء المبنى'), findsOneWidget);
            final terms = tester.getRect(find.text(LocaleKeys.rentalOfferSuitability));
            final descriptionHeading = tester.getRect(find.text(LocaleKeys.rentalOfferDescription));
            final descriptionRect = tester.getRect(find.text(description));
            final rulesHeading = tester.getRect(find.text(LocaleKeys.rentalRules));
            expect(descriptionHeading.top - terms.bottom, greaterThanOrEqualTo(20));
            expect(rulesHeading.top - descriptionRect.bottom, greaterThanOrEqualTo(20));
            expect(tester.takeException(), isNull);
            if (locale == 'ar' && !dark && width == 390 && scale == 1) {
              await tester.runAsync(() async {
                final render = boundary.currentContext!.findRenderObject()! as RenderRepaintBoundary;
                final image = await render.toImage(pixelRatio: 2);
                final bytes = await image.toByteData(format: ui.ImageByteFormat.png);
                await File('/tmp/rental-details-readable-ar.png').writeAsBytes(bytes!.buffer.asUint8List());
                image.dispose();
              });
            }
          });
        }
      }
    }
  }
}
