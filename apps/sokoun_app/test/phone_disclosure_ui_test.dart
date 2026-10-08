import 'dart:convert';
import 'dart:io';
import 'dart:ui' as ui;

import 'package:easy_localization/easy_localization.dart';
import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';
import 'package:flutter/services.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:sokoun_app/features/owner/visits/imports.dart';
import 'package:sokoun_app/features/shared/contact/presentation/widgets/revealed_phone_card.dart';
import 'package:sokoun_app/features/tenant/visits/imports.dart';
import 'package:sokoun_app/shared_widgets/app_scaffold.dart';
import 'package:sokoun_app/shared_widgets/sokoun_theme.dart';

const String _phone = '+20 100 123 4567';
final Map<String, Map<String, dynamic>> _translations = {};

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  const channel = MethodChannel('plugins.flutter.io/shared_preferences');

  setUpAll(() async {
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(
          channel,
          (call) async => call.method == 'getAll' ? <String, Object>{} : true,
        );
    await EasyLocalization.ensureInitialized();
    for (final language in ['ar', 'en']) {
      _translations[language] = Map<String, dynamic>.from(
        jsonDecode(
              await rootBundle.loadString(
                'packages/melos_core/assets/translations/$language.json',
              ),
            )
            as Map,
      );
    }
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

  tearDownAll(() {
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(channel, null);
  });

  final request = OwnerVisitRequestDetailsContent.fromJson({
    'id': 'visit',
    'status': 'accepted',
    'status_label': 'Accepted',
    'tenant': {
      'id': 'tenant',
      'name': 'Tenant',
      'phone_number': _phone,
      'masked_phone_number': '010****432',
      'is_phone_revealed': true,
      'phone_notice': 'Phone number hidden',
    },
    'property': {'id': 'property', 'title': 'Apartment'},
    'day_label': 'Saturday',
    'time_label': '3:00 pm',
  });

  testWidgets('owner contact replaces a stale backend privacy notice', (
    tester,
  ) async {
    await _pump(
      tester,
      OwnerRequestDetailsContent(
        request: request,
        actions: const SizedBox.shrink(),
      ),
    );
    expect(find.text(_phone), findsOneWidget);
    expect(find.text('Phone number hidden'), findsNothing);
    expect(find.text('010****432'), findsNothing);
    expect(find.byIcon(Icons.phone_outlined), findsOneWidget);
    await _capture(tester, 'owner-accepted');
  });

  testWidgets('pending owner request retains privacy and has no phone action', (
    tester,
  ) async {
    await _pump(
      tester,
      OwnerRequestDetailsContent(
        request: request.copyWith(
          status: OwnerVisitRequestStatus.pending,
          tenant: request.tenant.copyWith(isPhoneRevealed: false),
        ),
        actions: const SizedBox.shrink(),
      ),
    );
    expect(find.text(_phone), findsNothing);
    expect(find.text('Phone number hidden'), findsOneWidget);
    expect(find.byIcon(Icons.phone_outlined), findsNothing);
    await _capture(tester, 'owner-pending');
  });

  testWidgets('tenant accepted contact omits the masked phone', (tester) async {
    final details = TenantVisitDetailsContent.fromJson({
      'id': 'visit',
      'status': 'accepted',
      'day_label': 'Saturday',
      'time_label': '3:00 pm',
      'property': {'id': 'property', 'title': 'Apartment'},
      'owner': {
        'name': 'Owner',
        'phone_number': _phone,
        'masked_phone_number': '010****432',
        'is_phone_revealed': true,
      },
      'actions': {'can_cancel': false, 'can_chat': false, 'can_review': false},
    });
    await _pump(
      tester,
      VisitDetailsContent(visit: details.visit, details: details),
    );
    expect(find.text(_phone), findsOneWidget);
    expect(find.text('010****432'), findsNothing);
    await _capture(tester, 'tenant-accepted');
  });

  for (final String language in ['ar', 'en']) {
    for (final double width in [320, 390, 600, 768, 1024, 1366]) {
      for (final double scale in [1, 1.3, 2]) {
        testWidgets('contact card at $width/$scale in $language', (
          tester,
        ) async {
          await _pump(
            tester,
            const RevealedPhoneCard(phoneNumber: _phone),
            width: width,
            scale: scale,
            language: language,
          );
          expect(find.text(_phone), findsOneWidget);
          final phoneDirection = tester.widget<Directionality>(
            find
                .ancestor(
                  of: find.byType(SelectableText),
                  matching: find.byType(Directionality),
                )
                .first,
          );
          expect(phoneDirection.textDirection, ui.TextDirection.ltr);
          expect(tester.takeException(), isNull);
        });
      }
    }
  }
}

Future<void> _pump(
  WidgetTester tester,
  Widget content, {
  double width = 390,
  double scale = 1,
  String language = 'en',
}) async {
  tester.view.physicalSize = Size(width, 844);
  tester.view.devicePixelRatio = 1;
  addTearDown(tester.view.resetPhysicalSize);
  addTearDown(tester.view.resetDevicePixelRatio);
  await tester.pumpWidget(
    EasyLocalization(
      supportedLocales: const [Locale('ar'), Locale('en')],
      startLocale: Locale(language),
      fallbackLocale: const Locale('en'),
      path: 'unused',
      assetLoader: const _Translations(),
      child: ScreenUtilInit(
        designSize: Size(ScreenSizes.width, ScreenSizes.height),
        builder: (context, _) => MaterialApp(
          theme: SokounTheme.light,
          localizationsDelegates: context.localizationDelegates,
          supportedLocales: context.supportedLocales,
          locale: context.locale,
          builder: (context, child) => MediaQuery(
            data: MediaQuery.of(
              context,
            ).copyWith(textScaler: TextScaler.linear(scale)),
            child: child!,
          ),
          home: RepaintBoundary(
            child: AppScaffold(title: 'Visit', body: content),
          ),
        ),
      ),
    ),
  );
  await tester.pumpAndSettle();
  expect(tester.takeException(), isNull);
}

class _Translations extends AssetLoader {
  const _Translations();
  @override
  Future<Map<String, dynamic>> load(String path, Locale locale) async =>
      _translations[locale.languageCode]!;
}

Future<void> _capture(WidgetTester tester, String name) async {
  const directory = String.fromEnvironment('UI_REVIEW_DIR');
  if (directory.isEmpty) return;
  await tester.runAsync(() async {
    final boundary = tester.renderObject<RenderRepaintBoundary>(
      find.byType(RepaintBoundary).first,
    );
    final image = await boundary.toImage();
    final bytes = await image.toByteData(format: ui.ImageByteFormat.png);
    await Directory(directory).create(recursive: true);
    await File(
      '$directory/$name.png',
    ).writeAsBytes(bytes!.buffer.asUint8List());
    image.dispose();
  });
}
