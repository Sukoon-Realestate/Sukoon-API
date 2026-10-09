import 'package:toastification/toastification.dart';
import 'dart:async';
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
import 'package:melos_core/core/base_crud/code/domain/base_domain_imports.dart';
import 'package:melos_core/core/base_crud/code/domain/usecases/pagination_response.dart';
import 'package:melos_core/core/error/failure.dart';
import 'package:melos_core/core/helpers/cache_service.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/core/network/api_endpoints.dart';
import 'package:melos_core/core/network/network_request.dart';
import 'package:melos_core/core/network/network_service.dart';
import 'package:melos_core/core/shared/models/user_models/user_model.dart';
import 'package:melos_core/core/widgets/exeption_view.dart';
import 'package:multiple_result/multiple_result.dart';
import 'package:sokoun_app/features/main_view/data/enums/app_workspace.dart';
import 'package:sokoun_app/features/shared/notifications/data/enums/notification_role.dart';
import 'package:sokoun_app/features/shared/notifications/presentation/screens/notification_settings_screen.dart';
import 'package:sokoun_app/features/shared/profile/imports.dart';
import 'package:sokoun_app/features/shared/public_pages/data/enums/public_page.dart';
import 'package:sokoun_app/features/shared/public_pages/presentation/screens/public_page_screen.dart';
import 'package:sokoun_app/features/shared/support/imports.dart';
import 'package:sokoun_app/shared_widgets/sokoun_theme.dart';
import 'package:sokoun_app/shared_widgets/back_button.dart';

import 'helpers/account_test_dependencies.dart';
import 'helpers/collection_responses.dart';

