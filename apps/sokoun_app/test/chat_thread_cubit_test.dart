import 'dart:async';

import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:melos_core/core/helpers/cache_service.dart';
import 'package:sokoun_app/features/shared/chat/data/chat_realtime_service.dart';
import 'package:sokoun_app/features/shared/chat/data/models/chat_socket_message.dart';
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
    await CacheStorage.write('user', const <String, dynamic>{
      'id': 'current-user-id',
      'name': 'Current User',
      'phone': '',
      'email': '',
      'type': 'tenant',
    });
  });

  tearDown(() => CacheStorage.delete('user'));

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
    isConnected = true;
    _statuses.add(ChatRealtimeStatus.connected);
  }

  @override
  Future<void> disconnect() async {
    isConnected = false;
    _statuses.add(ChatRealtimeStatus.disconnected);
  }

  @override
  Future<void> markConversationAsRead(String conversationId) async {}

  @override
  Future<void> sendMessage({
    required String conversationId,
    required String content,
  }) async {
    final ChatSocketMessage? echoedMessage = messageToEcho;
    if (echoedMessage != null) _messages.add(echoedMessage);
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
