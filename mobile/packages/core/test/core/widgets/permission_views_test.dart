import 'dart:convert';

import 'package:easy_localization/easy_localization.dart' hide TextDirection;
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/core/widgets/location_permission_view.dart';
import 'package:melos_core/core/widgets/notification_permission_view.dart';
import 'package:melos_core/core/widgets/permissions/permission_actions.dart';

final _translations = <String, Map<String, dynamic>>{};

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  const preferencesChannel = MethodChannel(
    'plugins.flutter.io/shared_preferences',
  );

  setUpAll(() async {
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(preferencesChannel, (call) async {
          return call.method == 'getAll' ? <String, Object>{} : true;
        });
    await EasyLocalization.ensureInitialized();
    final fonts = FontLoader(ConstantManager.fontFamily);
    for (final weight in ['Regular', 'Medium', 'Bold', 'Black']) {
      fonts.addFont(
        rootBundle.load('assets/fonts/Tajawal/Tajawal-$weight.ttf'),
      );
    }
    await fonts.load();
    await (FontLoader(
      'MaterialIcons',
    )..addFont(rootBundle.load('fonts/MaterialIcons-Regular.otf'))).load();
    for (final language in ['ar', 'en']) {
      _translations[language] =
          jsonDecode(
                await rootBundle.loadString(
                  'assets/translations/$language.json',
                ),
              )
              as Map<String, dynamic>;
    }
  });

  tearDownAll(() {
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(preferencesChannel, null);
  });

  final prompts = <String, Future<bool?> Function()>{
    'location': () => LocationPermissionView.show(),
    'notifications': () => NotificationPermissionView.show(),
  };

  for (final prompt in prompts.entries) {
    for (final bool allow in [true, false]) {
      testWidgets('${prompt.key} returns the selected choice: $allow', (
        tester,
      ) async {
        await _pumpApp(tester);
        final result = prompt.value();
        await tester.pumpAndSettle();

        final button = allow ? _actions.first : _actions.last;
        await tester.ensureVisible(button);
        await tester.tap(button);
        await tester.pumpAndSettle();

        expect(await result, allow);
        expect(find.byType(PermissionActions), findsNothing);
        expect(tester.takeException(), isNull);
      });
    }

    testWidgets('${prompt.key} dismissal does not opt in', (tester) async {
      await _pumpApp(tester);
      final result = prompt.value();
      await tester.pumpAndSettle();

      await tester.tapAt(const Offset(10, 10));
      await tester.pumpAndSettle();

      expect(await result, isNull);
      expect(find.byType(PermissionActions), findsNothing);
    });

    for (final String language in ['ar', 'en']) {
      testWidgets(
        '${prompt.key} supports $language with large text on a small screen',
        (tester) async {
          await _pumpApp(
            tester,
            locale: Locale(language),
            size: const Size(320, 568),
            textScale: 2,
            bottomInset: 34,
          );
          final result = prompt.value();
          await tester.pumpAndSettle();

          expect(
            Directionality.of(tester.element(find.byType(PermissionActions))),
            language == 'ar' ? TextDirection.rtl : TextDirection.ltr,
          );
          expect(tester.takeException(), isNull);

          await tester.ensureVisible(_actions.last);
          await tester.pumpAndSettle();
          expect(
            tester.getBottomRight(_actions.last).dy,
            lessThanOrEqualTo(534),
          );
          await tester.tap(_actions.last);
          await tester.pumpAndSettle();

          expect(await result, isFalse);
          expect(tester.takeException(), isNull);
        },
      );
    }
  }
}

Finder get _actions => find.descendant(
  of: find.byType(PermissionActions),
  matching: find.byType(ElevatedButton),
);

Future<void> _pumpApp(
  WidgetTester tester, {
  Locale locale = const Locale('ar'),
  Size size = const Size(390, 844),
  double textScale = 1,
  double bottomInset = 0,
}) async {
  tester.view.physicalSize = size;
  tester.view.devicePixelRatio = 1;
  tester.view.padding = FakeViewPadding(bottom: bottomInset);
  addTearDown(tester.view.reset);

  await tester.pumpWidget(
    EasyLocalization(
      supportedLocales: const [Locale('ar'), Locale('en')],
      startLocale: locale,
      saveLocale: false,
      path: 'assets/translations',
      assetLoader: const _Translations(),
      child: ScreenUtilInit(
        designSize: const Size(360, 690),
        minTextAdapt: true,
        builder: (context, _) => MaterialApp(
          navigatorKey: Go.navigatorKey,
          localizationsDelegates: context.localizationDelegates,
          supportedLocales: context.supportedLocales,
          locale: context.locale,
          theme: ThemeData(fontFamily: ConstantManager.fontFamily),
          builder: (context, child) => MediaQuery(
            data: MediaQuery.of(
              context,
            ).copyWith(textScaler: TextScaler.linear(textScale)),
            child: child!,
          ),
          home: const Scaffold(backgroundColor: AppColors.scaffoldBackground),
        ),
      ),
    ),
  );
  await tester.pumpAndSettle();
}

class _Translations extends AssetLoader {
  const _Translations();

  @override
  Future<Map<String, dynamic>> load(String path, Locale locale) async {
    return _translations[locale.languageCode]!;
  }
}
