import 'dart:async';

import 'package:flutter/services.dart';
import 'package:flutter/widgets.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:melos_core/core/helpers/cache_service.dart';
import 'package:melos_core/core/network/account_session.dart';
import 'package:sokoun_app/features/shared/chat/data/chat_data.dart';
import 'package:sokoun_app/features/shared/chat/data/chat_realtime_service.dart';
import 'package:sokoun_app/features/shared/chat/data/models/chat_socket_message.dart';
import 'package:sokoun_app/features/shared/chat/data/models/chat_read_content.dart';
import 'package:sokoun_app/features/shared/chat/presentation/cubits/chat_thread_cubit.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  const MethodChannel sharedPreferencesChannel = MethodChannel(
    'plugins.flutter.io/shared_preferences',
  );

  setUpAll(() async {
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(sharedPreferencesChannel, (call) async {
          return call.method == 'getAll' ? <String, Object>{} : true;
        });
    await CacheStorage.init();
  });

  tearDownAll(() {
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(sharedPreferencesChannel, null);
  });

  setUp(() async {
    AccountSession.begin('current-user-id');
    await CacheStorage.write('user', const <String, dynamic>{
      'id': 'current-user-id',
      'name': 'Current User',
      'phone': '',
      'email': '',
      'type': 'tenant',
    });
  });

  tearDown(() async {
    AccountSession.end();
    await CacheStorage.delete('user');
  });

  test('closing a chat disconnects its socket', () async {
    final realtime = _FakeChatRealtimeGateway();
    final cubit = ChatThreadCubit(
      conversationId: 'conversation-1',
      realtimeService: realtime,
    );
    addTearDown(realtime.close);
    await cubit.connect();
    expect(realtime.isConnected, isTrue);
    await cubit.close();
    expect(realtime.disconnectCount, 1);
    expect(realtime.isConnected, isFalse);
    expect(realtime.activeConversationId, isNull);
  });

  test(
    'closing an older thread preserves the active thread connection',
    () async {
      final realtime = _FakeChatRealtimeGateway();
      final first = ChatThreadCubit(
        conversationId: 'conversation-1',
        realtimeService: realtime,
      );
      final second = ChatThreadCubit(
        conversationId: 'conversation-2',
        realtimeService: realtime,
      );
      addTearDown(() async {
        await second.close();
        await realtime.close();
      });
      await first.connect();
      await second.connect();
      await first.close();
      expect(realtime.disconnectCount, 0);
      expect(realtime.isConnected, isTrue);
      expect(realtime.activeConversationId, 'conversation-2');
    },
  );

  for (final bool closeThread in [true, false]) {
    test(
      '${closeThread ? 'closing the thread' : 'logout'} suppresses a pending connect and later read requests',
      () async {
        final realtime = _FakeChatRealtimeGateway()
          ..connectGate = Completer<void>();
        final data = _ReadTrackingDataSource();
        final cubit = ChatThreadCubit(
          conversationId: 'conversation-1',
          realtimeService: realtime,
          dataSource: data,
        );
        addTearDown(() async {
          if (!cubit.isClosed) await cubit.close();
          await realtime.close();
        });
        final connecting = cubit.connect();
        if (closeThread) {
          await cubit.close();
        } else {
          AccountSession.end();
        }
        realtime.connectGate!.complete();
        await connecting;
        await cubit.onAppLifecycleStateChanged(AppLifecycleState.resumed);
        await cubit.markConversationAsRead();
        expect(realtime.connectCount, 1);
        expect(realtime.readCount, 0);
        expect(data.readCount, 0);
      },
    );
  }

  test(
    'accepts a numeric-conversation socket echo as send confirmation',
    () async {
      final _FakeChatRealtimeGateway realtime = _FakeChatRealtimeGateway();
      final ChatThreadCubit cubit = ChatThreadCubit(
        conversationId: 'conversation-uuid',
        otherParticipantId: 'other-user-id',
        realtimeService: realtime,
      );
      addTearDown(() async {
        await cubit.close();
        await realtime.close();
      });
      await cubit.connect();

      realtime.messageToEcho = _message(
        conversationId: '1',
        senderId: 'current-user-id',
        content: 'Hello',
      );

      final ChatSendResult result = await cubit.sendTextMessage('Hello');

      expect(result.isSent, isTrue);
      expect(result.restMessage?.id, 'message-id');
      expect(cubit.state.receivedMessage?.id, 'message-id');
    },
  );

  test('connects the socket before sending when it is disconnected', () async {
    final _FakeChatRealtimeGateway realtime = _FakeChatRealtimeGateway();
    final ChatThreadCubit cubit = ChatThreadCubit(
      conversationId: 'conversation-uuid',
      otherParticipantId: 'other-user-id',
      realtimeService: realtime,
    );
    addTearDown(() async {
      await cubit.close();
      await realtime.close();
    });

    realtime.messageToEcho = _message(
      conversationId: '1',
      senderId: 'current-user-id',
      content: 'Connect then send',
    );

    final ChatSendResult result = await cubit.sendTextMessage(
      'Connect then send',
    );

    expect(realtime.connectCount, 1);
    expect(result.isSent, isTrue);
    expect(result.restMessage?.content, 'Connect then send');
  });

  test('queues messages while disconnected and sends them in order', () async {
    final _FakeChatRealtimeGateway realtime = _FakeChatRealtimeGateway()
      ..canConnect = false
      ..echoSentMessages = true;
    final ChatThreadCubit cubit = ChatThreadCubit(
      conversationId: 'conversation-uuid',
      otherParticipantId: 'other-user-id',
      realtimeService: realtime,
    );
    addTearDown(() async {
      await cubit.close();
      await realtime.close();
    });

    final ChatSendResult first = await cubit.sendTextMessage(
      'First',
      localMessageId: 'local-first',
    );
    final ChatSendResult second = await cubit.sendTextMessage(
      'Second',
      localMessageId: 'local-second',
    );

    expect(first.isQueued, isTrue);
    expect(second.isQueued, isTrue);
    expect(cubit.queuedMessageCount, 2);
    expect(realtime.sentContents, isEmpty);

    realtime.setConnected(true);
    await pumpEventQueue();

    expect(realtime.sentContents, <String>['First', 'Second']);
    expect(cubit.queuedMessageCount, 0);
    expect(cubit.state.queuedMessageCount, 0);
    expect(cubit.state.confirmedLocalMessageId, 'local-second');
  });

  test(
    'accepts numeric conversation messages from the active participant',
    () async {
      final _FakeChatRealtimeGateway realtime = _FakeChatRealtimeGateway();
      final ChatThreadCubit cubit = ChatThreadCubit(
        conversationId: 'conversation-uuid',
        otherParticipantId: 'other-user-id',
        realtimeService: realtime,
      );
      addTearDown(() async {
        await cubit.close();
        await realtime.close();
      });
      await cubit.connect();

      realtime.addMessage(
        _message(
          conversationId: '1',
          senderId: 'other-user-id',
          content: 'Incoming',
        ),
      );

      expect(cubit.state.receivedMessage?.content, 'Incoming');
    },
  );

  test(
    'rejects numeric conversation messages from another participant',
    () async {
      final _FakeChatRealtimeGateway realtime = _FakeChatRealtimeGateway();
      final ChatThreadCubit cubit = ChatThreadCubit(
        conversationId: 'conversation-uuid',
        otherParticipantId: 'other-user-id',
        realtimeService: realtime,
      );
      addTearDown(() async {
        await cubit.close();
        await realtime.close();
      });
      await cubit.connect();

      realtime.addMessage(
        _message(
          conversationId: '2',
          senderId: 'unrelated-user-id',
          content: 'Wrong thread',
        ),
      );

      expect(cubit.state.receivedMessage, isNull);
    },
  );
}

