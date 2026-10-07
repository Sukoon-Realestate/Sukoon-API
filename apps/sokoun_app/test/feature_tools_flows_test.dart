import 'package:sokoun_app/features/owner/properties/data/models/owner_property_content.dart';
import 'package:sokoun_app/features/owner/promotions/presentation/screens/promotions_screen.dart';
import 'package:sokoun_app/features/shared/digital_leases/presentation/screens/digital_lease_details_screen.dart';
import 'package:sokoun_app/features/shared/rent_management/presentation/screens/rent_invoice_screen.dart';
import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/core/error/failure.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:sokoun_app/features/main_view/data/enums/app_workspace.dart';
import 'package:sokoun_app/features/main_view/data/enums/workspace_tab.dart';
import 'package:sokoun_app/features/owner/ai_assistant/data/models/listing_suggestion.dart';
import 'package:sokoun_app/features/owner/ai_assistant/data/models/listing_ai_facts.dart';
import 'package:sokoun_app/features/owner/ai_assistant/presentation/screens/listing_ai_screen.dart';
import 'package:sokoun_app/features/owner/ai_assistant/presentation/widgets/listing_ai_review.dart';
import 'package:sokoun_app/features/owner/promotions/data/models/promotion_body.dart';
import 'package:sokoun_app/features/owner/promotions/presentation/cubits/promotion_submit_cubit.dart';
import 'package:sokoun_app/features/shared/digital_leases/data/models/digital_lease.dart';
import 'package:sokoun_app/features/shared/digital_leases/presentation/widgets/digital_lease_details_view.dart';
import 'package:sokoun_app/features/shared/notifications/data/models/app_notification_content.dart';
import 'package:sokoun_app/features/shared/notifications/data/notification_destination.dart';
import 'package:sokoun_app/features/shared/premium/data/enums/premium_feature.dart';
import 'package:sokoun_app/features/shared/premium/data/enums/premium_status.dart';
import 'package:sokoun_app/features/shared/premium/data/models/premium_money.dart';
import 'package:sokoun_app/features/shared/premium/data/premium_api_constants.dart';
import 'package:sokoun_app/features/shared/premium/presentation/cubits/feature_configuration_cubit.dart';
import 'package:sokoun_app/features/shared/premium/presentation/screens/premium_screen.dart';
import 'package:sokoun_app/features/shared/premium/presentation/widgets/shared/feature_workspace_guard.dart';
import 'package:sokoun_app/features/shared/rent_management/data/models/rent_invoice.dart';
import 'package:sokoun_app/features/shared/rent_management/presentation/widgets/rent_invoice_details_view.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_search_model.dart';
import 'package:sokoun_app/features/tenant/premium_alerts/data/models/premium_alert_body.dart';
import 'package:sokoun_app/features/tenant/premium_alerts/presentation/cubits/premium_alert_submit_cubit.dart';
import 'package:sokoun_app/features/tenant/premium_alerts/presentation/widgets/premium_alert_composer.dart';
import 'package:sokoun_app/features/tenant/premium_alerts/presentation/screens/premium_alerts_screen.dart';
import 'helpers/feature_tools_test_dependencies.dart';

