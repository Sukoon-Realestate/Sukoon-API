import 'dart:io';
import 'dart:ui' as ui;
import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart'
    show injector, ConstantManager;
import 'package:melos_core/core/network/api_endpoints.dart';
import 'package:melos_core/core/network/account_session.dart';
import 'package:melos_core/core/shared/models/user_models/user_model.dart';
import 'package:sokoun_app/features/main_view/data/enums/app_workspace.dart';
import 'package:sokoun_app/features/main_view/presentation/verified_feature_routes.dart';
import 'package:sokoun_app/features/owner/visits/imports.dart';
import 'package:sokoun_app/features/shared/digital_leases/presentation/screens/lease_draft_screen.dart';
import 'package:sokoun_app/features/shared/digital_leases/presentation/widgets/lease_tenant_selector.dart';
import 'package:sokoun_app/features/shared/notifications/data/enums/app_notification_kind.dart';
import 'package:sokoun_app/features/shared/notifications/data/models/app_notification_content.dart';
import 'package:sokoun_app/features/shared/notifications/data/notification_destination.dart';
import 'package:sokoun_app/features/shared/premium/data/premium_api_constants.dart';
import 'package:sokoun_app/features/shared/profile/presentation/widgets/contracts/contracts_journey_actions.dart';
import 'package:sokoun_app/features/shared/rental_offers/data/models/rental_selection.dart';
import 'package:sokoun_app/features/shared/rental_offers/presentation/widgets/rental_offer_picker.dart';
import 'package:sokoun_app/features/shared/tenancy_invitations/data/tenancy_invitation_capabilities.dart';
import 'package:sokoun_app/features/shared/tenancy_invitations/data/tenancy_invitations_data.dart';
import 'package:sokoun_app/features/shared/tenancy_invitations/presentation/screens/tenancy_invite_screen.dart';
import 'package:sokoun_app/features/shared/tenancy_invitations/presentation/screens/tenancy_invitation_detail_screen.dart';
import 'package:sokoun_app/features/shared/tenancy_invitations/presentation/screens/tenancy_invitations_screen.dart';
import 'package:sokoun_app/features/shared/tenancy_invitations/presentation/widgets/tenancy_invitation_card.dart';
import 'package:sokoun_app/features/shared/tenancy_invitations/presentation/widgets/tenancy_invitations_empty_state.dart';
import 'package:sokoun_app/features/shared/tenancy_invitations/presentation/widgets/tenancy_invitation_response_actions.dart';
import 'helpers/account_test_dependencies.dart';
import 'helpers/feature_tools_test_dependencies.dart';
import 'helpers/rental_offer_fixtures.dart';
import 'helpers/tenancy_invitation_fixtures.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  late FeatureTestRepository repository;
  late FeatureTestNetwork network;
  late Map<String, dynamic> remote;
  setUpAll(() async {
    await initializeFeatureTestEnvironment();
    final font = FontLoader(ConstantManager.fontFamily);
    for (final weight in ['Regular', 'Medium', 'Bold']) {
      font.addFont(
        rootBundle.load(
          'packages/melos_core/assets/fonts/Tajawal/Tajawal-$weight.ttf',
        ),
      );
    }
    await font.load();
    await (FontLoader(
      'MaterialIcons',
    )..addFont(rootBundle.load('fonts/MaterialIcons-Regular.otf'))).load();
  });
  setUp(() async {
    repository = FeatureTestRepository();
    network = FeatureTestNetwork();
    await registerFeatureTestDependencies(repository, network: network);
    remote = invitationJson(owner: 'owner-a', tenant: 'tenant-a');
    repository.handler = (request) async {
      if (request.endpoint ==
          ApiConstants.ownerVisitRequestDetails('visit-a')) {
        return const FeatureTestReply(
          data: {
            'id': 'visit-a',
            'tenant': {
              'id': 'tenant-a',
              'name': 'أحمد محمد',
              'is_verified': true,
            },
            'property': {'id': 'property-a', 'title': 'شقة المعادي'},
            'status': 'confirmed',
            'visit_date': '2026-10-08',
            'visit_time': '10:00:00',
            'actions': {
              'can_accept': false,
              'can_reject': false,
              'can_chat': true,
            },
          },
        );
      }
      if (request.endpoint == ApiConstants.propertyDetails('property-a')) {
        return const FeatureTestReply(
          data: {'id': 'property-a', 'title': 'شقة المعادي'},
        );
      }
      if (request.endpoint == TenancyInvitationApi.collection) {
        remote = invitationJson(
          owner: TenancyInvitationsData.accountId,
          tenant: request.body['tenant_id'] as String,
        );
        return FeatureTestReply(data: remote);
      }
      if (request.endpoint == TenancyInvitationApi.detail('invitation-a')) {
        return FeatureTestReply(
          data: {
            ...remote,
            'actions': {
              'can_respond':
                  TenancyInvitationsData.accountId == remote['tenant_id'] &&
                  remote['status'] == 'pending',
            },
          },
        );
      }
      if (request.endpoint == TenancyInvitationApi.respond('invitation-a')) {
        final accepted = request.body['decision'] == 'accepted';
        remote = {
          ...remote,
          'status': request.body['decision'],
          'revision': 2,
          'accepted_at': accepted ? '2026-10-08T10:00:00Z' : null,
          'rejected_at': accepted ? null : '2026-10-08T10:00:00Z',
          'eligible_for_lease': accepted,
          'actions': {'can_respond': false},
        };
        return FeatureTestReply(data: remote);
      }
      if (request.endpoint == PremiumApiConstants.leaseConfiguration) {
        return const FeatureTestReply(
          data: {
            'can_create': true,
            'templates': [
              {
                'id': 'template-a',
                'title': 'عقد سكني',
                'jurisdiction': 'EG',
                'language': 'ar',
                'version': '1',
              },
            ],
          },
        );
      }
      return repository.defaultReply(request);
    };
  });
  tearDown(() async {
    await injector.reset();
    AccountSession.end();
  });

  Future<void> actor(String id) => registerAuthenticatedTestAccount(
    user: UserModel(id: id, name: id, phone: '', email: '', isVerified: true),
  );
  void enable() => injector.registerSingleton<TenancyInvitationCapabilities>(
    const TenancyInvitationCapabilities(enabled: true),
  );
  void viewport(WidgetTester tester, double width) {
    tester.view.physicalSize = Size(width, 1000);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
  }

  Future<void> cleanup(WidgetTester tester) async {
    await tester.pumpWidget(const SizedBox.shrink());
    await tester.pump(const Duration(seconds: 6));
    await tester.pumpAndSettle();
  }

  testWidgets(
    'owner request details expose the invitation form without calling proposed APIs before enablement',
    (tester) async {
      viewport(tester, 390);
      await actor('owner-a');
      await mountFeatureTest(
        tester,
        const OwnerRequestDetailsScreen(requestId: 'visit-a'),
      );
      await tester.ensureVisible(find.text(LocaleKeys.tenancyInviteToRent));
      await tester.tap(find.text(LocaleKeys.tenancyInviteToRent));
      await tester.pumpAndSettle();
      expect(find.byType(TenancyInviteScreen), findsOneWidget);
      expect(find.text('أحمد محمد'), findsOneWidget);
      expect(find.text('شقة المعادي'), findsOneWidget);
      expect(
        find.text(LocaleKeys.tenancyInvitationsUnavailable),
        findsOneWidget,
      );
      final send = tester.widget<FilledButton>(
        filledButton(LocaleKeys.tenancySendInvitation),
      );
      expect(send.onPressed, isNull);
      expect(repository.requests.map((r) => r.endpoint), [
        ApiConstants.ownerVisitRequestDetails('visit-a'),
      ]);
      expect(network.requests, isEmpty);
      await cleanup(tester);
    },
  );

  for (final workspace in AppWorkspace.values) {
    testWidgets('$workspace Contracts opens the gated invitation history', (
      tester,
    ) async {
      viewport(tester, 390);
      await mountFeatureTest(
        tester,
        Scaffold(body: ContractsJourneyActions(workspace: workspace)),
      );
      await tester.tap(find.text(LocaleKeys.tenancyInvitations));
      await tester.pumpAndSettle();
      expect(find.byType(TenancyInvitationsScreen), findsOneWidget);
      expect(
        find.text(LocaleKeys.tenancyInvitationsUnavailable),
        findsOneWidget,
      );
      expect(repository.requests, isEmpty);
      expect(network.requests, isEmpty);
      await cleanup(tester);
    });
  }

  testWidgets(
    'owner sends, tenant accepts from Contracts, owner proceeds to the existing lease draft and tenant picker',
    (tester) async {
      viewport(tester, 390);
      enable();
      await actor('owner-a');
      await mountFeatureTest(
        tester,
        const OwnerRequestDetailsScreen(requestId: 'visit-a'),
      );
      await tester.ensureVisible(find.text(LocaleKeys.tenancyInviteToRent));
      await tester.tap(find.text(LocaleKeys.tenancyInviteToRent));
      await tester.pumpAndSettle();
      await tester.tap(find.text(LocaleKeys.tenancySendInvitation));
      await tester.pumpAndSettle();
      expect(find.byType(TenancyInvitationDetailScreen), findsOneWidget);
      expect(find.text(LocaleKeys.tenancyInvitationPending), findsOneWidget);
      expect(find.byType(TenancyInvitationResponseActions), findsNothing);
      final create = repository.requests.firstWhere(
        (r) => r.endpoint == TenancyInvitationApi.collection,
      );
      expect(create.body['property_id'], 'property-a');
      expect(create.body['tenant_id'], 'tenant-a');
      expect(remote['status'], 'pending');
      expect(remote['eligible_for_lease'], isFalse);
      await cleanup(tester);

      await actor('tenant-a');
      network.page = {
        'results': [remote],
        'count': 1,
        'per_page': 20,
        'total_pages': 1,
      };
      await mountFeatureTest(
        tester,
        const Scaffold(
          body: ContractsJourneyActions(workspace: AppWorkspace.tenant),
        ),
      );
      await tester.tap(find.text(LocaleKeys.tenancyInvitations));
      await tester.pumpAndSettle();
      expect(find.byType(TenancyInvitationCard), findsOneWidget);
      await tester.tap(find.byType(TenancyInvitationCard));
      await tester.pumpAndSettle();
      await tester.ensureVisible(find.text(LocaleKeys.tenancyAcceptInvitation));
      await tester.tap(find.text(LocaleKeys.tenancyAcceptInvitation));
      await tester.pumpAndSettle();
      await tester.tap(
        find.descendant(
          of: find.byType(AlertDialog),
          matching: filledButton(LocaleKeys.tenancyAcceptInvitation),
        ),
      );
      await tester.pumpAndSettle();
      expect(remote['status'], 'accepted');
      expect(remote['eligible_for_lease'], isTrue);
      expect(find.text(LocaleKeys.tenancyInvitationAccepted), findsOneWidget);
      expect(find.text(LocaleKeys.tenancyAcceptInvitation), findsNothing);
      await cleanup(tester);

      await actor('owner-a');
      await mountFeatureTest(
        tester,
        const TenancyInvitationDetailScreen(
          invitationId: 'invitation-a',
          workspace: AppWorkspace.owner,
        ),
      );
      await tester.ensureVisible(find.text(LocaleKeys.paidCreateLease));
      await tester.tap(find.text(LocaleKeys.paidCreateLease));
      await tester.pumpAndSettle();
      expect(find.byType(LeaseDraftScreen), findsOneWidget);
      expect(
        tester
            .widget<LeaseDraftScreen>(find.byType(LeaseDraftScreen))
            .property
            ?.id,
        'property-a',
      );
      expect(
        tester
            .widget<LeaseTenantSelector>(find.byType(LeaseTenantSelector))
            .propertyId,
        'property-a',
      );
      network.page = {
        'results': [
          {'id': 'tenant-a', 'display_name': 'أحمد محمد'},
        ],
        'count': 1,
        'per_page': 20,
        'total_pages': 1,
      };
      await tester.ensureVisible(find.text(LocaleKeys.paidLeaseTenant));
      await tester.tap(find.text(LocaleKeys.paidLeaseTenant));
      await tester.pumpAndSettle();
      expect(network.requests.last.path, PremiumApiConstants.leaseTenants);
      expect(
        network.requests.last.queryParameters?['property_id'],
        'property-a',
      );
      await tester.tap(find.text('أحمد محمد'));
      await tester.pumpAndSettle();
      expect(
        tester
            .widget<LeaseTenantSelector>(find.byType(LeaseTenantSelector))
            .tenant
            ?.id,
        'tenant-a',
      );
      await cleanup(tester);
    },
  );

  testWidgets(
    'tenant rejection refreshes status and removes response controls',
    (tester) async {
      viewport(tester, 390);
      enable();
      await actor('tenant-a');
      await mountFeatureTest(
        tester,
        const TenancyInvitationDetailScreen(
          invitationId: 'invitation-a',
          workspace: AppWorkspace.tenant,
        ),
      );
      await tester.ensureVisible(find.text(LocaleKeys.tenancyRejectInvitation));
      await tester.tap(find.text(LocaleKeys.tenancyRejectInvitation));
      await tester.pumpAndSettle();
      await tester.tap(
        find.descendant(
          of: find.byType(AlertDialog),
          matching: filledButton(LocaleKeys.tenancyRejectInvitation),
        ),
      );
      await tester.pumpAndSettle();
      expect(find.text(LocaleKeys.tenancyInvitationRejected), findsOneWidget);
      expect(find.text(LocaleKeys.tenancyAcceptInvitation), findsNothing);
      expect(remote['eligible_for_lease'], isFalse);
      await cleanup(tester);
    },
  );

  testWidgets('cached tenant details show the history but disable responses', (
    tester,
  ) async {
    viewport(tester, 390);
    enable();
    await actor('tenant-a');
    repository.handler = (_) async => FeatureTestReply(
      data: {
        ...remote,
        'actions': {'can_respond': true},
      },
      key: 'fromCache',
    );
    await mountFeatureTest(
      tester,
      const TenancyInvitationDetailScreen(
        invitationId: 'invitation-a',
        workspace: AppWorkspace.tenant,
      ),
    );
    expect(find.text(LocaleKeys.tenancyFreshRequired), findsOneWidget);
    expect(
      tester
          .widget<FilledButton>(
            filledButton(LocaleKeys.tenancyAcceptInvitation),
          )
          .onPressed,
      isNull,
    );
    expect(repository.requests, hasLength(1));
    await cleanup(tester);
  });

  testWidgets('expired pending invitations have no tenant response controls', (
    tester,
  ) async {
    viewport(tester, 390);
    enable();
    await actor('tenant-a');
    remote = {
      ...remote,
      'created_at': '2000-01-01T00:00:00Z',
      'expires_at': '2001-01-01T00:00:00Z',
    };
    await mountFeatureTest(
      tester,
      const TenancyInvitationDetailScreen(
        invitationId: 'invitation-a',
        workspace: AppWorkspace.tenant,
      ),
    );
    expect(find.text(LocaleKeys.tenancyInvitationExpired), findsOneWidget);
    expect(find.text(LocaleKeys.tenancyAcceptInvitation), findsNothing);
    await cleanup(tester);
  });

  testWidgets('an enabled empty history has the feature empty state', (
    tester,
  ) async {
    enable();
    await actor('tenant-a');
    await mountFeatureTest(
      tester,
      const TenancyInvitationsScreen(workspace: AppWorkspace.tenant),
    );
    expect(find.byType(TenancyInvitationsEmptyState), findsOneWidget);
    expect(find.text(LocaleKeys.tenancyInvitationsEmpty), findsOneWidget);
    await cleanup(tester);
  });

  test(
    'new invitation routes use the account gate and notifications select the correct workspace',
    () {
      expect(
        VerifiedFeatureRoutes.requiresVerification(
          const TenancyInviteScreen(
            propertyId: 'p',
            propertyTitle: '',
            tenantId: 't',
            tenantName: '',
          ),
        ),
        isTrue,
      );
      expect(
        VerifiedFeatureRoutes.requiresVerification(
          const TenancyInvitationDetailScreen(
            invitationId: 'i',
            workspace: AppWorkspace.tenant,
          ),
        ),
        isTrue,
      );
      expect(
        VerifiedFeatureRoutes.requiresVerification(
          const TenancyInvitationsScreen(workspace: AppWorkspace.owner),
        ),
        isTrue,
      );
      for (final workspace in AppWorkspace.values) {
        final notification = AppNotificationContent.fromPushPayload({
          'notification_type': workspace.isOwner
              ? 'tenancy_invitation_response'
              : 'tenancy_invitation',
          'action_type': 'open_tenancy_invitation',
          'target_id': 'invitation-a',
          'workspace': workspace.name,
        });
        expect(
          notification.kind,
          workspace.isOwner
              ? AppNotificationKind.tenancyInvitationResponse
              : AppNotificationKind.tenancyInvitation,
        );
        expect(notification.primaryTargetId, 'invitation-a');
        expect(
          NotificationDestination.resolve(notification).workspace,
          workspace,
        );
        expect(
          AppNotificationContent.fromJson(
            notification.toJson(),
          ).payload.workspace,
          workspace.name,
        );
      }
    },
  );

  testWidgets(
    'changed accommodation blocks sending until the owner reviews and selects the refreshed offer',
    (tester) async {
      viewport(tester, 390);
      enable();
      await actor('owner-a');
      final originalHandler = repository.handler!;
      var reads = 0;
      final changed = bedOffer.copyWith(revision: bedOffer.revision + 1);
      repository.handler = (request) async {
        if (request.endpoint == ApiConstants.propertyDetails('property-a')) {
          reads++;
          return FeatureTestReply(
            data: rentalProperty(
              inventory: rentalInventory(
                offers: [reads == 1 ? bedOffer : changed],
              ),
            ).toJson(),
          );
        }
        if (request.endpoint == TenancyInvitationApi.collection) {
          return FeatureTestReply(
            data: invitationJson(
              owner: 'owner-a',
              tenant: 'tenant-a',
              selection: RentalSelection.fromOffer(
                propertyId: 'property-a',
                inventory: rentalInventory(offers: [changed]),
                offer: changed,
              ),
            ),
          );
        }
        return originalHandler(request);
      };
      await mountFeatureTest(
        tester,
        const TenancyInviteScreen(
          propertyId: 'property-a',
          propertyTitle: '',
          tenantId: 'tenant-a',
          tenantName: 'أحمد محمد',
        ),
      );
      final offer = find
          .descendant(
            of: find.byType(RentalOfferPicker),
            matching: find.byType(ListTile),
          )
          .first;
      await tester.ensureVisible(offer);
      await tester.tap(offer);
      await tester.pumpAndSettle();
      final send = filledButton(LocaleKeys.tenancySendInvitation);
      await tester.ensureVisible(send);
      await tester.tap(send);
      await tester.pumpAndSettle();
      expect(
        repository.requests.where(
          (request) => request.endpoint == TenancyInvitationApi.collection,
        ),
        isEmpty,
      );
      expect(tester.widget<FilledButton>(send).onPressed, isNull);
      await tester.ensureVisible(offer);
      await tester.tap(offer);
      await tester.pumpAndSettle();
      await tester.ensureVisible(send);
      expect(tester.widget<FilledButton>(send).onPressed, isNotNull);
      await tester.tap(send);
      await tester.pumpAndSettle();
      expect(
        repository.requests
            .singleWhere(
              (request) => request.endpoint == TenancyInvitationApi.collection,
            )
            .body['expected_offer_revision'],
        changed.revision,
      );
      expect(tester.takeException(), isNull);
      await cleanup(tester);
    },
  );

  for (final locale in ['ar', 'en']) {
    for (final width in [320.0, 390.0, 600.0, 768.0, 1024.0, 1366.0]) {
      for (final scale in [1.0, 1.3, 2.0]) {
        final size = (width, scale);
        testWidgets(
          'invitation form and tenant review fit $locale width ${size.$1} scale ${size.$2}',
          (tester) async {
            viewport(tester, size.$1);
            await actor('owner-a');
            await tester.pumpWidget(
              featureTestHost(
                const RepaintBoundary(
                  child: TenancyInviteScreen(
                    propertyId: 'property-a',
                    propertyTitle: 'شقة المعادي بالقرب من المواصلات',
                    tenantId: 'tenant-a',
                    tenantName: 'أحمد محمد',
                  ),
                ),
                locale: locale,
                scale: size.$2,
                dark: size.$1 == 768,
              ),
            );
            await tester.pumpAndSettle();
            expect(tester.takeException(), isNull);
            if (locale == 'ar' && size.$1 == 390 && size.$2 == 1) {
              await exportPng(
                tester,
                '/private/tmp/darak-tenancy-invite-ar.png',
              );
            }
            await cleanup(tester);
            enable();
            await actor('tenant-a');
            await tester.pumpWidget(
              featureTestHost(
                const RepaintBoundary(
                  child: TenancyInvitationDetailScreen(
                    invitationId: 'invitation-a',
                    workspace: AppWorkspace.tenant,
                  ),
                ),
                locale: locale,
                scale: size.$2,
                dark: size.$1 == 768,
              ),
            );
            await tester.pumpAndSettle();
            await tester.ensureVisible(
              find.text(LocaleKeys.tenancyRejectInvitation),
            );
            await tester.pumpAndSettle();
            expect(tester.takeException(), isNull);
            expect(
              find.text(LocaleKeys.tenancyAcceptInvitation),
              findsOneWidget,
            );
            if (locale == 'en' && size.$1 == 390 && size.$2 == 1) {
              await exportPng(
                tester,
                '/private/tmp/darak-tenancy-response-en.png',
              );
            }
            await cleanup(tester);
          },
        );
      }
    }
  }
}

Future<void> exportPng(WidgetTester tester, String path) async {
  final boundary = tester.renderObject<RenderRepaintBoundary>(
    find.byType(RepaintBoundary).first,
  );
  await tester.runAsync(() async {
    final image = await boundary.toImage(pixelRatio: 1);
    final bytes = await image.toByteData(format: ui.ImageByteFormat.png);
    await File(path).writeAsBytes(bytes!.buffer.asUint8List());
    image.dispose();
  });
}

Finder filledButton(String label) => find.ancestor(
  of: find.text(label),
  matching: find.byWidgetPredicate((widget) => widget is FilledButton),
);
