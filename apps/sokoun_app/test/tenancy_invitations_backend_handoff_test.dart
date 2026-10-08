import 'dart:convert';
import 'dart:io';
import 'dart:typed_data';

import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart' show injector;
import 'package:melos_core/core/base_crud/code/data/base_data_imports.dart';
import 'package:melos_core/core/base_crud/code/domain/base_domain_imports.dart';
import 'package:melos_core/core/network/account_session.dart';
import 'package:melos_core/core/network/api_endpoints.dart';
import 'package:melos_core/core/network/dio_service.dart';
import 'package:melos_core/core/network/network_service.dart';
import 'package:sokoun_app/features/main_view/data/enums/app_workspace.dart';
import 'package:sokoun_app/features/owner/visits/imports.dart';
import 'package:sokoun_app/features/shared/notifications/data/enums/app_notification_kind.dart';
import 'package:sokoun_app/features/shared/notifications/data/models/app_notification_content.dart';
import 'package:sokoun_app/features/shared/notifications/data/notification_destination.dart';
import 'package:sokoun_app/features/shared/tenancy_invitations/data/enums/tenancy_invitation_status.dart';
import 'package:sokoun_app/features/shared/tenancy_invitations/data/models/create_tenancy_invitation_body.dart';
import 'package:sokoun_app/features/shared/tenancy_invitations/data/models/tenancy_invitation.dart';
import 'package:sokoun_app/features/shared/tenancy_invitations/data/tenancy_invitation_capabilities.dart';
import 'package:sokoun_app/features/shared/tenancy_invitations/data/tenancy_invitations_data.dart';
import 'package:sokoun_app/features/shared/tenancy_invitations/presentation/screens/tenancy_invitation_detail_screen.dart';
import 'package:sokoun_app/features/shared/tenancy_invitations/presentation/widgets/tenancy_invitation_labels.dart';
import 'helpers/feature_tools_test_dependencies.dart';
import 'helpers/tenancy_invitation_fixtures.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  late FeatureTestRepository repository;
  setUpAll(initializeFeatureTestEnvironment);
  setUp(() async {
    repository = FeatureTestRepository();
    await registerFeatureTestDependencies(repository);
    injector.registerSingleton<TenancyInvitationCapabilities>(
      const TenancyInvitationCapabilities(enabled: true),
    );
  });
  tearDown(() async {
    await injector.reset();
    AccountSession.end();
  });

  Future<void> cleanup(WidgetTester tester) async {
    await tester.pumpWidget(const SizedBox.shrink());
    await tester.pump(const Duration(seconds: 6));
    await tester.pumpAndSettle();
  }

  for (final source in [
    (status: 'pending', verified: true, visible: true),
    (status: 'confirmed', verified: true, visible: true),
    (status: 'rejected', verified: true, visible: false),
    (status: 'cancelled', verified: true, visible: false),
    (status: 'completed', verified: true, visible: false),
    (status: 'future_status', verified: true, visible: false),
    (status: '', verified: true, visible: false),
    (status: 'pending', verified: false, visible: false),
  ]) {
    testWidgets(
      '${source.status} visit with verified=${source.verified} follows the backend invitation source policy',
      (tester) async {
        final json = {
          'id': 'visit-a',
          if (source.status.isNotEmpty) 'status': source.status,
          'tenant': {
            'id': 'tenant-a',
            'name': 'Tenant',
            'is_verified': source.verified,
          },
          'property': {'id': 'property-a', 'title': 'Property'},
          'actions': {
            'can_accept': false,
            'can_reject': false,
            'can_chat': true,
          },
        };
        final model = OwnerVisitRequestDetailsContent.fromJson(json);
        expect(model.canInviteToLease, source.visible);
        expect(
          OwnerVisitRequestDetailsContent.fromJson(
            model.toJson(),
          ).canInviteToLease,
          source.visible,
        );
        repository.replies[ApiConstants.ownerVisitRequestDetails('visit-a')] =
            FeatureTestReply(data: json);
        await mountFeatureTest(
          tester,
          const OwnerRequestDetailsScreen(requestId: 'visit-a'),
        );
        expect(
          find.text(LocaleKeys.tenancyInviteToRent),
          source.visible ? findsOneWidget : findsNothing,
        );
        expect(tester.takeException(), isNull);
        await cleanup(tester);
      },
    );
  }

  test(
    'a cached confirmed source preserves its wire status and explicit transitions',
    () {
      final confirmed = OwnerVisitRequestDetailsContent.fromJson({
        'id': 'visit-a',
        'status': 'confirmed',
        'tenant': {'id': 'tenant-a', 'is_verified': true},
        'property': {'id': 'property-a'},
      });
      expect(confirmed.status, OwnerVisitRequestStatus.accepted);
      expect(confirmed.toJson()['status'], 'confirmed');
      expect(
        OwnerVisitRequestDetailsContent.fromJson(confirmed.toJson()),
        confirmed,
      );
      expect(
        confirmed
            .copyWith(status: OwnerVisitRequestStatus.rejected)
            .canInviteToLease,
        isFalse,
      );
      expect(
        confirmed.copyWith(statusValue: 'cancelled').status,
        OwnerVisitRequestStatus.canceled,
      );
    },
  );

  test(
    'backend lifecycle timestamps survive cache restoration and disable terminal actions',
    () {
      final respondedAt = DateTime.utc(2026, 10, 8, 10);
      for (final status in [
        TenancyInvitationStatus.rejected,
        TenancyInvitationStatus.revoked,
      ]) {
        final item = TenancyInvitation.fromJson({
          ...invitationJson(),
          'status': status.name,
          'revision': 2,
          'rejected_at': status == TenancyInvitationStatus.rejected
              ? respondedAt.toIso8601String()
              : null,
          'revoked_at': status == TenancyInvitationStatus.revoked
              ? respondedAt.toIso8601String()
              : null,
          'actions': {'can_respond': false},
        });
        expect(TenancyInvitation.fromJson(item.toJson()), item);
        expect(item.rejectedAt ?? item.revokedAt, respondedAt);
        expect(item.copyWith(revision: 3).rejectedAt, item.rejectedAt);
        expect(item.copyWith(revision: 3).revokedAt, item.revokedAt);
        expect(item.isEligible, isFalse);
        expect(item.canRespondAs(item.tenantId), isFalse);
      }
    },
  );

  testWidgets(
    'linked accepted history keeps its status after the invitation deadline',
    (tester) async {
      final item = TenancyInvitation.fromJson({
        ...invitationJson(),
        'status': 'accepted',
        'revision': 2,
        'created_at': '1999-10-08T09:00:00Z',
        'expires_at': '1999-10-15T09:00:00Z',
        'accepted_at': '1999-10-08T10:00:00Z',
        'lease_id': 'cancelled-draft-a',
        'eligible_for_lease': false,
        'actions': {'can_respond': false},
      });
      expect(item.hasValidIdentity, isTrue);
      expect(item.isEligible, isFalse);
      repository.replies[TenancyInvitationApi.detail(item.id)] =
          FeatureTestReply(data: item.toJson());
      await mountFeatureTest(
        tester,
        TenancyInvitationDetailScreen(
          invitationId: item.id,
          workspace: AppWorkspace.owner,
        ),
      );
      expect(find.text(LocaleKeys.tenancyInvitationAccepted), findsOneWidget);
      expect(find.text(LocaleKeys.tenancyInvitationExpired), findsNothing);
      expect(find.text(LocaleKeys.paidCreateLease), findsNothing);
      final unused = item.copyWith(leaseId: '');
      expect(
        TenancyInvitationLabels.status(unused),
        LocaleKeys.tenancyInvitationExpired,
      );
      await cleanup(tester);
    },
  );

  for (final workspace in AppWorkspace.values) {
    test(
      'flat ${workspace.name} notification data and projected detail actions retain the invitation target',
      () {
        final json = {
          'id': 'notification-a',
          'notification_type': workspace.isOwner
              ? 'tenancy_invitation_response'
              : 'tenancy_invitation',
          'data': {
            'workspace': workspace.name,
            'action_type': 'open_tenancy_invitation',
            'target_id': 'invitation-a',
            'action_label': 'Review invitation',
          },
        };
        final flat = AppNotificationContent.fromJson(json);
        expect(
          flat.kind,
          workspace.isOwner
              ? AppNotificationKind.tenancyInvitationResponse
              : AppNotificationKind.tenancyInvitation,
        );
        expect(flat.primaryActionType, 'open_tenancy_invitation');
        expect(flat.primaryTargetId, 'invitation-a');
        expect(NotificationDestination.resolve(flat).workspace, workspace);
        final cached = AppNotificationContent.fromJson(flat.toJson());
        expect(cached.payload, flat.payload);
        expect(cached.primaryTargetId, flat.primaryTargetId);
        expect(NotificationDestination.resolve(cached).workspace, workspace);
        final detail = AppNotificationContent.fromJson({
          ...json,
          'actions': {
            'primary': {
              'label': 'Review invitation',
              'action_type': 'open_tenancy_invitation',
              'target_id': 'invitation-from-detail',
            },
          },
        });
        expect(detail.primaryTargetId, 'invitation-from-detail');
        expect(
          flat.payload.copyWith(targetId: 'invitation-b').targetId,
          'invitation-b',
        );
      },
    );
  }

  for (final locale in ['ar', 'en']) {
    test(
      'Dio decodes the returned $locale envelopes, queries, and localized conflicts',
      () async {
        final directory = Directory.systemTemp.createTempSync(
          'tenancy-handoff-',
        );
        addTearDown(() => directory.deleteSync(recursive: true));
        final adapter = _HandoffAdapter(locale);
        final service = DioService(
          initialBaseUrl: 'https://api.example.com/api/v1/',
          initialLanguageCode: locale,
          cookieDirectoryProvider: () async => directory,
          httpClientAdapter: adapter,
        );
        await injector.unregister<BaseCrudUseCase>();
        await injector.unregister<NetworkService>();
        injector.registerSingleton<NetworkService>(service);
        final cache = _MemoryCache();
        injector.registerSingleton<BaseCrudUseCase>(
          BaseCrudUseCase(
            repository: BaseRepositoryImpl(
              baseRemoteDataSource: BaseRemoteDataSourceImpl(
                dioService: service,
              ),
              baseLocalDataSource: cache,
            ),
          ),
        );
        const body = CreateTenancyInvitationBody(
          propertyId: 'property-a',
          tenantId: 'tenant-a',
          requestKey: 'c347686e-65bd-4c81-8efb-ec3e5c0a71d2',
        );
        final created = await TenancyInvitationsData.create(body);
        expect(
          created.tryGetSuccess()?.data.status,
          TenancyInvitationStatus.pending,
        );
        expect(created.tryGetSuccess()?.msg, adapter.successMessage);
        expect(adapter.requests.last.method, 'POST');
        expect(
          adapter.requests.last.uri.path,
          '/api/v1/features/v1/tenancy-invitations/',
        );
        final detail = await TenancyInvitationsData.get(
          id: 'invitation-a',
          workspace: AppWorkspace.owner,
        );
        expect(detail.tryGetSuccess()?.data.hasValidIdentity, isTrue);
        expect(detail.tryGetSuccess()?.data.rejectedAt, isNull);
        expect(adapter.requests.last.uri.query, isEmpty);
        expect(cache.records.values.single, containsPair('revoked_at', null));
        final page = await TenancyInvitationsData.getPage(
          page: 2,
          workspace: AppWorkspace.owner,
          propertyId: 'property-a',
        );
        expect(page.$1.single.id, 'invitation-a');
        expect(page.$2.totalPages, 2);
        expect(adapter.requests.last.uri.queryParameters, {
          'workspace': 'owner',
          'property_id': 'property-a',
          'page': '2',
          'page_size': '20',
        });
        for (final status in [400, 403, 404, 409]) {
          adapter.status = status;
          final failed = await TenancyInvitationsData.create(body);
          expect(failed.tryGetError()?.message, adapter.errorMessage);
        }
        expect(
          adapter.requests.every(
            (request) =>
                request.headers[HttpHeaders.acceptLanguageHeader] == locale,
          ),
          isTrue,
        );
      },
    );
  }
}

