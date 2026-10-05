import 'dart:convert';
import 'dart:io';
import 'dart:ui' as ui;

import 'package:easy_localization/easy_localization.dart';
import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';
import 'package:flutter/services.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/helpers/cache_service.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/core/widgets/buttons/default_button.dart';
import 'package:sokoun_app/features/main_view/data/enums/app_workspace.dart';
import 'package:sokoun_app/features/shared/appearance/data/theme_preferences.dart';
import 'package:sokoun_app/features/shared/appearance/presentation/cubits/theme_cubit.dart';
import 'package:sokoun_app/features/shared/appearance/presentation/screens/appearance_screen.dart';
import 'package:sokoun_app/features/shared/appearance/presentation/widgets/theme_option_card.dart';
import 'package:sokoun_app/features/shared/profile/imports.dart';
import 'package:sokoun_app/features/tenant/visits/imports.dart'
    show VisitTimePickerField;
import 'package:sokoun_app/shared_widgets/name_field.dart';
import 'package:sokoun_app/shared_widgets/sokoun_map_style.dart';
import 'package:sokoun_app/shared_widgets/sokoun_theme.dart';
import 'package:sokoun_app/shared_widgets/sokoun_theme_config.dart';
import 'package:sokoun_app/shared_widgets/sokoun_themed_app.dart';

