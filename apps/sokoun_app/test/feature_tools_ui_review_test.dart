import 'dart:io';
import 'dart:ui' as ui;
import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:sokoun_app/features/main_view/data/enums/app_workspace.dart';
import 'package:sokoun_app/features/owner/advanced_analytics/data/models/advanced_analytics_content.dart';
import 'package:sokoun_app/features/owner/advanced_analytics/data/models/analytics_metric.dart';
import 'package:sokoun_app/features/owner/advanced_analytics/presentation/widgets/advanced_analytics_summary.dart';
import 'package:sokoun_app/features/owner/ai_assistant/data/models/listing_suggestion.dart';
import 'package:sokoun_app/features/owner/ai_assistant/presentation/widgets/listing_ai_review.dart';
import 'package:sokoun_app/features/owner/promotions/presentation/widgets/promotion_composer.dart';
import 'package:sokoun_app/features/owner/properties/data/models/owner_property_content.dart';
import 'package:sokoun_app/features/shared/digital_leases/data/models/digital_lease.dart';
import 'package:sokoun_app/features/shared/digital_leases/data/models/lease_template.dart';
import 'package:sokoun_app/features/shared/digital_leases/presentation/widgets/digital_lease_details_view.dart';
import 'package:sokoun_app/features/shared/digital_leases/presentation/widgets/lease_draft_form.dart';
import 'package:sokoun_app/features/shared/premium/data/enums/premium_status.dart';
import 'package:sokoun_app/features/shared/premium/data/models/feature_configuration.dart';
import 'package:sokoun_app/features/shared/premium/data/models/premium_money.dart';
import 'package:sokoun_app/features/shared/premium/data/models/promotion_option.dart';
import 'package:sokoun_app/features/shared/premium/presentation/widgets/premium_dashboard/premium_dashboard.dart';
import 'package:sokoun_app/features/shared/premium/presentation/widgets/premium_dashboard/premium_entry_tile.dart';
import 'package:sokoun_app/features/shared/premium/presentation/widgets/shared/premium_empty_state.dart';
import 'package:sokoun_app/features/shared/rent_management/data/models/rent_invoice.dart';
import 'package:sokoun_app/features/shared/rent_management/presentation/widgets/rent_invoice_details_view.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_search_model.dart';
import 'package:sokoun_app/features/tenant/premium_alerts/presentation/cubits/premium_alert_submit_cubit.dart';
import 'package:sokoun_app/features/tenant/premium_alerts/presentation/widgets/premium_alert_composer.dart';
import 'package:sokoun_app/shared_widgets/app_scaffold.dart';
import 'helpers/feature_tools_test_dependencies.dart';

