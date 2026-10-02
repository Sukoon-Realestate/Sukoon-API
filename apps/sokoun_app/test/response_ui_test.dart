import 'dart:convert';
import 'dart:io';
import 'dart:ui' as ui;

import 'package:easy_localization/easy_localization.dart';
import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';
import 'package:flutter/services.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:melos_core/config/language/languages.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/helpers/cache_service.dart';
import 'package:sokoun_app/features/owner/home/presentation/widgets/owner_visit_requests/owner_visit_request_card.dart';
import 'package:sokoun_app/features/owner/home/presentation/widgets/owner_visit_requests/owner_visit_request_identity_row.dart';
import 'package:sokoun_app/features/owner/visits/imports.dart';
import 'package:sokoun_app/features/shared/profile/imports.dart';
import 'package:sokoun_app/features/tenant/home/data/models/home_page_model.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_details_model.dart';
import 'package:sokoun_app/features/tenant/home/data/models/tenant_property_content.dart';
import 'package:sokoun_app/features/tenant/home/presentation/screens/tenant_property_photos_screen.dart';
import 'package:sokoun_app/features/tenant/home/presentation/widgets/tenant_property_details/rental_details.dart';
import 'package:sokoun_app/features/tenant/home/presentation/widgets/tenant_widgets/home_property_item.dart';
import 'package:sokoun_app/shared_widgets/app_scaffold.dart';
import 'package:sokoun_app/shared_widgets/sokoun_layout.dart';
import 'package:sokoun_app/shared_widgets/sokoun_theme.dart';