ChatSocketMessage _message({
  required String conversationId,
  required String senderId,
  required String content,
}) {
  return ChatSocketMessage(
    id: 'message-id',
    conversationId: conversationId,
    sender: ChatSocketSender(
      id: senderId,
      name: 'Sender',
      avatarUrl: '',
      isOnline: true,
    ),
    content: content,
    createdAt: DateTime(2026),
  );
}

class _FakeChatRealtimeGateway implements ChatRealtimeGateway {
  final StreamController<ChatSocketMessage> _messages =
      StreamController<ChatSocketMessage>.broadcast(sync: true);
  final StreamController<ChatReadReceipt> _readReceipts =
      StreamController<ChatReadReceipt>.broadcast(sync: true);
  final StreamController<ChatRealtimeStatus> _statuses =
      StreamController<ChatRealtimeStatus>.broadcast(sync: true);

  ChatSocketMessage? messageToEcho;
  int connectCount = 0;
  int disconnectCount = 0;
  int readCount = 0;
  int _connectionVersion = 0;
  Completer<void>? connectGate;
  int _sentMessageCount = 0;
  bool canConnect = true;
  bool echoSentMessages = false;
  final List<String> sentContents = [];

  @override
  String? activeConversationId;

  @override
  bool isConnected = false;

  @override
  Stream<ChatSocketMessage> get messages => _messages.stream;

  @override
  Stream<ChatReadReceipt> get readReceipts => _readReceipts.stream;

  @override
  ChatRealtimeStatus get status => isConnected
      ? ChatRealtimeStatus.connected
      : ChatRealtimeStatus.disconnected;

  @override
  Stream<ChatRealtimeStatus> get statuses => _statuses.stream;

  void addMessage(ChatSocketMessage message) => _messages.add(message);

  @override
  Future<void> connect() async {
    connectCount++;
    final int version = _connectionVersion;
    await connectGate?.future;
    if (version != _connectionVersion) return;
    setConnected(canConnect);
  }

  @override
  Future<void> disconnect() async {
    disconnectCount++;
    _connectionVersion++;
    isConnected = false;
    _statuses.add(ChatRealtimeStatus.disconnected);
  }

  @override
  Future<void> markConversationAsRead(String conversationId) async {
    readCount++;
  }

  @override
  Future<void> sendMessage({
    required String conversationId,
    required String content,
  }) async {
    sentContents.add(content);
    final ChatSocketMessage? echoedMessage = echoSentMessages
        ? ChatSocketMessage(
            id: 'message-${++_sentMessageCount}',
            conversationId: conversationId,
            sender: const ChatSocketSender(
              id: 'current-user-id',
              name: 'Current User',
              avatarUrl: '',
              isOnline: true,
            ),
            content: content,
            createdAt: DateTime(2026),
          )
        : messageToEcho;
    if (echoedMessage != null) _messages.add(echoedMessage);
  }

  void setConnected(bool connected) {
    isConnected = connected;
    _statuses.add(
      connected
          ? ChatRealtimeStatus.connected
          : ChatRealtimeStatus.disconnected,
    );
  }

  @override
  void setActiveConversation(String? conversationId) {
    activeConversationId = conversationId;
  }

  Future<void> close() async {
    await Future.wait([
      _messages.close(),
      _readReceipts.close(),
      _statuses.close(),
    ]);
  }
}

class _ReadTrackingDataSource implements ChatDataSource {
  int readCount = 0;

  @override
  Future<ChatReadContent> markConversationAsRead(String conversationId) async {
    readCount++;
    return const ChatReadContent.initial();
  }

  @override
  dynamic noSuchMethod(Invocation invocation) => super.noSuchMethod(invocation);
}
