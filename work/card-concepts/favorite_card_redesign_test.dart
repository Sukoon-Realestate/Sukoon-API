import 'dart:io';
import 'dart:ui' as ui;
import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:sokoun_app/features/tenant/favorites/data/models/favorites_content.dart';
import 'package:sokoun_app/features/tenant/favorites/presentation/widgets/favorite_property_card.dart';
import 'package:sokoun_app/features/tenant/favorites/presentation/widgets/favorite_offer_row.dart';
import 'package:sokoun_app/features/shared/rental_offers/data/models/rental_selection.dart';
import 'package:sokoun_app/features/shared/rental_offers/data/models/rental_terms.dart';
import 'helpers/feature_tools_test_dependencies.dart';

FavoritePropertyContent fixture(String kind) => FavoritePropertyContent(
  id: 'saved-card', mainImage: '',
  title: 'شقة عائلية واسعة في حي الجامعة - المنصورة',
  city: 'المنصورة', district: 'حي الجامعة',
  propertyType: 'apartment', isFurnished: true,
  bedrooms: 3, bathrooms: 2, area: 150,
  price: '9500', pricePeriod: 'monthly', rating: 4.8,
  savedAt: '', isSaved: true,
  rentalSchemaVersion: kind == 'legacy' ? null : 1,
  savedOffers: kind == 'legacy' ? [] : [
    kind == 'missing'
      ? const RentalSelection(offerId: 'missing-offer')
      : const RentalSelection(
          offerId: 'room-offer', scopeValue: 'room', name: 'الغرفة المطلة على الحديقة',
          availability: 'available', capacity: 2, bathroomAccess: ['shared'],
          terms: RentalTerms(price: '2500', pricePeriod: 'monthly'),
        ),
  ],
);

void main() {
  setUpAll(initializeFeatureTestEnvironment);
  setUp(() => registerFeatureTestDependencies(FeatureTestRepository()));
  for (final kind in ['missing', 'offer', 'legacy']) {
    for (final locale in ['ar', 'en']) {
      for (final width in [320.0, 390.0]) {
        for (final dark in [false, true]) {
          for (final scale in [1.0, 2.0]) {
            testWidgets('saved card $kind $locale $width dark=$dark scale=$scale', (tester) async {
              tester.view.physicalSize = Size(width, 1100);
              tester.view.devicePixelRatio = 1;
              addTearDown(tester.view.reset);
              final boundary = GlobalKey();
              await tester.pumpWidget(featureTestHost(
                Scaffold(body: SingleChildScrollView(child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: RepaintBoundary(key: boundary, child: FavoritePropertyCard(
                    item: fixture(kind), onRemove: () {}, onOfferRemoved: () {},
                  )),
                ))),
                locale: locale, dark: dark, scale: scale,
              ));
              await tester.pumpAndSettle();
              expect(find.text(fixture(kind).title), findsOneWidget);
              expect(tester.takeException(), isNull);
              if (kind == 'missing') {
                expect(find.text(LocaleKeys.rentalSnapshotMissing), findsOneWidget);
                expect(find.text(LocaleKeys.rentalUnknownAvailability), findsOneWidget);
                expect(find.byType(FavoriteOfferRow), findsOneWidget);
              }
              final remove = find.byTooltip(LocaleKeys.favoriteRemoveSemanticLabel);
              expect(remove, findsOneWidget);
              final rect = tester.getRect(remove);
              expect(rect.width, greaterThanOrEqualTo(48));
              expect(rect.height, greaterThanOrEqualTo(48));
              final organize = find.byTooltip(LocaleKeys.personalOrganize);
              expect(organize, findsOneWidget);
              if (kind != 'legacy') {
                expect((tester.getCenter(organize).dy - tester.getCenter(remove).dy).abs(), lessThan(1));
              }
              if (locale == 'ar' && width == 390 && !dark && scale == 1) {
                await tester.runAsync(() async {
                  final render = boundary.currentContext!.findRenderObject()! as RenderRepaintBoundary;
                  final image = await render.toImage(pixelRatio: 2);
                  final bytes = await image.toByteData(format: ui.ImageByteFormat.png);
                  await File('/tmp/favorite-card-$kind-ar.png').writeAsBytes(bytes!.buffer.asUint8List());
                  image.dispose();
                });
              }
            });
          }
        }
      }
    }
  }
  testWidgets('organize opens the same persisted folder and pin sheet', (tester) async {
    await tester.pumpWidget(featureTestHost(Scaffold(body: SingleChildScrollView(
      child: FavoritePropertyCard(item: fixture('missing'), onRemove: () {}, onOfferRemoved: () {}),
    )), reducedMotion: false));
    await tester.pumpAndSettle();
    final organize = find.byTooltip(LocaleKeys.personalOrganize);
    await tester.ensureVisible(organize);
    await tester.tap(organize);
    await tester.pumpAndSettle();
    expect(find.text(LocaleKeys.personalPin), findsOneWidget);
    expect(find.text(LocaleKeys.personalDeviceOnly), findsOneWidget);
    expect(tester.takeException(), isNull);
  });
  testWidgets('legacy removal keeps its callback', (tester) async {
    var removes = 0;
    await tester.pumpWidget(featureTestHost(Scaffold(body: SingleChildScrollView(
      child: FavoritePropertyCard(item: fixture('legacy'), onRemove: () => removes++),
    ))));
    await tester.pumpAndSettle();
    await tester.tap(find.byTooltip(LocaleKeys.favoriteRemoveSemanticLabel));
    await tester.pumpAndSettle();
    expect(removes, 1);
    expect(tester.takeException(), isNull);
  });
}
