import 'dart:async';

import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/base_crud/code/domain/base_domain_imports.dart';
import 'package:melos_core/core/base_crud/code/domain/usecases/pagination_response.dart';
import 'package:melos_core/core/error/failure.dart';
import 'package:melos_core/core/helpers/cache_service.dart';
import 'package:melos_core/core/network/account_session.dart';
import 'package:melos_core/core/network/api_endpoints.dart';
import 'package:melos_core/core/network/network_request.dart';
import 'package:melos_core/core/network/network_service.dart';
import 'package:multiple_result/multiple_result.dart';
import 'package:sokoun_app/features/main_view/data/enums/app_workspace.dart';
import 'package:sokoun_app/features/main_view/presentation/cubits/workspace_counts_cubit.dart';
import 'package:sokoun_app/features/shared/chat/data/chat_realtime_service.dart';
import 'package:sokoun_app/features/shared/chat/data/chat_unread_refresh_bus.dart';
import 'package:sokoun_app/features/shared/chat/data/models/chat_socket_message.dart';
import 'package:sokoun_app/features/shared/chat/presentation/cubits/chat_unread_cubit.dart';
import 'package:sokoun_app/features/shared/notifications/data/foreground_notification_bus.dart';
import 'package:sokoun_app/features/shared/notifications/data/notification_refresh_bus.dart';
import 'package:sokoun_app/features/shared/notifications/presentation/cubits/unread_notifications_cubit.dart';

import 'helpers/account_test_dependencies.dart';
import 'helpers/home_page_test_dependencies.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  late _CountsRepository repository;
  late _Realtime realtime;
  late WorkspaceCountsCubit tenant;
  late WorkspaceCountsCubit owner;
  late UnreadNotificationsCubit notifications;
  late ChatUnreadCubit chat;

  setUpAll(() async {
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(
          const MethodChannel('plugins.flutter.io/shared_preferences'),
          (call) async => call.method == 'getAll' ? <String, Object>{} : true,
        );
    await CacheStorage.init();
  });

  setUp(() async {
    await injector.reset();
    await CacheStorage.deleteAll();
    registerHomePageTestDependencies();
    await injector.unregister<NetworkService>();
    injector.registerSingleton<NetworkService>(_AuthenticatedNetwork());
    await registerAuthenticatedTestAccount();
    repository = _CountsRepository();
    await injector.unregister<BaseCrudUseCase>();
    injector.registerSingleton<BaseCrudUseCase>(
      BaseCrudUseCase(repository: repository),
    );
    realtime = _Realtime();
    tenant = WorkspaceCountsCubit(AppWorkspace.tenant)..watch();
    owner = WorkspaceCountsCubit(AppWorkspace.owner)..watch();
    notifications = UnreadNotificationsCubit()..watchRefreshRequests();
    chat = ChatUnreadCubit(realtimeService: realtime);
  });

  tearDown(() async {
    await Future.wait([
      tenant.close(),
      owner.close(),
      notifications.close(),
      chat.close(),
    ]);
    await realtime.close();
    await injector.reset();
    AccountSession.end();
  });

  Future<void> load() => Future.wait([
    tenant.load(),
    owner.load(),
    notifications.loadUnreadCount(),
    chat.start(),
  ]);

  void receive(
    String type, {
    String? id,
    Map<String, dynamic> data = const {},
  }) {
    ForegroundNotificationBus.receive({
      'notification_type': type,
      if (id != null) 'notification_id': id,
      ...data,
    });
  }

  test('foreground types update only their badges without fetching', () async {
    await load();
    final int requests = repository.requests;
    receive('visit_request');
    expect(owner.data.visits, 5);
    expect(tenant.data.visits, 2);
    expect(tenant.data.favorites, 6);
    expect(notifications.data.count, 4);
    expect(chat.data.count, 7);

    receive('visit_accepted');
    expect(tenant.data.visits, 2);
    receive('visit_rejected');
    expect(tenant.data.visits, 1);
    receive('visit_rejected');
    receive('visit_rejected');
    expect(tenant.data.visits, 0);
    expect(owner.data.visits, 5);

    for (final String type in [
      'new_message',
      'owner_message',
      'tenant_message',
    ]) {
      receive(type);
    }
    ForegroundNotificationBus.receive({'type': 'new_message'});
    receive('unknown', data: {'category': 'chat'});
    expect(chat.data.count, 12);
    receive('promotion');
    receive('visit_review');
    expect(notifications.data.count, 15);
    expect(tenant.data.favorites, 6);
    expect(owner.data.visits, 5);
    expect(chat.data.count, 12);
    expect(repository.requests, requests);
  });

  test('repeated notification deliveries increment once', () async {
    await load();
    receive('visit_request', id: 'request-1');
    receive('visit_request', id: 'request-1');
    ForegroundNotificationBus.receive({
      'notification_type': 'promotion',
    }, deliveryId: 'fcm-1');
    ForegroundNotificationBus.receive({
      'notification_type': 'promotion',
    }, deliveryId: 'fcm-1');
    expect(notifications.data.count, 5);
    expect(owner.data.visits, 5);
  });

  for (final bool pushFirst in [true, false]) {
    test(
      'chat push and socket count once with push first=$pushFirst',
      () async {
        await load();
        final int requests = repository.requests;
        void push() => receive(
          'new_message',
          data: {
            'message_id': 'message-1',
            'conversation_id': 'conversation-1',
            'sender_id': 'other-user',
          },
        );
        void socket() => realtime.messagesController.add(
          _message('message-1', 'conversation-1'),
        );
        if (pushFirst) {
          push();
          socket();
        } else {
          socket();
          push();
        }
        expect(chat.data.count, 8);
        expect(notifications.data.count, 4);
        expect(repository.requests, requests);
      },
    );
  }

  test(
    'active conversations and own messages do not add chat unread',
    () async {
      await load();
      realtime.setActiveConversation('active');
      receive(
        'new_message',
        data: {'message_id': 'active-message', 'conversation_id': 'active'},
      );
      realtime.setActiveConversation(null);
      realtime.messagesController.add(_message('active-message', 'active'));
      receive(
        'new_message',
        data: {'message_id': 'own-message', 'sender_id': '1'},
      );
      realtime.messagesController.add(
        _message(
          'own-message',
          'conversation-1',
        ).copyWith(sender: const ChatSocketSender.initial().copyWith(id: '1')),
      );
      expect(chat.data.count, 7);
      expect(notifications.data.count, 5);
    },
  );

  test('deliveries during loading survive the count response', () async {
    repository.gate = Completer<void>();
    final Future<void> request = load();
    await Future<void>.delayed(Duration.zero);
    expect(repository.requests, 4);
    receive('visit_request');
    receive('visit_rejected');
    receive('new_message', data: {'message_id': 'loading-message'});
    repository.gate!.complete();
    await request;
    expect(owner.data.visits, 5);
    expect(tenant.data.visits, 1);
    expect(notifications.data.count, 6);
    expect(chat.data.count, 8);
    expect(repository.requests, 4);
  });

  test('read actions still reconcile counts and start is idempotent', () async {
    await load();
    await chat.start();
    expect(repository.requests, 4);
    expect(realtime.connections, 1);
    ChatUnreadRefreshBus.requestRefresh(removedUnreadCount: 4);
    expect(chat.data.count, 3);
    expect(repository.requests, 4);
    NotificationRefreshBus.requestRefresh();
    await Future<void>.delayed(Duration.zero);
    expect(repository.requests, 5);
  });

  test(
    'closed cubits and a previous session ignore foreground messages',
    () async {
      await load();
      AccountSession.end();
      receive('visit_request');
      receive('new_message');
      expect(owner.data.visits, 4);
      expect(notifications.data.count, 3);
      expect(chat.data.count, 7);
      await Future.wait([
        tenant.close(),
        owner.close(),
        notifications.close(),
        chat.close(),
      ]);
      receive('visit_request');
      expect(owner.data.visits, 4);
      expect(notifications.data.count, 3);
    },
  );
}

