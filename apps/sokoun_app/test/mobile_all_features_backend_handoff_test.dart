import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/language/languages.dart';
import 'package:melos_core/core/network/account_session.dart';
import 'package:melos_core/core/error/failure.dart';
import 'package:melos_core/core/network/api_endpoints.dart';
import 'package:sokoun_app/features/owner/properties/data/owner_properties_data.dart';
import 'package:sokoun_app/features/owner/properties/data/enums/owner_property_filter.dart';
import 'package:sokoun_app/features/shared/rental_offers/data/enums/rental_listing_category.dart';
import 'package:sokoun_app/features/main_view/data/enums/app_workspace.dart';
import 'package:sokoun_app/features/owner/properties/data/models/owner_property_content.dart';
import 'package:sokoun_app/features/shared/digital_leases/data/models/lease_draft_body.dart';
import 'package:sokoun_app/features/shared/digital_leases/presentation/cubits/lease_draft_cubit.dart';
import 'package:sokoun_app/features/shared/digital_leases/presentation/cubits/digital_lease_details_cubit.dart';
import 'package:sokoun_app/features/shared/digital_leases/presentation/widgets/digital_lease_details_view.dart';
import 'package:sokoun_app/features/shared/digital_leases/presentation/screens/digital_lease_details_screen.dart';
import 'package:sokoun_app/features/shared/digital_leases/presentation/widgets/lease_rental_offer_selector.dart';
import 'package:sokoun_app/features/shared/digital_leases/data/models/digital_lease.dart';
import 'package:sokoun_app/features/shared/premium/data/feature_service_capabilities.dart';
import 'package:sokoun_app/features/shared/premium/data/models/premium_money.dart';
import 'package:sokoun_app/features/shared/premium/data/enums/premium_status.dart';
import 'package:sokoun_app/features/shared/premium/data/premium_api_constants.dart';
import 'package:sokoun_app/features/shared/premium/data/premium_api_data.dart';
import 'package:sokoun_app/features/shared/premium/data/premium_json.dart';
import 'package:sokoun_app/features/shared/rental_offers/data/models/rental_inventory.dart';
import 'package:sokoun_app/features/shared/rental_offers/data/models/rental_selection.dart';
import 'package:sokoun_app/features/shared/rent_management/data/models/rent_invoice.dart';
import 'package:sokoun_app/features/shared/rent_management/presentation/widgets/rent_invoice_details_view.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_filter_options_model.dart';
import 'package:sokoun_app/features/tenant/premium_alerts/data/models/premium_search_alert.dart';
import 'package:sokoun_app/features/tenant/premium_alerts/presentation/widgets/premium_alert_details_view.dart';
import 'package:sokoun_app/features/tenant/premium_alerts/presentation/screens/premium_alerts_screen.dart';
import 'package:sokoun_app/features/tenant/premium_alerts/presentation/screens/premium_alert_detail_screen.dart';
import 'helpers/feature_tools_test_dependencies.dart';
import 'helpers/rental_offer_fixtures.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  late FeatureTestRepository repository;
  setUpAll(initializeFeatureTestEnvironment);
  setUp(() async {
    repository = FeatureTestRepository();
    await registerFeatureTestDependencies(repository);
  });

  LeaseDraftBody draft(RentalSelection? selection) => LeaseDraftBody(
    hasRentalOffers: true,
    propertyId: 'property-a',
    tenantId: 'tenant-a',
    offerId: selection?.offerId ?? '',
    rentalSelection: selection,
    templateId: 'eg-residential-v1',
    templateVersion: '1',
    startDate: '2026-10-10',
    endDate: '2027-10-10',
    rent: const PremiumMoney(amountMinor: 325000, currency: 'EGP'),
    requestKey: 'a8b9d21a-137b-40c0-af9d-b70f520b7373',
  );

  void propertyReply(RentalInventory inventory, {bool cached = false}) {
    repository.replies['properties/property-a/'] = FeatureTestReply(
      data: rentalProperty(inventory: inventory).toJson(),
      key: cached ? 'fromCache' : 'success',
    );
  }

  for (final offer in [
    wholeOffer,
    independentRooms.first,
    groupOffer,
    bedOffer,
  ]) {
    testWidgets(
      'lease creation preserves the ${offer.scopeValue} offer identity and manual accounting rent',
      (tester) async {
        await mountFeatureTest(tester, const Scaffold());
        final inventory = rentalInventory(
          offers: [offer],
          mode: offer.scopeValue == 'entire_property' ? 'whole' : 'partial',
        );
        propertyReply(inventory);
        final selection = RentalSelection.fromOffer(
          propertyId: 'property-a',
          inventory: inventory,
          offer: offer,
        );
        final body = draft(selection);
        repository.replies[PremiumApiConstants.leases] = FeatureTestReply(
          data: {
            'id': 'lease-a',
            'property_id': body.propertyId,
            'offer_id': offer.id,
            'offer_snapshot': selection.toJson(),
            'rent': body.rent.toJson(),
            'status': 'draft',
            'revision': 1,
          },
        );
        final cubit = LeaseDraftCubit();
        final lease = await cubit.create(body);
        expect(lease?.rentalSelection?.offerId, offer.id);
        expect(lease?.rent.amountMinor, 325000);
        expect(repository.requests.last.body['offer_id'], offer.id);
        expect(repository.requests.last.body['rent'], body.rent.toJson());
        expect(
          repository.requests.last.body.containsKey('offer_snapshot'),
          isFalse,
        );
        await cubit.close();
      },
    );
  }

  test('an inventory lease cannot submit without a selected offer', () async {
    final cubit = LeaseDraftCubit();
    expect(await cubit.create(draft(null)), isNull);
    expect(repository.requests, isEmpty);
    await cubit.close();
  });

  for (final change in [
    'revision',
    'availability',
    'cache',
    'ignored_offer',
    'other_offer',
    'other_amount',
    'other_terms',
  ]) {
    testWidgets('$change cannot be reported as a successful offer lease', (
      tester,
    ) async {
      await mountFeatureTest(tester, const Scaffold());
      final inventory = rentalInventory();
      final selected = RentalSelection.fromOffer(
        propertyId: 'property-a',
        inventory: inventory,
        offer: bedOffer,
      );
      final body = draft(selected);
      propertyReply(
        inventory.copyWith(
          offers: [
            bedOffer.copyWith(
              revision: change == 'revision' ? 8 : 7,
              availability: change == 'availability' ? 'rented' : 'available',
            ),
          ],
        ),
        cached: change == 'cache',
      );
      repository.replies[PremiumApiConstants.leases] = FeatureTestReply(
        data: {
          'id': 'lease-a',
          'property_id': 'property-a',
          if (change != 'ignored_offer') ...{
            'offer_id': change == 'other_offer' ? 'other-offer' : bedOffer.id,
            'offer_snapshot':
                (change == 'other_terms'
                        ? selected.copyWith(
                            terms: selected.terms.copyWith(price: '9999'),
                          )
                        : selected)
                    .toJson(),
          },
          'rent': change == 'other_amount'
              ? const PremiumMoney(
                  amountMinor: 150000,
                  currency: 'EGP',
                ).toJson()
              : body.rent.toJson(),
          'status': 'draft',
          'revision': 1,
        },
      );
      final cubit = LeaseDraftCubit();
      expect(await cubit.create(body), isNull);
      expect(cubit.state.isError, isTrue);
      expect(
        repository.requests,
        hasLength(
          const ['revision', 'availability', 'cache'].contains(change) ? 1 : 2,
        ),
      );
      await cubit.close();
      await tester.pump(const Duration(seconds: 5));
    });
  }

  test(
    'legacy empty inventory from the deployed API stays legacy while unknown versions stay unsupported',
    () {
      expect(
        RentalInventory.read({
          'rental_schema_version': null,
          'rental_inventory': {'offers': []},
        }),
        isNull,
      );
      expect(RentalInventory.read({'rental_schema_version': null}), isNull);
      expect(
        RentalInventory.read({
          'rental_inventory': {'offers': [], 'schema_version': 99},
        })?.schemaVersion,
        99,
      );
      expect(
        RentalInventory.read({'rental_inventory': null})?.isSupported,
        isFalse,
      );
    },
  );

  test('owner scope and manageable count survive cached summaries', () {
    final property = OwnerPropertyContent.fromJson({
      'id': 'property-a',
      'rental_scopes': ['room', 'bed'],
      'manageable_offer_count': 3,
    });
    expect(property.hasRentalOffers, isTrue);
    expect(OwnerPropertyContent.fromJson(property.toJson()), property);
  });

  test(
    'owner scope filtering is sent with the requested page and partitioned in cache',
    () async {
      final network = FeatureTestNetwork();
      await registerFeatureTestDependencies(repository, network: network);
      const source = OwnerPropertiesApiDataSource();
      await source.getOwnedPropertiesPage(
        page: 3,
        filter: OwnerPropertyFilter.accepted,
        category: RentalListingCategory.bed,
      );
      expect(network.requests.single.path, ApiConstants.ownedProperties);
      expect(
        network.requests.single.queryParameters,
        containsPair('rental_scope', 'bed'),
      );
      expect(network.requests.single.queryParameters, containsPair('page', 3));
      expect(
        OwnerPropertiesData.cacheKeyFor(
          OwnerPropertyFilter.accepted,
          category: RentalListingCategory.bed,
        ),
        isNot(
          OwnerPropertiesData.cacheKeyFor(
            OwnerPropertyFilter.accepted,
            category: RentalListingCategory.room,
          ),
        ),
      );
    },
  );

  testWidgets(
    'failed alert updates retain their retry key and refresh the saved revision',
    (tester) async {
      final network = FeatureTestNetwork()
        ..page = {
          'results': [
            const PremiumSearchAlert(
              id: 'alert-a',
              name: 'Saved search',
              cadence: 'daily',
              enabled: true,
              canManage: true,
              revision: 2,
            ).toJson(),
          ],
          'count': 1,
          'per_page': 20,
          'total_pages': 1,
        };
      repository.replies[PremiumApiConstants.alert('alert-a')] =
          const FeatureTestReply(failure: ServerFailure('Revision conflict'));
      await registerFeatureTestDependencies(repository, network: network);
      await mountFeatureTest(tester, const PremiumAlertsScreen());
      for (var attempt = 0; attempt < 2; attempt++) {
        await tester.ensureVisible(find.text(LocaleKeys.paidAlertPause));
        await tester.tap(find.text(LocaleKeys.paidAlertPause));
        await tester.pumpAndSettle();
        expect(find.text('Saved search'), findsOneWidget);
      }
      expect(repository.requests, hasLength(2));
      expect(repository.requests.first.body, repository.requests.last.body);
      expect(repository.requests.first.body['request_key'], isNotEmpty);
      expect(network.requests, hasLength(3));
      expect(repository.requests.last.body['revision'], 2);
    },
  );

  testWidgets(
    'offer selection loads the full property rather than relying on a collection summary',
    (tester) async {
      propertyReply(rentalInventory());
      RentalSelection? selected;
      await mountFeatureTest(
        tester,
        Scaffold(
          body: SingleChildScrollView(
            child: LeaseRentalOfferSelector(
              propertyId: 'property-a',
              selection: null,
              enabled: true,
              onSelected: (value) => selected = value,
            ),
          ),
        ),
      );
      expect(repository.requests.single.endpoint, 'properties/property-a/');
      await tester.tap(find.textContaining(bedOffer.name).first);
      await tester.pumpAndSettle();
      expect(selected?.bedId, 'bed-a1');
      expect(selected?.offerRevision, 7);
    },
  );

  testWidgets('lease detail rejects a response for another resource', (
    tester,
  ) async {
    await mountFeatureTest(tester, const Scaffold());
    repository.replies[PremiumApiConstants.lease('expected')] =
        const FeatureTestReply(data: {'id': 'other'});
    final cubit = DigitalLeaseDetailsCubit();
    await cubit.load('expected');
    expect(cubit.state.isError, isTrue);
    await cubit.close();
    await tester.pump(const Duration(seconds: 5));
  });

  testWidgets('locale changes partition feature caches', (tester) async {
    await tester.pumpWidget(featureTestHost(const Scaffold(), locale: 'ar'));
    await tester.pumpAndSettle();
    final arabicKey = premiumCacheKey('lease', ['same-resource']);
    final arabicOwnerKey = OwnerPropertiesData.cacheKeyFor(
      OwnerPropertyFilter.accepted,
      category: RentalListingCategory.bed,
    );
    await tester.pumpWidget(const SizedBox.shrink());
    await tester.pumpWidget(featureTestHost(const Scaffold(), locale: 'en'));
    await tester.pumpAndSettle();
    expect(premiumCacheKey('lease', ['same-resource']), isNot(arabicKey));
    expect(
      OwnerPropertiesData.cacheKeyFor(
        OwnerPropertyFilter.accepted,
        category: RentalListingCategory.bed,
      ),
      isNot(arabicOwnerKey),
    );
    expect(Languages.currentLanguage, Languages.english);
  });

  testWidgets(
    'a response from a previous signed-in account cannot become mutation success',
    (tester) async {
      await mountFeatureTest(tester, const Scaffold());
      final gate = Completer<FeatureTestReply>();
      repository.handler = (_) => gate.future;
      final action = PremiumApiData.mutate<DigitalLease>(
        endpoint: PremiumApiConstants.leases,
        body: const {},
        fromJson: DigitalLease.fromJson,
        valid: (lease) => lease.id.isNotEmpty,
      );
      AccountSession.begin('other-account');
      gate.complete(const FeatureTestReply(data: {'id': 'lease'}));
      expect((await action).isError(), isTrue);
    },
  );

  testWidgets(
    'lease and invoice details show the complete saved accommodation while providers stay gated',
    (tester) async {
      final selection = RentalSelection.fromOffer(
        propertyId: 'property-a',
        inventory: rentalInventory(),
        offer: bedOffer,
      );
      await mountFeatureTest(
        tester,
        Scaffold(
          body: DigitalLeaseDetailsView(
            lease: DigitalLease(
              id: 'lease-a',
              propertyTitle: 'Stored lease',
              rentalSelection: selection,
              rent: const PremiumMoney(amountMinor: 325000, currency: 'EGP'),
              status: PremiumStatus.pending,
              canSign: true,
              revision: 1,
              documentUrl: 'https://example.invalid/document',
            ),
            workspace: AppWorkspace.tenant,
            isFresh: true,
            onRefresh: () async {},
          ),
        ),
      );
      expect(find.text(offerTerms.description), findsOneWidget);
      expect(find.text(offerTerms.rules.single), findsOneWidget);
      expect(find.text(LocaleKeys.rentalHistoricalTerms), findsOneWidget);
      expect(find.text('3,250.00 EGP'), findsOneWidget);
      expect(find.text(LocaleKeys.paidLeaseSign), findsNothing);
      expect(find.text(LocaleKeys.paidLeaseDocument), findsNothing);
      await mountFeatureTest(
        tester,
        Scaffold(
          body: RentInvoiceDetailsView(
            invoice: RentInvoice(
              id: 'invoice-a',
              leaseId: 'lease-a',
              propertyTitle: 'Stored invoice',
              rentalSelection: selection,
              reference: 'INV-1',
              amount: const PremiumMoney(amountMinor: 475000, currency: 'EGP'),
              status: PremiumStatus.due,
              canPay: true,
            ),
            isFresh: true,
            onRefresh: () async {},
          ),
        ),
      );
      expect(find.text(offerTerms.description), findsOneWidget);
      expect(find.text('4,750.00 EGP'), findsOneWidget);
      expect(find.text(LocaleKeys.paidPayRent), findsNothing);
      expect(FeatureServiceCapabilities.configured.signedDocuments, isFalse);
    },
  );

  testWidgets(
    'an owner invoice opens its related lease without offering tenant checkout',
    (tester) async {
      repository.replies[PremiumApiConstants.lease(
        'lease-a',
      )] = const FeatureTestReply(
        data: {'id': 'lease-a', 'status': 'draft', 'revision': 1},
      );
      await mountFeatureTest(
        tester,
        Scaffold(
          body: RentInvoiceDetailsView(
            invoice: const RentInvoice(
              id: 'invoice-a',
              leaseId: 'lease-a',
              amount: PremiumMoney(amountMinor: 325000, currency: 'EGP'),
              status: PremiumStatus.due,
              canPay: true,
            ),
            workspace: AppWorkspace.owner,
            capabilities: const FeatureServiceCapabilities(rentCheckout: true),
            isFresh: true,
            onRefresh: () async {},
          ),
        ),
      );
      expect(find.text(LocaleKeys.paidPayRent), findsNothing);
      await tester.tap(find.text(LocaleKeys.journeyViewLease));
      await tester.pumpAndSettle();
      expect(
        tester
            .widget<DigitalLeaseDetailsScreen>(
              find.byType(DigitalLeaseDetailsScreen),
            )
            .workspace,
        AppWorkspace.owner,
      );
      expect(
        repository.requests.single.endpoint,
        PremiumApiConstants.lease('lease-a'),
      );
    },
  );

  testWidgets(
    'alert details retain every saved criterion and use server labels',
    (tester) async {
      final alert = PremiumSearchAlert.fromJson({
        'id': 'alert',
        'name': 'Saved alert',
        'cadence': 'daily',
        'enabled': true,
        'last_matched_at': '2026-10-08T10:00:00+03:00',
        'filters': {
          'search': 'Near campus',
          'city': 'Cairo',
          'district': 'Maadi',
          'rental_scope': 'bed',
          'price_min': 1000,
          'price_max': 3000,
          'price_period': 'monthly',
          'suitable_for': 'students',
          'is_furnished': true,
          'is_verified': true,
          'smoking_allowed': false,
          'bedrooms': 2,
          'bathrooms': 1,
          'amenities': ['has_wifi'],
        },
      });
      final options = PropertyFilterOptionsModel.fromJson({
        'ordering': [
          {'value': '-created_at', 'label': 'Server newest'},
        ],
        'price_periods': [
          {'value': 'monthly', 'label': 'Server monthly'},
        ],
        'suitable_for': [
          {'value': 'students', 'label': 'Server students'},
        ],
        'amenities': [
          {
            'value': 'wifi',
            'query_parameter': 'has_wifi',
            'label': 'Server WiFi',
          },
        ],
      });
      await mountFeatureTest(
        tester,
        Scaffold(
          body: PremiumAlertDetailsView(alert: alert, options: options),
        ),
      );
      for (final label in [
        'Near campus',
        'Cairo',
        'Maadi',
        'Server monthly',
        'Server students',
        'Server WiFi',
        'Server newest',
      ]) {
        expect(find.text(label), findsOneWidget);
      }
      expect(find.textContaining(LocaleKeys.featureFilterNo), findsOneWidget);
      expect(find.text(LocaleKeys.paidAlertDaily), findsOneWidget);
      expect(find.text(LocaleKeys.featureAlertLastMatch), findsOneWidget);
      expect(PremiumSearchAlert.fromJson(alert.toJson()), alert);
    },
  );

  testWidgets(
    'an alert card opens authorized details with localized filter metadata',
    (tester) async {
      const alert = PremiumSearchAlert(
        id: 'alert-a',
        name: 'Saved search',
        cadence: 'daily',
        enabled: true,
        revision: 1,
      );
      final network = FeatureTestNetwork()
        ..page = {
          'results': [alert.toJson()],
          'count': 1,
          'per_page': 20,
          'total_pages': 1,
        };
      repository.replies[PremiumApiConstants.alert(alert.id)] =
          FeatureTestReply(data: alert.toJson());
      repository.replies[ApiConstants.propertyFilterOptions] =
          const FeatureTestReply(data: {});
      await registerFeatureTestDependencies(repository, network: network);
      await mountFeatureTest(tester, const PremiumAlertsScreen());
      await tester.ensureVisible(find.text(LocaleKeys.featureAlertDetails));
      await tester.tap(find.text(LocaleKeys.featureAlertDetails));
      await tester.pumpAndSettle();
      expect(find.byType(PremiumAlertDetailScreen), findsOneWidget);
      expect(find.byType(PremiumAlertDetailsView), findsOneWidget);
      expect(
        repository.requests.map((request) => request.endpoint),
        unorderedEquals([
          PremiumApiConstants.alert(alert.id),
          ApiConstants.propertyFilterOptions,
        ]),
      );
      expect(
        repository.requests.every((request) => request.hasSerializers),
        isTrue,
      );
    },
  );
}