class _MemoryCache implements BaseLocalDataSource {
  final Map<String, Map<String, dynamic>> records = {};
  @override
  Map<String, dynamic>? read(String key) => records[key];
  @override
  void save(String key, Map<String, dynamic> json) => records[key] = json;
}

class _HandoffAdapter implements HttpClientAdapter {
  _HandoffAdapter(this.locale);
  final String locale;
  int status = 200;
  final List<RequestOptions> requests = [];
  String get successMessage =>
      locale == 'ar' ? 'تم إنشاء الدعوة.' : 'Invitation created.';
  String get errorMessage => locale == 'ar'
      ? 'لم تعد الدعوة متاحة.'
      : 'This invitation is no longer available.';
  @override
  Future<ResponseBody> fetch(
    RequestOptions options,
    Stream<Uint8List>? requestStream,
    Future<void>? cancelFuture,
  ) async {
    requests.add(options);
    final item = {
      ...invitationJson(),
      'offer_id': '',
      'offer_snapshot': null,
      'actions': {'can_respond': false},
    };
    final data =
        options.method == 'GET' &&
            options.path == TenancyInvitationApi.collection
        ? {
            'results': [item],
            'count': 21,
            'per_page': 20,
            'total_pages': 2,
            'next': null,
            'previous': null,
          }
        : item;
    return ResponseBody.fromString(
      jsonEncode(
        status >= 400
            ? {'message': errorMessage}
            : {'key': 'success', 'msg': successMessage, 'data': data},
      ),
      status >= 400
          ? status
          : options.method == 'POST'
          ? 201
          : 200,
      headers: {
        Headers.contentTypeHeader: [Headers.jsonContentType],
        'content-language': [locale],
        'vary': ['Accept-Language'],
      },
    );
  }

  @override
  void close({bool force = false}) {}
}