ChatSocketMessage _message(String id, String conversationId) =>
    const ChatSocketMessage.initial().copyWith(
      id: id,
      conversationId: conversationId,
      sender: const ChatSocketSender.initial().copyWith(id: 'other-user'),
    );

class _CountsRepository implements BaseRepository {
  int requests = 0;
  Completer<void>? gate;

  @override
  Future<Result<BaseModel<T>, Failure>> crudCall<T>(
    CrudBaseParmas<T> params,
  ) async {
    requests++;
    await gate?.future;
    return Success(
      BaseModel<T>(
        key: '',
        msg: '',
        data: params.mapper!({
          'favorites_count': 6,
          'visit_requests_count': params.api == ApiConstants.ownerUnreadCounts
              ? 4
              : 2,
          'unread_chat_messages_count': 7,
          'unread_notifications_count': 3,
        }),
      ),
    );
  }

  @override
  Future<Result<List<T>, Failure>> getBaseIdAndNameEntity<T extends BaseEntity>(
    GetBaseEntityParams? param,
  ) => throw UnimplementedError();
}

class _AuthenticatedNetwork implements NetworkService {
  @override
  Future<bool> hasSessionCookies() async => true;
  @override
  Future<void> clearSessionCookies() async {}
  @override
  Future<void> updateBaseUrl() async {}
  @override
  Future<BaseModel<T>> callApi<T>(
    NetworkRequest request, {
    T Function(dynamic)? mapper,
  }) => throw UnimplementedError();
}

class _Realtime implements ChatRealtimeGateway {
  final StreamController<ChatSocketMessage> messagesController =
      StreamController<ChatSocketMessage>.broadcast(sync: true);
  int connections = 0;
  @override
  String? activeConversationId;
  @override
  Stream<ChatSocketMessage> get messages => messagesController.stream;
  @override
  Stream<ChatReadReceipt> get readReceipts => const Stream.empty();
  @override
  Stream<ChatRealtimeStatus> get statuses => const Stream.empty();
  @override
  ChatRealtimeStatus get status => ChatRealtimeStatus.connected;
  @override
  bool get isConnected => true;
  @override
  void setActiveConversation(String? conversationId) =>
      activeConversationId = conversationId;
  @override
  Future<void> connect() async {
    connections++;
  }

  @override
  Future<void> disconnect() async {}
  @override
  Future<void> sendMessage({
    required String conversationId,
    required String content,
  }) async {}
  @override
  Future<void> markConversationAsRead(String conversationId) async {}
  Future<void> close() => messagesController.close();
}
