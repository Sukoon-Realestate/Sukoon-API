import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart' show injector;
import 'package:melos_core/core/shared/user_cubit/user_cubit.dart';
import 'package:melos_core/core/base_crud/code/domain/base_domain_imports.dart'
    show HttpRequestType;
import 'package:melos_core/core/error/failure.dart';
import 'package:melos_core/core/network/account_session.dart';
import 'package:melos_core/core/network/api_endpoints.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/core/widgets/app_pagify.dart';
import 'package:melos_core/core/widgets/exeption_view.dart';
import 'package:pagify/helpers/errors.dart';
import 'package:sokoun_app/features/main_view/data/enums/app_workspace.dart';
import 'package:sokoun_app/features/main_view/presentation/workspace_navigation.dart';
import 'package:sokoun_app/features/owner/advanced_analytics/presentation/screens/advanced_analytics_screen.dart';
import 'package:sokoun_app/features/owner/ai_assistant/data/models/listing_suggestion.dart';
import 'package:sokoun_app/features/owner/ai_assistant/presentation/screens/listing_ai_screen.dart';
import 'package:sokoun_app/features/owner/ai_assistant/presentation/widgets/listing_ai_entry.dart';
import 'package:sokoun_app/features/owner/home/data/models/owner_add_property_content.dart';
import 'package:sokoun_app/features/owner/home/presentation/widgets/owner_widgets/owner_operations_section.dart';
import 'package:sokoun_app/features/owner/promotions/presentation/widgets/owner_property_premium_actions.dart';
import 'package:sokoun_app/features/owner/promotions/presentation/screens/promotions_screen.dart';
import 'package:sokoun_app/features/owner/properties/data/enums/owner_property_status.dart';
import 'package:sokoun_app/features/owner/properties/data/models/owner_property_content.dart';
import 'package:sokoun_app/features/shared/digital_leases/data/digital_leases_data.dart';
import 'package:sokoun_app/features/shared/digital_leases/data/models/digital_lease.dart';
import 'package:sokoun_app/features/shared/digital_leases/data/models/lease_template.dart';
import 'package:sokoun_app/features/shared/digital_leases/presentation/screens/digital_leases_screen.dart';
import 'package:sokoun_app/features/shared/digital_leases/presentation/screens/digital_lease_details_screen.dart';
import 'package:sokoun_app/features/shared/digital_leases/presentation/widgets/digital_lease_details_view.dart';
import 'package:sokoun_app/features/shared/digital_leases/presentation/widgets/lease_draft_form.dart';
import 'package:sokoun_app/features/shared/digital_leases/presentation/widgets/lease_tenant_selector.dart';
import 'package:sokoun_app/features/shared/premium/data/enums/premium_status.dart';
import 'package:sokoun_app/features/shared/premium/data/models/premium_money.dart';
import 'package:sokoun_app/features/shared/premium/data/premium_api_constants.dart';
import 'package:sokoun_app/features/shared/premium/presentation/widgets/shared/premium_property_selector.dart';
import 'package:sokoun_app/features/shared/profile/imports.dart';
import 'package:sokoun_app/features/shared/rent_management/data/models/rent_invoice.dart';
import 'package:sokoun_app/features/shared/rent_management/data/models/rent_overview.dart';
import 'package:sokoun_app/features/shared/rent_management/data/rent_management_data.dart';
import 'package:sokoun_app/features/shared/rent_management/data/rent_overview_data.dart';
import 'package:sokoun_app/features/shared/rent_management/presentation/cubits/rent_overview_cubit.dart';
import 'package:sokoun_app/features/shared/rent_management/presentation/screens/rent_management_screen.dart';
import 'package:sokoun_app/features/shared/rent_management/presentation/screens/rent_invoice_screen.dart';
import 'package:sokoun_app/features/shared/rent_management/presentation/widgets/rent_overview_card.dart';
import 'package:sokoun_app/features/shared/rent_management/presentation/widgets/rent_overview_empty_state.dart';
import 'package:sokoun_app/features/shared/rent_management/presentation/widgets/rent_overview_section.dart';
import 'package:sokoun_app/features/tenant/home/data/models/home_page_model.dart';
import 'package:sokoun_app/features/tenant/home/presentation/widgets/tenant_widgets/tenant_home_content.dart';
import 'package:sokoun_app/features/tenant/home/presentation/screens/tenant_home_screen.dart';
import 'package:sokoun_app/features/tenant/home/presentation/widgets/tenant_widgets/tenant_home_app_bar_title.dart';
import 'package:sokoun_app/features/tenant/home/presentation/widgets/tenant_widgets/home_search_box.dart';
import 'package:sokoun_app/features/tenant/home/presentation/widgets/tenant_widgets/home_property_item.dart';
import 'package:sokoun_app/features/tenant/home/presentation/widgets/tenant_widgets/tenant_search_tools.dart';
import 'helpers/account_test_dependencies.dart';
import 'helpers/feature_tools_test_dependencies.dart';

