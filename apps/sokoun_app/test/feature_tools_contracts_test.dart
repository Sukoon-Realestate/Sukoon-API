import 'package:flutter_test/flutter_test.dart';
import 'package:melos_core/core/network/account_session.dart';
import 'package:sokoun_app/features/main_view/data/enums/app_workspace.dart';
import 'package:sokoun_app/features/owner/advanced_analytics/data/models/advanced_analytics_content.dart';
import 'package:sokoun_app/features/owner/advanced_analytics/data/models/analytics_metric.dart';
import 'package:sokoun_app/features/owner/advanced_analytics/presentation/cubits/advanced_analytics_cubit.dart';
import 'package:sokoun_app/features/owner/ai_assistant/data/models/listing_ai_facts.dart';
import 'package:sokoun_app/features/tenant/home/data/models/home_page_model.dart';
import 'package:sokoun_app/features/owner/promotions/data/models/promotion_campaign.dart';
import 'package:sokoun_app/features/owner/promotions/data/promotions_data.dart';
import 'package:sokoun_app/features/shared/digital_leases/data/lease_rules.dart';
import 'package:sokoun_app/features/shared/digital_leases/data/digital_leases_data.dart';
import 'package:sokoun_app/features/shared/digital_leases/data/lease_tenants_data.dart';
import 'package:sokoun_app/features/shared/digital_leases/data/models/digital_lease.dart';
import 'package:sokoun_app/features/shared/digital_leases/data/models/lease_configuration.dart';
import 'package:sokoun_app/features/shared/digital_leases/data/models/lease_draft_body.dart';
import 'package:sokoun_app/features/shared/premium/data/models/premium_action_receipt.dart';
import 'package:sokoun_app/features/shared/premium/data/models/feature_configuration.dart';
import 'package:sokoun_app/features/shared/premium/data/models/premium_money.dart';
import 'package:sokoun_app/features/shared/premium/data/premium_api_data.dart';
import 'package:sokoun_app/features/shared/premium/data/premium_api_constants.dart';
import 'package:sokoun_app/features/shared/premium/data/feature_configuration_data.dart';
import 'package:sokoun_app/features/shared/premium/data/premium_hosted_data.dart';
import 'package:sokoun_app/features/shared/rent_management/data/models/rent_invoice.dart';
import 'package:sokoun_app/features/shared/rent_management/data/rent_management_data.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_details_model.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_search_model.dart';
import 'package:sokoun_app/features/tenant/premium_alerts/data/models/premium_alert_body.dart';
import 'package:sokoun_app/features/tenant/premium_alerts/data/models/premium_search_alert.dart';
import 'package:sokoun_app/features/tenant/premium_alerts/data/premium_alerts_data.dart';
import 'helpers/feature_tools_test_dependencies.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  late FeatureTestRepository repository;
  setUp(() async {
    repository = FeatureTestRepository();
    await registerFeatureTestDependencies(repository);
  });
  tearDown(AccountSession.end);

  test('money keeps exact minor units and rejects malformed amounts', () {
    expect(LeaseRules.money('123.10').amountMinor, 12310);
    expect(LeaseRules.money('0.01').display, '0.01 EGP');
    expect(LeaseRules.money('999999999.99').amountMinor, 99999999999);
    for (final value in [
      '1.234',
      '-1',
      'NaN',
      'Infinity',
      '1e3',
      '1,000',
      '1000000000',
    ]) {
      expect(LeaseRules.money(value).isKnown, isFalse, reason: value);
    }
    for (final json in [
      {'amount_minor': 10.2, 'currency': 'EGP'},
      {'amount_minor': -1, 'currency': 'EGP'},
      {'amount_minor': 100, 'currency': 'egp'},
      {'amount_minor': 100, 'currency': 'EGP', 'exponent': 'broken'},
    ]) {
      expect(PremiumMoney.fromJson(json).isKnown, isFalse);
    }
    expect(const PremiumMoney.initial().display, '—');
  });
  test(
    'lease drafts reject impossible dates and incomplete or ambiguous terms',
    () {
      const draft = LeaseDraftBody(
        propertyId: 'property',
        tenantId: 'tenant',
        templateId: 'template',
        templateVersion: 'v1',
        startDate: '2026-10-10',
        endDate: '2027-10-10',
        rent: PremiumMoney(amountMinor: 1200000, currency: 'EGP'),
        requestKey: 'fixture-key',
      );
      expect(LeaseRules.valid(draft), isTrue);
      for (final invalid in [
        draft.copyWith(startDate: '2026-02-31'),
        draft.copyWith(endDate: '2026-10-10'),
        draft.copyWith(templateVersion: ''),
        draft.copyWith(tenantId: ''),
        draft.copyWith(propertyId: ''),
        draft.copyWith(
          rent: const PremiumMoney(amountMinor: 120, currency: 'USD'),
        ),
        draft.copyWith(
          rent: const PremiumMoney(
            amountMinor: 120,
            currency: 'EGP',
            exponent: 3,
          ),
        ),
      ]) {
        expect(LeaseRules.valid(invalid), isFalse);
      }
      expect(LeaseRules.date('2028-02-29'), isNotNull);
      expect(LeaseRules.date('2027-02-29'), isNull);
    },
  );
  test(
    'free configuration ignores old payment fields and needs no credits',
    () {
      final configuration = FeatureConfiguration.fromJson({
        'workspace': 'owner',
        'boost_options': [
          {'id': 'week', 'title': 'Week', 'duration_days': 7, 'credit_cost': 2},
        ],
        'alert_cadences': ['daily', 'daily', ''],
        'products': [
          {'kind': 'subscription'},
        ],
        'grants': [
          {'remaining': 0},
        ],
      });
      expect(configuration.boostOptions.single.isValid, isTrue);
      expect(configuration.alertCadences, ['daily']);
      expect(configuration.toJson().containsKey('products'), isFalse);
      expect(configuration.toJson().containsKey('grants'), isFalse);
      expect(
        configuration.boostOptions.single.toJson().containsKey('credit_cost'),
        isFalse,
      );
    },
  );
  test(
    'search alert serialization preserves every search dimension and resets paging',
    () {
      const filters = PropertySearchFilters.initial(
        search: 'معادي',
        district: 'zone',
        priceMin: '12000',
        priceMax: '20000',
        propertyType: 'apartment',
        pricePeriod: 'monthly',
        suitableFor: 'family',
        isFurnished: 'true',
        isVerified: 'true',
        smokingAllowed: 'false',
        bedrooms: '2',
        bathrooms: '1',
        amenities: {'wifi', 'balcony'},
      );
      final body = PremiumAlertBody(
        name: 'قرب العمل',
        cadence: 'daily',
        filters: filters.copyWith(page: 4, city: 'city'),
        requestKey: 'fixture-key',
      );
      final restored = PremiumAlertBody.fromJson(body.toJson());
      expect(restored.filters, body.filters.copyWith(page: 1));
      expect(restored.isValid, isTrue);
      expect(restored.filters.amenities, filters.amenities);
      expect(
        body
            .copyWith(
              filters: filters.copyWith(priceMin: '30000', priceMax: '10000'),
            )
            .isValid,
        isFalse,
      );
    },
  );
  test(
    'AI facts whitelist listing fields and exclude private documents and contact data',
    () {
      final facts = ListingAiFacts.fromJson({
        'title': 'شقة',
        'description': 'وصف',
        'price': '12000',
        'phone': 'fixture-phone',
        'email': 'private@example.invalid',
        'ownership_proof': 'private-document',
        'latitude': 30.1,
        'longitude': 31.2,
      });
      final json = facts.toJson();
      expect(json['title'], 'شقة');
      for (final private in [
        'phone',
        'email',
        'ownership_proof',
        'latitude',
        'longitude',
      ]) {
        expect(json.containsKey(private), isFalse);
      }
    },
  );
  test('hosted sessions require HTTPS without embedded credentials', () {
    for (final value in [
      'http://example.invalid/pay',
      'javascript:alert(1)',
      'https://name:secret@example.invalid/pay',
      'https:///pay',
      '',
    ]) {
      expect(PremiumHostedData.httpsUri(value), isNull);
    }
    expect(
      PremiumHostedData.httpsUri('https://example.invalid/pay?session=fixture'),
      isNotNull,
    );
  });
  test(
    'metrics preserve fractional rates and render missing values as unknown',
    () {
      expect(
        AnalyticsMetric.fromJson({'value': 3.25, 'unit': 'percent'}).display,
        '3.25%',
      );
      expect(AnalyticsMetric.fromJson({'value': 'NaN'}).display, '—');
      expect(AnalyticsMetric.fromJson({}).display, '—');
    },
  );
  test(
    'all persisted feature responses preserve their domain values across cache round trips',
    () {
      void check<T>(
        T value,
        T Function(Map<String, dynamic>) decode,
        Map<String, dynamic> Function(T) encode,
      ) => expect(decode(encode(value)), value);
      final configuration = FeatureConfiguration.fromJson({
        'workspace': 'owner',
        'boost_options': [
          {'id': 'week', 'title': 'أسبوع', 'duration_days': 7},
        ],
        'alert_cadences': ['daily'],
      });
      check(
        configuration,
        FeatureConfiguration.fromJson,
        (value) => value.toJson(),
      );
      final campaign = PromotionCampaign.fromJson({
        'id': 'campaign',
        'property_id': 'property',
        'property_title': 'شقة',
        'status': 'active',
        'starts_at': '2026-10-06T00:00:00Z',
        'ends_at': '2026-10-13T00:00:00Z',
        'duration_days': 7,
        'impressions': 8,
      });
      check(campaign, PromotionCampaign.fromJson, (value) => value.toJson());
      final alert = PremiumSearchAlert.fromJson({
        'id': 'alert',
        'name': 'شقة',
        'enabled': true,
        'can_manage': true,
        'revision': 2,
        'cadence': 'daily',
        'filters': const PropertySearchFilters.initial().toJson(),
      });
      check(alert, PremiumSearchAlert.fromJson, (value) => value.toJson());
      final analytics = AdvancedAnalyticsContent.fromJson({
        'property_id': 'property',
        'period_days': 30,
        'measured_at': '2026-10-06T00:00:00Z',
        'metrics': [
          {
            'key': 'conversion',
            'label': 'معدل التحويل',
            'value': 3.5,
            'unit': 'percent',
            'definition': 'التعريف',
          },
        ],
        'methodology': 'تعريف القياس',
        'export_url': 'https://example.invalid/report',
      });
      check(
        analytics,
        AdvancedAnalyticsContent.fromJson,
        (value) => value.toJson(),
      );
      final lease = DigitalLease.fromJson({
        'id': 'lease',
        'property_id': 'property',
        'property_title': 'شقة',
        'owner_name': 'مالك',
        'tenant_name': 'مستأجر',
        'start_date': '2026-10-06',
        'end_date': '2027-10-06',
        'rent': {'amount_minor': 1200000, 'currency': 'EGP', 'exponent': 2},
        'status': 'pending',
        'revision': 2,
        'can_sign': true,
        'can_cancel': false,
        'document_url': 'https://example.invalid/lease',
      });
      check(lease, DigitalLease.fromJson, (value) => value.toJson());
      final config = LeaseConfiguration.fromJson({
        'can_create': true,
        'templates': [
          {
            'id': 'template',
            'title': 'عقد',
            'jurisdiction': 'EG',
            'language': 'ar',
            'version': 'v1',
          },
        ],
      });
      check(config, LeaseConfiguration.fromJson, (value) => value.toJson());
      final invoice = RentInvoice.fromJson({
        'id': 'invoice',
        'lease_id': 'lease',
        'property_title': 'شقة',
        'reference': 'INV-1',
        'due_date': '2026-11-01',
        'amount': {'amount_minor': 1200000, 'currency': 'EGP', 'exponent': 2},
        'status': 'due',
        'can_pay': true,
        'receipt_url': '',
      });
      check(invoice, RentInvoice.fromJson, (value) => value.toJson());
      final receipt = PremiumActionReceipt.fromJson({
        'id': 'session',
        'subject_id': 'invoice',
        'status': 'pending',
        'amount': invoice.amount.toJson(),
        'hosted_url': 'https://example.invalid/pay',
        'expires_at': '2050-01-01T00:00:00Z',
      });
      check(receipt, PremiumActionReceipt.fromJson, (value) => value.toJson());
    },
  );
  test(
    'GET cache identities separate accounts workspaces languages properties and periods',
    () async {
      repository.handler = (request) async =>
          request.endpoint.startsWith(
            '${PremiumApiConstants.prefix}owner-analytics/',
          )
          ? FeatureTestReply(
              data: {
                'property_id': request.endpoint
                    .split('/')
                    .where((part) => part.isNotEmpty)
                    .last,
                'period_days': request.query!['period_days'],
              },
            )
          : repository.defaultReply(request);
      await FeatureConfigurationData.get(AppWorkspace.owner, language: 'ar');
      await FeatureConfigurationData.get(AppWorkspace.owner, language: 'en');
      await FeatureConfigurationData.get(AppWorkspace.tenant, language: 'ar');
      final analytics = AdvancedAnalyticsCubit();
      await analytics.load(propertyId: 'one', periodDays: 7, language: 'ar');
      await analytics.load(propertyId: 'one', periodDays: 30, language: 'ar');
      await analytics.load(propertyId: 'two', periodDays: 7, language: 'ar');
      await analytics.close();
      expect(
        repository.requests.map((value) => value.cacheKey).toSet(),
        hasLength(repository.requests.length),
      );
      expect(
        repository.requests.every((value) => value.hasSerializers),
        isTrue,
      );
      final first = repository.requests.first.cacheKey;
      AccountSession.begin('another-account');
      await FeatureConfigurationData.get(AppWorkspace.owner, language: 'ar');
      expect(repository.requests.last.cacheKey, isNot(first));
      expect(
        DigitalLeasesData.cacheKey(AppWorkspace.owner),
        isNot(DigitalLeasesData.cacheKey(AppWorkspace.tenant)),
      );
      expect(
        RentManagementData.cacheKey(AppWorkspace.owner),
        isNot(RentManagementData.cacheKey(AppWorkspace.tenant)),
      );
      expect(
        LeaseTenantsData.cacheKey('one'),
        isNot(LeaseTenantsData.cacheKey('two')),
      );
      expect(
        PromotionsData.cacheKey,
        startsWith('account_v1_another-account_'),
      );
      expect(
        PremiumAlertsData.cacheKey,
        startsWith('account_v1_another-account_'),
      );
    },
  );
  test(
    'pagination accepts true empty results and preserves backend paging boundaries',
    () {
      final (empty, pagination) = PremiumApiData.parsePage(
        {'results': [], 'count': 0, 'per_page': 20},
        page: 1,
        fromJson: PromotionCampaign.fromJson,
      );
      expect(empty, isEmpty);
      expect(pagination.totalPages, 1);
      final (items, pages) = PremiumApiData.parsePage(
        {
          'results': [
            {'id': 'campaign'},
          ],
          'count': 45,
          'per_page': 20,
        },
        page: 1,
        fromJson: PromotionCampaign.fromJson,
      );
      expect(items.single.id, 'campaign');
      expect(pages.totalPages, 3);
    },
  );
  test(
    'sponsorship remains independent of verification and survives existing caches',
    () {
      final property = const PropertyDetailsModel.initial().copyWith(
        id: 'property',
        isSponsored: true,
        isVerified: false,
      );
      expect(PropertyDetailsModel.fromJson(property.toJson()), property);
      expect(property.isVerified, isFalse);
      final home = const HomePropertyModel.initial().copyWith(
        id: 'property',
        isSponsored: true,
      );
      expect(HomePropertyModel.fromJson(home.toJson()), home);
      expect(HomePropertyModel.fromJson({}).isSponsored, isFalse);
    },
  );
}