const _user = UserModel(
  id: 'account',
  name: 'أحمد محمد',
  phone: '01012345678',
  email: 'account@example.invalid',
);
const _help = {
  'phone': '',
  'email': '',
  'hours': '',
  'faqs': [
    {
      'id': 'booking',
      'question': 'كيف أحجز زيارة للعقار؟',
      'answer': 'اختر العقار والموعد ثم أرسل طلب الزيارة.',
    },
    {
      'id': 'verification',
      'question': 'كيف أوثق حسابي؟',
      'answer': 'افتح ملفك الشخصي ثم حالة توثيق الهوية.',
    },
  ],
};
const _ticket = {
  'id': 'ticket-1',
  'reference': 'SUP-001',
  'subject': 'مشكلة في طلب الزيارة',
  'status': 'open',
  'created_at': '2026-10-03T10:15:00Z',
  'messages': [
    {
      'id': 'message-1',
      'sender': 'user',
      'body': 'أحتاج مساعدة في طلب الزيارة.',
      'created_at': '2026-10-03T10:15:00Z',
      'attachments': [],
    },
  ],
};

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  const output = String.fromEnvironment('ACCOUNT_UI_REVIEW_DIR');
  late _Repository repository;
  late _Network network;

  setUpAll(() async {
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(
          const MethodChannel('plugins.flutter.io/shared_preferences'),
          (call) async => call.method == 'getAll' ? <String, Object>{} : true,
        );
    await EasyLocalization.ensureInitialized();
    await CacheStorage.init();
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(
          const MethodChannel('dev.fluttercommunity.plus/connectivity'),
          (call) async => call.method == 'check' ? <String>['wifi'] : null,
        );
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(
          const MethodChannel('dev.fluttercommunity.plus/connectivity_status'),
          (_) async => null,
        );
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
  setUp(() async {
    toastification.managers.clear();
    await injector.reset();
    repository = _Repository();
    network = _Network();
    injector.registerSingleton<BaseCrudUseCase>(
      BaseCrudUseCase(repository: repository),
    );
    injector.registerSingleton<NetworkService>(network);
    await registerAuthenticatedTestAccount(user: _user);
  });
  tearDown(() => injector.reset());

  void viewport(
    WidgetTester tester, {
    double width = 390,
    double height = 844,
  }) {
    tester.view.physicalSize = Size(width, height);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.reset);
  }

  Future<void> mount(
    WidgetTester tester,
    Widget screen, {
    String locale = 'ar',
    double scale = 1,
  }) async {
    await tester.pumpWidget(_app(screen, locale: locale, scale: scale));
    await tester.pumpAndSettle();
    toastification.dismissAll(delayForAnimation: false);
    await tester.pump(const Duration(seconds: 1));
  }

  test('new response models preserve all data across cache serialization', () {
    final help = SupportHelpContent.fromJson(_help);
    final ticket = SupportTicketContent.fromJson(_ticket);
    expect(SupportHelpContent.fromJson(help.toJson()), help);
    expect(SupportTicketContent.fromJson(ticket.toJson()), ticket);
    final message = SupportMessage.fromJson({
      ...(_ticket['messages'] as List).first as Map,
      'attachments': [
        {
          'id': 'image-1',
          'name': 'screen.png',
          'url': 'https://example.invalid/screen.png',
        },
      ],
    });
    expect(SupportMessage.fromJson(message.toJson()), message);
    final verification = ProfileVerificationContent.fromJson({
      'status': 'rejected',
      'rejection_reason': 'صورة غير واضحة',
    });
    expect(
      ProfileVerificationContent.fromJson(verification.toJson()),
      verification,
    );
    expect(verification.status.canSubmit, isTrue);
    expect(
      ProfileVerificationContent.fromJson({'status': 'future_status'}).status,
      ProfileVerificationStatus.unknown,
    );
    final contract = ProfileContractContent.fromJson({
      'id': 'contract-1',
      'property_title': 'شقة',
      'status': 'active',
    });
    expect(ProfileContractContent.fromJson(contract.toJson()), contract);
  });

  test(
    'complaint categories follow the current workspace and preserve file bodies',
    () {
      expect(
        SupportTopic.forWorkspace(AppWorkspace.tenant),
        contains(SupportTopic.reportOwner),
      );
      expect(
        SupportTopic.forWorkspace(AppWorkspace.tenant),
        isNot(contains(SupportTopic.reportTenant)),
      );
      expect(
        SupportTopic.forWorkspace(AppWorkspace.owner),
        contains(SupportTopic.reportTenant),
      );
      final image = File('/tmp/support-image.png');
      final body =
          const SupportTicketBody.initial(
            workspace: AppWorkspace.owner,
          ).copyWith(
            topic: SupportTopic.reportTenant,
            subject: ' Subject ',
            description: ' Details ',
            attachments: [image],
          );
      expect(body.toJson(), {
        'workspace': 'owner',
        'category': 'report_tenant',
        'subject': 'Subject',
        'description': 'Details',
        'attachments': [image],
      });
    },
  );

  test(
    'GET contracts include stable resource dimensions and both cache serializers',
    () async {
      final help = SupportHelpCubit();
      final ticket = SupportTicketCubit();
      final verification = ProfileVerificationCubit();
      addTearDown(help.close);
      addTearDown(ticket.close);
      addTearDown(verification.close);
      await help.load(workspace: AppWorkspace.owner, language: 'ar');
      await ticket.load(id: 'ticket-1', workspace: AppWorkspace.tenant);
      await verification.load();
      expect(repository.requests.map((request) => request.cacheKey), [
        'support_help_owner_ar',
        'support_ticket_tenant_ticket-1',
        'profile_verification_status_v1',
      ]);
      for (final dynamic request in repository.requests) {
        expect(request.fromCacheJson, isNotNull);
        expect(request.toJson, isNotNull);
      }
      expect(repository.requests.first.queryParameters, {
        'workspace': 'owner',
        'lang': 'ar',
      });
    },
  );

  for (final role in AppWorkspace.values) {
    testWidgets(
      '${role.name} Profile has shared account actions and only its role activity',
      (tester) async {
        viewport(tester);
        await mount(tester, ProfileScreen(workspace: role, user: _user));
        expect(find.text(LocaleKeys.profile), findsOneWidget);
        expect(find.byType(ProfileHeaderCard), findsOneWidget);
        expect(find.text(LocaleKeys.toolsTitle), findsNothing);
        expect(find.byIcon(Icons.apps_outlined), findsNothing);
        expect(find.byType(ProfileVerificationTile), findsOneWidget);
        expect(find.byIcon(Icons.settings_outlined), findsOneWidget);
        expect(find.byIcon(Icons.support_agent_rounded), findsOneWidget);
        expect(find.byIcon(Icons.calendar_month_outlined), findsNothing);
        expect(find.byIcon(Icons.language_rounded), findsNothing);
        expect(find.byType(ProfileLogoutButton), findsNothing);
        expect(find.byType(ProfileDeleteAccountButton), findsNothing);

        final edit = find.ancestor(
          of: find.text(LocaleKeys.profileEditAction),
          matching: find.byWidgetPredicate(
            (widget) => widget is OutlinedButton,
          ),
        );
        expect(edit, findsOneWidget);
        expect(tester.getSize(edit).height, greaterThanOrEqualTo(48));
        await tester.tap(edit);
        await tester.pumpAndSettle();
        expect(
          tester
              .widget<ProfileEditScreen>(find.byType(ProfileEditScreen))
              .workspace,
          role,
        );
        expect(find.byType(ProfileEditView), findsOneWidget);
        Go.back();
        await tester.pumpAndSettle();

        await tester.scrollUntilVisible(
          find.byType(
            role.isOwner ? OwnerProfileActions : TenantProfileActions,
          ),
          200,
          scrollable: find
              .descendant(
                of: find.byType(ProfileContentView),
                matching: find.byType(Scrollable),
              )
              .first,
        );
        expect(
          find.byIcon(Icons.account_balance_wallet_outlined),
          role.isOwner ? findsOneWidget : findsNothing,
        );
        expect(
          find.byIcon(Icons.description_outlined),
          role.isTenant ? findsOneWidget : findsNothing,
        );
        expect(tester.takeException(), isNull);
      },
    );
    testWidgets(
      '${role.name} Profile keeps Settings and Support accessible after a profile failure',
      (tester) async {
        viewport(tester);
        repository.fail = true;
        await mount(tester, ProfileScreen(workspace: role, user: _user));
        expect(find.byType(ExceptionView), findsOneWidget);
        await tester.tap(find.byIcon(Icons.settings_outlined));
        await tester.pumpAndSettle();
        expect(
          tester
              .widget<ProfileSettingsScreen>(find.byType(ProfileSettingsScreen))
              .workspace,
          role,
        );
        Go.back();
        await tester.pumpAndSettle();
        repository.fail = false;
        await tester.tap(find.byIcon(Icons.support_agent_rounded));
        await tester.pumpAndSettle();
        expect(
          tester.widget<SupportScreen>(find.byType(SupportScreen)).workspace,
          role,
        );
        expect(tester.takeException(), isNull);
      },
    );
    testWidgets(
      '${role.name} Profile opens the shared verification flow with its workspace',
      (tester) async {
        viewport(tester);
        await mount(tester, ProfileScreen(workspace: role, user: _user));
        await tester.ensureVisible(find.byType(ProfileVerificationTile));
        await tester.tap(find.byIcon(Icons.verified_user_outlined));
        await tester.pumpAndSettle();
        expect(
          tester
              .widget<ProfileVerificationScreen>(
                find.byType(ProfileVerificationScreen),
              )
              .workspace,
          role,
        );
        Go.back();
        await tester.pumpAndSettle();
        expect(find.byType(ProfileScreen), findsOneWidget);
        expect(
          repository.requests.where(
            (request) =>
                request.api ==
                (role.isOwner
                    ? ApiConstants.ownerProfile
                    : ApiConstants.getAccData),
          ),
          hasLength(1),
        );
        expect(tester.takeException(), isNull);
      },
    );
    testWidgets(
      '${role.name} Settings has no profile or activity duplicates and opens correct notifications',
      (tester) async {
        viewport(tester);
        await mount(tester, ProfileSettingsScreen(workspace: role));
        expect(find.byType(ProfileAccountDetailsCard), findsNothing);
        expect(find.byType(ProfileAvatar), findsNothing);
        expect(find.byIcon(Icons.verified_user_outlined), findsNothing);
        expect(repository.requests, isEmpty);
        await tester.tap(find.byIcon(Icons.notifications_outlined));
        await tester.pumpAndSettle();
        final screen = tester.widget<NotificationSettingsScreen>(
          find.byType(NotificationSettingsScreen),
        );
        expect(
          screen.role,
          role.isOwner ? NotificationRole.owner : NotificationRole.tenant,
        );
        expect(tester.takeException(), isNull);
      },
    );
    testWidgets(
      '${role.name} profile entry reaches support with the same workspace',
      (tester) async {
        viewport(tester);
        await mount(tester, ProfileScreen(workspace: role, user: _user));
        await tester.tap(find.byIcon(Icons.support_agent_rounded));
        await tester.pumpAndSettle();
        expect(
          tester.widget<SupportScreen>(find.byType(SupportScreen)).workspace,
          role,
        );
        expect(repository.requests.last.queryParameters, {
          'workspace': role.name,
          'lang': 'ar',
        });
        await tester.tap(find.text(LocaleKeys.supportNewTicket));
        await tester.pumpAndSettle();
        expect(
          find.text(
            role.isOwner
                ? LocaleKeys.supportTopicReportTenant
                : LocaleKeys.supportTopicReportOwner,
          ),
          findsOneWidget,
        );
        expect(
          find.text(
            role.isOwner
                ? LocaleKeys.supportTopicReportOwner
                : LocaleKeys.supportTopicReportTenant,
          ),
          findsNothing,
        );
      },
    );
  }

  testWidgets(
    'privacy renders only privacy preferences and commits after success',
    (tester) async {
      viewport(tester);
      await mount(
        tester,
        const ProfilePrivacyScreen(workspace: AppWorkspace.tenant),
      );
      expect(find.byType(SwitchListTile), findsNWidgets(2));
      await tester.tap(find.byType(SwitchListTile).first);
      await tester.pumpAndSettle();
      expect(repository.requests.last.httpRequestType, HttpRequestType.patch);
      expect(repository.requests.last.body, {
        'share_location_for_search': true,
      });
      expect(
        tester.widget<SwitchListTile>(find.byType(SwitchListTile).first).value,
        isTrue,
      );
    },
  );

  testWidgets(
    'password mismatch is rejected before network and success preserves exact credentials',
    (tester) async {
      viewport(tester);
      await mount(tester, const ProfileSettingsScreen());
      await tester.tap(find.byIcon(Icons.lock_outline_rounded));
      await tester.pumpAndSettle();
      final fields = find.byType(TextFormField);
      await tester.enterText(fields.at(0), ' old password ');
      await tester.enterText(fields.at(1), ' new password ');
      await tester.enterText(fields.at(2), 'mismatch');
      await tester.tap(find.text(LocaleKeys.settingsSavePassword));
      await tester.pumpAndSettle();
      expect(repository.requests, isEmpty);
      await tester.enterText(fields.at(2), ' new password ');
      await tester.tap(find.text(LocaleKeys.settingsSavePassword));
      await tester.pumpAndSettle();
      expect(repository.requests.single.body, {
        'current_password': ' old password ',
        'new_password': ' new password ',
        're_new_password': ' new password ',
      });
      expect(find.byType(ChangePasswordScreen), findsNothing);
      expect(find.byType(ProfileSettingsScreen), findsOneWidget);
    },
  );

  testWidgets(
    'help search and expansion survive a phone-to-tablet resize without another GET',
    (tester) async {
      viewport(tester);
      await mount(tester, const SupportScreen(workspace: AppWorkspace.tenant));
      await tester.enterText(find.byType(TextFormField), 'زيارة');
      await tester.pumpAndSettle();
      expect(find.text('كيف أحجز زيارة للعقار؟'), findsOneWidget);
      expect(find.text('كيف أوثق حسابي؟'), findsNothing);
      await tester.tap(find.text('كيف أحجز زيارة للعقار؟'));
      await tester.pumpAndSettle();
      tester.view.physicalSize = const Size(1024, 768);
      await tester.pumpAndSettle();
      expect(
        find.text('اختر العقار والموعد ثم أرسل طلب الزيارة.'),
        findsOneWidget,
      );
      expect(repository.requests.length, 1);
      expect(tester.takeException(), isNull);
    },
  );

  testWidgets(
    'support ticket validates, suppresses duplicate submits and opens returned ID',
    (tester) async {
      viewport(tester);
      await mount(
        tester,
        const SupportNewTicketScreen(workspace: AppWorkspace.owner),
      );
      await tester.tap(find.text(LocaleKeys.supportSendTicket));
      await tester.pumpAndSettle();
      expect(repository.requests, isEmpty);
      await tester.enterText(find.byType(TextFormField).at(0), 'موضوع المشكلة');
      await tester.enterText(
        find.byType(TextFormField).at(1),
        'تفاصيل المشكلة التي تحتاج إلى متابعة.',
      );
      final pending = Completer<void>();
      repository.pending = pending;
      await tester.tap(find.text(LocaleKeys.supportSendTicket));
      await tester.pump();
      expect(repository.requests.length, 1);
      expect(
        tester
            .widget<AbsorbPointer>(
              find
                  .descendant(
                    of: find.byType(SupportTicketForm),
                    matching: find.byType(AbsorbPointer),
                  )
                  .first,
            )
            .absorbing,
        isTrue,
      );
      await tester.tap(
        find.text(LocaleKeys.supportSendTicket),
        warnIfMissed: false,
      );
      await tester.pump();
      expect(repository.requests.length, 1);
      pending.complete();
      await tester.pumpAndSettle();
      expect(repository.requests.first.body?['workspace'], 'owner');
      expect(
        tester
            .widget<SupportTicketDetailScreen>(
              find.byType(SupportTicketDetailScreen),
            )
            .id,
        'ticket-1',
      );
      expect(
        repository.requests.last.api,
        ApiConstants.supportTicket('ticket-1'),
      );
    },
  );

  testWidgets('failed ticket save preserves the draft and stays on the form', (
    tester,
  ) async {
    viewport(tester);
    repository.fail = true;
    await mount(
      tester,
      const SupportNewTicketScreen(workspace: AppWorkspace.tenant),
    );
    await tester.enterText(find.byType(TextFormField).at(0), 'موضوع المشكلة');
    await tester.enterText(
      find.byType(TextFormField).at(1),
      'تفاصيل المشكلة التي تحتاج إلى متابعة.',
    );
    await tester.tap(find.text(LocaleKeys.supportSendTicket));
    await tester.pumpAndSettle();
    expect(find.byType(SupportNewTicketScreen), findsOneWidget);
    expect(find.byType(SupportTicketDetailScreen), findsNothing);
    expect(
      tester
          .widget<TextFormField>(find.byType(TextFormField).first)
          .controller
          ?.text,
      'موضوع المشكلة',
    );
    expect(tester.takeException(), isNull);
  });

  testWidgets('failed privacy save preserves its previous value', (
    tester,
  ) async {
    viewport(tester);
    await mount(
      tester,
      const ProfilePrivacyScreen(workspace: AppWorkspace.owner),
    );
    repository.fail = true;
    await tester.tap(find.byType(SwitchListTile).first);
    await tester.pumpAndSettle();
    expect(
      tester.widget<SwitchListTile>(find.byType(SwitchListTile).first).value,
      isFalse,
    );
  });

  testWidgets(
    'resolved ticket removes reply and provides a new-ticket action',
    (tester) async {
      viewport(tester);
      repository.ticket = {..._ticket, 'status': 'resolved'};
      await mount(
        tester,
        const SupportTicketDetailScreen(
          id: 'ticket-1',
          workspace: AppWorkspace.tenant,
        ),
      );
      expect(find.byType(SupportTicketReply), findsNothing);
      expect(find.text(LocaleKeys.supportNewTicket), findsOneWidget);
      expect(find.text(LocaleKeys.supportStatusResolved), findsOneWidget);
    },
  );

  testWidgets(
    'reply uses the ticket endpoint and only clears after confirmed success',
    (tester) async {
      viewport(tester);
      await mount(
        tester,
        const SupportTicketDetailScreen(
          id: 'ticket-1',
          workspace: AppWorkspace.owner,
        ),
      );
      await tester.enterText(find.byType(TextFormField), ' متابعة المشكلة ');
      repository.fail = true;
      await tester.tap(find.text(LocaleKeys.supportSendReply));
      await tester.pumpAndSettle();
      expect(
        tester
            .widget<TextFormField>(find.byType(TextFormField))
            .controller
            ?.text,
        ' متابعة المشكلة ',
      );
      repository.fail = false;
      await tester.tap(find.text(LocaleKeys.supportSendReply));
      await tester.pumpAndSettle();
      expect(
        repository.requests.last.api,
        ApiConstants.supportTicketReplies('ticket-1'),
      );
      expect(repository.requests.last.body, {'body': 'متابعة المشكلة'});
      expect(
        tester
            .widget<TextFormField>(find.byType(TextFormField))
            .controller
            ?.text,
        isEmpty,
      );
    },
  );

  testWidgets(
    'successful empty help keeps ticket actions and uses its contextual empty state',
    (tester) async {
      viewport(tester);
      repository.help = const {'faqs': []};
      await mount(tester, const SupportScreen(workspace: AppWorkspace.tenant));
      expect(find.byType(SupportFaqEmptyState), findsOneWidget);
      expect(find.byType(ExceptionView), findsNothing);
      expect(find.text(LocaleKeys.supportNewTicket), findsOneWidget);
    },
  );

  testWidgets(
    'help error without cache is an exception, not a successful empty state',
    (tester) async {
      viewport(tester);
      repository.fail = true;
      await mount(tester, const SupportScreen(workspace: AppWorkspace.owner));
      expect(find.byType(ExceptionView), findsOneWidget);
      expect(find.byType(SupportFaqEmptyState), findsNothing);
      expect(find.text(LocaleKeys.supportNewTicket), findsOneWidget);
    },
  );

  testWidgets(
    'empty paginated tickets and contracts render their own empty states',
    (tester) async {
      viewport(tester);
      network.empty = true;
      await mount(
        tester,
        const SupportTicketsScreen(workspace: AppWorkspace.owner),
      );
      expect(find.byType(SupportTicketsEmptyState), findsOneWidget);
      expect(network.requests.single.queryParameters?['workspace'], 'owner');
      await tester.pumpWidget(const SizedBox.shrink());
      await tester.pumpAndSettle();
      await mount(tester, const ProfileContractsScreen());
      expect(find.byType(ProfileContractsEmptyState), findsOneWidget);
      expect(find.byType(ExceptionView), findsNothing);
    },
  );

  testWidgets(
    'search misses preserve query and clear action restores FAQ content',
    (tester) async {
      viewport(tester);
      await mount(tester, const SupportScreen(workspace: AppWorkspace.owner));
      await tester.enterText(find.byType(TextFormField), 'missing-query');
      await tester.pumpAndSettle();
      expect(find.text(LocaleKeys.supportSearchEmptyTitle), findsOneWidget);
      await tester.tap(find.text(LocaleKeys.supportClearSearch));
      await tester.pumpAndSettle();
      expect(find.byType(SupportFaqTile), findsNWidgets(2));
    },
  );

  testWidgets(
    'ticket refresh preserves a reply draft and disables sending during the read',
    (tester) async {
      viewport(tester);
      await mount(
        tester,
        const SupportTicketDetailScreen(
          id: 'ticket-1',
          workspace: AppWorkspace.tenant,
        ),
      );
      await tester.enterText(find.byType(TextFormField), 'مسودة رد لم تكتمل');
      final pending = Completer<void>();
      repository.pending = pending;
      await tester.tap(find.byIcon(Icons.refresh_rounded));
      await tester.pump();
      expect(tester.widget<TextField>(find.byType(TextField)).readOnly, isTrue);
      expect(
        tester
            .widget<TextFormField>(find.byType(TextFormField))
            .controller
            ?.text,
        'مسودة رد لم تكتمل',
      );
      pending.complete();
      await tester.pumpAndSettle();
      expect(
        tester
            .widget<TextFormField>(find.byType(TextFormField))
            .controller
            ?.text,
        'مسودة رد لم تكتمل',
      );
      expect(
        tester.widget<TextField>(find.byType(TextField)).readOnly,
        isFalse,
      );
    },
  );

  testWidgets(
    'an incomplete create response preserves the draft and explains the failure',
    (tester) async {
      viewport(tester);
      repository.ticket = {..._ticket, 'id': ''};
      repository.message = 'Server could not create this ticket';
      await mount(
        tester,
        const SupportNewTicketScreen(workspace: AppWorkspace.tenant),
      );
      await tester.enterText(find.byType(TextFormField).at(0), 'موضوع المشكلة');
      await tester.enterText(
        find.byType(TextFormField).at(1),
        'تفاصيل المشكلة التي تحتاج إلى متابعة.',
      );
      await tester.tap(find.text(LocaleKeys.supportSendTicket));
      await tester.pump();
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 250));
      expect(find.text(repository.message), findsOneWidget);
      expect(find.text(LocaleKeys.supportInvalidResponse), findsNothing);
      await tester.pumpAndSettle();
      expect(find.byType(SupportTicketDetailScreen), findsNothing);
      expect(
        tester
            .widget<TextFormField>(find.byType(TextFormField).first)
            .controller
            ?.text,
        'موضوع المشكلة',
      );
    },
  );

  testWidgets('unknown ticket status cannot accept replies', (tester) async {
    viewport(tester);
    repository.ticket = {..._ticket, 'status': 'future_status'};
    await mount(
      tester,
      const SupportTicketDetailScreen(
        id: 'ticket-1',
        workspace: AppWorkspace.owner,
      ),
    );
    expect(find.byType(SupportTicketReply), findsNothing);
    expect(find.text(LocaleKeys.supportStatusUnknown), findsOneWidget);
  });

  testWidgets('English help uses its own language and cache identity', (
    tester,
  ) async {
    viewport(tester);
    await mount(
      tester,
      const SupportScreen(workspace: AppWorkspace.owner),
      locale: 'en',
    );
    expect(repository.requests.single.queryParameters, {
      'workspace': 'owner',
      'lang': 'en',
    });
    expect(repository.requests.single.cacheKey, 'support_help_owner_en');
  });

  for (final status in [
    'incomplete',
    'pending',
    'approved',
    'rejected',
    'unknown',
  ]) {
    testWidgets('verification $status exposes only valid upload actions', (
      tester,
    ) async {
      viewport(tester);
      repository.verification = {
        'status': status,
        'full_name': _user.name,
        'rejection_reason': status == 'rejected' ? 'صورة غير واضحة' : '',
      };
      await mount(
        tester,
        const ProfileVerificationScreen(workspace: AppWorkspace.owner),
      );
      expect(
        find.text(LocaleKeys.uploadDocuments),
        status == 'incomplete' || status == 'rejected'
            ? findsOneWidget
            : findsNothing,
      );
      if (status == 'rejected') {
        expect(find.text('صورة غير واضحة'), findsOneWidget);
      }
      if (status == 'unknown') {
        expect(
          find.text(LocaleKeys.profileVerificationUnknownDescription),
          findsOneWidget,
        );
      }
    });
  }

  testWidgets('empty privacy success uses its own empty state', (tester) async {
    viewport(tester);
    repository.settings = {};
    await mount(
      tester,
      const ProfilePrivacyScreen(workspace: AppWorkspace.tenant),
    );
    expect(find.byType(ProfileSettingsEmptyState), findsOneWidget);
    expect(find.byType(SwitchListTile), findsNothing);
    expect(find.byType(ExceptionView), findsNothing);
  });

  testWidgets(
    'failed paginated reads remain errors for tickets and contracts',
    (tester) async {
      viewport(tester);
      network.fail = true;
      await mount(
        tester,
        const SupportTicketsScreen(workspace: AppWorkspace.tenant),
      );
      expect(find.byType(ExceptionView), findsOneWidget);
      expect(find.byType(SupportTicketsEmptyState), findsNothing);
      await tester.pumpWidget(const SizedBox.shrink());
      await tester.pumpAndSettle();
      await mount(tester, const ProfileContractsScreen());
      expect(find.byType(ExceptionView), findsOneWidget);
      expect(find.byType(ProfileContractsEmptyState), findsNothing);
    },
  );

  const mainScreens = [
    'profile_tenant',
    'profile_owner',
    'settings_tenant',
    'settings_owner',
    'support_tenant',
    'support_owner',
    'edit_tenant',
    'edit_owner',
    'edit_error_tenant',
    'edit_error_owner',
  ];
  for (final width in [320.0, 390.0, 600.0, 768.0, 1024.0, 1366.0]) {
    for (final scale in [1.0, 1.3, 2.0]) {
      for (final locale in ['ar', 'en']) {
        for (final subject in mainScreens) {
          testWidgets('$subject $locale width $width scale $scale', (
            tester,
          ) async {
            viewport(tester, width: width, height: width >= 600 ? 768 : 844);
            if (subject.startsWith('edit_error')) {
              repository.fail = true;
              repository.failureMessage = locale == 'ar'
                  ? 'تعذر تحميل بيانات الحساب. حاول مرة أخرى.'
                  : 'Account details could not be loaded. Please try again.';
            }
            await mount(tester, _screen(subject), locale: locale, scale: scale);
            expect(tester.takeException(), isNull);
            if (output.isNotEmpty &&
                locale == 'ar' &&
                ((width == 390 && scale == 1) ||
                    (width == 768 && scale == 1) ||
                    (width == 320 && scale == 2))) {
              await _capture(
                tester,
                '$output/$subject-$locale-${width.toInt()}-${scale.toStringAsFixed(1)}.png',
              );
            }
          });
        }
      }
    }
  }
  for (final subject in mainScreens) {
    testWidgets('$subject Arabic landscape at large text', (tester) async {
      viewport(tester, width: 600, height: 360);
      repository.fail = subject.startsWith('edit_error');
      await mount(tester, _screen(subject), scale: 2);
      expect(tester.takeException(), isNull);
    });
  }
  for (final subject in [
    'new_ticket',
    'ticket_detail',
    'privacy',
    'password',
    'delete',
    'contracts',
    'terms',
    'about',
    'edit_tenant',
    'edit_owner',
    'edit_error_tenant',
    'edit_error_owner',
  ]) {
    for (final locale in ['ar', 'en']) {
      testWidgets('$subject $locale small phone, large text and keyboard', (
        tester,
      ) async {
        viewport(tester, width: 320);
        repository.fail = subject.startsWith('edit_error');
        await mount(tester, _screen(subject), locale: locale, scale: 2);
        expect(tester.takeException(), isNull);
        if (find.byType(TextFormField).evaluate().isNotEmpty) {
          tester.view.viewInsets = const FakeViewPadding(bottom: 280);
          await tester.pumpAndSettle();
          expect(tester.takeException(), isNull);
        }
        if (output.isNotEmpty && locale == 'ar') {
          tester.view.viewInsets = const FakeViewPadding();
          await tester.pumpAndSettle();
          await _capture(tester, '$output/$subject-$locale-320-2.0.png');
          await tester.pumpWidget(const SizedBox.shrink());
          tester.view.physicalSize = const Size(390, 844);
          await mount(tester, _screen(subject), locale: locale);
          await _capture(tester, '$output/$subject-$locale-390-1.0.png');
        }
      });
    }
  }

  for (final workspace in AppWorkspace.values) {
    testWidgets(
      '${workspace.name} pushed editor shows its back button after a read error',
      (tester) async {
        viewport(tester);
        await mount(tester, ProfileScreen(workspace: workspace, user: _user));
        repository.fail = true;
        repository.failureMessage = 'تعذر تحميل بيانات الحساب. حاول مرة أخرى.';
        await tester.tap(find.text(LocaleKeys.profileEditAction));
        await tester.pumpAndSettle();
        expect(find.byType(ProfileEditScreen), findsOneWidget);
        expect(
          find.text(LocaleKeys.profileEditDetailsUnavailable),
          findsOneWidget,
        );
        expect(find.text(LocaleKeys.ownerRetryAction), findsOneWidget);
        expect(tester.takeException(), isNull);
        if (output.isNotEmpty) {
          await _capture(
            tester,
            '$output/edit_route_error_${workspace.name}-ar-390-1.0.png',
          );
        }
        await tester.tap(find.byType(SokoonBackButton));
        await tester.pumpAndSettle();
        expect(find.byType(ProfileEditScreen), findsNothing);
        expect(find.byType(ProfileScreen), findsOneWidget);
        expect(tester.takeException(), isNull);
      },
    );
    testWidgets(
      '${workspace.name} edit loading stays visible on a small phone and tablet',
      (tester) async {
        viewport(tester, width: 390);
        final pending = Completer<void>();
        repository.pending = pending;
        await tester.pumpWidget(
          _app(
            ProfileEditScreen(initialValue: _user, workspace: workspace),
            locale: 'ar',
            scale: 1,
          ),
        );
        await tester.pump();
        await tester.pump(const Duration(milliseconds: 300));
        expect(find.byType(ProfileEditScreen), findsOneWidget);
        expect(find.text(LocaleKeys.profileEditLoadingDetails), findsOneWidget);
        expect(find.byType(FormField<ProfileGender>), findsNothing);
        expect(tester.takeException(), isNull);
        if (output.isNotEmpty) {
          await _capture(
            tester,
            '$output/edit_loading_${workspace.name}-ar-390-1.0.png',
          );
        }
        tester.view.physicalSize = const Size(768, 768);
        await tester.pump();
        expect(repository.requests, hasLength(1));
        expect(tester.takeException(), isNull);
        pending.complete();
        await tester.pumpAndSettle();
        expect(find.byType(FormField<ProfileGender>), findsOneWidget);
        expect(repository.requests, hasLength(1));
        expect(tester.takeException(), isNull);
      },
    );
  }
}

