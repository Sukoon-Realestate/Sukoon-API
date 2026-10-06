import 'dart:async';
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
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/widget_extension.dart';
import 'package:melos_core/core/widgets/app_logo_widget.dart';
import 'package:sokoun_app/shared_widgets/sokoun_refresh_indicator.dart';
import 'package:sokoun_app/shared_widgets/sokoun_theme.dart';

const _preview = ValueKey('refresh-preview');

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  setUpAll(() async {
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(
          const MethodChannel('plugins.flutter.io/shared_preferences'),
          (call) async => call.method == 'getAll' ? <String, Object>{} : true,
        );
    await EasyLocalization.ensureInitialized();
    final fonts = FontLoader(ConstantManager.fontFamily);
    for (final weight in ['Regular', 'Medium']) {
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

  for (final platform in [TargetPlatform.android, TargetPlatform.iOS]) {
    testWidgets('$platform shows pull, release and pending refresh states', (
      tester,
    ) async {
      _size(tester, 390);
      final pending = Completer<void>();
      int calls = 0;
      await tester.pumpWidget(
        _app(
          platform: platform,
          child: _scrollView().withPullRefresher(
            onRefresh: () {
              calls++;
              return pending.future;
            },
          ),
        ),
      );
      await tester.pumpAndSettle();
      expect(_visible(tester), isFalse);
      final gesture = await tester.startGesture(const Offset(190, 200));
      await gesture.moveBy(const Offset(0, 20));
      await gesture.moveBy(const Offset(0, 60));
      await tester.pump(const Duration(milliseconds: 200));
      expect(_status(tester), RefreshIndicatorStatus.drag);
      expect(find.text('Pull to refresh'), findsOneWidget);
      expect(calls, 0);
      await gesture.moveBy(const Offset(0, 280));
      await tester.pump(const Duration(milliseconds: 200));
      expect(_status(tester), RefreshIndicatorStatus.armed);
      expect(find.text('Release to refresh'), findsOneWidget);
      expect(calls, 0);
      await gesture.up();
      await tester.pump();
      await tester.pump(const Duration(seconds: 1));
      expect(_status(tester), RefreshIndicatorStatus.refresh);
      expect(calls, 1);
      expect(find.text('Refreshing'), findsOneWidget);
      expect(find.byType(RefreshProgressIndicator), findsNothing);
      expect(find.byType(AppLogoWidget), findsOneWidget);

      await tester.drag(find.byType(Scrollable), const Offset(0, 350));
      await tester.pump(const Duration(seconds: 1));
      expect(calls, 1);
      expect(_visible(tester), isTrue);
      pending.complete();
      await tester.pumpAndSettle();
      expect(_visible(tester), isFalse);
      expect(tester.takeException(), isNull);
    });
  }

  testWidgets('normal scrolling and a canceled pull do not refresh', (
    tester,
  ) async {
    _size(tester, 390);
    int calls = 0;
    await tester.pumpWidget(
      _app(
        child: _scrollView(
          height: 1600,
        ).withPullRefresher(onRefresh: () async => calls++),
      ),
    );
    await tester.pumpAndSettle();
    final scroll = await tester.startGesture(const Offset(190, 300));
    await scroll.moveBy(const Offset(0, -100));
    await tester.pump(const Duration(milliseconds: 200));
    expect(_visible(tester), isFalse);
    await scroll.up();
    await tester.pumpAndSettle();
    tester.state<ScrollableState>(find.byType(Scrollable)).position.jumpTo(0);
    await tester.pumpAndSettle();
    final pull = await tester.startGesture(const Offset(190, 200));
    await pull.moveBy(const Offset(0, 20));
    await pull.moveBy(const Offset(0, 60));
    await tester.pump(const Duration(milliseconds: 200));
    expect(_visible(tester), isTrue);
    await pull.up();
    await tester.pumpAndSettle();
    expect(_visible(tester), isFalse);
    expect(calls, 0);
    expect(tester.takeException(), isNull);
  });

  testWidgets('leaving during a refresh releases the custom indicator', (
    tester,
  ) async {
    _size(tester, 390);
    final pending = Completer<void>();
    await tester.pumpWidget(
      _app(
        child: _scrollView().withPullRefresher(onRefresh: () => pending.future),
      ),
    );
    await tester.pumpAndSettle();
    await tester.drag(find.byType(Scrollable), const Offset(0, 350));
    await tester.pump();
    await tester.pump(const Duration(seconds: 1));
    expect(_status(tester), RefreshIndicatorStatus.refresh);
    await tester.pumpWidget(const SizedBox.shrink());
    pending.complete();
    await tester.pumpAndSettle();
    expect(tester.takeException(), isNull);
  });

  for (final locale in ['ar', 'en']) {
    for (final width in [320.0, 390.0, 1366.0]) {
      testWidgets('$locale refresh at $width supports layout and semantics', (
        tester,
      ) async {
        _size(tester, width);
        final semantics = tester.ensureSemantics();
        await tester.pumpWidget(
          _app(
            locale: locale,
            textScale: width == 320 ? 2 : 1,
            child: const Column(
              children: [
                SokounRefreshIndicator(status: RefreshIndicatorStatus.drag),
                SokounRefreshIndicator(status: RefreshIndicatorStatus.armed),
                SokounRefreshIndicator(status: RefreshIndicatorStatus.refresh),
              ],
            ),
          ),
        );
        await tester.pump();
        await tester.pump(const Duration(milliseconds: 200));
        final String label = locale == 'ar' ? 'جارٍ التحديث' : 'Refreshing';
        expect(find.text(label), findsOneWidget);
        expect(
          tester
              .getSemantics(find.bySemanticsLabel(label))
              .flagsCollection
              .isLiveRegion,
          isTrue,
        );
        final icon = tester.getCenter(find.byType(AppLogoWidget));
        final text = tester.getCenter(find.text(label));
        expect(locale == 'ar' ? icon.dx > text.dx : icon.dx < text.dx, isTrue);
        expect(tester.takeException(), isNull);
        if (width == 390) await _capture(tester, 'refresh-$locale');
        semantics.dispose();
      });
    }
  }

  for (final accessibleNavigation in [false, true]) {
    testWidgets('reduced motion ($accessibleNavigation) keeps loading static', (
      tester,
    ) async {
      _size(tester, 390);
      await tester.pumpWidget(
        _app(
          disableAnimations: !accessibleNavigation,
          accessibleNavigation: accessibleNavigation,
          child: const SokounRefreshIndicator(
            status: RefreshIndicatorStatus.refresh,
          ),
        ),
      );
      await tester.pumpAndSettle();
      expect(find.byType(AppLogoWidget), findsOneWidget);
      expect(tester.hasRunningAnimations, isFalse);
      expect(find.text('Refreshing'), findsOneWidget);
      expect(tester.takeException(), isNull);
    });
  }
}

Widget _app({
  required Widget child,
  String locale = 'en',
  double textScale = 1,
  bool disableAnimations = false,
  bool accessibleNavigation = false,
  TargetPlatform platform = TargetPlatform.android,
}) => EasyLocalization(
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
      theme: SokounTheme.light.copyWith(platform: platform),
      locale: context.locale,
      supportedLocales: context.supportedLocales,
      localizationsDelegates: context.localizationDelegates,
      builder: (context, child) => MediaQuery(
        data: MediaQuery.of(context).copyWith(
          textScaler: TextScaler.linear(textScale),
          disableAnimations: disableAnimations,
          accessibleNavigation: accessibleNavigation,
        ),
        child: child!,
      ),
      home: RepaintBoundary(
        key: _preview,
        child: Scaffold(body: child),
      ),
    ),
  ),
);

