import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart' show injector;
import 'package:melos_core/core/base_crud/code/domain/usecases/pagination_response.dart';
import 'package:melos_core/core/helpers/cache_service.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/core/navigation/page_router/imports_page_router_builder.dart';
import 'package:melos_core/core/network/account_session.dart';
import 'package:melos_core/core/shared/models/user_models/user_model.dart';
import 'package:melos_core/core/shared/user_cubit/user_cubit.dart';
import 'package:multiple_result/multiple_result.dart';
import 'package:sokoun_app/features/main_view/data/account_access.dart';
import 'package:sokoun_app/features/main_view/data/enums/app_workspace.dart';
import 'package:sokoun_app/features/main_view/data/enums/workspace_tab.dart';
import 'package:sokoun_app/features/main_view/presentation/cubits/verified_action_cubit.dart';
import 'package:sokoun_app/features/main_view/presentation/models/home_tab.dart';
import 'package:sokoun_app/features/main_view/presentation/verified_feature_routes.dart';
import 'package:sokoun_app/features/main_view/presentation/widgets/verified_account_gate.dart';
import 'package:sokoun_app/features/owner/home/data/models/owner_add_property_content.dart';
import 'package:sokoun_app/features/owner/home/presentation/cubits/property_submission_cubit.dart';
import 'package:sokoun_app/features/owner/home/presentation/cubits/upload_property_images_cubit.dart';
import 'package:sokoun_app/features/owner/home/presentation/screens/owner_property_flow_screen.dart';
import 'package:sokoun_app/features/owner/visits/imports.dart';
import 'package:sokoun_app/features/shared/chat/data/chat_data.dart';
import 'package:sokoun_app/features/shared/chat/presentation/cubits/create_conversation_cubit.dart';
import 'package:sokoun_app/features/shared/chat/presentation/screens/start_conversation_screen.dart';
import 'package:sokoun_app/features/shared/premium/data/premium_api_constants.dart';
import 'package:sokoun_app/features/shared/premium/data/premium_api_data.dart';
import 'package:sokoun_app/features/shared/profile/imports.dart';
import 'package:sokoun_app/features/tenant/decision_tools/data/decision_tools_data.dart';
import 'package:sokoun_app/features/tenant/decision_tools/data/models/decision_notebook.dart';
import 'package:sokoun_app/features/tenant/decision_tools/presentation/cubits/decision_tools_cubit.dart';
import 'package:sokoun_app/features/tenant/visits/imports.dart';

