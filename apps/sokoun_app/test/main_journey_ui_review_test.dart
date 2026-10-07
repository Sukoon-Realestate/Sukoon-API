import 'dart:io';
import 'dart:ui' as ui;
import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:sokoun_app/features/main_view/data/enums/app_workspace.dart';
import 'package:sokoun_app/features/owner/home/data/models/owner_dashboard_model.dart';
import 'package:sokoun_app/features/owner/home/presentation/widgets/owner_widgets/owner_dashboard_content.dart';
import 'package:sokoun_app/features/owner/properties/imports.dart';
import 'package:sokoun_app/features/shared/digital_leases/data/models/digital_lease.dart';
import 'package:sokoun_app/features/shared/digital_leases/data/models/lease_template.dart';
import 'package:sokoun_app/features/shared/digital_leases/presentation/widgets/digital_lease_details_view.dart';
import 'package:sokoun_app/features/shared/digital_leases/presentation/widgets/lease_draft_form.dart';
import 'package:sokoun_app/features/shared/premium/data/enums/premium_status.dart';
import 'package:sokoun_app/features/shared/premium/data/models/premium_money.dart';
import 'package:sokoun_app/features/shared/profile/imports.dart';
import 'package:sokoun_app/features/shared/profile/presentation/widgets/contracts/contracts_journey_actions.dart';
import 'package:sokoun_app/features/shared/rent_management/data/models/rent_invoice.dart';
import 'package:sokoun_app/features/shared/rent_management/presentation/widgets/rent_overview_card.dart';
import 'package:sokoun_app/features/shared/rent_management/presentation/widgets/rent_overview_empty_state.dart';
import 'package:sokoun_app/features/tenant/home/presentation/widgets/tenant_widgets/tenant_home_header.dart';
import 'package:sokoun_app/shared_widgets/app_scaffold.dart';
import 'package:sokoun_app/shared_widgets/sokoun_layout.dart';
import 'helpers/feature_tools_test_dependencies.dart';

