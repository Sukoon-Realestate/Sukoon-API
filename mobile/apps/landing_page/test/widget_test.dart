import 'dart:convert';
import 'dart:io';

// ignore: implementation_imports
import 'package:easy_localization/src/localization.dart';
// ignore: implementation_imports
import 'package:easy_localization/src/translations.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:landing_page/landing/pages/landing_page.dart';
import 'package:landing_page/landing/theme/landing_theme.dart';
import 'package:landing_page/landing/widgets/shared/audience_toggle.dart';
import 'package:landing_page/landing/widgets/audience_features/audience_features_section.dart';
import 'package:landing_page/landing/widgets/how_it_works/how_it_works_section.dart';
import 'package:landing_page/landing/widgets/shared/scroll_reveal.dart';
import 'package:landing_page/landing/models/landing_content.dart';
import 'package:melos_core/config/language/languages.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  late Map<String, dynamic> arabicTranslations;
  late Map<String, dynamic> englishTranslations;

  setUpAll(() async {
    final translationsDirectory = Platform.script.resolve(
      '../../packages/core/assets/translations/',
    );
    arabicTranslations =
        jsonDecode(
              await File.fromUri(
                translationsDirectory.resolve('ar.json'),
              ).readAsString(),
            )
            as Map<String, dynamic>;
    englishTranslations =
        jsonDecode(
              await File.fromUri(
                translationsDirectory.resolve('en.json'),
              ).readAsString(),
            )
            as Map<String, dynamic>;
  });

  Widget buildApp(Locale locale) {
    final activeTranslations = locale.languageCode == 'ar'
        ? arabicTranslations
        : englishTranslations;
    Localization.load(locale, translations: Translations(activeTranslations));

    return MaterialApp(
      debugShowCheckedModeBanner: false,
      theme: LandingTheme.theme,
      home: Directionality(
        textDirection: locale.languageCode == 'ar'
            ? TextDirection.rtl
            : TextDirection.ltr,
        child: const LandingPage(),
      ),
    );
  }

  testWidgets('renders the Sokoon landing-page hero', (tester) async {
    tester.view.physicalSize = const Size(1440, 900);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    await tester.pumpWidget(buildApp(Languages.arabic.locale));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 500));
    await tester.pumpAndSettle();

    expect(find.text('سكنك المناسب،\nبطريقة أسهل وأأمن'), findsOneWidget);
    expect(find.text('ابحث عن سكن'), findsOneWidget);
    expect(find.text('اعرض عقارك'), findsWidgets);
  });

  testWidgets('switches the audience feature content', (tester) async {
    tester.view.physicalSize = const Size(1440, 900);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    await tester.pumpWidget(buildApp(Languages.arabic.locale));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 500));
    await tester.pumpAndSettle();
    await tester.scrollUntilVisible(
      find.byType(AudienceFeaturesSection),
      500,
      scrollable: find.byType(Scrollable).first,
    );
    await tester.pumpAndSettle();
    final audienceToggle = find.descendant(
      of: find.byType(AudienceFeaturesSection),
      matching: find.byType(AudienceToggle),
    );

    await tester.tap(
      find.descendant(of: audienceToggle, matching: find.text('للمالك')),
    );
    await tester.pump(const Duration(milliseconds: 300));

    expect(find.text('اعرض عقارك وأدر كل شيء من مكان واحد'), findsOneWidget);
    expect(find.text('إدارة طلبات الزيارة'), findsOneWidget);
    await tester.scrollUntilVisible(
      find.byType(HowItWorksSection),
      400,
      scrollable: find.byType(Scrollable).first,
    );
    await tester.pumpAndSettle();
    expect(
      tester.widget<HowItWorksSection>(find.byType(HowItWorksSection)).audience,
      Audience.owner,
    );
  });

  testWidgets('renders all sections without overflow on mobile', (
    tester,
  ) async {
    tester.view.physicalSize = const Size(390, 844);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    await tester.pumpWidget(buildApp(Languages.english.locale));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 500));
    await tester.pumpAndSettle();

    expect(find.byIcon(Icons.menu_rounded), findsOneWidget);
    expect(find.text('Your ideal home\nmade easier and safer'), findsOneWidget);

    for (var index = 0; index < 18; index++) {
      await tester.drag(find.byType(CustomScrollView), const Offset(0, -700));
      await tester.pump(const Duration(milliseconds: 80));
    }
  });
  for (final locale in [Languages.arabic.locale, Languages.english.locale]) {
    testWidgets('all sections fit at 320px in ${locale.languageCode}', (
      tester,
    ) async {
      tester.view.physicalSize = const Size(320, 780);
      tester.view.devicePixelRatio = 1;
      addTearDown(tester.view.resetPhysicalSize);
      addTearDown(tester.view.resetDevicePixelRatio);
      await tester.pumpWidget(buildApp(locale));
      await tester.pumpAndSettle();
      for (var index = 0; index < 30; index++) {
        await tester.drag(find.byType(CustomScrollView), const Offset(0, -500));
        await tester.pumpAndSettle();
      }
    });
  }

  testWidgets('reduced motion reveals content without waiting for animation', (
    tester,
  ) async {
    await tester.pumpWidget(
      const MaterialApp(
        home: MediaQuery(
          data: MediaQueryData(disableAnimations: true),
          child: ScrollReveal(delay: 400, child: Text('Visible immediately')),
        ),
      ),
    );
    expect(
      tester
          .widget<FadeTransition>(
            find.descendant(
              of: find.byType(ScrollReveal),
              matching: find.byType(FadeTransition),
            ),
          )
          .opacity
          .value,
      1,
    );
    await tester.pumpWidget(const SizedBox.shrink());
    expect(tester.takeException(), isNull);
  });

  testWidgets(
    'header navigation selects owner and reaches launch information',
    (tester) async {
      tester.view.physicalSize = const Size(1440, 900);
      tester.view.devicePixelRatio = 1;
      addTearDown(tester.view.resetPhysicalSize);
      addTearDown(tester.view.resetDevicePixelRatio);
      await tester.pumpWidget(buildApp(Languages.english.locale));
      await tester.pumpAndSettle();
      await tester.tap(find.text('For owners').first);
      await tester.pumpAndSettle();
      expect(
        tester
            .widget<AudienceFeaturesSection>(
              find.byType(AudienceFeaturesSection),
            )
            .audience,
        Audience.owner,
      );
      await tester.tap(find.text('Get started').first);
      await tester.pumpAndSettle();
      expect(
        find
            .textContaining('Sokoon is coming to iOS and Android.')
            .hitTestable(),
        findsOneWidget,
      );
    },
  );
}