import 'helpers/account_test_dependencies.dart';
import 'helpers/feature_tools_test_dependencies.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  late FeatureTestRepository repository;
  late FeatureTestNetwork network;
  late TestAccountCubit account;

  setUpAll(initializeFeatureTestEnvironment);
  setUp(() async {
    repository = FeatureTestRepository();
    network = FeatureTestNetwork();
    await registerFeatureTestDependencies(repository, network: network);
    account = injector<UserCubit>() as TestAccountCubit;
  });
  tearDown(() async {
    PageRouterBuilder().pageDecorator = null;
    await injector.reset();
    await CacheStorage.deleteAll();
    AccountSession.end();
  });

  test(
    'verification comes from the account flag and survives storage and edits',
    () {
      for (final Object? flag in [null, false, true, 'true', 1]) {
        final user = UserModel.fromJson({
          'user': {'id': '1', 'is_verified': true},
          if (flag != null) 'is_verified': flag,
        });
        expect(user.isVerified, flag == null || flag == true);
        expect(UserModel.fromJson(user.toJson()).isVerified, user.isVerified);
        expect(user.copyWith(name: 'Edited').isVerified, user.isVerified);
      }
      expect(UserModel.fromJson({'id': '1'}).isVerified, isFalse);
      expect(
        AccountContent.fromJson({
          'is_verified': false,
          'user': {'id': '1', 'is_verified': true},
          'menu_items': {
            'verification': {'is_verified': true},
          },
        }).identity.isVerified,
        isFalse,
      );
    },
    skip: UserModel.bypassVerification,
  );

  test(
    'unverified tenant and owner actions never call their repositories',
    () async {
      account.setVerified(false);
      bool succeeded = false;
      final conversation = CreateConversationCubit();
      final booking = BookVisitCubit();
      final submission = PropertySubmissionCubit();
      final upload = UploadPropertyImagesCubit();
      final visits = OwnerVisitStatusCubit();
      addTearDown(conversation.close);
      addTearDown(booking.close);
      addTearDown(submission.close);
      addTearDown(upload.close);
      addTearDown(visits.close);
      await conversation.createOrGet(
        userId: 'other',
        onSuccess: (_) => succeeded = true,
      );
      await booking.bookVisit(
        propertyId: 'property',
        visitDate: '2099-01-01',
        visitHour: 10,
        visitMinute: 0,
        note: '',
        onSuccess: () => succeeded = true,
      );
      await submission.save(
        form: OwnerAddPropertyFormState.initial(),
        onSuccess: (_) => succeeded = true,
      );
      await upload.uploadImages(
        propertyId: 'property',
        photos: const [],
        onPhotoUploaded: ({required photo, required image}) => succeeded = true,
        onSuccess: () => succeeded = true,
      );
      await visits.acceptVisitRequest(
        requestId: 'visit',
        onSuccess: () => succeeded = true,
      );
      expect(succeeded, isFalse);
      expect(repository.requests, isEmpty);
      for (final cubit in <VerifiedActionCubit<dynamic>>[
        conversation,
        booking,
        submission,
        upload,
        visits,
      ]) {
        expect(cubit.state.isError, isTrue);
        expect(cubit.state.msg, LocaleKeys.accountVerificationRequired);
      }
    },
  );

  test(
    'direct chat and newer feature requests also deny unverified accounts',
    () async {
      account.setVerified(false);
      await expectLater(ChatData.createConversation('other'), throwsStateError);
      await expectLater(
        ChatData.sendMessage(conversationId: 'thread', content: 'Hello'),
        throwsStateError,
      );
      final result = await PremiumApiData.mutate<Map<String, dynamic>>(
        endpoint: PremiumApiConstants.aiSuggestions,
        body: const {},
        fromJson: (json) => json,
        valid: (_) => true,
      );
      expect(
        result.tryGetError()?.message,
        LocaleKeys.accountVerificationRequired,
      );
      await expectLater(
        PremiumApiData.page(
          endpoint: PremiumApiConstants.leases,
          page: 1,
          fromJson: (json) => json,
        ),
        throwsStateError,
      );
      expect(repository.requests, isEmpty);
      expect(network.requests, isEmpty);
    },
  );

  test('local tools deny writes after verification is removed', () async {
    final store = _NotebookStore();
    final cubit = DecisionToolsCubit(accountId: account.user.id, store: store);
    addTearDown(cubit.close);
    await cubit.load();
    await cubit.saveDecision(
      const PropertyDecision(propertyId: 'one', title: 'One'),
    );
    expect(store.writes, 1);
    account.setVerified(false);
    await expectLater(
      cubit.saveDecision(
        const PropertyDecision(propertyId: 'two', title: 'Two'),
      ),
      throwsStateError,
    );
    expect(store.writes, 1);
  });

  testWidgets(
    'verified actions succeed and revoked in-flight actions cannot report success',
    (tester) async {
      await mountFeatureTest(tester, const Scaffold());
      final cubit = _ProtectedAction();
      addTearDown(cubit.close);
      expect(await cubit.run(), isTrue);
      expect(cubit.requests, 1);
      cubit.pending = Completer<void>();
      final operation = cubit.run();
      account.setVerified(false);
      cubit.pending!.complete();
      expect(await operation, isFalse);
      expect(cubit.state.isError, isTrue);
      expect(cubit.state.msg, LocaleKeys.accountVerificationRequired);
      await tester.pumpAndSettle();
      await tester.pump(const Duration(seconds: 5));
      await tester.pumpAndSettle();
    },
  );

  test('messages and visits are gated in both workspaces', () {
    final tabs = HomeTab.createWorkspaces();
    for (final workspace in AppWorkspace.values) {
      final messages = tabs[workspace]!.singleWhere(
        (tab) => tab.tab == WorkspaceTab.messages,
      );
      expect(messages.screen, isA<VerifiedAccountGate>());
      final visits = tabs[workspace]!.singleWhere(
        (tab) =>
            tab.tab ==
            (workspace == AppWorkspace.owner
                ? WorkspaceTab.requests
                : WorkspaceTab.visits),
      );
      expect(visits.screen, isA<VerifiedAccountGate>());
    }
  });

  testWidgets(
    'route gates stop chat creation and property editor initialization',
    (tester) async {
      account.setVerified(false);
      PageRouterBuilder().pageDecorator = VerifiedFeatureRoutes.wrap;
      await mountFeatureTest(tester, const Scaffold());
      for (final screen in [
        const StartConversationScreen(userId: 'other'),
        const OwnerPropertyFlowScreen(),
      ]) {
        unawaited(Go.to(screen));
        await tester.pumpAndSettle();
        expect(find.byType(screen.runtimeType), findsNothing);
        expect(
          find.text(LocaleKeys.accountVerificationRequiredTitle),
          findsOneWidget,
        );
        Go.back();
        await tester.pumpAndSettle();
      }
      expect(repository.requests, isEmpty);
      expect(network.requests, isEmpty);
    },
  );

  testWidgets(
    'verification changes mount and remove protected content immediately',
    (tester) async {
      account.setVerified(false);
      int mounts = 0;
      int disposals = 0;
      await mountFeatureTest(
        tester,
        VerifiedAccountGate(
          showBackButton: false,
          child: _ProtectedContent(
            onMount: () => mounts++,
            onDispose: () => disposals++,
          ),
        ),
      );
      expect(mounts, 0);
      account.setVerified(true);
      await tester.pumpAndSettle();
      expect(mounts, 1);
      account.setVerified(false);
      await tester.pumpAndSettle();
      expect(disposals, 1);
      expect(
        find.text(LocaleKeys.accountVerificationRequiredTitle),
        findsOneWidget,
      );
    },
  );

  for (final locale in ['ar', 'en']) {
    for (final width in [320.0, 390.0, 600.0, 768.0, 1024.0, 1366.0]) {
      testWidgets(
        'verification prompt fits $locale at $width with large text',
        (tester) async {
          account.setVerified(false);
          await tester.binding.setSurfaceSize(Size(width, 844));
          addTearDown(() => tester.binding.setSurfaceSize(null));
          await tester.pumpWidget(
            featureTestHost(
              const VerifiedAccountGate(
                showBackButton: false,
                child: SizedBox(),
              ),
              locale: locale,
              scale: 2,
            ),
          );
          await tester.pumpAndSettle();
          expect(tester.takeException(), isNull);
          expect(find.text(LocaleKeys.chatVerifyNow), findsOneWidget);
          expect(AccountAccess.isVerified, isFalse);
        },
      );
    }
  }
}