import 'helpers/home_page_test_dependencies.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  const output = String.fromEnvironment('THEME_REVIEW_DIR');

  setUpAll(() async {
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(
          const MethodChannel('plugins.flutter.io/shared_preferences'),
          (call) async => call.method == 'getAll' ? <String, Object>{} : true,
        );
    await CacheStorage.init();
    await EasyLocalization.ensureInitialized();
    final fonts = FontLoader(ConstantManager.fontFamily);
    for (final weight in ['Regular', 'Medium', 'Bold', 'ExtraBold']) {
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
  setUp(() async {
    await CacheStorage.deleteAll();
    await injector.reset();
    registerHomePageTestDependencies();
  });
  tearDown(() => injector.reset());

  test('missing or invalid preferences use the configured default', () async {
    expect(ThemePreferences.read(), SokounThemeConfig.defaultMode);
    for (final value in ['invalid', true, 42]) {
      await CacheStorage.write(SokounThemeConfig.preferenceKey, value);
      expect(ThemePreferences.read(), SokounThemeConfig.defaultMode);
    }
  });

  test('all modes persist and closed cubits ignore changes', () async {
    final cubit = ThemeCubit(initialMode: ThemePreferences.read());
    for (final mode in [ThemeMode.dark, ThemeMode.light, ThemeMode.system]) {
      await cubit.setMode(mode);
      expect(cubit.state, mode);
      expect(ThemePreferences.read(), mode);
    }
    await cubit.close();
    await cubit.setMode(ThemeMode.dark);
    expect(ThemePreferences.read(), ThemeMode.system);
  });

  test('dark text and semantic ink have readable surface contrast', () {
    final palette = SokounTheme.dark.extension<AppColorTheme>()!;
    for (final ink in [
      AppColors.sokoonNavy,
      AppColors.sokoonGray,
      AppColors.sokoonMuted,
      AppColors.sokoonTeal,
      AppColors.sokoonGold,
    ]) {
      expect(
        _contrast(
          palette.resolve(ink),
          palette.resolve(AppColors.white, surface: true),
        ),
        greaterThanOrEqualTo(4.5),
        reason: '$ink on a dark surface',
      );
    }
    for (final pair in [
      (AppColors.greenStrong, AppColors.greenPale),
      (AppColors.sokoonRose, AppColors.redPale),
      (AppColors.blue, AppColors.bluePale),
      (AppColors.brown, AppColors.amberPale),
    ]) {
      expect(
        _contrast(
          palette.resolve(pair.$1),
          palette.resolve(pair.$2, surface: true),
        ),
        greaterThanOrEqualTo(4.5),
      );
    }
    expect(palette.resolve(AppColors.white), AppColors.white);
    expect(
      palette.resolve(AppColors.sokoonTeal, surface: true),
      AppColors.sokoonTeal,
    );
    expect(SokounMapStyle.dark, isNot(SokounMapStyle.light));
  });

  testWidgets('colors are opt-in and interpolate with the theme', (
    tester,
  ) async {
    late BuildContext appContext;
    await tester.pumpWidget(
      MaterialApp(
        home: Builder(
          builder: (context) {
            appContext = context;
            return const SizedBox.shrink();
          },
        ),
      ),
    );
    expect(appContext.appColor(AppColors.sokoonNavy), AppColors.sokoonNavy);
    expect(
      appContext.appColor(AppColors.white, surface: true),
      AppColors.white,
    );
    final midpoint = ThemeData.lerp(
      SokounTheme.light,
      SokounTheme.dark,
      .5,
    ).extension<AppColorTheme>()!;
    expect(
      midpoint.resolve(AppColors.white, surface: true),
      Color.lerp(AppColors.white, AppColors.sokoonDarkSurface, .5),
    );
    expect(
      midpoint.resolve(AppColors.sokoonNavy),
      Color.lerp(AppColors.sokoonNavy, AppColors.sokoonDarkText, .5),
    );
  });

  testWidgets(
    'selection animates, saves, and preserves routes and form state',
    (tester) async {
      _viewport(tester, 390);
      final cubit = ThemeCubit(initialMode: ThemeMode.light);
      addTearDown(cubit.close);
      await tester.pumpWidget(
        _app(cubit, const _FormHome(), reducedMotion: false),
      );
      await tester.pumpAndSettle();
      final State formState = tester.state(find.byType(_FormHome));
      await tester.enterText(find.byType(TextFormField), 'Saved draft');
      await tester.tap(find.text('Open appearance'));
      await tester.pumpAndSettle();
      expect(find.byType(AppearanceScreen), findsOneWidget);

      await tester.tap(find.text(LocaleKeys.appearanceDark));
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 160));
      final Scaffold transitioning = tester.widget(
        find.descendant(
          of: find.byType(AppearanceScreen),
          matching: find.byType(Scaffold),
        ),
      );
      expect(
        transitioning.backgroundColor,
        isNot(AppColors.scaffoldBackground),
      );
      expect(transitioning.backgroundColor, isNot(AppColors.sokoonDarkCanvas));
      await tester.pumpAndSettle();
      expect(ThemePreferences.read(), ThemeMode.dark);
      expect(
        tester
            .widget<MaterialApp>(find.byType(MaterialApp))
            .themeAnimationDuration,
        const Duration(milliseconds: SokounThemeConfig.transitionMilliseconds),
      );
      expect(
        tester
            .widget<ThemeOptionCard>(
              find.widgetWithText(ThemeOptionCard, LocaleKeys.appearanceDark),
            )
            .selected,
        isTrue,
      );

      Go.back();
      await tester.pumpAndSettle();
      expect(tester.state(find.byType(_FormHome)), same(formState));
      final field = tester.widget<TextFormField>(find.byType(TextFormField));
      expect(field.controller!.text, 'Saved draft');
      final TextField input = tester.widget(find.byType(TextField));
      expect(input.decoration!.fillColor, AppColors.sokoonDarkSurface);
      expect(input.style!.color, AppColors.sokoonDarkText);
      expect(tester.takeException(), isNull);

      await tester.pumpWidget(const SizedBox.shrink());
      final restored = ThemeCubit(initialMode: ThemePreferences.read());
      addTearDown(restored.close);
      await tester.pumpWidget(_app(restored, const AppearanceScreen()));
      await tester.pumpAndSettle();
      expect(
        Theme.of(tester.element(find.byType(AppearanceScreen))).brightness,
        Brightness.dark,
      );
    },
  );

  testWidgets(
    'system follows device brightness and manual selection overrides it',
    (tester) async {
      _viewport(tester, 390);
      tester.platformDispatcher.platformBrightnessTestValue = Brightness.light;
      addTearDown(tester.platformDispatcher.clearPlatformBrightnessTestValue);
      final cubit = ThemeCubit(initialMode: ThemeMode.system);
      addTearDown(cubit.close);
      await tester.pumpWidget(_app(cubit, const AppearanceScreen()));
      await tester.pumpAndSettle();
      Brightness brightness() =>
          Theme.of(tester.element(find.byType(AppearanceScreen))).brightness;
      expect(brightness(), Brightness.light);
      tester.platformDispatcher.platformBrightnessTestValue = Brightness.dark;
      await tester.pumpAndSettle();
      expect(brightness(), Brightness.dark);
      await tester.tap(find.text(LocaleKeys.appearanceLight));
      await tester.pumpAndSettle();
      expect(brightness(), Brightness.light);
      tester.platformDispatcher.platformBrightnessTestValue = Brightness.light;
      await tester.pumpAndSettle();
      tester.platformDispatcher.platformBrightnessTestValue = Brightness.dark;
      await tester.pumpAndSettle();
      expect(brightness(), Brightness.light);
      await tester.tap(find.text(LocaleKeys.appearanceSystem));
      await tester.pumpAndSettle();
      expect(brightness(), Brightness.dark);
    },
  );

  for (final accessible in [false, true]) {
    testWidgets(
      'theme respects ${accessible ? 'accessible navigation' : 'reduced motion'}',
      (tester) async {
        _viewport(tester, 390);
        final cubit = ThemeCubit(initialMode: ThemeMode.light);
        addTearDown(cubit.close);
        await tester.pumpWidget(
          _app(
            cubit,
            const AppearanceScreen(),
            reducedMotion: !accessible,
            accessibleNavigation: accessible,
          ),
        );
        await tester.pumpAndSettle();
        expect(
          tester
              .widget<MaterialApp>(find.byType(MaterialApp))
              .themeAnimationDuration,
          Duration.zero,
        );
        await tester.tap(find.text(LocaleKeys.appearanceDark));
        await tester.pump();
        expect(
          Theme.of(
            tester.element(find.byType(AppearanceScreen)),
          ).scaffoldBackgroundColor,
          AppColors.sokoonDarkCanvas,
        );
        expect(
          tester
              .widget<AnimatedContainer>(
                find.descendant(
                  of: find.byType(ThemeOptionCard).first,
                  matching: find.byType(AnimatedContainer),
                ),
              )
              .duration,
          Duration.zero,
        );
      },
    );
  }

  testWidgets(
    'visit time picker uses the dark surface and readable dial labels',
    (tester) async {
      _viewport(tester, 390);
      final cubit = ThemeCubit(initialMode: ThemeMode.dark);
      addTearDown(cubit.close);
      await tester.pumpWidget(
        _app(
          cubit,
          Scaffold(
            body: SafeArea(
              child: VisitTimePickerField(
                selectedTime: null,
                onTimeSelected: (_) {},
              ),
            ),
          ),
        ),
      );
      await tester.pumpAndSettle();
      await tester.tap(find.byType(VisitTimePickerField));
      await tester.pumpAndSettle();
      final pickerContext = tester.element(find.byType(TimePickerDialog));
      final theme = Theme.of(pickerContext);
      expect(theme.brightness, Brightness.dark);
      expect(theme.colorScheme.surface, AppColors.sokoonDarkSurface);
      expect(
        _contrast(theme.colorScheme.primary, theme.colorScheme.onPrimary),
        greaterThanOrEqualTo(4.5),
      );
      expect(tester.takeException(), isNull);
      await tester.tap(
        find.text(MaterialLocalizations.of(pickerContext).cancelButtonLabel),
      );
      await tester.pumpAndSettle();
    },
  );

  for (final mode in [ThemeMode.light, ThemeMode.dark]) {
    for (final locale in ['ar', 'en']) {
      for (final width in [320.0, 390.0, 600.0, 768.0, 1024.0, 1366.0]) {
        for (final scale in [1.0, 1.3, 2.0]) {
          testWidgets('appearance ${mode.name} $locale $width at $scale', (
            tester,
          ) async {
            _viewport(tester, width);
            final cubit = ThemeCubit(initialMode: mode);
            addTearDown(cubit.close);
            await tester.pumpWidget(
              _app(
                cubit,
                const AppearanceScreen(),
                locale: locale,
                scale: scale,
              ),
            );
            await tester.pumpAndSettle();
            expect(find.byType(ThemeOptionCard), findsNWidgets(3));
            expect(tester.takeException(), isNull);
            if (output.isNotEmpty && width == 390 && scale == 1) {
              await _capture(
                tester,
                '$output/appearance-${mode.name}-$locale.png',
              );
            }
          });
        }
      }
    }
    for (final workspace in AppWorkspace.values) {
      testWidgets(
        '${workspace.name} settings reaches appearance in ${mode.name}',
        (tester) async {
          _viewport(tester, 390);
          final cubit = ThemeCubit(initialMode: mode);
          addTearDown(cubit.close);
          await tester.pumpWidget(
            _app(cubit, ProfileSettingsScreen(workspace: workspace)),
          );
          await tester.pumpAndSettle();
          if (output.isNotEmpty) {
            await _capture(
              tester,
              '$output/settings-${workspace.name}-${mode.name}.png',
            );
          }
          await tester.tap(find.text(LocaleKeys.appearanceTitle));
          await tester.pumpAndSettle();
          expect(find.byType(AppearanceScreen), findsOneWidget);
          expect(tester.takeException(), isNull);
        },
      );
    }
  }
}