const _invoice = RentInvoice(
  id: 'invoice',
  propertyTitle: 'شقة في المعادي',
  reference: 'INV-1',
  status: PremiumStatus.due,
  canPay: true,
  amount: PremiumMoney(amountMinor: 1200000, currency: 'EGP'),
);

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  late FeatureTestRepository repository;
  setUpAll(initializeFeatureTestEnvironment);
  setUp(() async {
    repository = FeatureTestRepository();
    await registerFeatureTestDependencies(repository);
  });

  testWidgets(
    'free tools hub lists every owner tool without any access request',
    (tester) async {
      await mountFeatureTest(
        tester,
        const PremiumScreen(workspace: AppWorkspace.owner),
      );
      for (final feature in PremiumFeature.values.where(
        (value) => !value.tenantOnly,
      )) {
        expect(find.text(feature.label), findsOneWidget);
      }
      expect(find.text(PremiumFeature.priorityAlerts.label), findsNothing);
      expect(find.byIcon(Icons.lock_outline), findsNothing);
      expect(repository.requests, isEmpty);
    },
  );
  testWidgets(
    'free tools hub lists tenant alerts leases and rent without subscriptions',
    (tester) async {
      await mountFeatureTest(
        tester,
        const PremiumScreen(workspace: AppWorkspace.tenant),
      );
      for (final feature in PremiumFeature.values.where(
        (value) => !value.ownerOnly,
      )) {
        expect(find.text(feature.label), findsOneWidget);
      }
      expect(find.text(PremiumFeature.aiAssistant.label), findsNothing);
      expect(repository.requests, isEmpty);
    },
  );
  testWidgets(
    'role guard opens free tools directly and retains workspace boundaries',
    (tester) async {
      await mountFeatureTest(
        tester,
        const Scaffold(
          body: FeatureWorkspaceGuard(
            feature: PremiumFeature.aiAssistant,
            workspace: AppWorkspace.owner,
            child: Text('fixture-feature'),
          ),
        ),
      );
      expect(find.text('fixture-feature'), findsOneWidget);
      expect(repository.requests, isEmpty);
      await mountFeatureTest(
        tester,
        const Scaffold(
          body: FeatureWorkspaceGuard(
            feature: PremiumFeature.aiAssistant,
            workspace: AppWorkspace.tenant,
            child: Text('fixture-feature'),
          ),
        ),
      );
      expect(find.text('fixture-feature'), findsNothing);
      expect(repository.requests, isEmpty);
    },
  );
  testWidgets('configuration for another workspace is rejected', (
    tester,
  ) async {
    await mountFeatureTest(tester, const Scaffold());
    final cubit = FeatureConfigurationCubit();
    repository.replies[PremiumApiConstants.configuration] =
        const FeatureTestReply(data: {'workspace': 'tenant'});
    await cubit.load(AppWorkspace.owner, language: 'ar');
    expect(cubit.state.isError, isTrue);
    await cubit.close();
    await tester.pumpAndSettle();
  });
  testWidgets('cached operational options remain identifiable as cached', (
    tester,
  ) async {
    await mountFeatureTest(tester, const Scaffold());
    final cubit = FeatureConfigurationCubit();
    repository.handler = (request) async => FeatureTestReply(
      data: repository.defaultReply(request).data,
      key: 'fromCache',
    );
    await cubit.load(AppWorkspace.owner, language: 'ar');
    expect(cubit.isCached, isTrue);
    expect(repository.requests.single.query, {
      'workspace': 'owner',
      'lang': 'ar',
    });
    await cubit.close();
    await tester.pumpAndSettle();
  });
  testWidgets(
    'AI generation needs consent and facts but no purchase allowance',
    (tester) async {
      repository.replies[PremiumApiConstants.aiSuggestions] =
          const FeatureTestReply(
            data: {
              'id': 'suggestion',
              'suggested_title': 'Reviewed title',
              'suggested_description': 'Description based on provided facts',
            },
          );
      await mountFeatureTest(
        tester,
        const ListingAiScreen(
          facts: ListingAiFacts(
            title: 'Owner supplied title',
            description: 'Owner supplied facts',
          ),
          canApply: true,
        ),
      );
      expect(repository.requests, isEmpty);
      expect(
        tester.widget<FilledButton>(find.byType(FilledButton)).onPressed,
        isNull,
      );
      await tester.tap(find.byType(CheckboxListTile));
      await tester.pumpAndSettle();
      expect(
        tester.widget<FilledButton>(find.byType(FilledButton)).onPressed,
        isNotNull,
      );
      await tester.tap(find.text(LocaleKeys.paidAiGenerate));
      await tester.pumpAndSettle();
      expect(
        repository.requests.single.endpoint,
        PremiumApiConstants.aiSuggestions,
      );
      expect(repository.requests.single.body['request_key'], isNotEmpty);
      expect(find.byType(ListingAiReview), findsOneWidget);
    },
  );
  testWidgets(
    'free alerts can be created and existing alerts remain manageable',
    (tester) async {
      final network = FeatureTestNetwork()
        ..page = {
          'results': [
            {
              'id': 'existing-alert',
              'name': 'Existing alert',
              'cadence': 'daily',
              'enabled': true,
              'can_manage': true,
              'revision': 2,
              'filters': const PropertySearchFilters.initial(
                search: 'Maadi',
              ).toJson(),
            },
          ],
          'count': 1,
          'per_page': 20,
          'total_pages': 1,
        };
      await registerFeatureTestDependencies(repository, network: network);
      await mountFeatureTest(
        tester,
        const PremiumAlertsScreen(
          filters: PropertySearchFilters.initial(search: 'Maadi'),
          name: 'New alert',
        ),
      );
      expect(find.text('Existing alert'), findsOneWidget);
      await tester.tap(find.byType(DropdownButtonFormField<String>));
      await tester.pumpAndSettle();
      await tester.tap(find.text(LocaleKeys.paidAlertDaily).last);
      await tester.pumpAndSettle();
      expect(
        tester.widget<FilledButton>(find.byType(FilledButton)).onPressed,
        isNotNull,
      );
      final pause = tester.widget<TextButton>(
        find.ancestor(
          of: find.text(LocaleKeys.paidAlertPause),
          matching: find.byType(TextButton),
        ),
      );
      expect(pause.onPressed, isNotNull);
      expect(network.requests, hasLength(1));
      expect(
        repository.requests.single.endpoint,
        PremiumApiConstants.configuration,
      );
    },
  );
  testWidgets(
    'free promotion submits only the owned listing option and retry key',
    (tester) async {
      repository.replies[PremiumApiConstants
          .campaigns] = const FeatureTestReply(
        data: {'id': 'campaign', 'subject_id': 'property', 'status': 'active'},
      );
      await mountFeatureTest(
        tester,
        PromotionsScreen(
          property: OwnerPropertyContent.initial().copyWith(
            id: 'property',
            title: 'My listing',
          ),
        ),
      );
      await tester.tap(find.byType(DropdownButtonFormField<String>));
      await tester.pumpAndSettle();
      await tester.tap(find.text('أسبوع').last);
      await tester.pumpAndSettle();
      await tester.tap(find.text(LocaleKeys.paidStartBoost));
      await tester.pumpAndSettle();
      expect(
        find.text(LocaleKeys.toolsBoostDuration.replaceAll('{days}', '7')),
        findsWidgets,
      );
      await tester.tap(find.text(LocaleKeys.paidStartBoost).last);
      await tester.pumpAndSettle();
      expect(repository.requests, hasLength(2));
      expect(
        repository.requests.first.endpoint,
        PremiumApiConstants.configuration,
      );
      final request = repository.requests.last;
      expect(request.endpoint, PremiumApiConstants.campaigns);
      expect(request.body.keys.toSet(), {
        'property_id',
        'option_id',
        'request_key',
      });
      expect(request.body['property_id'], 'property');
      expect(request.body['option_id'], 'fixture-week');
      expect(request.body['request_key'], isNotEmpty);
    },
  );
  testWidgets(
    'rent checkout remains reachable without a feature access request',
    (tester) async {
      repository.replies[PremiumApiConstants.invoice('invoice')] =
          FeatureTestReply(data: _invoice.toJson());
      await mountFeatureTest(
        tester,
        const RentInvoiceScreen(
          invoiceId: 'invoice',
          workspace: AppWorkspace.tenant,
        ),
      );
      expect(
        repository.requests.single.endpoint,
        PremiumApiConstants.invoice('invoice'),
      );
      expect(find.text(LocaleKeys.paidPayRent), findsOneWidget);
      final pay = tester.widget<FilledButton>(
        find.ancestor(
          of: find.text(LocaleKeys.paidPayRent),
          matching: find.byType(FilledButton),
        ),
      );
      expect(pay.onPressed, isNotNull);
    },
  );
  testWidgets(
    'lease participants can read and sign without a subscription request',
    (tester) async {
      const lease = DigitalLease(
        id: 'lease',
        propertyTitle: 'My listing',
        revision: 2,
        status: PremiumStatus.pending,
        canSign: true,
        documentUrl: 'https://example.invalid/document',
      );
      repository.replies[PremiumApiConstants.lease('lease')] = FeatureTestReply(
        data: lease.toJson(),
      );
      await mountFeatureTest(
        tester,
        const DigitalLeaseDetailsScreen(
          leaseId: 'lease',
          workspace: AppWorkspace.tenant,
        ),
      );
      expect(
        repository.requests.single.endpoint,
        PremiumApiConstants.lease('lease'),
      );
      expect(find.text(LocaleKeys.paidLeaseSign), findsOneWidget);
      final sign = tester.widget<FilledButton>(
        find.ancestor(
          of: find.text(LocaleKeys.paidLeaseSign),
          matching: find.byType(FilledButton),
        ),
      );
      expect(sign.onPressed, isNotNull);
    },
  );
  testWidgets(
    'alert configuration failure leaves existing history and management available',
    (tester) async {
      repository.replies[PremiumApiConstants.configuration] =
          const FeatureTestReply(
            failure: ServerFailure('Fixture configuration unavailable'),
          );
      final network = FeatureTestNetwork()
        ..page = {
          'results': [
            {
              'id': 'existing-alert',
              'name': 'Existing alert',
              'cadence': 'daily',
              'enabled': true,
              'can_manage': true,
              'revision': 2,
              'filters': const PropertySearchFilters.initial(
                search: 'Maadi',
              ).toJson(),
            },
          ],
          'count': 1,
          'per_page': 20,
          'total_pages': 1,
        };
      await registerFeatureTestDependencies(repository, network: network);
      await mountFeatureTest(
        tester,
        const PremiumAlertsScreen(
          filters: PropertySearchFilters.initial(search: 'Maadi'),
          name: 'New alert',
        ),
      );
      expect(find.text('Existing alert'), findsOneWidget);
      final pause = tester.widget<TextButton>(
        find.ancestor(
          of: find.text(LocaleKeys.paidAlertPause),
          matching: find.byType(TextButton),
        ),
      );
      expect(pause.onPressed, isNotNull);
      expect(
        repository.requests.single.endpoint,
        PremiumApiConstants.configuration,
      );
    },
  );
  testWidgets('zero or negative invoices cannot initiate paid checkout', (
    tester,
  ) async {
    for (final amount in [0, -1]) {
      await mountFeatureTest(
        tester,
        Scaffold(
          body: RentInvoiceDetailsView(
            invoice: _invoice.copyWith(
              amount: PremiumMoney(amountMinor: amount, currency: 'EGP'),
            ),
            isFresh: true,
            onRefresh: () async {},
          ),
        ),
      );
      expect(find.text(LocaleKeys.paidPayRent), findsNothing);
      expect(repository.requests, isEmpty);
    }
  });
  testWidgets(
    'failed rent checkout preserves due status and does not invent a receipt',
    (tester) async {
      repository.replies[PremiumApiConstants.rentCheckout(
        'invoice',
      )] = const FeatureTestReply(
        failure: ServerFailure('Fixture payment unavailable'),
      );
      await mountFeatureTest(
        tester,
        Scaffold(
          body: RentInvoiceDetailsView(
            invoice: _invoice,
            isFresh: true,
            onRefresh: () async {},
          ),
        ),
      );
      await tester.tap(find.text(LocaleKeys.paidPayRent));
      await tester.pumpAndSettle();
      expect(find.text(LocaleKeys.paidDue), findsOneWidget);
      expect(find.text(LocaleKeys.paidPaid), findsNothing);
      expect(find.text(LocaleKeys.paidViewReceipt), findsNothing);
      expect(repository.requests.single.body['request_key'], isNotEmpty);
    },
  );
  testWidgets(
    'unknown invoice status and cached data cannot initiate payment',
    (tester) async {
      await mountFeatureTest(
        tester,
        Scaffold(
          body: RentInvoiceDetailsView(
            invoice: _invoice.copyWith(status: PremiumStatus.unknown),
            isFresh: true,
            onRefresh: () async {},
          ),
        ),
      );
      expect(find.text(LocaleKeys.paidPayRent), findsNothing);
      await mountFeatureTest(
        tester,
        Scaffold(
          body: RentInvoiceDetailsView(
            invoice: _invoice,
            isFresh: false,
            onRefresh: () async {},
          ),
        ),
      );
      final button = tester.widget<FilledButton>(find.byType(FilledButton));
      expect(button.onPressed, isNull);
      expect(repository.requests, isEmpty);
    },
  );
  testWidgets(
    'checkout for another invoice is rejected before provider confirmation',
    (tester) async {
      repository.replies[PremiumApiConstants.rentCheckout(
        'invoice',
      )] = const FeatureTestReply(
        data: {
          'id': 'session',
          'subject_id': 'other-invoice',
          'status': 'pending',
          'hosted_url': 'https://example.invalid/pay',
          'expires_at': '2050-01-01T00:00:00Z',
          'amount': {'amount_minor': 1200000, 'currency': 'EGP'},
        },
      );
      await mountFeatureTest(
        tester,
        Scaffold(
          body: RentInvoiceDetailsView(
            invoice: _invoice,
            isFresh: true,
            onRefresh: () async {},
          ),
        ),
      );
      await tester.tap(find.text(LocaleKeys.paidPayRent));
      await tester.pumpAndSettle();
      expect(find.text(LocaleKeys.paidConfirmRent), findsNothing);
      expect(find.text(LocaleKeys.paidDue), findsOneWidget);
    },
  );
  testWidgets(
    'a signing session never changes a lease to signed on the client',
    (tester) async {
      repository.replies[PremiumApiConstants.signing(
        'lease',
      )] = const FeatureTestReply(
        failure: ServerFailure('Fixture signing unavailable'),
      );
      const lease = DigitalLease(
        id: 'lease',
        propertyTitle: 'شقة',
        revision: 2,
        status: PremiumStatus.pending,
        canSign: true,
        documentUrl: 'https://example.invalid/document',
      );
      await mountFeatureTest(
        tester,
        Scaffold(
          body: DigitalLeaseDetailsView(
            workspace: AppWorkspace.tenant,
            lease: lease,
            isFresh: true,
            onRefresh: () async {},
          ),
        ),
      );
      await tester.tap(find.text(LocaleKeys.paidLeaseSign));
      await tester.pumpAndSettle();
      expect(find.text(LocaleKeys.paidSigned), findsNothing);
      expect(find.text(LocaleKeys.paidPending), findsOneWidget);
    },
  );
  testWidgets(
    'unknown lease states cannot expose signing or draft cancellation',
    (tester) async {
      const lease = DigitalLease(
        id: 'lease',
        revision: 2,
        status: PremiumStatus.unknown,
        canSign: true,
        canCancel: true,
        documentUrl: 'https://example.invalid/document',
      );
      await mountFeatureTest(
        tester,
        Scaffold(
          body: DigitalLeaseDetailsView(
            workspace: AppWorkspace.tenant,
            lease: lease,
            isFresh: true,
            onRefresh: () async {},
          ),
        ),
      );
      expect(find.text(LocaleKeys.paidLeaseSign), findsNothing);
      expect(find.text(LocaleKeys.paidLeaseCancel), findsNothing);
    },
  );
  testWidgets(
    'AI suggestions require an explicit apply and preserve edits in the returned draft',
    (tester) async {
      await mountFeatureTest(tester, const Scaffold());
      const suggestion = ListingSuggestion(
        id: 'suggestion',
        suggestedTitle: 'عنوان مقترح',
        suggestedDescription: 'وصف مقترح',
      );
      final result = Go.to<ListingSuggestion>(
        const Scaffold(
          body: SingleChildScrollView(
            child: ListingAiReview(suggestion: suggestion, canApply: true),
          ),
        ),
      );
      await tester.pumpAndSettle();
      expect(find.byType(ListingAiReview), findsOneWidget);
      await tester.enterText(
        find.byType(TextFormField).first,
        'عنوان بعد المراجعة',
      );
      await tester.enterText(
        find.byType(TextFormField).last,
        'وصف بعد مراجعة المالك',
      );
      await tester.ensureVisible(find.text(LocaleKeys.paidAiApply));
      await tester.tap(find.text(LocaleKeys.paidAiApply));
      await tester.pumpAndSettle();
      final applied = await result;
      expect(applied?.suggestedTitle, 'عنوان بعد المراجعة');
      expect(applied?.suggestedDescription, 'وصف بعد مراجعة المالك');
      expect(repository.requests, isEmpty);
    },
  );
  testWidgets(
    'failed alert creation keeps the name and idempotency key for retry',
    (tester) async {
      final cubit = PremiumAlertSubmitCubit();
      repository.replies[PremiumApiConstants.alerts] = const FeatureTestReply(
        failure: ServerFailure('Fixture alert unavailable'),
      );
      await mountFeatureTest(
        tester,
        Scaffold(
          body: SingleChildScrollView(
            child: PremiumAlertComposer(
              filters: const PropertySearchFilters.initial(search: 'المعادي'),
              name: 'قرب العمل',
              cadences: const ['daily'],
              cubit: cubit,
              canChange: true,
              onSaved: () async {},
            ),
          ),
        ),
      );
      await tester.tap(find.byType(DropdownButtonFormField<String>));
      await tester.pumpAndSettle();
      await tester.tap(find.text(LocaleKeys.paidAlertDaily).last);
      await tester.pumpAndSettle();
      await tester.tap(find.text(LocaleKeys.paidCreateAlert));
      await tester.pumpAndSettle();
      expect(
        tester
            .widget<TextFormField>(find.byType(TextFormField))
            .controller
            ?.text,
        'قرب العمل',
      );
      await tester.tap(find.text(LocaleKeys.paidCreateAlert));
      await tester.pumpAndSettle();
      expect(repository.requests, hasLength(2));
      expect(
        repository.requests.first.body['request_key'],
        repository.requests.last.body['request_key'],
      );
      await cubit.close();
    },
  );
  testWidgets('duplicate promotion submissions produce one active request', (
    tester,
  ) async {
    await mountFeatureTest(tester, const Scaffold());
    final cubit = PromotionSubmitCubit();
    final response = Completer<FeatureTestReply>();
    repository.handler = (_) => response.future;
    const body = PromotionBody(
      propertyId: 'property',
      optionId: 'week',
      requestKey: 'fixture-key',
    );
    final first = cubit.submit(body);
    expect(await cubit.submit(body), isNull);
    response.complete(
      const FeatureTestReply(
        data: {'id': 'campaign', 'subject_id': 'property', 'status': 'pending'},
      ),
    );
    expect(await first, isNotNull);
    expect(repository.requests, hasLength(1));
    await cubit.close();
    await tester.pumpAndSettle();
  });
  testWidgets('invalid alert price bounds make no backend request', (
    tester,
  ) async {
    final cubit = PremiumAlertSubmitCubit();
    final body = PremiumAlertBody(
      name: 'بحث',
      cadence: 'daily',
      filters: const PropertySearchFilters.initial(
        priceMin: '30000',
        priceMax: '10000',
      ),
      requestKey: 'fixture-key',
    );
    expect(await cubit.create(body), isNull);
    expect(repository.requests, isEmpty);
    await cubit.close();
    await tester.pumpAndSettle();
  });
  test(
    'priority push resolves to the tenant workspace and preserves its alert ID',
    () {
      final notification = AppNotificationContent.fromPushPayload({
        'notification_type': 'search_alert_match',
        'action_type': 'open_search_alert',
        'target_id': 'alert-1',
      });
      final target = NotificationDestination.resolve(notification);
      expect(target.workspace, AppWorkspace.tenant);
      expect(target.tab, WorkspaceTab.home);
      expect(notification.primaryTargetId, 'alert-1');
    },
  );
}