final _property = OwnerPropertyContent.initial();
final _listing = _property.copyWith(
  id: 'property-1',
  title: 'شقة المعادي',
  status: OwnerPropertyStatus.accepted,
);
final _invoice = RentInvoice(
  id: 'invoice-1',
  leaseId: 'lease-1',
  propertyTitle: 'شقة المعادي',
  dueDate: DateTime(2026, 11, 1),
  status: PremiumStatus.due,
  canPay: true,
  amount: const PremiumMoney(amountMinor: 650050, currency: 'EGP'),
);

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  late FeatureTestRepository repository;
  late FeatureTestNetwork network;
  late WorkspaceSelection select;
  AppWorkspace? selectedWorkspace;
  setUpAll(initializeFeatureTestEnvironment);
  setUp(() async {
    repository = FeatureTestRepository();
    network = FeatureTestNetwork();
    await registerFeatureTestDependencies(repository, network: network);
    WorkspaceNavigation.clearPending();
    selectedWorkspace = null;
    select = (workspace, tab) async {
      selectedWorkspace = workspace;
    };
    WorkspaceNavigation.attach(select);
  });
  tearDown(() {
    WorkspaceNavigation.detach(select);
    WorkspaceNavigation.clearPending();
  });

  test(
    'scoped pages send real IDs and have distinct account and resource cache keys',
    () async {
      network.page = {
        'results': [
          DigitalLease(id: 'lease-1', propertyId: 'property-1').toJson(),
        ],
        'count': 1,
      };
      await DigitalLeasesData.getPage(
        page: 1,
        workspace: AppWorkspace.owner,
        propertyId: 'property-1',
      );
      expect(
        network.requests.single.queryParameters?['property_id'],
        'property-1',
      );
      final propertyCache = DigitalLeasesData.cacheKey(
        AppWorkspace.owner,
        propertyId: 'property-1',
      );
      expect(
        propertyCache,
        isNot(
          DigitalLeasesData.cacheKey(
            AppWorkspace.owner,
            propertyId: 'property-2',
          ),
        ),
      );
      expect(
        propertyCache,
        isNot(DigitalLeasesData.cacheKey(AppWorkspace.owner)),
      );
      network.page = {
        'results': [_invoice.toJson()],
        'count': 1,
      };
      await RentManagementData.getPage(
        page: 1,
        workspace: AppWorkspace.tenant,
        leaseId: 'lease-1',
      );
      expect(network.requests.last.queryParameters?['lease_id'], 'lease-1');
      final invoiceCache = RentManagementData.cacheKey(
        AppWorkspace.tenant,
        leaseId: 'lease-1',
      );
      expect(
        invoiceCache,
        isNot(
          RentManagementData.cacheKey(AppWorkspace.tenant, leaseId: 'lease-2'),
        ),
      );
      expect(
        invoiceCache,
        isNot(
          RentManagementData.cacheKey(AppWorkspace.owner, leaseId: 'lease-1'),
        ),
      );
      AccountSession.begin('another-account');
      expect(
        invoiceCache,
        isNot(
          RentManagementData.cacheKey(AppWorkspace.tenant, leaseId: 'lease-1'),
        ),
      );
    },
  );
  test(
    'ignored property and lease filters fail instead of showing another resource',
    () async {
      network.page = {
        'results': [
          DigitalLease(id: 'other', propertyId: 'property-2').toJson(),
        ],
        'count': 1,
      };
      await expectLater(
        DigitalLeasesData.getPage(
          page: 1,
          workspace: AppWorkspace.owner,
          propertyId: 'property-1',
        ),
        throwsA(isA<PagifyApiRequestException>()),
      );
      network.page = {
        'results': [_invoice.copyWith(leaseId: 'lease-2').toJson()],
        'count': 1,
      };
      await expectLater(
        RentManagementData.getPage(
          page: 1,
          workspace: AppWorkspace.tenant,
          leaseId: 'lease-1',
        ),
        throwsA(isA<PagifyApiRequestException>()),
      );
    },
  );
  test(
    'rent preview distinguishes an explicit empty response from malformed or unfiltered data',
    () {
      final overview = RentOverview.fromJson({
        'results': [_invoice.toJson()],
        'count': 2,
      });
      expect(overview.isValid, isTrue);
      expect(RentOverview.fromJson(overview.toJson()), overview);
      expect(
        RentOverview.fromJson({'results': [], 'count': 0}).isValid,
        isTrue,
      );
      for (final json in <Map<String, dynamic>>[
        {},
        {'results': []},
        {'results': [], 'count': 1},
        {'results': [], 'count': -1},
        {
          'results': [null],
          'count': 1,
        },
        {
          'results': [_invoice.copyWith(status: PremiumStatus.paid).toJson()],
          'count': 1,
        },
        {
          'results': [_invoice.copyWith(id: '').toJson()],
          'count': 1,
        },
        {
          'results': [_invoice.copyWith(leaseId: '').toJson()],
          'count': 1,
        },
      ]) {
        expect(RentOverview.fromJson(json).isValid, isFalse, reason: '$json');
      }
    },
  );
  test(
    'rent preview GET includes due ordering, complete cache contract and account isolation',
    () async {
      repository.replies[PremiumApiConstants.invoices] = FeatureTestReply(
        data: {
          'results': [_invoice.toJson()],
          'count': 1,
        },
      );
      expect(
        (await RentOverviewData.get(AppWorkspace.tenant)).isSuccess(),
        isTrue,
      );
      final first = repository.requests.single;
      expect(first.query, {
        'workspace': 'tenant',
        'status': 'due,overdue',
        'ordering': 'due_date',
        'page': 1,
        'page_size': 1,
      });
      expect(first.hasSerializers, isTrue);
      AccountSession.begin('other-account');
      await RentOverviewData.get(AppWorkspace.tenant);
      expect(repository.requests.last.cacheKey, isNot(first.cacheKey));
      repository.replies[PremiumApiConstants.invoices] =
          const FeatureTestReply();
      expect(
        (await RentOverviewData.get(AppWorkspace.tenant)).isError(),
        isTrue,
      );
    },
  );
  test(
    'legacy contracts preserve an explicit lease link without reusing document IDs',
    () {
      const old = ProfileContractContent(
        id: 'document-id',
        propertyTitle: '',
        status: '',
        startDate: '',
        endDate: '',
        documentUrl: '',
      );
      expect(ProfileContractContent.fromJson(old.toJson()).leaseId, isEmpty);
      final linked = old.copyWith(leaseId: 'lease-1');
      expect(ProfileContractContent.fromJson(linked.toJson()), linked);
      expect(linked.leaseId, isNot(linked.id));
    },
  );

  testWidgets(
    'editor assistant carries property and current facts and applies only a reviewed result',
    (tester) async {
      ListingSuggestion? applied;
      final form = OwnerAddPropertyFormState.initial().copyWith(
        title: 'Current title',
        description: 'Current owner description',
      );
      await mountFeatureTest(
        tester,
        Scaffold(
          body: ListingAiEntry(
            form: form,
            propertyId: 'property-1',
            onApplied: (suggestion) => applied = suggestion,
          ),
        ),
      );
      await tester.tap(find.text(LocaleKeys.paidAiAssistant));
      await tester.pumpAndSettle();
      final screen = tester.widget<ListingAiScreen>(
        find.byType(ListingAiScreen),
      );
      expect(screen.propertyId, 'property-1');
      expect(screen.facts?.title, 'Current title');
      expect(screen.facts?.description, 'Current owner description');
      expect(screen.canApply, isTrue);
      expect(applied, isNull);
      const reviewed = ListingSuggestion(
        id: 'suggestion',
        propertyId: 'property-1',
        suggestedTitle: 'Reviewed title',
        suggestedDescription: 'Reviewed description',
      );
      Go.back(reviewed);
      await tester.pumpAndSettle();
      expect(applied, reviewed);
    },
  );
  testWidgets('owner dashboard opens analytics in owner workspace', (
    tester,
  ) async {
    await registerAuthenticatedTestAccount();
    await mountFeatureTest(
      tester,
      const Scaffold(
        body: SingleChildScrollView(child: OwnerOperationsSection()),
      ),
    );
    await tester.tap(find.text(LocaleKeys.paidAdvancedAnalytics));
    await tester.pumpAndSettle();
    expect(selectedWorkspace, AppWorkspace.owner);
    expect(find.byType(AdvancedAnalyticsScreen), findsOneWidget);
  });
  testWidgets('owner dashboard opens Contracts with owner lease access', (
    tester,
  ) async {
    await registerAuthenticatedTestAccount();
    await mountFeatureTest(
      tester,
      const Scaffold(
        body: SingleChildScrollView(child: OwnerOperationsSection()),
      ),
    );
    await tester.tap(find.text(LocaleKeys.profileContracts));
    await tester.pumpAndSettle();
    expect(
      tester
          .widget<ProfileContractsScreen>(find.byType(ProfileContractsScreen))
          .workspace,
      AppWorkspace.owner,
    );
    await tester.tap(find.text(LocaleKeys.paidDigitalLeases));
    await tester.pumpAndSettle();
    expect(
      tester
          .widget<DigitalLeasesScreen>(find.byType(DigitalLeasesScreen))
          .workspace,
      AppWorkspace.owner,
    );
    expect(find.text(LocaleKeys.paidCreateLease), findsOneWidget);
  });
  testWidgets(
    'listing tools promote published properties and preserve property context',
    (tester) async {
      await mountFeatureTest(
        tester,
        Scaffold(body: OwnerPropertyPremiumActions(property: _listing)),
      );
      await tester.tap(find.text(LocaleKeys.paidListingBoost));
      await tester.pumpAndSettle();
      expect(
        tester
            .widget<PromotionsScreen>(find.byType(PromotionsScreen))
            .property
            ?.id,
        'property-1',
      );
      Go.back();
      await tester.pumpAndSettle();
      await tester.tap(find.text(LocaleKeys.paidDigitalLeases));
      await tester.pumpAndSettle();
      expect(
        tester
            .widget<DigitalLeasesScreen>(find.byType(DigitalLeasesScreen))
            .property
            ?.id,
        'property-1',
      );
      expect(
        network.requests.last.queryParameters?['property_id'],
        'property-1',
      );
    },
  );
  testWidgets(
    'under-review listings cannot be promoted and an inline action keeps its parent route',
    (tester) async {
      await mountFeatureTest(
        tester,
        Scaffold(
          body: OwnerPropertyPremiumActions(
            property: _listing.copyWith(status: OwnerPropertyStatus.pending),
          ),
        ),
      );
      expect(find.text(LocaleKeys.paidListingBoost), findsNothing);
      await tester.tap(find.text(LocaleKeys.paidAdvancedAnalytics));
      await tester.pumpAndSettle();
      expect(
        tester
            .widget<AdvancedAnalyticsScreen>(
              find.byType(AdvancedAnalyticsScreen),
            )
            .property
            ?.id,
        'property-1',
      );
      Go.back();
      await tester.pumpAndSettle();
      expect(find.byType(OwnerPropertyPremiumActions), findsOneWidget);
    },
  );
  testWidgets(
    'property-specific draft loads its full inventory and only its eligible tenants',
    (tester) async {
      repository.replies[ApiConstants.propertyDetails(_listing.id)] =
          FeatureTestReply(data: _listing.toJson());
      await mountFeatureTest(
        tester,
        Scaffold(
          body: LeaseDraftForm(
            property: _listing,
            templates: const [
              LeaseTemplate(id: 'template', title: 'عقد معتمد', version: 'v1'),
            ],
            isFresh: true,
          ),
        ),
      );
      final property = tester.widget<PremiumPropertySelector>(
        find.byType(PremiumPropertySelector),
      );
      expect(property.property?.id, 'property-1');
      expect(property.enabled, isFalse);
      final tenant = tester.widget<LeaseTenantSelector>(
        find.byType(LeaseTenantSelector),
      );
      expect(tenant.tenant, isNull);
      expect(tenant.propertyId, 'property-1');
      await tester.tap(find.text(LocaleKeys.paidLeaseTenant));
      await tester.pumpAndSettle();
      expect(network.requests.single.path, PremiumApiConstants.leaseTenants);
      expect(
        network.requests.single.queryParameters?['property_id'],
        'property-1',
      );
      expect(
        repository.requests.single.endpoint,
        ApiConstants.propertyDetails(_listing.id),
      );
      expect(repository.requests.single.method, HttpRequestType.get);
    },
  );
  testWidgets(
    'active lease opens invoices using its real lease ID and workspace',
    (tester) async {
      await mountFeatureTest(
        tester,
        Scaffold(
          body: DigitalLeaseDetailsView(
            lease: const DigitalLease(
              id: 'lease-1',
              propertyTitle: 'شقة المعادي',
              status: PremiumStatus.active,
            ),
            workspace: AppWorkspace.owner,
            isFresh: true,
            onRefresh: () async {},
          ),
        ),
      );
      await tester.tap(find.text(LocaleKeys.journeyLeaseInvoices));
      await tester.pumpAndSettle();
      final screen = tester.widget<RentManagementScreen>(
        find.byType(RentManagementScreen),
      );
      expect(screen.leaseId, 'lease-1');
      expect(screen.workspace, AppWorkspace.owner);
      expect(network.requests.single.queryParameters?['lease_id'], 'lease-1');
      expect(repository.requests, isEmpty);
    },
  );
  testWidgets(
    'draft lease does not advertise a confirmed tenancy or invoices',
    (tester) async {
      await mountFeatureTest(
        tester,
        Scaffold(
          body: DigitalLeaseDetailsView(
            lease: const DigitalLease(id: 'draft', status: PremiumStatus.draft),
            workspace: AppWorkspace.tenant,
            isFresh: true,
            onRefresh: () async {},
          ),
        ),
      );
      expect(find.text(LocaleKeys.journeyLeaseInvoices), findsNothing);
      expect(repository.requests, isEmpty);
    },
  );
  testWidgets(
    'legacy contract follows explicit lease_id and does not substitute contract id',
    (tester) async {
      await mountFeatureTest(
        tester,
        const Scaffold(
          body: ProfileContractCard(
            contract: ProfileContractContent(
              id: 'document-id',
              leaseId: 'lease-1',
              propertyTitle: 'شقة المعادي',
              status: 'active',
              startDate: '',
              endDate: '',
              documentUrl: '',
            ),
            workspace: AppWorkspace.tenant,
          ),
        ),
      );
      await tester.tap(find.text(LocaleKeys.journeyViewLease));
      await tester.pumpAndSettle();
      expect(
        tester
            .widget<DigitalLeaseDetailsScreen>(
              find.byType(DigitalLeaseDetailsScreen),
            )
            .leaseId,
        'lease-1',
      );
      expect(
        repository.requests.single.endpoint,
        PremiumApiConstants.lease('lease-1'),
      );
    },
  );
  testWidgets('guest discovery never requests private rent data', (
    tester,
  ) async {
    (injector<UserCubit>() as TestAccountCubit).signOut();
    await mountFeatureTest(tester, const Scaffold(body: TenantHomeContent()));
    expect(
      repository.requests.where(
        (request) => request.endpoint == PremiumApiConstants.invoices,
      ),
      isEmpty,
    );
    expect(find.byType(RentOverviewSection), findsNothing);
    expect(find.text(LocaleKeys.paidPriorityAlerts), findsOneWidget);
  });
  testWidgets(
    'tenant Home toolbar, search, rent and listings share one scroll surface',
    (tester) async {
      tester.view.physicalSize = const Size(390, 844);
      tester.view.devicePixelRatio = 1;
      addTearDown(tester.view.reset);
      await registerAuthenticatedTestAccount();
      repository.replies[PremiumApiConstants.invoices] = FeatureTestReply(
        data: {
          'results': [_invoice.toJson()],
          'count': 1,
        },
      );
      repository.replies[ApiConstants.homePage] = FeatureTestReply(
        data: const HomePageModel.initial()
            .copyWith(
              count: 20,
              results: List.generate(
                20,
                (index) => const HomePropertyModel.initial().copyWith(
                  id: 'listing-$index',
                  title: 'Property $index',
                  price: '6500',
                ),
              ),
            )
            .toJson(),
      );
      await mountFeatureTest(tester, const TenantHomeScreen());
      expect(find.byType(AppBar), findsNothing);
      final sections = [
        find.byType(TenantHomeAppBarTitle),
        find.byType(HomeSearchBox),
        find.byType(TenantSearchTools),
        find.byType(RentOverviewCard),
        find.byType(HomePropertyItem).first,
      ];
      final scrollable = Scrollable.of(tester.element(sections.first));
      for (final section in sections) {
        expect(Scrollable.of(tester.element(section)), same(scrollable));
      }
      final initialTops = [
        for (final section in sections) tester.getTopLeft(section).dy,
      ];
      await tester.drag(find.byType(HomeSearchBox), const Offset(0, -160));
      await tester.pumpAndSettle();
      expect(scrollable.position.pixels, greaterThan(0));
      for (int index = 0; index < sections.length; index++) {
        expect(
          initialTops[index] - tester.getTopLeft(sections[index]).dy,
          closeTo(scrollable.position.pixels, 0.1),
        );
      }
      expect(
        repository.requests.where(
          (request) => request.endpoint == PremiumApiConstants.invoices,
        ),
        hasLength(1),
      );
      expect(
        repository.requests.where(
          (request) => request.endpoint == ApiConstants.homePage,
        ),
        hasLength(1),
      );
      expect(tester.takeException(), isNull);
    },
  );
  testWidgets(
    'tenant Home keeps one preview request across feed rebuilds and opens fresh invoice details',
    (tester) async {
      await registerAuthenticatedTestAccount();
      repository.replies[PremiumApiConstants.invoices] = FeatureTestReply(
        data: {
          'results': [_invoice.toJson()],
          'count': 1,
        },
      );
      repository.replies[PremiumApiConstants.invoice('invoice-1')] =
          FeatureTestReply(data: _invoice.toJson());
      await mountFeatureTest(tester, const Scaffold(body: TenantHomeContent()));
      expect(find.byType(RentOverviewCard), findsOneWidget);
      await tester.pumpWidget(
        featureTestHost(const Scaffold(body: TenantHomeContent())),
      );
      await tester.pumpAndSettle();
      expect(
        repository.requests.where(
          (r) => r.endpoint == PremiumApiConstants.invoices,
        ),
        hasLength(1),
      );
      await tester.ensureVisible(find.text(LocaleKeys.journeyViewInvoice));
      await tester.tap(find.text(LocaleKeys.journeyViewInvoice));
      await tester.pumpAndSettle();
      expect(
        tester
            .widget<RentInvoiceScreen>(find.byType(RentInvoiceScreen))
            .invoiceId,
        'invoice-1',
      );
      expect(
        repository.requests.any(
          (r) => r.endpoint == PremiumApiConstants.invoice('invoice-1'),
        ),
        isTrue,
      );
      expect(
        repository.requests.any((r) => r.endpoint.endsWith('checkout/')),
        isFalse,
      );
      Go.back();
      await tester.pumpAndSettle();
      expect(
        repository.requests.where(
          (r) => r.endpoint == PremiumApiConstants.invoices,
        ),
        hasLength(2),
      );
    },
  );
  testWidgets(
    'rent empty success is distinct from failure and cached preview never offers payment',
    (tester) async {
      final cubit = RentOverviewCubit();
      repository.replies[PremiumApiConstants.invoices] = const FeatureTestReply(
        data: {'results': [], 'count': 0},
      );
      final request = cubit.load();
      await mountFeatureTest(
        tester,
        Scaffold(
          body: SingleChildScrollView(
            child: RentOverviewSection(
              cubit: cubit,
              request: request,
              onRefresh: cubit.load,
            ),
          ),
        ),
      );
      expect(find.byType(RentOverviewEmptyState), findsOneWidget);
      expect(find.byType(ExceptionView), findsNothing);
      repository.replies[PremiumApiConstants.invoices] = const FeatureTestReply(
        failure: ServerFailure('backend unavailable'),
      );
      await cubit.load();
      await tester.pumpAndSettle();
      expect(find.byType(ExceptionView), findsOneWidget);
      expect(find.byType(RentOverviewEmptyState), findsNothing);
      repository.replies[PremiumApiConstants.invoices] = FeatureTestReply(
        key: 'fromCache',
        data: {
          'results': [_invoice.toJson()],
          'count': 1,
        },
      );
      await cubit.load();
      await tester.pumpAndSettle();
      expect(find.text(LocaleKeys.journeyRentCached), findsOneWidget);
      expect(find.text(LocaleKeys.paidPayRent), findsNothing);
      await tester.pumpWidget(const SizedBox());
      await cubit.close();
      await tester.pumpAndSettle();
    },
  );
  testWidgets('Home rent loads independently of a pending discovery request', (
    tester,
  ) async {
    await registerAuthenticatedTestAccount();
    final gate = Completer<FeatureTestReply>();
    repository.handler = (request) async =>
        request.endpoint == ApiConstants.homePage
        ? gate.future
        : FeatureTestReply(
            data: {
              'results': [_invoice.toJson()],
              'count': 1,
            },
          );
    await tester.pumpWidget(
      featureTestHost(const Scaffold(body: TenantHomeContent())),
    );
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 100));
    expect(find.byType(RentOverviewCard), findsOneWidget);
    gate.complete(const FeatureTestReply(data: {'results': [], 'count': 0}));
    await tester.pumpAndSettle();
    expect(
      repository.requests.where(
        (r) => r.endpoint == PremiumApiConstants.invoices,
      ),
      hasLength(1),
    );
    final controller = tester
        .widget<AppPagify<HomePropertyModel>>(
          find.byType(AppPagify<HomePropertyModel>),
        )
        .pagifyController;
    controller.refresh();
    await tester.pumpAndSettle();
    expect(
      repository.requests.where(
        (r) => r.endpoint == PremiumApiConstants.invoices,
      ),
      hasLength(2),
    );
  });
}
