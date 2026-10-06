import 'dart:io';
import 'dart:ui' as ui;

import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/navigation/Constants/imports_constants.dart';
import 'package:melos_core/core/navigation/Transition/implementation/fade/Option/fade_animation_option.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/generated/assets.dart';
import 'package:sokoun_app/features/splash/presentation/widgets/animated_splash_logo.dart';

void main() {
  testWidgets('reveals the packaged logo once before releasing startup', (
    tester,
  ) async {
    _setSize(tester, const Size(390, 844));
    int completions = 0;
    void onCompleted() => completions++;

    await _pumpLogo(tester, onCompleted: onCompleted);
    final Image logo = tester.widget<Image>(find.byType(Image));
    final AssetImage asset = logo.image as AssetImage;
    expect(asset.assetName, Assets.png.logo.path);
    expect(asset.package, 'melos_core');
    expect(
      tester.renderObject<RenderImage>(find.byType(RawImage)).image,
      isNotNull,
    );

    await tester.pump(const Duration(milliseconds: 240));
    final FadeTransition fade = tester.widget(_logoDescendant(FadeTransition));
    expect(fade.opacity.value, inExclusiveRange(0, 1));
    expect(completions, 0);
    await _capture(tester, 'splash-0240ms');

    await tester.pump(const Duration(milliseconds: 560));
    await _capture(tester, 'splash-0800ms');
    await tester.pump(const Duration(milliseconds: 450));
    await _capture(tester, 'splash-1250ms');
    expect(completions, 0);
    await tester.pump(const Duration(milliseconds: 750));
    await _capture(tester, 'splash-2000ms');
    await tester.pump(const Duration(milliseconds: 16));
    expect(completions, 1);
    expect(
      tester
          .widget<FadeTransition>(_logoDescendant(FadeTransition))
          .opacity
          .value,
      1,
    );
    expect(
      tester
          .widget<ScaleTransition>(_logoDescendant(ScaleTransition))
          .scale
          .value,
      1,
    );
    expect(
      tester
          .widget<SlideTransition>(_logoDescendant(SlideTransition))
          .position
          .value,
      Offset.zero,
    );

    await tester.pumpWidget(_app(onCompleted: onCompleted));
    await tester.pump(const Duration(seconds: 3));
    expect(completions, 1);
    expect(tester.binding.transientCallbackCount, 0);
    expect(tester.takeException(), isNull);
  });

  for (final bool accessibleNavigation in [false, true]) {
    testWidgets(
      'skips motion and its wait for ${accessibleNavigation ? 'accessible navigation' : 'reduced motion'}',
      (tester) async {
        int completions = 0;
        await _pumpLogo(
          tester,
          onCompleted: () => completions++,
          reducedMotion: !accessibleNavigation,
          accessibleNavigation: accessibleNavigation,
        );
        expect(completions, 1);
        expect(
          tester
              .widget<FadeTransition>(_logoDescendant(FadeTransition))
              .opacity
              .value,
          1,
        );
        expect(tester.binding.transientCallbackCount, 0);
        expect(tester.takeException(), isNull);
      },
    );
  }

  testWidgets('completion hands off through the app fade route', (
    tester,
  ) async {
    await _pumpLogo(
      tester,
      onCompleted: () => Go.offAll(
        const Scaffold(body: Text('Ready')),
        transition: TransitionType.fade,
        options: const FadeAnimationOptions(
          duration: Duration(milliseconds: 400),
          curve: Curves.easeInOutCubic,
        ),
      ),
    );
    expect(find.text('Ready'), findsNothing);
    await tester.pump(const Duration(milliseconds: 2016));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 200));
    expect(find.text('Ready'), findsOneWidget);
    expect(
      find.byType(AnimatedSplashLogo, skipOffstage: false),
      findsOneWidget,
    );
    expect(tester.takeException(), isNull);
    await tester.pumpAndSettle();
    expect(find.byType(AnimatedSplashLogo, skipOffstage: false), findsNothing);
    expect(Go.canPop, isFalse);
  });

  testWidgets('honors reduced motion when enabled during the reveal', (
    tester,
  ) async {
    int completions = 0;
    void onCompleted() => completions++;
    await _pumpLogo(tester, onCompleted: onCompleted);
    await tester.pump(const Duration(milliseconds: 250));
    expect(completions, 0);
    await tester.pumpWidget(
      _app(onCompleted: onCompleted, reducedMotion: true),
    );
    expect(completions, 1);
    expect(
      tester
          .widget<FadeTransition>(_logoDescendant(FadeTransition))
          .opacity
          .value,
      1,
    );
    await tester.pumpWidget(_app(onCompleted: onCompleted));
    await tester.pump(const Duration(seconds: 3));
    expect(completions, 1);
    expect(tester.binding.transientCallbackCount, 0);
    expect(tester.takeException(), isNull);
  });

  testWidgets(
    'disposing an unfinished reveal cancels its ticker and callback',
    (tester) async {
      int completions = 0;
      await _pumpLogo(tester, onCompleted: () => completions++);
      await tester.pump(const Duration(milliseconds: 150));
      await tester.pumpWidget(const SizedBox.shrink());
      await tester.pump(const Duration(seconds: 3));
      expect(completions, 0);
      expect(tester.binding.transientCallbackCount, 0);
      expect(tester.takeException(), isNull);
    },
  );

  for (final double width in [320, 390, 600, 768, 1024, 1366]) {
    for (final double textScale in [1, 1.3, 2]) {
      for (final TextDirection direction in TextDirection.values) {
        testWidgets('logo fits $width at text scale $textScale in $direction', (
          tester,
        ) async {
          final Size viewport = Size(width, width > 600 ? 600 : 844);
          _setSize(tester, viewport);
          await _pumpLogo(
            tester,
            onCompleted: () {},
            reducedMotion: true,
            textScale: textScale,
            direction: direction,
          );
          final Rect logo = tester.getRect(find.byType(Image));
          expect(logo.left, greaterThanOrEqualTo(0));
          expect(logo.top, greaterThanOrEqualTo(0));
          expect(logo.right, lessThanOrEqualTo(viewport.width));
          expect(logo.bottom, lessThanOrEqualTo(viewport.height));
          expect(logo.width, lessThanOrEqualTo(320));
          expect(logo.center.dx, closeTo(viewport.width / 2, .001));
          expect(logo.center.dy, closeTo(viewport.height / 2, .001));
          expect(tester.takeException(), isNull);
          if (textScale == 1 && direction == TextDirection.rtl) {
            await _capture(tester, 'splash-${width.toInt()}px');
          }
        });
      }
    }
  }
}

