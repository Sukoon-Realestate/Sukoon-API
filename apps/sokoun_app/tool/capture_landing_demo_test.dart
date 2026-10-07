import 'dart:convert';
import 'dart:io';
import 'dart:ui' as ui;

// The capture harness uses the same image provider as melos_core's CachedImage.
// ignore: depend_on_referenced_packages
import 'package:cached_network_image/cached_network_image.dart';
// ignore: implementation_imports
import 'package:easy_localization/src/localization.dart';
// ignore: implementation_imports
import 'package:easy_localization/src/translations.dart';
import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:sokoun_app/features/main_view/presentation/models/home_navigation_destination.dart';
import 'package:sokoun_app/features/main_view/presentation/widgets/home_bottom_navigation.dart';
import 'package:sokoun_app/features/owner/home/data/models/owner_dashboard_model.dart';
import 'package:sokoun_app/features/owner/home/presentation/widgets/owner_widgets/owner_dashboard_content.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_details_model.dart';
import 'package:sokoun_app/features/tenant/home/data/models/tenant_property_content.dart';
import 'package:sokoun_app/features/tenant/home/presentation/widgets/tenant_property_details/details_body.dart';
import 'package:sokoun_app/features/tenant/home/presentation/widgets/tenant_widgets/tenant_home_header.dart';
import 'package:sokoun_app/features/tenant/home/presentation/widgets/tenant_widgets/tenant_property_card.dart';
import 'package:sokoun_app/features/tenant/visits/imports.dart';
import 'package:sokoun_app/shared_widgets/app_scaffold.dart';

// Tooling reuses the sibling app's illustration without a runtime dependency.
// ignore: avoid_relative_lib_imports
import '../../landing_page/lib/landing/widgets/shared/property_illustration.dart';
import '../test/helpers/feature_tools_test_dependencies.dart';

