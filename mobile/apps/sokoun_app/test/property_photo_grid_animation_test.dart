import 'dart:convert';
import 'dart:io';
import 'dart:ui' as ui;

import 'package:easy_localization/easy_localization.dart';
import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';
import 'package:flutter/services.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:sokoun_app/features/owner/home/data/models/owner_add_property_content.dart';
import 'package:sokoun_app/features/owner/home/presentation/widgets/owner_add_property/property_photo_grid.dart';
import 'package:sokoun_app/shared_widgets/sokoun_theme.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  late Directory images;
  late List<OwnerPropertyPhotoDraft> fixtures;

  setUpAll(() async {
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(
          const MethodChannel('plugins.flutter.io/shared_preferences'),
          (call) async => call.method == 'getAll' ? <String, Object>{} : true,
        );
    await EasyLocalization.ensureInitialized();
    final fonts = FontLoader(ConstantManager.fontFamily);
    for (final weight in ['Regular', 'Medium', 'Bold', 'ExtraBold', 'Black']) {
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
    images = Directory.systemTemp.createTempSync('animated-property-photos-');
    fixtures = [];
    for (final (index, color) in [
      AppColors.sokoonNavy,
      AppColors.sokoonTeal,
      AppColors.sokoonGold,
      AppColors.blue,
    ].indexed) {
      final recorder = ui.PictureRecorder();
      Canvas(
        recorder,
      ).drawRect(const Rect.fromLTWH(0, 0, 80, 80), Paint()..color = color);
      final picture = recorder.endRecording();
      final image = await picture.toImage(80, 80);
      final bytes = await image.toByteData(format: ui.ImageByteFormat.png);
      final file = File('${images.path}/photo-$index.png')
        ..writeAsBytesSync(bytes!.buffer.asUint8List());
      fixtures.add(OwnerPropertyPhotoDraft(file: file, name: 'Photo $index'));
      image.dispose();
      picture.dispose();
    }
  });

  tearDownAll(() {
    images.deleteSync(recursive: true);
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(
          const MethodChannel('plugins.flutter.io/shared_preferences'),
          null,
        );
  });

  Finder photo(String id) => find.byWidgetPredicate(
    (widget) => widget is PhotoTile && widget.photo?.id == id,
  );

  Future<void> mount(
    WidgetTester tester,
    ValueNotifier<List<OwnerPropertyPhotoDraft>> photos, {
    String locale = 'en',
    bool disableAnimations = false,
    bool accessibleNavigation = false,
  }) async {
    tester.view.physicalSize = const Size(390, 844);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.reset);
    // Decode the fixtures before Image.file starts work in the fake clock zone.
    final initialPhotos = photos.value;
    photos.value = [];
    await tester.pumpWidget(
      EasyLocalization(
        supportedLocales: const [Locale('ar'), Locale('en')],
        path: 'unused',
        assetLoader: const _Translations(),
        startLocale: Locale(locale),
        child: ScreenUtilInit(
          designSize: const Size(390, 844),
          enableScaleWH: () => false,
          enableScaleText: () => false,
          builder: (context, _) => MaterialApp(
            navigatorKey: Go.navigatorKey,
            theme: SokounTheme.light,
            locale: context.locale,
            supportedLocales: context.supportedLocales,
            localizationsDelegates: context.localizationDelegates,
            builder: (context, child) => MediaQuery(
              data: MediaQuery.of(context).copyWith(
                disableAnimations: disableAnimations,
                accessibleNavigation: accessibleNavigation,
              ),
              child: child!,
            ),
            home: RepaintBoundary(
              child: Scaffold(
                body: SingleChildScrollView(
                  padding: const EdgeInsets.all(16),
                  child: ValueListenableBuilder<List<OwnerPropertyPhotoDraft>>(
                    valueListenable: photos,
                    builder: (context, value, _) => PhotoGridSection(
                      photos: value,
                      onAddPhotos: () {},
                      onRemovePhoto: (index) =>
                          photos.value = List.of(photos.value)..removeAt(index),
                      onReplacePhoto: (_) {},
                      onMainPhotoSelected: (index) {
                        final reordered = List.of(photos.value);
                        reordered.insert(0, reordered.removeAt(index));
                        photos.value = reordered;
                      },
                    ),
                  ),
                ),
              ),
            ),
          ),
        ),
      ),
    );
    await tester.runAsync(() async => Future<void>.delayed(Duration.zero));
    await tester.pumpAndSettle();
    await tester.runAsync(() async {
      final context = tester.element(find.byType(PhotoGridSection));
      await Future.wait([
        for (final photo in fixtures)
          precacheImage(FileImage(photo.file!), context),
      ]);
    });
    photos.value = initialPhotos;
    await tester.pumpAndSettle();
  }

  for (final locale in ['en', 'ar']) {
    testWidgets(
      'cover promotion slides between slots and retains identity in $locale',
      (tester) async {
        final photos = ValueNotifier(List.of(fixtures));
        addTearDown(photos.dispose);
        await mount(tester, photos, locale: locale);
        final selected = photo(fixtures[2].id);
        final oldRect = tester.getRect(selected);
        final target = tester.getRect(photo(fixtures.first.id));
        final element = tester.element(selected);
        await _capture(tester, 'cover-$locale-before');
        await tester.tap(
          find.descendant(
            of: selected,
            matching: find.byTooltip(LocaleKeys.ownerAddPropertySetMainPhoto),
          ),
        );
        await tester.pump();
        await tester.pump(const Duration(milliseconds: 140));
        final traveling = tester.getRect(selected);
        expect(photos.value.first.id, fixtures[2].id);
        expect(traveling.top, greaterThan(target.top));
        expect(traveling.top, lessThan(oldRect.top));
        expect(tester.element(selected), same(element));
        await _capture(tester, 'cover-$locale-moving');
        await tester.pumpAndSettle();
        expect(tester.getRect(selected).topLeft, target.topLeft);
        expect(tester.widget<PhotoTile>(selected).isMainPhoto, isTrue);
        await _capture(tester, 'cover-$locale-after');
        expect(tester.takeException(), isNull);
      },
    );

    testWidgets(
      'deletion fades the photo and slides neighbors into the gap in $locale',
      (tester) async {
        final photos = ValueNotifier(List.of(fixtures));
        addTearDown(photos.dispose);
        await mount(tester, photos, locale: locale);
        final removed = photo(fixtures[1].id);
        final neighbor = photo(fixtures[2].id);
        final target = tester.getRect(removed);
        final originalNeighbor = tester.getRect(neighbor);
        await _capture(tester, 'delete-$locale-before');
        await tester.tap(
          find.descendant(
            of: removed,
            matching: find.byTooltip(LocaleKeys.ownerPropertiesDelete),
          ),
        );
        await tester.pump();
        await tester.pump(const Duration(milliseconds: 100));
        expect(
          photos.value.map((item) => item.id),
          isNot(contains(fixtures[1].id)),
        );
        expect(removed, findsOneWidget);
        final fade = tester.widget<FadeTransition>(
          find
              .ancestor(of: removed, matching: find.byType(FadeTransition))
              .first,
        );
        expect(fade.opacity.value, inExclusiveRange(0, 1));
        expect(
          tester.getRect(neighbor).top,
          inExclusiveRange(target.top, originalNeighbor.top),
        );
        await _capture(tester, 'delete-$locale-fading');
        await tester.pumpAndSettle();
        expect(removed, findsNothing);
        expect(tester.getRect(neighbor).topLeft, target.topLeft);
        await _capture(tester, 'delete-$locale-after');
        expect(tester.takeException(), isNull);
      },
    );
  }

  for (final accessibleNavigation in [false, true]) {
    testWidgets(
      'reduced motion immediately reorders and removes photos, accessibility=$accessibleNavigation',
      (tester) async {
        final photos = ValueNotifier(List.of(fixtures));
        addTearDown(photos.dispose);
        await mount(
          tester,
          photos,
          disableAnimations: !accessibleNavigation,
          accessibleNavigation: accessibleNavigation,
        );
        final target = tester.getRect(photo(fixtures.first.id));
        final selected = photo(fixtures[2].id);
        await tester.tap(
          find.descendant(
            of: selected,
            matching: find.byTooltip(LocaleKeys.ownerAddPropertySetMainPhoto),
          ),
        );
        await tester.pump();
        expect(tester.getRect(selected).topLeft, target.topLeft);
        await tester.tap(
          find.descendant(
            of: selected,
            matching: find.byTooltip(LocaleKeys.ownerPropertiesDelete),
          ),
        );
        await tester.pump();
        expect(selected, findsNothing);
        expect(
          tester.getRect(photo(fixtures.first.id)).topLeft,
          target.topLeft,
        );
        expect(tester.takeException(), isNull);
      },
    );
  }

  testWidgets('rapid promotion and removal preserve the remaining photos', (
    tester,
  ) async {
    final photos = ValueNotifier(List.of(fixtures));
    addTearDown(photos.dispose);
    await mount(tester, photos);
    final selected = photo(fixtures[2].id);
    await tester.tap(
      find.descendant(
        of: selected,
        matching: find.byTooltip(LocaleKeys.ownerAddPropertySetMainPhoto),
      ),
    );
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 60));
    tester.widget<PhotoTile>(photo(fixtures[1].id)).onRemovePhoto!();
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 40));
    tester.widget<PhotoTile>(photo(fixtures[3].id)).onMainPhotoSelected!();
    await tester.pumpAndSettle();
    expect(photos.value.map((item) => item.id), [
      fixtures[3].id,
      fixtures[2].id,
      fixtures[0].id,
    ]);
    expect(
      find.byWidgetPredicate(
        (widget) => widget is PhotoTile && widget.isMainPhoto,
      ),
      findsOneWidget,
    );
    expect(photo(fixtures[1].id), findsNothing);
    expect(tester.takeException(), isNull);
  });

  testWidgets('leaving during deletion cancels animation cleanup', (
    tester,
  ) async {
    final photos = ValueNotifier(List.of(fixtures));
    addTearDown(photos.dispose);
    await mount(tester, photos);
    photos.value = photos.value.skip(1).toList();
    await tester.pump();
    await tester.pumpWidget(const SizedBox.shrink());
    await tester.pump(const Duration(seconds: 1));
    expect(tester.takeException(), isNull);
  });
}

Future<void> _capture(WidgetTester tester, String name) async {
  const output = String.fromEnvironment('UI_REVIEW_DIR');
  if (output.isEmpty) return;
  final boundary = tester.renderObject<RenderRepaintBoundary>(
    find.byType(RepaintBoundary).first,
  );
  await tester.runAsync(() async {
    final image = await boundary.toImage();
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
