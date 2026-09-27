import 'dart:async';

import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/base_crud/code/presentation/cubit/base_cubit/async_cubit.dart';
import 'package:melos_core/core/base_crud/code/domain/usecases/pagination_response.dart';
import 'package:melos_core/core/helpers/cache_service.dart';
import 'package:melos_core/core/network/account_session.dart';
import 'package:melos_core/core/shared/models/user_models/user_model.dart';
import 'package:multiple_result/multiple_result.dart';
import 'package:sokoun_app/features/main_view/data/enums/app_workspace.dart';
import 'package:sokoun_app/features/main_view/data/enums/workspace_tab.dart';
import 'package:sokoun_app/features/main_view/data/workspace_preferences.dart';
import 'package:sokoun_app/features/main_view/presentation/cubits/workspace_cubit.dart';
import 'package:sokoun_app/features/shared/auth/data/models/register.dart';
import 'package:sokoun_app/features/shared/chat/presentation/cubits/start_chat.dart';
import 'package:sokoun_app/features/shared/notifications/data/models/app_notification_content.dart';
import 'package:sokoun_app/features/shared/notifications/data/notification_destination.dart';
import 'package:sokoun_app/features/tenant/visits/imports.dart';

import 'helpers/home_page_test_dependencies.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  const MethodChannel preferences = MethodChannel(
    'plugins.flutter.io/shared_preferences',
  );

  setUpAll(() async {
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(
          preferences,
          (call) async => call.method == 'getAll' ? <String, Object>{} : true,
        );
    await CacheStorage.init();
  });
  setUp(() async {
    await injector.reset();
    await CacheStorage.deleteAll();
    AccountSession.end();
    registerHomePageTestDependencies();
  });
  tearDown(() => injector.reset());
  tearDownAll(() {
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(preferences, null);
  });

  test(
    'account decoding is independent of device workspace and retains identity',
    () async {
      const Map<String, dynamic> json = {
        'id': 17,
        'full_name': 'One Account',
        'type': 'owner',
      };
      await CacheStorage.write('current_user_type', 'tenant');
      final UserModel first = UserModel.fromJson(json);
      await CacheStorage.write('current_user_type', 'owner');
      final UserModel second = UserModel.fromJson(json);
      expect(first.runtimeType, UserModel);
      expect(second.toJson(), first.toJson());
      expect(first.copyWith(name: 'Updated').id, '17');
      expect(first.copyWith(name: 'Updated').type, 'owner');
    },
  );

  test('registration does not assign an exclusive role', () {
    expect(RegisterBody.initial().toJson(), isNot(contains('type')));
  });

  test('legacy preference migrates only to its cached account, once', () async {
    await CacheStorage.write('user', {'id': 'old-owner', 'type': 'owner'});
    await CacheStorage.write('current_user_type', 'owner');
    await WorkspacePreferences.migrateLegacy();
    expect(WorkspacePreferences.read('old-owner'), AppWorkspace.owner);
    expect(WorkspacePreferences.read('new-account'), AppWorkspace.tenant);
    expect(CacheStorage.read('current_user_type'), isNull);
    await WorkspacePreferences.write('old-owner', AppWorkspace.tenant);
    await WorkspacePreferences.migrateLegacy();
    expect(WorkspacePreferences.read('old-owner'), AppWorkspace.tenant);
  });

  test(
    'an orphaned legacy role cannot become a new account preference',
    () async {
      await CacheStorage.write('current_user_type', 'owner');
      await WorkspacePreferences.migrateLegacy();
      expect(WorkspacePreferences.read('new-account'), AppWorkspace.tenant);
    },
  );

  test(
    'switching and restart preserve preference without changing account/session',
    () async {
      await CacheStorage.write('user', {'id': 'a', 'name': 'Shared account'});
      AccountSession.begin('a');
      final int generation = AccountSession.generation;
      final WorkspaceCubit cubit = WorkspaceCubit()..initialize('a');
      addTearDown(cubit.close);
      expect(cubit.state, AppWorkspace.tenant);
      await cubit.switchTo(AppWorkspace.owner);
      expect(cubit.state, AppWorkspace.owner);
      expect(AccountSession.generation, generation);
      expect(UserModel.currentUser?.id, 'a');
      cubit.reset();
      expect(cubit.state, AppWorkspace.tenant);
      cubit.initialize('b');
      expect(cubit.state, AppWorkspace.tenant);
      cubit.initialize('a');
      expect(cubit.state, AppWorkspace.owner);
      final WorkspaceCubit restarted = WorkspaceCubit()..initialize('a');
      addTearDown(restarted.close);
      expect(restarted.state, AppWorkspace.owner);
    },
  );

  test('guests cannot persist an owner workspace', () async {
    final WorkspaceCubit cubit = WorkspaceCubit();
    addTearDown(cubit.close);
    await cubit.switchTo(AppWorkspace.owner);
    expect(cubit.state, AppWorkspace.tenant);
  });

  test('private cache namespace follows account, not workspace', () {
    AccountSession.begin('a');
    final String aKey = AccountSession.cacheKey('owner_properties');
    AccountSession.begin('b');
    expect(AccountSession.cacheKey('owner_properties'), isNot(aKey));
    AccountSession.end();
    expect(AccountSession.cacheKey('owner_properties'), contains('guest'));
  });

  test(
    'late private response cannot emit or navigate after session changes',
    () async {
      AccountSession.begin('a');
      final _DelayedCubit cubit = _DelayedCubit();
      addTearDown(cubit.close);
      final Completer<void> response = Completer<void>();
      bool navigated = false;
      final Future<void> loading = cubit.load(
        response.future,
        () => navigated = true,
      );
      AccountSession.begin('b');
      response.complete();
      await loading;
      expect(cubit.data, 0);
      expect(navigated, isFalse);
    },
  );

  test(
    'notification context is derived from event, including ambiguous view_visit action',
    () {
      NotificationDestination resolve(String kind) =>
          NotificationDestination.resolve(
            AppNotificationContent.fromPushPayload({
              'notification_type': kind,
              'action_type': 'view_visit',
              'visit_id': 'visit-1',
            }),
          );
      expect(resolve('visit_request').workspace, AppWorkspace.owner);
      expect(resolve('visit_request').tab, WorkspaceTab.requests);
      expect(resolve('visit_accepted').workspace, AppWorkspace.tenant);
      expect(resolve('property_verified').workspace, AppWorkspace.owner);
      expect(resolve('property_update').workspace, AppWorkspace.tenant);
      expect(resolve('new_message').workspace, isNull);
      expect(resolve('new_message').tab, WorkspaceTab.messages);
      expect(resolve('account_verification').workspace, isNull);
      expect(resolve('unrecognized').workspace, isNull);
    },
  );

  test('self-chat and booking own property never submit', () async {
    await CacheStorage.write('user', {'id': 'a', 'name': 'Account'});
    final CreateConversationCubit chat = CreateConversationCubit();
    final BookVisitCubit booking = BookVisitCubit();
    addTearDown(chat.close);
    addTearDown(booking.close);
    bool submitted = false;
    await chat.createOrGet(userId: 'a', onSuccess: (_) => submitted = true);
    await booking.bookVisit(
      propertyId: 'p',
      ownerId: 'a',
      visitDate: '2026-10-01',
      visitHour: 10,
      visitMinute: 0,
      note: '',
      onSuccess: () => submitted = true,
    );
    expect(submitted, isFalse);
    expect(chat.state.isError, isTrue);
    expect(booking.state.isError, isTrue);
  });
}

class _DelayedCubit extends AsyncCubit<int> {
  _DelayedCubit() : super(0);

  Future<void> load(Future<void> response, void Function() onSuccess) =>
      executeAsyncWithBaseModel(
        operation: () async {
          await response;
          return Success(BaseModel<int>(key: '', msg: '', data: 7));
        },
        onSuccess: (_) => onSuccess(),
      );
}