Finder _logoDescendant(Type type) => find.descendant(
  of: find.byType(AnimatedSplashLogo),
  matching: find.byType(type),
);

void _setSize(WidgetTester tester, Size size) {
  tester.view.physicalSize = size;
  tester.view.devicePixelRatio = 1;
  addTearDown(tester.view.reset);
}

Future<void> _pumpLogo(
  WidgetTester tester, {
  required VoidCallback onCompleted,
  bool reducedMotion = false,
  bool accessibleNavigation = false,
  double textScale = 1,
  TextDirection direction = TextDirection.rtl,
}) async {
  await tester.pumpWidget(
    _app(
      onCompleted: onCompleted,
      reducedMotion: reducedMotion,
      accessibleNavigation: accessibleNavigation,
      textScale: textScale,
      direction: direction,
    ),
  );
  await tester.runAsync(
    () => precacheImage(
      Assets.png.logo.provider(package: 'melos_core'),
      tester.element(find.byType(AnimatedSplashLogo)),
    ),
  );
  await tester.pump();
}

Widget _app({
  required VoidCallback onCompleted,
  bool reducedMotion = false,
  bool accessibleNavigation = false,
  double textScale = 1,
  TextDirection direction = TextDirection.rtl,
}) => ScreenUtilInit(
  designSize: const Size(360, 690),
  enableScaleWH: () => false,
  enableScaleText: () => false,
  builder: (context, _) => MaterialApp(
    debugShowCheckedModeBanner: false,
    navigatorKey: Go.navigatorKey,
    builder: (context, child) => MediaQuery(
      data: MediaQuery.of(context).copyWith(
        disableAnimations: reducedMotion,
        accessibleNavigation: accessibleNavigation,
        textScaler: TextScaler.linear(textScale),
      ),
      child: Directionality(textDirection: direction, child: child!),
    ),
    home: RepaintBoundary(
      child: Scaffold(
        backgroundColor: AppColors.sokoonSplashBackground,
        body: AnimatedSplashLogo(onCompleted: onCompleted),
      ),
    ),
  ),
);

// Export representative animation frames without maintaining pixel goldens.
Future<void> _capture(WidgetTester tester, String name) async {
  const String directory = String.fromEnvironment('SPLASH_REVIEW_DIR');
  if (directory.isEmpty) return;
  final RenderRepaintBoundary boundary = tester.renderObject(
    find
        .ancestor(
          of: find.byType(Scaffold),
          matching: find.byType(RepaintBoundary),
        )
        .first,
  );
  await tester.runAsync(() async {
    final ui.Image image = await boundary.toImage();
    final bytes = await image.toByteData(format: ui.ImageByteFormat.png);
    await Directory(directory).create(recursive: true);
    await File(
      '$directory/$name.png',
    ).writeAsBytes(bytes!.buffer.asUint8List());
    image.dispose();
  });
}
