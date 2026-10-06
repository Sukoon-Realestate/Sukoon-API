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
import 'package:melos_core/core/helpers/cache_service.dart';
import 'package:sokoun_app/features/owner/home/data/models/owner_add_property_content.dart';
import 'package:sokoun_app/features/owner/home/presentation/widgets/owner_add_property/listing_quality_card.dart';
import 'package:sokoun_app/features/owner/home/presentation/widgets/owner_add_property/owner_draft_save_warning.dart';
import 'package:sokoun_app/features/shared/chat/data/models/chat_content.dart';
import 'package:sokoun_app/features/shared/chat/presentation/widgets/report/chat_report_sheet.dart';
import 'package:sokoun_app/features/tenant/decision_tools/data/decision_tools_data.dart';
import 'package:sokoun_app/features/tenant/decision_tools/data/models/comparison_property.dart';
import 'package:sokoun_app/features/tenant/decision_tools/data/models/decision_notebook.dart';
import 'package:sokoun_app/features/tenant/decision_tools/data/models/property_cost_breakdown.dart';
import 'package:sokoun_app/features/tenant/decision_tools/presentation/cubits/decision_tools_cubit.dart';
import 'package:sokoun_app/features/tenant/decision_tools/presentation/widgets/availability_confirmation_label.dart';
import 'package:sokoun_app/features/tenant/decision_tools/presentation/widgets/comparison_table.dart';
import 'package:sokoun_app/features/tenant/decision_tools/presentation/widgets/decision_editor.dart';
import 'package:sokoun_app/features/tenant/decision_tools/presentation/widgets/decision_notebook_view.dart';
import 'package:sokoun_app/features/tenant/decision_tools/presentation/widgets/property_cost_card.dart';
import 'package:sokoun_app/features/tenant/decision_tools/presentation/widgets/property_match_explanation.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_details_model.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_search_model.dart';
import 'package:sokoun_app/features/tenant/visits/imports.dart';
import 'package:sokoun_app/shared_widgets/app_scaffold.dart';
import 'package:sokoun_app/shared_widgets/sokoun_theme.dart';
import 'package:sokoun_app/shared_widgets/sokoun_layout.dart';
import 'helpers/home_page_test_dependencies.dart';