/// Export with --dart-define=MAIN_JOURNEY_UI_REVIEW_DIR=/tmp/sokoun-main-flow-after.
void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  const output = String.fromEnvironment('MAIN_JOURNEY_UI_REVIEW_DIR');
  setUpAll(() async {
    await initializeFeatureTestEnvironment();
    await registerFeatureTestDependencies(FeatureTestRepository());
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
  for (final locale in ['ar', 'en']) {
    for (final dark in [false, true]) {
      for (final width in [320.0, 390.0, 600.0, 768.0, 1024.0, 1366.0]) {
        for (final scale in [1.0, 1.3, 2.0]) {
          testWidgets(
            'main journeys $locale ${dark ? 'dark' : 'light'} $width scale $scale',
            (tester) async {
              tester.view.physicalSize = Size(width, width >= 600 ? 900 : 844);
              tester.view.devicePixelRatio = 1;
              addTearDown(tester.view.reset);
              final property = OwnerPropertyContent.initial().copyWith(
                id: 'property-1',
                title: locale == 'ar'
                    ? 'شقة واسعة بإضاءة طبيعية في المعادي'
                    : 'Bright apartment near work in Maadi',
                monthlyPrice: 6500.5,
                pricePeriod: 'monthly',
                status: OwnerPropertyStatus.accepted,
              );
              final invoice = RentInvoice(
                id: 'invoice-1',
                leaseId: 'lease-1',
                propertyTitle: property.title,
                dueDate: DateTime(2026, 11, 1),
                status: PremiumStatus.overdue,
                amount: const PremiumMoney(
                  amountMinor: 650050,
                  currency: 'EGP',
                ),
              );
              final panels = <String, Widget>{
                'dashboard': OwnerDashboardContent(
                  dashboard: const OwnerDashboardModel.initial(),
                  onRequestResolved: () async {},
                ),
                'property': SingleChildScrollView(
                  padding: const EdgeInsets.all(20),
                  child: OwnerPropertyCard(
                    property: property,
                    onEditPressed: () {},
                    onRejectedPressed: () {},
                    onDeletePressed: () {},
                  ),
                ),
                'tenant_home': SingleChildScrollView(
                  padding: const EdgeInsets.symmetric(horizontal: 20),
                  child: TenantHomeHeader(
                    banner: null,
                    rentOverview: RentOverviewCard(
                      invoice: invoice,
                      isCached: false,
                      onReturned: () async {},
                    ),
                  ),
                ),
                'rent_empty': const SingleChildScrollView(
                  padding: EdgeInsets.all(20),
                  child: RentOverviewEmptyState(),
                ),
                'rent_cached': SingleChildScrollView(
                  padding: const EdgeInsets.all(20),
                  child: RentOverviewCard(
                    invoice: invoice.copyWith(
                      amount: const PremiumMoney.initial(),
                    ),
                    isCached: true,
                    onReturned: () async {},
                  ),
                ),
                'contracts': const SingleChildScrollView(
                  padding: EdgeInsets.all(20),
                  child: Column(
                    children: [
                      ContractsJourneyActions(workspace: AppWorkspace.owner),
                      ProfileContractCard(
                        contract: ProfileContractContent(
                          id: 'document-1',
                          leaseId: 'lease-1',
                          propertyTitle: 'Apartment in Maadi',
                          status: 'active',
                          startDate: '2026-10-10',
                          endDate: '2027-10-10',
                          documentUrl: 'https://example.com/document.pdf',
                        ),
                        workspace: AppWorkspace.owner,
                      ),
                    ],
                  ),
                ),
                'lease_form': LeaseDraftForm(
                  property: property,
                  templates: const [
                    LeaseTemplate(
                      id: 'template',
                      title: 'عقد إيجار سكني معتمد',
                      version: 'v1',
                    ),
                  ],
                  isFresh: true,
                ),
                'lease': DigitalLeaseDetailsView(
                  lease: DigitalLease(
                    id: 'lease-1',
                    propertyTitle: property.title,
                    status: PremiumStatus.active,
                    rent: invoice.amount,
                  ),
                  workspace: AppWorkspace.tenant,
                  isFresh: true,
                  onRefresh: () async {},
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
                          contentWidth: SokounContentWidth.wide,
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
                expect(
                  tester.takeException(),
                  isNull,
                  reason: '${entry.key}: $locale $width $scale',
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
                    await Directory(output).create(recursive: true);
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
      'property lease input survives keyboard landscape and split view $locale',
      (tester) async {
        tester.view.physicalSize = const Size(390, 844);
        tester.view.devicePixelRatio = 1;
        addTearDown(tester.view.reset);
        final property = OwnerPropertyContent.initial().copyWith(
          id: 'property-1',
          title: 'Apartment in Maadi',
        );
        await tester.pumpWidget(
          featureTestHost(
            AppScaffold(
              title: LocaleKeys.paidCreateLease,
              body: LeaseDraftForm(
                property: property,
                templates: const [
                  LeaseTemplate(id: 'template', title: 'Lease', version: 'v1'),
                ],
                isFresh: true,
              ),
            ),
            locale: locale,
            scale: 2,
          ),
        );
        await tester.pumpAndSettle();
        final rent = find.widgetWithText(
          TextFormField,
          LocaleKeys.paidMonthlyRent,
        );
        await tester.ensureVisible(rent);
        await tester.enterText(rent, '6500.50');
        await tester.pumpAndSettle();
        for (final size in [
          const Size(844, 390),
          const Size(768, 900),
          const Size(320, 844),
        ]) {
          tester.view.physicalSize = size;
          tester.view.viewInsets = const FakeViewPadding(bottom: 240);
          await tester.pumpAndSettle();
          expect(find.text('6500.50'), findsOneWidget);
          expect(find.text('Apartment in Maadi'), findsOneWidget);
          expect(tester.takeException(), isNull);
        }
      },
    );
  }
}