Widget _screen(String subject) => switch (subject) {
  'profile_tenant' => const ProfileScreen(
    workspace: AppWorkspace.tenant,
    user: _user,
  ),
  'profile_owner' => const ProfileScreen(
    workspace: AppWorkspace.owner,
    user: _user,
  ),
  'settings_tenant' => const ProfileSettingsScreen(),
  'settings_owner' => const ProfileSettingsScreen(
    workspace: AppWorkspace.owner,
  ),
  'support_tenant' => const SupportScreen(workspace: AppWorkspace.tenant),
  'support_owner' => const SupportScreen(workspace: AppWorkspace.owner),
  'edit_tenant' || 'edit_error_tenant' => const ProfileEditScreen(
    initialValue: _user,
    workspace: AppWorkspace.tenant,
  ),
  'edit_owner' || 'edit_error_owner' => const ProfileEditScreen(
    initialValue: _user,
    workspace: AppWorkspace.owner,
  ),
  'new_ticket' => const SupportNewTicketScreen(workspace: AppWorkspace.owner),
  'ticket_detail' => const SupportTicketDetailScreen(
    id: 'ticket-1',
    workspace: AppWorkspace.tenant,
  ),
  'privacy' => const ProfilePrivacyScreen(workspace: AppWorkspace.tenant),
  'password' => const ChangePasswordScreen(),
  'delete' => const ProfileDeleteAccountScreen(),
  'contracts' => const ProfileContractsScreen(),
  'terms' => const PublicPageScreen(page: PublicPage.terms),
  _ => const PublicPageScreen(page: PublicPage.aboutUs),
};