/// Export rendered fixtures with --dart-define=FEATURE_TOOLS_UI_REVIEW_DIR=/tmp/sokoun-tools-after.
void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  const output = String.fromEnvironment('FEATURE_TOOLS_UI_REVIEW_DIR');
  late PremiumAlertSubmitCubit alerts;
  const configuration = FeatureConfiguration(
    workspace: 'owner',
    alertCadences: ['instant', 'daily'],
    boostOptions: [
      PromotionOption(
        id: 'week',
        title: 'أسبوع من الظهور المميز',
        durationDays: 7,
      ),
    ],
  );

  setUpAll(() async {
    await initializeFeatureTestEnvironment();
    await registerFeatureTestDependencies(FeatureTestRepository());
    alerts = PremiumAlertSubmitCubit();
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
  tearDownAll(() async {
    await alerts.close();
  });

  for (final locale in ['ar', 'en']) {
    for (final dark in [false, true]) {
      for (final width in [320.0, 390.0, 600.0, 768.0, 1024.0, 1366.0]) {
        for (final scale in [1.0, 1.3, 2.0]) {
          testWidgets(
            'free tools screens $locale ${dark ? 'dark' : 'light'} $width scale $scale',
            (tester) async {
              tester.view.physicalSize = Size(width, width >= 600 ? 900 : 844);
              tester.view.devicePixelRatio = 1;
              addTearDown(tester.view.reset);
              final property = OwnerPropertyContent.initial().copyWith(
                id: 'property',
                title: locale == 'ar'
                    ? 'شقة واسعة بإضاءة طبيعية في المعادي'
                    : 'Bright apartment near work in Maadi',
                location: locale == 'ar' ? 'المعادي القاهرة' : 'Maadi Cairo',
                monthlyPrice: 12000,
                pricePeriod: 'monthly',
              );
              final panels = <String, Widget>{
                'entries': Column(
                  children: const [
                    PremiumEntryTile(workspace: AppWorkspace.owner),
                    PremiumEntryTile(workspace: AppWorkspace.tenant),
                  ],
                ),
                'tools': PremiumDashboard(workspace: AppWorkspace.owner),
                'promotion': SingleChildScrollView(
                  child: PromotionComposer(
                    configuration: configuration,
                    isFresh: true,
                    initialProperty: property,
                    onSaved: () async {},
                  ),
                ),
                'alerts': SingleChildScrollView(
                  padding: const EdgeInsets.all(20),
                  child: PremiumAlertComposer(
                    filters: const PropertySearchFilters.initial(
                      search: 'المعادي',
                      priceMin: '10000',
                      priceMax: '18000',
                    ),
                    name: locale == 'ar'
                        ? 'قرب العمل في المعادي'
                        : 'Near work in Maadi',
                    cadences: const ['instant', 'daily'],
                    cubit: alerts,
                    canChange: true,
                    onSaved: () async {},
                  ),
                ),
                'analytics': SingleChildScrollView(
                  padding: const EdgeInsets.all(20),
                  child: AdvancedAnalyticsSummary(
                    content: AdvancedAnalyticsContent(
                      propertyId: 'property',
                      measuredAt: DateTime.utc(2026, 10, 6),
                      methodology: locale == 'ar'
                          ? 'عدد الزوار الفريدين وطلبات المعاينة خلال الفترة المختارة'
                          : 'Unique visitors and viewing requests during this period',
                      metrics: const [
                        AnalyticsMetric(
                          key: 'unique_views',
                          label: 'زوار الإعلان',
                          definition: 'الزوار الفريدون خلال الفترة المختارة',
                          value: 128,
                        ),
                        AnalyticsMetric(
                          key: 'conversion',
                          label: 'تحويل إلى طلب معاينة',
                          definition:
                              'طلبات المعاينة مقسومة على الزوار الفريدين',
                          value: 3.25,
                          unit: 'percent',
                        ),
                        AnalyticsMetric(
                          key: 'missing',
                          label: 'البيانات غير المتاحة',
                        ),
                      ],
                    ),
                  ),
                ),
                'ai': SingleChildScrollView(
                  padding: const EdgeInsets.all(20),
                  child: ListingAiReview(
                    suggestion: ListingSuggestion(
                      id: 'suggestion',
                      suggestedTitle: property.title,
                      suggestedDescription: locale == 'ar'
                          ? 'شقة مضيئة بغرفتين ومساحة مناسبة للأسرة. راجع التفاصيل وتأكد من مطابقتها للعقار قبل النشر.'
                          : 'Bright two bedroom apartment with space for a family. Review the supplied details before publishing.',
                      warnings: [
                        locale == 'ar'
                            ? 'راجع صحة جميع المعلومات قبل استخدام الاقتراح.'
                            : 'Check every statement before applying this suggestion.',
                      ],
                    ),
                    canApply: true,
                  ),
                ),
                'lease_form': const LeaseDraftForm(
                  templates: [
                    LeaseTemplate(
                      id: 'template',
                      title: 'عقد إيجار سكني معتمد',
                      jurisdiction: 'EG',
                      language: 'ar',
                      version: 'v1',
                    ),
                  ],
                  isFresh: true,
                ),
                'lease': DigitalLeaseDetailsView(
                  workspace: AppWorkspace.tenant,
                  lease: DigitalLease(
                    id: 'lease',
                    propertyId: property.id,
                    propertyTitle: property.title,
                    ownerName: 'أحمد محمد',
                    tenantName: 'سارة محمود',
                    startDate: DateTime(2026, 10, 10),
                    endDate: DateTime(2027, 10, 10),
                    rent: const PremiumMoney(
                      amountMinor: 1200000,
                      currency: 'EGP',
                    ),
                    status: PremiumStatus.pending,
                    revision: 2,
                    canSign: true,
                    documentUrl: 'https://example.invalid/lease',
                  ),
                  isFresh: true,
                  onRefresh: () async {},
                ),
                'rent': RentInvoiceDetailsView(
                  invoice: RentInvoice(
                    id: 'invoice',
                    propertyTitle: property.title,
                    reference: 'INV-2026-001',
                    dueDate: DateTime(2026, 11, 1),
                    amount: const PremiumMoney(
                      amountMinor: 1200000,
                      currency: 'EGP',
                    ),
                    status: PremiumStatus.due,
                    canPay: true,
                  ),
                  isFresh: true,
                  onRefresh: () async {},
                ),
                'empty': SingleChildScrollView(
                  child: PremiumEmptyState(
                    title: LocaleKeys.paidUnavailable,
                    description: LocaleKeys.paidUnavailableBody,
                  ),
                ),
              };
              for (final entry in panels.entries) {
                final boundaryKey = GlobalKey();
                await tester.pumpWidget(
                  KeyedSubtree(
                    key: ValueKey('$locale-$dark-$width-$scale-${entry.key}'),
                    child: featureTestHost(
                      RepaintBoundary(
                        key: boundaryKey,
                        child: AppScaffold(
                          title: LocaleKeys.toolsTitle,
                          body: entry.value,
                        ),
                      ),
                      locale: locale,
                      dark: dark,
                      scale: scale,
                    ),
                  ),
                );
                await tester.pumpAndSettle();
                if (entry.key == 'promotion' ||
                    entry.key == 'alerts' ||
                    entry.key == 'lease_form') {
                  final dropdown = find.byType(DropdownButtonFormField<String>);
                  await tester.ensureVisible(dropdown);
                  await tester.tap(dropdown);
                  await tester.pumpAndSettle();
                  final choice = entry.key == 'promotion'
                      ? 'أسبوع من الظهور المميز'
                      : entry.key == 'lease_form'
                      ? 'عقد إيجار سكني معتمد v1'
                      : LocaleKeys.paidAlertDaily;
                  await tester.tap(find.text(choice).last);
                  await tester.pumpAndSettle();
                }
                expect(
                  tester.takeException(),
                  isNull,
                  reason: '${entry.key} at $locale $width scale $scale',
                );
                if (output.isNotEmpty &&
                    (scale == 1 ||
                        (scale == 2 && (width == 320 || width == 1366)))) {
                  final boundary =
                      boundaryKey.currentContext!.findRenderObject()!
                          as RenderRepaintBoundary;
                  await tester.runAsync(() async {
                    final bitmap = await boundary.toImage(pixelRatio: 1);
                    final bytes = await bitmap.toByteData(
                      format: ui.ImageByteFormat.png,
                    );
                    bitmap.dispose();
                    final directory = Directory(output);
                    await directory.create(recursive: true);
                    await File(
                      '$output/${entry.key}_${locale}_${dark ? 'dark' : 'light'}_${width.toInt()}_scale${scale.toStringAsFixed(1)}.png',
                    ).writeAsBytes(bytes!.buffer.asUint8List());
                  });
                }
                await tester.pumpWidget(const SizedBox());
                await tester.pump();
              }
            },
          );
        }
      }
    }
  }
  for (final locale in ['ar', 'en']) {
    testWidgets(
      'alert draft survives keyboard and phone landscape resize $locale',
      (tester) async {
        tester.view.physicalSize = const Size(320, 844);
        tester.view.devicePixelRatio = 1;
        addTearDown(tester.view.reset);
        await tester.pumpWidget(
          featureTestHost(
            AppScaffold(
              title: LocaleKeys.paidPriorityAlerts,
              body: SingleChildScrollView(
                padding: const EdgeInsets.all(20),
                child: PremiumAlertComposer(
                  filters: const PropertySearchFilters.initial(search: 'Maadi'),
                  name: 'Original',
                  cadences: const ['daily'],
                  cubit: alerts,
                  canChange: true,
                  onSaved: () {},
                ),
              ),
            ),
            locale: locale,
            dark: true,
            scale: 1.3,
          ),
        );
        await tester.pumpAndSettle();
        final name = find.byType(TextFormField);
        await tester.enterText(name, 'Edited viewing search');
        tester.view.viewInsets = const FakeViewPadding(bottom: 300);
        await tester.pumpAndSettle();
        await tester.ensureVisible(find.byType(FilledButton));
        await tester.pumpAndSettle();
        expect(tester.getCenter(find.byType(FilledButton)).dy, lessThan(544));
        tester.view.physicalSize = const Size(844, 390);
        tester.view.viewInsets = const FakeViewPadding(bottom: 140);
        await tester.pumpAndSettle();
        await tester.ensureVisible(find.byType(FilledButton));
        await tester.pumpAndSettle();
        expect(tester.getCenter(find.byType(FilledButton)).dy, lessThan(250));
        expect(
          tester.widget<TextFormField>(name).controller!.text,
          'Edited viewing search',
        );
        expect(tester.takeException(), isNull);
      },
    );
    testWidgets(
      'AI review edits survive tablet split view and keyboard $locale',
      (tester) async {
        tester.view.physicalSize = const Size(1024, 900);
        tester.view.devicePixelRatio = 1;
        addTearDown(tester.view.reset);
        await tester.pumpWidget(
          featureTestHost(
            const AppScaffold(
              body: SingleChildScrollView(
                padding: EdgeInsets.all(20),
                child: ListingAiReview(
                  suggestion: ListingSuggestion(
                    id: 'suggestion',
                    suggestedTitle: 'Suggested title',
                    suggestedDescription: 'Suggested description',
                  ),
                  canApply: true,
                ),
              ),
            ),
            locale: locale,
            scale: 2,
          ),
        );
        await tester.pumpAndSettle();
        await tester.enterText(
          find.byType(TextFormField).last,
          'Owner reviewed description',
        );
        tester.view.physicalSize = const Size(600, 900);
        tester.view.viewInsets = const FakeViewPadding(bottom: 300);
        await tester.pumpAndSettle();
        await tester.ensureVisible(find.text(LocaleKeys.paidAiApply));
        await tester.pumpAndSettle();
        expect(
          tester.getCenter(find.text(LocaleKeys.paidAiApply)).dy,
          lessThan(600),
        );
        expect(
          tester
              .widget<TextFormField>(find.byType(TextFormField).last)
              .controller!
              .text,
          'Owner reviewed description',
        );
        expect(tester.takeException(), isNull);
      },
    );
  }
}