/// Opt-in asset export, kept outside the normal test suite.
/// Run from apps/sokoun_app with flutter test tool/capture_landing_demo_test.dart.
void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  const String output = String.fromEnvironment(
    'DEMO_CAPTURE_DIR',
    defaultValue: '../landing_page/tool/demo_video/captures',
  );
  const String imageUrl = 'https://demo.sokoon.invalid/interior.png';

  setUpAll(() async {
    await initializeFeatureTestEnvironment();
    await registerFeatureTestDependencies(FeatureTestRepository());
    Localization.load(
      const Locale('ar'),
      translations: Translations(
        jsonDecode(
              File(
                '../../packages/core/assets/translations/ar.json',
              ).readAsStringSync(),
            )
            as Map<String, dynamic>,
      ),
    );
    final FontLoader fonts = FontLoader(ConstantManager.fontFamily);
    for (final String weight in ['Regular', 'Medium', 'Bold', 'ExtraBold']) {
      fonts.addFont(
        rootBundle.load(
          'packages/melos_core/assets/fonts/Tajawal/Tajawal-$weight.ttf',
        ),
      );
    }
    await fonts.load();
    await (FontLoader(
      'MaterialIcons',
    )..addFont(rootBundle.load('fonts/MaterialIcons-Regular.otf'))).load();
  });

  testWidgets('capture the landing demo from Sokoun widgets', (tester) async {
    tester.view.physicalSize = const Size(390, 844);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.reset);
    final Directory destination = Directory(output);
    destination.createSync(recursive: true);

    // Use the landing page's local sample illustration for listing media. Seed
    // the image cache so rendering is deterministic and makes no HTTP requests.
    final GlobalKey illustrationKey = GlobalKey();
    await tester.pumpWidget(
      MaterialApp(
        home: Center(
          child: RepaintBoundary(
            key: illustrationKey,
            child: const SizedBox(
              width: 390,
              height: 220,
              child: PropertyIllustration(tint: Color(0xFFCBD5C5)),
            ),
          ),
        ),
      ),
    );
    await tester.pumpAndSettle();
    final RenderRepaintBoundary illustrationBoundary =
        illustrationKey.currentContext!.findRenderObject()!
            as RenderRepaintBoundary;
    late ui.Image illustration;
    await tester.runAsync(() async {
      illustration = await illustrationBoundary.toImage(pixelRatio: 2);
    });
    for (final (int?, int?) dimensions in [
      (96, 96),
      (null, 258),
      (64, 48),
      (58, 48),
    ]) {
      final CachedNetworkImageProvider original = CachedNetworkImageProvider(
        imageUrl,
        maxWidth: dimensions.$1,
        maxHeight: dimensions.$2,
      );
      for (final ImageProvider provider in [
        original,
        ResizeImage.resizeIfNeeded(dimensions.$1, dimensions.$2, original),
      ]) {
        final Object cacheKey = await provider.obtainKey(
          const ImageConfiguration(devicePixelRatio: 1),
        );
        PaintingBinding.instance.imageCache.putIfAbsent(
          cacheKey,
          () => OneFrameImageStreamCompleter(
            Future.value(ImageInfo(image: illustration.clone())),
          ),
        );
      }
    }
    illustration.dispose();

    final TenantPropertyDetailsContent property =
        TenantPropertyDetailsContent.fromModel(
          PropertyDetailsModel.fromJson({
            'id': 'demo-property',
            'owner_id': 'demo-owner',
            'title': 'شقة بإضاءة طبيعية في المعادي',
            'description':
                'شقة مفروشة قريبة من الخدمات بمساحات مريحة وإضاءة طبيعية.',
            'price': '6500',
            'price_period': 'monthly',
            'property_type': 'apartment',
            'bedrooms': 2,
            'bathrooms': 1,
            'space': '120',
            'rental_period': 6,
            'deposit': 'one_month',
            'is_verified': true,
            'city': {'name': 'المعادي'},
            'governorate': {'name': 'القاهرة'},
            'district': 'دجلة',
            'images': [
              {'id': 'demo-image', 'image': imageUrl, 'name': 'غرفة المعيشة'},
            ],
            'amenities': ['wifi', 'air_conditioning'],
          }),
        );

    Future<void> capture(String name, Widget Function() build) async {
      final GlobalKey boundaryKey = GlobalKey();
      await tester.pumpWidget(
        KeyedSubtree(
          key: UniqueKey(),
          child: featureTestHost(
            Builder(
              builder: (_) => RepaintBoundary(key: boundaryKey, child: build()),
            ),
          ),
        ),
      );
      await tester.pumpAndSettle();
      expect(tester.takeException(), isNull, reason: name);
      final RenderRepaintBoundary boundary =
          boundaryKey.currentContext!.findRenderObject()!
              as RenderRepaintBoundary;
      await tester.runAsync(() async {
        final ui.Image bitmap = await boundary.toImage(pixelRatio: 2);
        final data = await bitmap.toByteData(format: ui.ImageByteFormat.png);
        bitmap.dispose();
        await File(
          '$output/$name.png',
        ).writeAsBytes(data!.buffer.asUint8List());
      });
      await tester.pumpWidget(const SizedBox.shrink());
      await tester.pump();
    }

    Widget navigation({bool owner = false}) => HomeBottomNavigation(
      destinations: [
        HomeNavigationDestination(
          icon: Icons.home_outlined,
          selectedIcon: Icons.home_rounded,
          label: LocaleKeys.home,
        ),
        HomeNavigationDestination(
          icon: Icons.calendar_month_outlined,
          selectedIcon: Icons.calendar_month,
          label: LocaleKeys.tenantVisitsTitle,
        ),
        HomeNavigationDestination(
          icon: owner ? Icons.apartment_outlined : Icons.favorite_border,
          selectedIcon: owner ? Icons.apartment : Icons.favorite,
          label: owner
              ? LocaleKeys.landingListProperty
              : LocaleKeys.favoritesTitle,
        ),
      ],
      currentIndex: 0,
      onDestinationSelected: (_) {},
    );

    await capture(
      'discovery',
      () => AppScaffold(
        showBackButton: false,
        bottomBar: navigation(),
        body: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: 20),
          child: Column(
            children: [
              const TenantHomeHeader(banner: null),
              const SizedBox(height: 8),
              TenantPropertyCard(
                title: property.title,
                rating: '4.8',
                area: 'المعادي · القاهرة',
                price: '${property.price} ${property.pricePeriodLabel}',
                icon: Icons.apartment_outlined,
                imageUrl: imageUrl,
                imageCount: 4,
              ),
              const SizedBox(height: 14),
              const TenantPropertyCard(
                title: 'استوديو مفروش بالقرب من الجامعة',
                rating: '4.6',
                area: 'مدينة نصر · القاهرة',
                price: '4,200 ج.م / شهر',
                icon: Icons.apartment_outlined,
                imageUrl: imageUrl,
                imageCount: 3,
              ),
            ],
          ),
        ),
      ),
    );

    for (final bool saved in [false, true]) {
      await capture(
        saved ? 'property_saved' : 'property',
        () => AppScaffold(
          title: LocaleKeys.tenantFilterPropertyDetails,
          body: TenantPropertyDetailsBody(
            property: property,
            isSaved: saved,
            onSavedPressed: () {},
            onChatPressed: () {},
          ),
        ),
      );
    }

    final TextEditingController notes = TextEditingController();
    addTearDown(notes.dispose);
    for (final bool selected in [false, true]) {
      await capture(
        selected ? 'visit_selected' : 'visit',
        () => AppScaffold(
          title: LocaleKeys.tenantVisitBookTitle,
          body: BookVisitForm(
            property: VisitPropertyContent.fromPropertyDetails(property),
            days: const [
              VisitDayContent(
                weekday: 'السبت',
                day: '17',
                month: 'أكتوبر',
                visitDate: '2040-10-17',
              ),
              VisitDayContent(
                weekday: 'الأحد',
                day: '18',
                month: 'أكتوبر',
                visitDate: '2040-10-18',
              ),
              VisitDayContent(
                weekday: 'الاثنين',
                day: '19',
                month: 'أكتوبر',
                visitDate: '2040-10-19',
              ),
            ],
            selectedDayIndex: 0,
            selectedTime: selected
                ? const TimeOfDay(hour: 14, minute: 0)
                : null,
            noteController: notes,
            onDaySelected: (_) {},
            onTimeSelected: (_) {},
            onConfirmPressed: (_) async {},
            timeSelector: VisitAvailableTimes(
              date: '2040-10-17',
              slots: const [
                VisitTimeSlotContent(label: '10:00', visitTime: '10:00:00'),
                VisitTimeSlotContent(label: '14:00', visitTime: '14:00:00'),
                VisitTimeSlotContent(label: '16:00', visitTime: '16:00:00'),
              ],
              selectedTime: selected
                  ? const TimeOfDay(hour: 14, minute: 0)
                  : null,
              onSelected: (_) {},
            ),
          ),
        ),
      );
    }

    await capture(
      'owner',
      () => AppScaffold(
        showBackButton: false,
        title: LocaleKeys.landingOwnerDashboardPreviewLabel,
        bottomBar: navigation(owner: true),
        body: OwnerDashboardContent(
          dashboard: OwnerDashboardModel.fromJson({
            'active_properties': 3,
            'visits_this_week': 8,
            'overall_rating': 4.8,
            'pending_requests': 2,
            'pending_visits': [
              {
                'id': 'demo-visit',
                'tenant_name': 'أحمد محمد',
                'property_title': property.title,
                'property_district': 'المعادي',
                'scheduled_at': '17 أكتوبر · 2:00 مساءً',
              },
            ],
          }),
          onRequestResolved: () async {},
        ),
      ),
    );
    await injector.reset();
  });
}