double _contrast(Color first, Color second) {
  final a = first.computeLuminance();
  final b = second.computeLuminance();
  return a > b ? (a + .05) / (b + .05) : (b + .05) / (a + .05);
}

void _viewport(WidgetTester tester, double width) {
  tester.view.physicalSize = Size(width, width >= 600 ? 768 : 844);
  tester.view.devicePixelRatio = 1;
  addTearDown(tester.view.reset);
}

Widget _app(
  ThemeCubit cubit,
  Widget home, {
  String locale = 'en',
  double scale = 1,
  bool reducedMotion = true,
  bool accessibleNavigation = false,
}) => EasyLocalization(
  supportedLocales: const [Locale('ar'), Locale('en')],
  path: 'unused',
  startLocale: Locale(locale),
  saveLocale: false,
  assetLoader: const _Translations(),
  child: ScreenUtilInit(
    designSize: const Size(360, 690),
    enableScaleWH: () => false,
    enableScaleText: () => false,
    fontSizeResolver: (size, _) => size.toDouble(),
    builder: (context, _) => MediaQuery(
      data: MediaQuery.of(context).copyWith(
        textScaler: TextScaler.linear(scale),
        disableAnimations: reducedMotion,
        accessibleNavigation: accessibleNavigation,
      ),
      child: BlocProvider.value(
        value: cubit,
        child: SokounThemedApp(home: RepaintBoundary(child: home)),
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

class _FormHome extends StatefulWidget {
  const _FormHome();
  @override
  State<_FormHome> createState() => _FormHomeState();
}

class _FormHomeState extends State<_FormHome> {
  final TextEditingController controller = TextEditingController();
  @override
  void dispose() {
    controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => Scaffold(
    body: SafeArea(
      child: Column(
        children: [
          SokoonNameField(controller: controller),
          DefaultButton(
            title: 'Open appearance',
            onTap: () => Go.to(const AppearanceScreen()),
          ),
        ],
      ),
    ),
  );
}

Future<void> _capture(WidgetTester tester, String path) async {
  final boundary = tester.renderObject<RenderRepaintBoundary>(
    find.byType(RepaintBoundary).first,
  );
  await tester.runAsync(() async {
    final image = await boundary.toImage();
    final bytes = await image.toByteData(format: ui.ImageByteFormat.png);
    await File(path).parent.create(recursive: true);
    await File(path).writeAsBytes(bytes!.buffer.asUint8List());
    image.dispose();
  });
}
