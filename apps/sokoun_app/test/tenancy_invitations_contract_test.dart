import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:melos_core/config/language/languages.dart';
import 'package:melos_core/config/res/config_imports.dart' show injector;
import 'package:melos_core/core/error/failure.dart';
import 'package:melos_core/core/network/account_session.dart';
import 'package:melos_core/core/network/api_endpoints.dart';
import 'package:sokoun_app/features/main_view/data/enums/app_workspace.dart';
import 'package:sokoun_app/features/shared/digital_leases/data/lease_tenants_data.dart';
import 'package:sokoun_app/features/shared/rental_offers/data/models/rental_selection.dart';
import 'package:sokoun_app/features/shared/tenancy_invitations/data/enums/tenancy_invitation_status.dart';
import 'package:sokoun_app/features/shared/tenancy_invitations/data/models/create_tenancy_invitation_body.dart';
import 'package:sokoun_app/features/shared/tenancy_invitations/data/models/tenancy_invitation.dart';
import 'package:sokoun_app/features/shared/tenancy_invitations/data/tenancy_invitation_capabilities.dart';
import 'package:sokoun_app/features/shared/tenancy_invitations/data/tenancy_invitations_data.dart';
import 'package:sokoun_app/features/shared/tenancy_invitations/presentation/cubits/tenancy_invitation_create_cubit.dart';
import 'package:sokoun_app/features/shared/tenancy_invitations/presentation/cubits/tenancy_invitation_details_cubit.dart';
import 'package:sokoun_app/features/shared/tenancy_invitations/presentation/cubits/tenancy_invitation_response_cubit.dart';
import 'helpers/feature_tools_test_dependencies.dart';
import 'helpers/rental_offer_fixtures.dart';
import 'helpers/tenancy_invitation_fixtures.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  late FeatureTestRepository repository;
  late FeatureTestNetwork network;
  setUpAll(initializeFeatureTestEnvironment);
  setUp(() async {
    repository = FeatureTestRepository();
    network = FeatureTestNetwork();
    await registerFeatureTestDependencies(repository, network: network);
    injector.registerSingleton(
      const TenancyInvitationCapabilities(enabled: true),
    );
  });
  tearDown(() async {
    await injector.reset();
    AccountSession.end();
  });

  test('the agreed API stays disabled until staging is verified', () {
    expect(
      TenancyInvitationCapabilities.configured.enabled,
      const bool.fromEnvironment('SOKOUN_TENANCY_INVITATIONS'),
    );
  });

  test(
    'legacy nullable snapshots and all statuses round-trip without authorizing expired responses',
    () {
      final json = invitationJson(owner: 'owner-a', tenant: 'fixture-account')
        ..['offer_snapshot'] = null;
      final pending = TenancyInvitation.fromJson(json);
      expect(pending.hasValidIdentity, isTrue);
      expect(pending.canRespondAs('fixture-account'), isTrue);
      expect(pending.canRespondAs('owner-a'), isFalse);
      for (final status in TenancyInvitationStatus.values) {
        final item = pending.copyWith(status: status);
        expect(TenancyInvitation.fromJson(item.toJson()), item);
        if (status != TenancyInvitationStatus.pending) {
          expect(item.canRespondAs('fixture-account'), isFalse);
        }
      }
      expect(
        pending
            .copyWith(expiresAt: DateTime.utc(2026, 10, 9))
            .canRespondAs('fixture-account'),
        DateTime.utc(2026, 10, 9).isAfter(DateTime.now()),
      );
      expect(
        pending
            .copyWith(expiresAt: DateTime.utc(2000))
            .canRespondAs('fixture-account'),
        isFalse,
      );
      expect(
        pending.copyWith(leaseId: 'lease-a').canRespondAs('fixture-account'),
        isFalse,
      );
    },
  );

  testWidgets(
    'disabled capability denies reads, writes and fresh-property loading',
    (tester) async {
      await mountFeatureTest(tester, const Scaffold());
      await injector.unregister<TenancyInvitationCapabilities>();
      injector.registerSingleton(const TenancyInvitationCapabilities());
      final invitation = TenancyInvitation.fromJson(
        invitationJson(owner: 'owner-a', tenant: 'fixture-account'),
      );
      expect(
        (await TenancyInvitationsData.get(
          id: invitation.id,
          workspace: AppWorkspace.tenant,
        )).isError(),
        isTrue,
      );
      expect(
        (await TenancyInvitationsData.create(
          const CreateTenancyInvitationBody(
            propertyId: 'property-a',
            tenantId: 'tenant-a',
            requestKey: 'key',
          ),
        )).isError(),
        isTrue,
      );
      expect(
        (await TenancyInvitationsData.respond(
          invitation: invitation,
          decision: TenancyInvitationStatus.accepted,
          requestKey: 'key',
        )).isError(),
        isTrue,
      );
      await expectLater(
        TenancyInvitationsData.getPage(page: 1, workspace: AppWorkspace.tenant),
        throwsStateError,
      );
      final cubit = TenancyInvitationCreateCubit();
      expect(
        await cubit.create(propertyId: 'property-a', tenantId: 'tenant-a'),
        isNull,
      );
      expect(repository.requests, isEmpty);
      expect(network.requests, isEmpty);
      await cubit.close();
      await tester.pump(const Duration(seconds: 6));
      await tester.pumpAndSettle();
    },
  );

  for (final offer in [
    wholeOffer,
    independentRooms.first,
    groupOffer,
    bedOffer,
  ]) {
    testWidgets(
      'create validates fresh ${offer.scopeValue} accommodation and preserves exact identity',
      (tester) async {
        await mountFeatureTest(tester, const Scaffold());
        final inventory = rentalInventory(
          offers: [offer],
          mode: offer.scopeValue == 'entire_property' ? 'whole' : 'partial',
        );
        final selection = RentalSelection.fromOffer(
          propertyId: 'property-a',
          inventory: inventory,
          offer: offer,
        );
        repository.replies[ApiConstants.propertyDetails(
          'property-a',
        )] = FeatureTestReply(
          data: rentalProperty(inventory: inventory).toJson(),
        );
        repository.replies[TenancyInvitationApi.collection] = FeatureTestReply(
          data: invitationJson(selection: selection),
        );
        final cubit = TenancyInvitationCreateCubit();
        final result = await cubit.create(
          propertyId: 'property-a',
          tenantId: 'tenant-a',
          selection: selection,
        );
        expect(result?.status, TenancyInvitationStatus.pending);
        expect(result?.rentalSelection?.sameTermsAs(selection), isTrue);
        expect(
          repository.requests.last.body,
          containsPair('expected_offer_revision', offer.revision),
        );
        expect(
          repository.requests.last.body,
          containsPair('offer_id', offer.id),
        );
        expect(
          repository.requests.last.body['request_key'],
          matches(RegExp(r'^[a-f0-9-]{36}$')),
        );
        expect(repository.requests.last.body.containsKey('owner_id'), isFalse);
        expect(result?.isEligible, isFalse);
        await cubit.close();
        await tester.pump(const Duration(seconds: 6));
        await tester.pumpAndSettle();
      },
    );
  }

  for (final changed in [
    'cached',
    'revision',
    'unavailable',
    'missing_selection',
    'wrong_receipt',
  ]) {
    testWidgets('create rejects $changed accommodation or confirmation', (
      tester,
    ) async {
      await mountFeatureTest(tester, const Scaffold());
      final inventory = rentalInventory();
      final selection = RentalSelection.fromOffer(
        propertyId: 'property-a',
        inventory: inventory,
        offer: bedOffer,
      );
      final current = changed == 'revision'
          ? bedOffer.copyWith(revision: 8)
          : changed == 'unavailable'
          ? bedOffer.copyWith(availability: 'unavailable')
          : bedOffer;
      repository.replies[ApiConstants.propertyDetails(
        'property-a',
      )] = FeatureTestReply(
        data: rentalProperty(
          inventory: rentalInventory(offers: [current]),
        ).toJson(),
        key: changed == 'cached' ? 'fromCache' : 'success',
      );
      repository.replies[TenancyInvitationApi.collection] = FeatureTestReply(
        data: invitationJson(selection: selection)
          ..['tenant_id'] = 'wrong-tenant',
      );
      final cubit = TenancyInvitationCreateCubit();
      expect(
        await cubit.create(
          propertyId: 'property-a',
          tenantId: 'tenant-a',
          selection: changed == 'missing_selection' ? null : selection,
        ),
        isNull,
      );
      if (changed != 'wrong_receipt') {
        expect(
          repository.requests.every(
            (r) => r.endpoint != TenancyInvitationApi.collection,
          ),
          isTrue,
        );
      }
      await cubit.close();
      await tester.pump(const Duration(seconds: 6));
      await tester.pumpAndSettle();
    });
  }

  testWidgets(
    'a failed create preserves the request key while a changed accommodation gets a new key',
    (tester) async {
      await mountFeatureTest(tester, const Scaffold());
      final inventory = rentalInventory(offers: independentRooms);
      repository.replies[ApiConstants.propertyDetails('property-a')] =
          FeatureTestReply(data: rentalProperty(inventory: inventory).toJson());
      repository.replies[TenancyInvitationApi.collection] = FeatureTestReply(
        failure: ServerFailure('Server retry message'),
      );
      final cubit = TenancyInvitationCreateCubit();
      final first = RentalSelection.fromOffer(
        propertyId: 'property-a',
        inventory: inventory,
        offer: independentRooms.first,
      );
      final second = RentalSelection.fromOffer(
        propertyId: 'property-a',
        inventory: inventory,
        offer: independentRooms.last,
      );
      await cubit.create(
        propertyId: 'property-a',
        tenantId: 'tenant-a',
        selection: first,
      );
      expect(cubit.state.msg, 'Server retry message');
      await cubit.create(
        propertyId: 'property-a',
        tenantId: 'tenant-a',
        selection: first,
      );
      await cubit.create(
        propertyId: 'property-a',
        tenantId: 'tenant-a',
        selection: second,
      );
      final sends = repository.requests
          .where((r) => r.endpoint == TenancyInvitationApi.collection)
          .toList();
      expect(sends[0].body['request_key'], sends[1].body['request_key']);
      expect(sends[2].body['request_key'], isNot(sends[0].body['request_key']));
      await cubit.close();
      await tester.pump(const Duration(seconds: 6));
      await tester.pumpAndSettle();
    },
  );

  for (final decision in [
    TenancyInvitationStatus.accepted,
    TenancyInvitationStatus.rejected,
  ]) {
    testWidgets(
      'only the addressed tenant can respond $decision and retries retain the same request key',
      (tester) async {
        await mountFeatureTest(tester, const Scaffold());
        final invitation = TenancyInvitation.fromJson(
          invitationJson(owner: 'owner-a', tenant: 'fixture-account'),
        );
        repository.replies[TenancyInvitationApi.respond(invitation.id)] =
            FeatureTestReply(failure: ServerFailure('Retry response'));
        final cubit = TenancyInvitationResponseCubit();
        await cubit.respond(invitation, decision);
        final firstKey = repository.requests.last.body['request_key'];
        repository.replies[TenancyInvitationApi.respond(
          invitation.id,
        )] = FeatureTestReply(
          data: {
            ...invitation.toJson(),
            'status': decision.name,
            'revision': 2,
            'accepted_at': decision == TenancyInvitationStatus.accepted
                ? '2026-10-08T10:00:00Z'
                : null,
            'eligible_for_lease': decision == TenancyInvitationStatus.accepted,
            'actions': {'can_respond': false},
          },
        );
        final result = await cubit.respond(invitation, decision);
        expect(result?.status, decision);
        expect(
          result?.isEligible,
          decision == TenancyInvitationStatus.accepted,
        );
        expect(repository.requests.last.body['request_key'], firstKey);
        expect(repository.requests.last.body['revision'], 1);
        expect(repository.requests.last.body['decision'], decision.name);
        await cubit.close();
        await tester.pump(const Duration(seconds: 6));
        await tester.pumpAndSettle();
      },
    );
  }

  test(
    'wrong actor, expiry and terminal status deny responses without API writes',
    () async {
      final invitation = TenancyInvitation.fromJson(invitationJson());
      for (final item in [
        invitation,
        TenancyInvitation.fromJson(
          invitationJson(owner: 'owner-a', tenant: 'fixture-account'),
        ).copyWith(expiresAt: DateTime.utc(2000)),
        TenancyInvitation.fromJson(
          invitationJson(owner: 'owner-a', tenant: 'fixture-account'),
        ).copyWith(status: TenancyInvitationStatus.rejected),
      ]) {
        expect(
          (await TenancyInvitationsData.respond(
            invitation: item,
            decision: TenancyInvitationStatus.accepted,
            requestKey: 'key',
          )).isError(),
          isTrue,
        );
      }
      expect(repository.requests, isEmpty);
    },
  );

  test(
    'response receipts cannot change participants, subject or decision',
    () async {
      final invitation = TenancyInvitation.fromJson(
        invitationJson(owner: 'owner-a', tenant: 'fixture-account'),
      );
      for (final alteration in [
        {'id': 'other-invitation'},
        {'tenant_id': 'other-tenant'},
        {'property_id': 'other-property'},
        {'status': 'rejected'},
        {'revision': 1},
      ]) {
        repository.replies[TenancyInvitationApi.respond(
          invitation.id,
        )] = FeatureTestReply(
          data: {
            ...invitation.toJson(),
            'status': 'accepted',
            'revision': 2,
            'eligible_for_lease': true,
            'actions': {'can_respond': false},
            ...alteration,
          },
        );
        expect(
          (await TenancyInvitationsData.respond(
            invitation: invitation,
            decision: TenancyInvitationStatus.accepted,
            requestKey: 'key',
          )).isError(),
          isTrue,
        );
      }
    },
  );

  test(
    'collection scopes the owner/property before accepting returned rows',
    () async {
      network.page = {
        'results': [invitationJson()],
        'count': 1,
        'per_page': 20,
        'total_pages': 1,
      };
      final page = await TenancyInvitationsData.getPage(
        page: 2,
        workspace: AppWorkspace.owner,
        propertyId: 'property-a',
      );
      expect(page.$1.single.id, 'invitation-a');
      expect(network.requests.single.queryParameters, {
        'workspace': 'owner',
        'property_id': 'property-a',
        'page': 2,
        'page_size': 20,
      });
      network.page = {
        'results': [invitationJson(owner: 'another-owner')],
        'count': 1,
      };
      await expectLater(
        TenancyInvitationsData.getPage(page: 1, workspace: AppWorkspace.owner),
        throwsStateError,
      );
      network.page = {
        'results': [invitationJson()..['property_id'] = 'another-property'],
        'count': 1,
      };
      await expectLater(
        TenancyInvitationsData.getPage(
          page: 1,
          workspace: AppWorkspace.owner,
          propertyId: 'property-a',
        ),
        throwsStateError,
      );
    },
  );

  testWidgets(
    'detail reads include complete scoped cache contracts and cached records block actions',
    (tester) async {
      await mountFeatureTest(tester, const Scaffold());
      final invitation = invitationJson(
        owner: 'owner-a',
        tenant: 'fixture-account',
      );
      repository.replies[TenancyInvitationApi.detail('invitation-a')] =
          FeatureTestReply(data: invitation, key: 'fromCache');
      final cubit = TenancyInvitationDetailsCubit();
      await cubit.load('invitation-a', AppWorkspace.tenant);
      expect(cubit.isCached, isTrue);
      expect(cubit.data.id, 'invitation-a');
      expect(repository.requests.last.hasSerializers, isTrue);
      expect(repository.requests.last.query, isNull);
      expect(
        repository.requests.last.cacheKey,
        contains(AccountSession.cacheKey('')),
      );
      final firstKey = TenancyInvitationsData.cacheKey(
        AppWorkspace.tenant,
        propertyId: 'property-a',
      );
      final ownerKey = TenancyInvitationsData.cacheKey(
        AppWorkspace.owner,
        propertyId: 'property-a',
      );
      expect(firstKey, isNot(ownerKey));
      Languages.setLocale(Languages.english);
      await tester.pumpAndSettle();
      expect(
        TenancyInvitationsData.cacheKey(
          AppWorkspace.tenant,
          propertyId: 'property-a',
        ),
        isNot(firstKey),
      );
      final englishKey = TenancyInvitationsData.cacheKey(AppWorkspace.tenant);
      AccountSession.begin('different-account');
      expect(
        TenancyInvitationsData.cacheKey(AppWorkspace.tenant),
        isNot(englishKey),
      );
      await cubit.close();
      await tester.pump(const Duration(seconds: 6));
      await tester.pumpAndSettle();
    },
  );

  testWidgets(
    'a session change during property loading cannot send an invitation',
    (tester) async {
      await mountFeatureTest(tester, const Scaffold());
      final gate = Completer<FeatureTestReply>();
      repository.handler = (_) => gate.future;
      final cubit = TenancyInvitationCreateCubit();
      final operation = cubit.create(
        propertyId: 'property-a',
        tenantId: 'tenant-a',
      );
      AccountSession.begin('another-account');
      gate.complete(const FeatureTestReply(data: {'id': 'property-a'}));
      expect(await operation, isNull);
      expect(repository.requests, hasLength(1));
      await cubit.close();
      await tester.pump(const Duration(seconds: 6));
      await tester.pumpAndSettle();
    },
  );

  test(
    'tenant picker caches and requests preserve exact offer scope after enablement',
    () async {
      await LeaseTenantsData.getPage(
        propertyId: 'property-a',
        page: 1,
        offerId: 'offer-a',
      );
      expect(network.requests.last.queryParameters?['offer_id'], 'offer-a');
      expect(
        LeaseTenantsData.cacheKey('property-a', offerId: 'offer-a'),
        isNot(LeaseTenantsData.cacheKey('property-a', offerId: 'offer-b')),
      );
      await injector.unregister<TenancyInvitationCapabilities>();
      injector.registerSingleton(const TenancyInvitationCapabilities());
      await LeaseTenantsData.getPage(
        propertyId: 'property-a',
        page: 1,
        offerId: 'offer-a',
      );
      expect(
        network.requests.last.queryParameters?.containsKey('offer_id'),
        isFalse,
      );
    },
  );
}