/// Export representative renders with --dart-define=FREE_UI_REVIEW_DIR=/tmp/review.
void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  const output = String.fromEnvironment('FREE_UI_REVIEW_DIR');
  late DecisionToolsCubit decisions;
  setUpAll(() async {
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(
          const MethodChannel('plugins.flutter.io/shared_preferences'),
          (call) async => call.method == 'getAll' ? <String, Object>{} : true,
        );
    await EasyLocalization.ensureInitialized();
    await CacheStorage.init();
    registerHomePageTestDependencies();
    decisions = DecisionToolsCubit(accountId: 'review', store: _ReviewStore());
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
  });
  tearDownAll(() => decisions.close());

  for (final locale in ['ar', 'en']) {
    for (final dark in [false, true]) {
      for (final width in [320.0, 390.0, 600.0, 768.0, 1024.0, 1366.0]) {
        for (final scale in [1.0, 1.3, 2.0]) {
          testWidgets(
            'free features $locale ${dark ? 'dark' : 'light'} $width scale $scale',
            (tester) async {
              tester.view.physicalSize = Size(width, width >= 600 ? 900 : 844);
              tester.view.devicePixelRatio = 1;
              addTearDown(tester.view.reset);
              final property = const PropertyDetailsModel.initial().copyWith(
                id: 'review-property',
                title: locale == 'ar'
                    ? 'شقة واسعة بإضاءة طبيعية في المعادي'
                    : 'Bright apartment near work in Maadi',
                price: '18000',
                pricePeriod: 'monthly',
                deposit: 'one_month',
                rentalPeriod: 6,
                propertyType: 'apartment',
                bedrooms: 2,
                bathrooms: 1,
                space: '120',
                amenities: ['wifi'],
                isVerified: true,
              );
              final decision = PropertyDecision(
                propertyId: property.id,
                title: property.title,
                list: locale == 'ar' ? 'قريبة من العمل' : 'Near work',
                note: locale == 'ar'
                    ? 'اسأل عن ضغط المياه وصوت الشارع وتكلفة الصيانة.'
                    : 'Ask about water pressure, street noise and maintenance costs.',
                checkedItems: const {'water', 'light'},
              );
              const filters = PropertySearchFilters.initial(
                priceMax: '20000',
                pricePeriod: 'monthly',
                amenities: {'wifi'},
              );
              final notebook = DecisionNotebook(
                properties: [decision],
                comparisonIds: [property.id],
                searches: [
                  SavedPropertySearch(
                    id: 'search',
                    name: locale == 'ar' ? 'بالقرب من العمل' : 'Near work',
                    filters: filters,
                  ),
                ],
              );
              for (final subject in [
                'costs',
                'comparison',
                'notebook',
                'viewing_notes',
                'listing_quality',
                'visit_times',
                'report',
              ]) {
                late Widget panel;
                switch (subject) {
                  case 'costs':
                    panel = Column(
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: [
                        AvailabilityConfirmationLabel(
                          confirmedAt: DateTime.utc(2026, 9, 1),
                        ),
                        const SizedBox(height: 12),
                        const AvailabilityConfirmationLabel(confirmedAt: null),
                        PropertyMatchExplanation(
                          property: property,
                          preferences: filters,
                        ),
                        PropertyCostCard(
                          cost: PropertyCostBreakdown.fromProperty(property),
                          periodLabel: property.pricePeriodLabel,
                        ),
                      ],
                    );
                  case 'comparison':
                    panel = ComparisonTable(
                      savedTitles: {
                        'removed': locale == 'ar'
                            ? 'استوديو بالقرب من الجامعة'
                            : 'Studio near the university',
                      },
                      properties: [
                        ComparisonProperty(
                          propertyId: property.id,
                          property: property,
                          isCached: false,
                          error: '',
                        ),
                        ComparisonProperty(
                          propertyId: 'cached',
                          property: property.copyWith(
                            id: 'cached',
                            deposit: '',
                          ),
                          isCached: true,
                          error: '',
                        ),
                        const ComparisonProperty(
                          propertyId: 'removed',
                          property: PropertyDetailsModel.initial(),
                          isCached: false,
                          error: '404',
                        ),
                      ],
                      onRemove: (_) {},
                    );
                  case 'notebook':
                    panel = DecisionNotebookView(
                      notebook: notebook,
                      cubit: decisions,
                      onReturned: () async {},
                    );
                  case 'viewing_notes':
                    panel = DecisionEditor(
                      cubit: decisions,
                      decision: decision,
                    );
                  case 'listing_quality':
                    panel = Column(
                      children: [
                        ListingQualityCard(
                          form: OwnerAddPropertyFormState.initial().copyWith(
                            description: decision.note,
                            deposit: 'none',
                          ),
                        ),
                        OwnerDraftSaveWarning(onRetry: () async {}),
                      ],
                    );
                  case 'visit_times':
                    panel = Column(
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: [
                        VisitAvailableTimes(
                          date: '2040-06-15',
                          slots: const [
                            VisitTimeSlotContent(
                              label: '9 AM',
                              visitTime: '09:00:00',
                            ),
                            VisitTimeSlotContent(
                              label: '2 PM',
                              visitTime: '14:00:00',
                            ),
                            VisitTimeSlotContent(
                              label: '4 PM',
                              visitTime: '16:00:00',
                              isAvailable: false,
                            ),
                          ],
                          selectedTime: const TimeOfDay(hour: 14, minute: 0),
                          onSelected: (_) {},
                        ),
                        const SizedBox(height: 24),
                        VisitAvailableTimes(
                          date: '2040-06-15',
                          slots: const [],
                          isCached: true,
                          selectedTime: null,
                          onSelected: (_) {},
                        ),
                        const SizedBox(height: 24),
                        VisitCalendarButton(
                          visit: TenantVisitContent(
                            id: 'visit',
                            propertyTitle: property.title,
                            visitDate: '2040-06-15',
                            visitTime: '14:00:00',
                            day: '',
                            time: '',
                            status: TenantVisitStatus.accepted,
                            statusText: '',
                          ),
                        ),
                      ],
                    );
                  case 'report':
                    panel = const ChatReportSheet(
                      conversation: ConversationContent.initial(),
                    );
                }
                await tester.pumpWidget(
                  EasyLocalization(
                    key: ValueKey('$locale-$dark-$width-$scale-$subject'),
                    supportedLocales: const [Locale('ar'), Locale('en')],
                    startLocale: Locale(locale),
                    fallbackLocale: const Locale('en'),
                    saveLocale: false,
                    path: 'unused',
                    assetLoader: const _Translations(),
                    child: ScreenUtilInit(
                      designSize: const Size(360, 690),
                      enableScaleWH: () => false,
                      enableScaleText: () => false,
                      fontSizeResolver: (size, _) => size.toDouble(),
                      builder: (context, _) => MaterialApp(
                        theme: dark ? SokounTheme.dark : SokounTheme.light,
                        locale: context.locale,
                        supportedLocales: context.supportedLocales,
                        localizationsDelegates: context.localizationDelegates,
                        home: Builder(
                          builder: (context) => MediaQuery(
                            data: MediaQuery.of(context).copyWith(
                              textScaler: TextScaler.linear(scale),
                              disableAnimations: true,
                            ),
                            child: RepaintBoundary(
                              child: AppScaffold(
                                title: LocaleKeys.freeDecisionTools,
                                contentWidth: subject == 'comparison'
                                    ? SokounContentWidth.wide
                                    : SokounContentWidth.readable,
                                body:
                                    subject == 'report' ||
                                        subject == 'viewing_notes'
                                    ? panel
                                    : SingleChildScrollView(
                                        padding: const EdgeInsets.all(20),
                                        child: panel,
                                      ),
                              ),
                            ),
                          ),
                        ),
                      ),
                    ),
                  ),
                );
                await tester.pumpAndSettle();
                expect(
                  tester.takeException(),
                  isNull,
                  reason: '$subject at $locale/$dark/$width/$scale',
                );
                if (subject == 'comparison') {
                  expect(find.text('404'), findsNothing);
                  expect(
                    find.text(
                      locale == 'ar'
                          ? 'استوديو بالقرب من الجامعة'
                          : 'Studio near the university',
                    ),
                    findsOneWidget,
                  );
                }
                if (output.isNotEmpty &&
                    scale == 1 &&
                    (width == 390 || width == 1024)) {
                  final RenderRepaintBoundary boundary = tester.renderObject(
                    find.byType(RepaintBoundary).first,
                  );
                  await tester.runAsync(() async {
                    final ui.Image picture = await boundary.toImage();
                    final bytes = await picture.toByteData(
                      format: ui.ImageByteFormat.png,
                    );
                    await Directory(output).create(recursive: true);
                    await File(
                      '$output/$subject-$locale-${dark ? 'dark' : 'light'}-${width.toInt()}.png',
                    ).writeAsBytes(bytes!.buffer.asUint8List());
                    picture.dispose();
                  });
                }
              }
            },
          );
        }
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

class _ReviewStore implements DecisionToolsStore {
  @override
  Future<DecisionNotebook> read(String accountId) async =>
      const DecisionNotebook.initial();
  @override
  Future<void> write(String accountId, DecisionNotebook notebook) async {}
}