import 'helpers/collection_responses.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  const output = String.fromEnvironment('UI_REVIEW_DIR');

  setUpAll(() async {
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(
          const MethodChannel('plugins.flutter.io/shared_preferences'),
          (call) async => call.method == 'getAll' ? <String, Object>{} : true,
        );
    await EasyLocalization.ensureInitialized();
    await CacheStorage.init();
    if (output.isNotEmpty) {
      final FontLoader fonts = FontLoader(ConstantManager.fontFamily);
      for (final weight in [
        'Regular',
        'Medium',
        'Bold',
        'ExtraBold',
        'Black',
      ]) {
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
    }
  });

  final property = PropertyDetailsModel.fromJson(
    collectionResponseData(r'/properties/[a-f0-9-]+/$'),
  );
  final propertyContent = TenantPropertyDetailsContent.fromModel(property);
  final photoIndex = propertyContent.photoDescriptions.indexWhere(
    (description) => description.isNotEmpty,
  );
  final calendar = OwnerVisitCalendarContent.fromJson(
    collectionResponseData(r'/properties/owner/calendar/$'),
  );
  final requests = OwnerVisitRequestContent.listFromResponse(
    collectionResponseData(r'/properties/owner/visits/requests/$'),
  );
  final request = requests.firstWhere(
    (item) => item.verificationWarning.isNotEmpty,
  );
  final account = AccountContent.fromJson(
    collectionResponseData(r'/profiles/my-account/$'),
  );
  final home = HomePageModel.fromJson(
    collectionResponseData(r'/homepage/$'),
  ).results.first;

  Widget scroll(Widget child) => AppScaffold(
    showBackButton: false,
    body: SingleChildScrollView(
      padding: const EdgeInsets.all(20),
      child: child,
    ),
  );
  Widget screenFor(String subject) => switch (subject) {
    'discovery' => scroll(
      HomePropertyItem(property: home.copyWith(mainImage: '')),
    ),
    'rental_details' => scroll(
      TenantPropertyRentalDetails(property: propertyContent),
    ),
    'owner_request' => scroll(
      OwnerVisitRequestCard(
        request: request,
        onPressed: null,
        onAcceptPressed: null,
        onRejectPressed: null,
      ),
    ),
    'calendar' => AppScaffold(
      showBackButton: false,
      contentWidth: SokounContentWidth.readable,
      body: OwnerCalendarContent(
        calendar: calendar,
        selectedDate: calendar.selectedDateValue,
        onDaySelected: (_) {},
        onAvailabilityPressed: null,
      ),
    ),
    'profile_actions' => scroll(
      TenantProfileActions(menuItems: account.menuItems),
    ),
    _ => TenantPropertyPhotosScreen(
      property: propertyContent,
      initialIndex: photoIndex < 0 ? 0 : photoIndex,
    ),
  };

  for (final width in [320.0, 390.0, 600.0, 768.0, 1024.0, 1366.0]) {
    for (final scale in [1.0, 1.3, 2.0]) {
      for (final locale in ['ar', 'en']) {
        for (final subject in [
          'discovery',
          'rental_details',
          'owner_request',
          'calendar',
          'profile_actions',
          'gallery',
        ]) {
          testWidgets('response $subject $locale width=$width text=$scale', (
            tester,
          ) async {
            tester.view.physicalSize = Size(width, width > 900 ? 768 : 844);
            tester.view.devicePixelRatio = 1;
            addTearDown(tester.view.reset);
            await tester.pumpWidget(
              _localized(screenFor(subject), locale: locale, scale: scale),
            );
            await tester.pump();
            await tester.pump(const Duration(milliseconds: 250));
            switch (subject) {
              case 'discovery':
                if (home.imagesCount > 0) {
                  expect(find.text('${home.imagesCount}'), findsOneWidget);
                }
                if (home.rate > 5 || home.rate < 0) {
                  expect(find.text('—'), findsOneWidget);
                }
              case 'rental_details':
                expect(
                  find.text(LocaleKeys.tenantPropertyDetailsRentalDetails),
                  findsOneWidget,
                );
                expect(
                  find.text(
                    property.smokingAllowed == true
                        ? LocaleKeys.tenantPropertyDetailsSmokingAllowed
                        : LocaleKeys.tenantPropertyDetailsSmokingNotAllowed,
                  ),
                  findsOneWidget,
                );
              case 'owner_request':
                expect(find.text(request.verificationWarning), findsOneWidget);
                expect(find.text(request.subtitle), findsOneWidget);
                expect(find.text(request.statusLabel), findsOneWidget);
              case 'calendar':
                expect(find.text(calendar.selectedDateLabel), findsOneWidget);
                expect(
                  find.text(calendar.visits.single.timeFormatted),
                  findsOneWidget,
                );
                expect(
                  find.text(calendar.visits.single.statusLabel),
                  findsOneWidget,
                );
              case 'profile_actions':
                expect(
                  find.text(account.menuItems.visitRequests.title),
                  findsOneWidget,
                );
                expect(
                  find.text(account.menuItems.verification.subtitle),
                  findsOneWidget,
                );
              case 'gallery':
                if (photoIndex >= 0) {
                  expect(
                    find.text(propertyContent.photoDescriptions[photoIndex]),
                    findsOneWidget,
                  );
                }
            }
            expect(tester.takeException(), isNull);
            if (output.isNotEmpty &&
                [390.0, 1024.0].contains(width) &&
                [1.0, 2.0].contains(scale)) {
              final RenderRepaintBoundary boundary = tester.renderObject(
                find.byType(RepaintBoundary).first,
              );
              await tester.runAsync(() async {
                final image = await boundary.toImage();
                final bytes = await image.toByteData(
                  format: ui.ImageByteFormat.png,
                );
                await Directory(output).create(recursive: true);
                await File(
                  '$output/response-$subject-$locale-${width.toInt()}-text-$scale.png',
                ).writeAsBytes(bytes!.buffer.asUint8List());
                image.dispose();
              });
            }
            await tester.pumpWidget(const SizedBox.shrink());
          });
        }
      }
    }
  }

  testWidgets('rental details omit unspecified rules', (tester) async {
    await tester.pumpWidget(
      _localized(
        scroll(
          TenantPropertyRentalDetails(
            property: TenantPropertyDetailsContent.fromModel(
              const PropertyDetailsModel.initial(),
            ),
          ),
        ),
      ),
    );
    await tester.pumpAndSettle();
    expect(
      find.text(LocaleKeys.tenantPropertyDetailsRentalDetails),
      findsNothing,
    );
  });

  testWidgets('verified tenants do not show an outdated warning', (
    tester,
  ) async {
    await tester.pumpWidget(
      _localized(
        scroll(
          OwnerVisitRequestCard(
            request: request.copyWith(isVerified: true),
            onPressed: null,
            onAcceptPressed: null,
            onRejectPressed: null,
          ),
        ),
      ),
    );
    await tester.pumpAndSettle();
    expect(find.text(request.verificationWarning), findsNothing);
  });

  testWidgets('backend permission disables the owner request chat button', (
    tester,
  ) async {
    await tester.pumpWidget(
      _localized(
        scroll(
          OwnerVisitRequestIdentityRow(
            request: request.copyWith(
              actions: request.actions!.copyWith(canChat: false),
            ),
          ),
        ),
      ),
    );
    await tester.pumpAndSettle();
    expect(
      tester.widget<IconButton>(find.byType(IconButton)).onPressed,
      isNull,
    );
  });

  testWidgets('calendar exposes counts and keeps day selection accessible', (
    tester,
  ) async {
    int selections = 0;
    final semantics = tester.ensureSemantics();
    try {
      await tester.pumpWidget(
        _localized(
          scroll(
            OwnerCalendarDay(
              day: 1,
              isSelected: true,
              hasVisit: true,
              visitCount: 2,
              onPressed: () => selections++,
            ),
          ),
        ),
      );
      await tester.pumpAndSettle();
      final label = LocaleKeys.ownerCalendarDayVisitCount
          .replaceAll('{day}', '1')
          .replaceAll('{count}', '2');
      expect(find.bySemanticsLabel(label), findsOneWidget);
      expect(
        tester
            .getSemantics(find.bySemanticsLabel(label))
            .getSemanticsData()
            .hasAction(ui.SemanticsAction.tap),
        isTrue,
      );
      await tester.tap(find.bySemanticsLabel(label));
      expect(selections, 1);
    } finally {
      semantics.dispose();
    }
  });
}

Widget _localized(Widget screen, {String locale = 'en', double scale = 1}) =>
    EasyLocalization(
      supportedLocales: Languages.supportedLocales,
      path: Languages.translationsPath,
      startLocale: Locale(locale),
      saveLocale: false,
      assetLoader: const _Translations(),
      child: ScreenUtilInit(
        designSize: const Size(360, 690),
        enableScaleWH: () => false,
        enableScaleText: () => false,
        fontSizeResolver: (size, _) => size.toDouble(),
        builder: (context, _) => MaterialApp(
          theme: SokounTheme.light,
          locale: context.locale,
          supportedLocales: context.supportedLocales,
          localizationsDelegates: context.localizationDelegates,
          home: MediaQuery(
            data: MediaQuery.of(context).copyWith(
              textScaler: TextScaler.linear(scale),
              disableAnimations: true,
            ),
            child: RepaintBoundary(child: screen),
          ),
        ),
      ),
    );

class _Translations extends AssetLoader {
  const _Translations();
  @override
  Future<Map<String, dynamic>> load(String path, Locale locale) async =>
      jsonDecode(
            File(
              '../../packages/core/assets/translations/${locale.languageCode}.json',
            ).readAsStringSync(),
          )
          as Map<String, dynamic>;
}