Widget _app(Widget screen, {required String locale, required double scale}) =>
    EasyLocalization(
      supportedLocales: const [Locale('ar'), Locale('en')],
      path: 'unused',
      assetLoader: const _Translations(),
      startLocale: Locale(locale),
      fallbackLocale: const Locale('ar'),
      saveLocale: false,
      child: ScreenUtilInit(
        designSize: const Size(360, 690),
        enableScaleWH: () => false,
        enableScaleText: () => false,
        fontSizeResolver: (size, _) => size.toDouble(),
        builder: (context, _) => MaterialApp(
          navigatorKey: Go.navigatorKey,
          theme: SokounTheme.light,
          locale: context.locale,
          localizationsDelegates: context.localizationDelegates,
          supportedLocales: context.supportedLocales,
          builder: (context, child) => MediaQuery(
            data: MediaQuery.of(context).copyWith(
              textScaler: TextScaler.linear(scale),
              disableAnimations: true,
            ),
            child: child!,
          ),
          home: RepaintBoundary(child: screen),
        ),
      ),
    );

Future<void> _capture(WidgetTester tester, String path) async {
  final boundary = tester.renderObject<RenderRepaintBoundary>(
    find.byType(RepaintBoundary).first,
  );
  await tester.runAsync(() async {
    final image = await boundary.toImage();
    final bytes = await image.toByteData(format: ui.ImageByteFormat.png);
    await File(path).parent.create(recursive: true);
    await File(path).writeAsBytes(bytes!.buffer.asUint8List());
    image.dispose();
  });
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

class _Repository implements BaseRepository {
  final List<CrudBaseParmas<dynamic>> requests = [];
  bool fail = false;
  String failureMessage = 'تعذّر حفظ الطلب';
  String message = '';
  Completer<void>? pending;
  Map<String, dynamic> help = Map.of(_help);
  Map<String, dynamic> ticket = Map.of(_ticket);
  Map<String, dynamic> settings = {
    'visit_notifications': true,
    'promotions_and_updates': true,
    'share_location_for_search': false,
    'show_profile_in_search': true,
  };
  Map<String, dynamic> verification = {
    'status': 'approved',
    'full_name': _user.name,
    'submitted_at': '',
    'rejection_reason': '',
  };
  @override
  Future<Result<BaseModel<T>, Failure>> crudCall<T>(
    CrudBaseParmas<T> params,
  ) async {
    requests.add(params);
    if (pending != null) await pending!.future;
    if (fail) return Error(ServerFailure(failureMessage));
    final Object payload = switch (params.api) {
      ApiConstants.getAccData => collectionResponseData(
        r'/profiles/my-account/$',
      ),
      ApiConstants.ownerProfile => collectionResponseData(
        r'/properties/owner/profile/$',
      ),
      ApiConstants.tenantAccountSummary => collectionResponseData(
        r'/profiles/account-summary/$',
      ),
      ApiConstants.userProfile => collectionResponseData(
        r'/profiles/user/my-profile/$',
      ),
      ApiConstants.supportHelpCenter => help,
      ApiConstants.supportTickets => ticket,
      ApiConstants.profileSettings => settings,
      ApiConstants.notificationSettings => {'id': 'settings', 'items': []},
      ApiConstants.verificationStatus => verification,
      ApiConstants.terms ||
      ApiConstants.aboutUs ||
      ApiConstants.privacyPolicy => {
        'slug': 'page',
        'title': 'عن سكون',
        'content':
            'سكون يساعدك في البحث عن العقارات وتنظيم الزيارات والتواصل مع الملاك.',
        'content_format': 'plain_text',
        'language': 'ar',
        'updated_at': '2026-10-03',
      },
      _ =>
        params.api.startsWith(ApiConstants.supportTickets) ? ticket : const {},
    };
    return Success(
      BaseModel<T>(key: 'success', msg: message, data: params.mapper!(payload)),
    );
  }

  @override
  Future<Result<List<T>, Failure>> getBaseIdAndNameEntity<T extends BaseEntity>(
    GetBaseEntityParams? param,
  ) => throw UnimplementedError();
}

class _Network implements NetworkService {
  final List<NetworkRequest> requests = [];
  bool empty = false;
  bool fail = false;
  @override
  Future<BaseModel<T>> callApi<T>(
    NetworkRequest request, {
    T Function(dynamic)? mapper,
  }) async {
    requests.add(request);
    if (fail) throw Exception('Failed test read');
    final List<Map<String, dynamic>> results = empty
        ? []
        : request.path == ApiConstants.accountContracts
        ? [
            {
              'id': 'contract-1',
              'property_title': 'شقة في المعادي',
              'status': 'active',
              'start_date': '2026-10-01',
              'end_date': '2027-09-30',
              'document_url': '',
            },
          ]
        : [_ticket];
    final payload = {
      'count': results.length,
      'per_page': 20,
      'total_pages': 1,
      'next': null,
      'results': results,
    };
    return BaseModel<T>(key: 'success', msg: '', data: mapper!(payload));
  }

  @override
  Future<bool> hasSessionCookies() async => true;
  @override
  Future<void> clearSessionCookies() async {}
  @override
  Future<void> updateBaseUrl() async {}
}
