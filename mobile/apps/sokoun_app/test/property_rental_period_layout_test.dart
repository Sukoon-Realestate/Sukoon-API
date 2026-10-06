import 'dart:convert';
import 'dart:io';

import 'package:easy_localization/easy_localization.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:sokoun_app/features/owner/home/data/models/owner_add_property_content.dart';
import 'package:sokoun_app/features/owner/home/presentation/widgets/owner_add_property/add_property_rental_period_section.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_filter_options_model.dart';
import 'package:sokoun_app/shared_widgets/sokoun_theme.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  setUpAll(() async {
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(
          const MethodChannel('plugins.flutter.io/shared_preferences'),
          (call) async => call.method == 'getAll' ? <String, Object>{} : true,
        );
    await EasyLocalization.ensureInitialized();
  });
  tearDownAll(() {
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(
          const MethodChannel('plugins.flutter.io/shared_preferences'),
          null,
        );
  });

  for (final locale in ['ar', 'en']) {
    for (final width in [320.0, 390.0]) {
      for (final scale in [1.0, 2.0]) {
        testWidgets(
          'rental months and price period align horizontally in $locale at $width and $scale',
          (tester) async {
            tester.view.physicalSize = Size(width, 844);
            tester.view.devicePixelRatio = 1;
            addTearDown(tester.view.reset);
            final duration = TextEditingController(text: '12');
            addTearDown(duration.dispose);
            final durationKey = GlobalKey();
            final periodKey = GlobalKey();
            String? period;
            final weekly = locale == 'ar' ? 'أسبوعي' : 'Weekly';
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
                      data: MediaQuery.of(
                        context,
                      ).copyWith(textScaler: TextScaler.linear(scale)),
                      child: child!,
                    ),
                    home: Scaffold(
                      body: SingleChildScrollView(
                        padding: const EdgeInsets.all(16),
                        child: Form(
                          child: AddPropertyRentalPeriodSection(
                            form: OwnerAddPropertyFormState.initial().copyWith(
                              rentalDuration: '12',
                              rentalUnit: 'monthly',
                            ),
                            rentalDurationController: duration,
                            durationFieldKey: durationKey,
                            unitFieldKey: periodKey,
                            onRentalDurationChanged: (_) {},
                            onRentalUnitChanged: (value) => period = value,
                            options: [
                              TenantFilterOption(
                                value: 'daily',
                                label: locale == 'ar' ? 'يومي' : 'Daily',
                              ),
                              TenantFilterOption(
                                value: 'weekly',
                                label: weekly,
                              ),
                              TenantFilterOption(
                                value: 'monthly',
                                label: locale == 'ar' ? 'شهري' : 'Monthly',
                              ),
                              TenantFilterOption(
                                value: 'yearly',
                                label: locale == 'ar' ? 'سنوي' : 'Yearly',
                              ),
                            ],
                          ),
                        ),
                      ),
                    ),
                  ),
                ),
              ),
            );
            await tester.pumpAndSettle();
            final monthsRect = tester.getRect(find.byKey(durationKey));
            final periodRect = tester.getRect(find.byKey(periodKey));
            expect(monthsRect.top, closeTo(periodRect.top, .01));
            expect(monthsRect.overlaps(periodRect), isFalse);
            if (locale == 'ar') {
              expect(monthsRect.left, greaterThan(periodRect.left));
            } else {
              expect(monthsRect.left, lessThan(periodRect.left));
            }
            await tester.tap(find.byKey(periodKey));
            await tester.pumpAndSettle();
            await tester.tap(find.text(weekly).last);
            await tester.pumpAndSettle();
            expect(period, 'weekly');
            expect(duration.text, '12');
            expect(tester.takeException(), isNull);
          },
        );
      }
    }
  }
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
