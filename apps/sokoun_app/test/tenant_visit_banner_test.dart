import 'dart:io';
import 'dart:ui' as ui;

import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/network/account_session.dart';
import 'package:melos_core/core/network/api_endpoints.dart';
import 'package:sokoun_app/features/tenant/home/data/models/home_page_model.dart';
import 'package:sokoun_app/features/tenant/home/presentation/widgets/tenant_widgets/tenant_visit_banner.dart';
import 'package:sokoun_app/features/tenant/visits/imports.dart';
import 'package:sokoun_app/shared_widgets/app_scaffold.dart';

import 'helpers/feature_tools_test_dependencies.dart';
import 'helpers/home_page_test_dependencies.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  final banner = HomeVisitBannerModel.fromJson(homeVisitBannerFixture);

  setUpAll(() async {
    await initializeFeatureTestEnvironment();
    final fonts = FontLoader(ConstantManager.fontFamily);
    for (final weight in ['Regular', 'Medium', 'Bold']) {
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

  for (final language in ['ar', 'en']) {
    for (final double width in [320, 390, 600, 768, 1024, 1366]) {
      for (final double scale in [1, 1.3, 2]) {
        testWidgets('visit reminder $language $width text=$scale', (
          tester,
        ) async {
          await _pump(
            tester,
            banner,
            language: language,
            width: width,
            scale: scale,
          );
          expect(find.text('saudi arabia · any'), findsOneWidget);
          expect(
            find.text(
              language == 'ar'
                  ? 'عندك زيارة قريباً'
                  : 'You have an upcoming visit',
            ),
            findsOneWidget,
          );
          if (language == 'en') {
            expect(find.text('Oct 9, 2026 · 12:00 PM'), findsOneWidget);
          }
          expect(
            find.byIcon(
              language == 'ar'
                  ? Icons.chevron_left_rounded
                  : Icons.chevron_right_rounded,
            ),
            findsOneWidget,
          );
          expect(tester.takeException(), isNull);
          if (width == 390 && scale == 1) {
            await _capture(tester, language);
          }
        });
      }
    }
  }

  testWidgets(
    'server today flag chooses the heading independently of the clock',
    (tester) async {
      await _pump(tester, banner.copyWith(isToday: true));
      expect(find.text('You have a visit today'), findsOneWidget);
      expect(find.text('You have an upcoming visit'), findsNothing);
      expect(find.text('Oct 9, 2026 · 12:00 PM'), findsOneWidget);
      expect(tester.takeException(), isNull);
    },
  );

  testWidgets('visit reminder opens the confirmed visits collection', (
    tester,
  ) async {
    final network = FeatureTestNetwork();
    await registerFeatureTestDependencies(
      FeatureTestRepository(),
      network: network,
    );
    addTearDown(() async {
      await injector.reset();
      AccountSession.end();
    });

    await _pump(tester, banner);
    await tester.tap(find.byType(TenantVisitBanner));
    await tester.pumpAndSettle();

    expect(find.byType(TenantVisitsScreen), findsOneWidget);
    expect(network.requests.single.path, ApiConstants.tenantVisits);
    expect(tester.takeException(), isNull);
  });
}

Future<void> _pump(
  WidgetTester tester,
  HomeVisitBannerModel banner, {
  String language = 'en',
  double width = 390,
  double scale = 1,
}) async {
  tester.view.physicalSize = Size(width, 844);
  tester.view.devicePixelRatio = 1;
  addTearDown(tester.view.reset);
  await tester.pumpWidget(
    featureTestHost(
      RepaintBoundary(
        child: AppScaffold(
          title: 'Home',
          body: SingleChildScrollView(
            child: Padding(
              padding: const EdgeInsets.all(20),
              child: TenantVisitBanner(banner: banner),
            ),
          ),
        ),
      ),
      locale: language,
      scale: scale,
    ),
  );
  await tester.pumpAndSettle();
}

Future<void> _capture(WidgetTester tester, String language) async {
  const directory = String.fromEnvironment('TENANT_BANNER_UI_REVIEW_DIR');
  if (directory.isEmpty) return;
  await tester.runAsync(() async {
    final boundary = tester.renderObject<RenderRepaintBoundary>(
      find.byType(RepaintBoundary).first,
    );
    final image = await boundary.toImage();
    final bytes = await image.toByteData(format: ui.ImageByteFormat.png);
    await Directory(directory).create(recursive: true);
    await File(
      '$directory/banner-$language.png',
    ).writeAsBytes(bytes!.buffer.asUint8List());
    image.dispose();
  });
}