class _ProtectedAction extends VerifiedActionCubit<bool> {
  _ProtectedAction() : super(false);
  int requests = 0;
  Completer<void>? pending;
  Future<bool> run() async {
    bool succeeded = false;
    await executeAsyncWithBaseModel(
      operation: () async {
        requests++;
        await pending?.future;
        return Success(BaseModel(key: 'success', msg: '', data: true));
      },
      onSuccess: (_) => succeeded = true,
    );
    return succeeded;
  }
}

class _NotebookStore implements DecisionToolsStore {
  int writes = 0;
  @override
  Future<DecisionNotebook> read(String accountId) async =>
      const DecisionNotebook.initial();
  @override
  Future<void> write(String accountId, DecisionNotebook notebook) async =>
      writes++;
}

class _ProtectedContent extends StatefulWidget {
  const _ProtectedContent({required this.onMount, required this.onDispose});
  final VoidCallback onMount;
  final VoidCallback onDispose;
  @override
  State<_ProtectedContent> createState() => _ProtectedContentState();
}

class _ProtectedContentState extends State<_ProtectedContent> {
  @override
  void initState() {
    super.initState();
    widget.onMount();
  }

  @override
  void dispose() {
    widget.onDispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) =>
      const Scaffold(body: Text('Protected content'));
}