Widget _scrollView({double height = 40}) => SizedBox.expand(
  child: SingleChildScrollView(
    child: SizedBox(height: height, child: const Text('Content')),
  ),
);

void _size(WidgetTester tester, double width) {
  tester.view.physicalSize = Size(width, 844);
  tester.view.devicePixelRatio = 1;
  addTearDown(tester.view.reset);
}

RefreshIndicatorStatus? _status(WidgetTester tester) => tester
    .widget<SokounRefreshIndicator>(find.byType(SokounRefreshIndicator))
    .status;

bool _visible(WidgetTester tester) =>
    tester
        .widget<AnimatedOpacity>(
          find.descendant(
            of: find.byType(SokounRefreshIndicator),
            matching: find.byType(AnimatedOpacity),
          ),
        )
        .opacity ==
    1;

Future<void> _capture(WidgetTester tester, String name) async {
  const String output = String.fromEnvironment('UI_REVIEW_DIR');
  if (output.isEmpty) return;
  final RenderRepaintBoundary boundary = tester.renderObject(
    find.byKey(_preview),
  );
  await tester.runAsync(() async {
    final image = await boundary.toImage(pixelRatio: 2);
    final bytes = await image.toByteData(format: ui.ImageByteFormat.png);
    await Directory(output).create(recursive: true);
    await File('$output/$name.png').writeAsBytes(bytes!.buffer.asUint8List());
    image.dispose();
  });
}

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
