import 'package:pagify/helpers/data_and_pagination_data.dart';
import 'package:sokoun_app/features/shared/chat/data/models/conversation_content.dart';
import 'package:sokoun_app/features/shared/chat/data/models/chat_message_acknowledgement.dart';
import 'package:sokoun_app/features/shared/chat/data/chat_local_data.dart';
import 'package:sokoun_app/features/shared/chat/data/models/chat_local_state.dart';
import 'package:sokoun_app/features/shared/chat/data/models/chat_participant_content.dart';
import 'dart:async';

import 'package:flutter/services.dart';
import 'package:flutter/widgets.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:melos_core/core/helpers/cache_service.dart';
import 'package:melos_core/core/network/account_session.dart';
import 'package:melos_core/core/shared/models/user_models/user_model.dart';
import 'package:sokoun_app/features/shared/chat/data/chat_data.dart';
import 'package:sokoun_app/features/shared/chat/data/chat_realtime_service.dart';
import 'package:sokoun_app/features/shared/chat/data/models/chat_socket_message.dart';
import 'package:sokoun_app/features/shared/chat/data/models/chat_read_content.dart';
import 'package:sokoun_app/features/shared/chat/data/models/chat_message_content.dart';
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
      'is_verified': true,
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

  test(
    'acceptance during an old contact read schedules a fresh read',
    () async {
      final realtime = _FakeChatRealtimeGateway();
      final source = _ReadTrackingDataSource();
      source.contactResponse = Completer<ConversationContent>();
      final cubit = ChatThreadCubit(
        conversationId: 'thread',
        otherParticipantId: 'other',
        realtimeService: realtime,
        dataSource: source,
      );
      final first = cubit.refreshContact();
      final queued = cubit.refreshContact(afterVisitAcceptance: true);
      expect(source.contactRequests, 1);
      source.contactResponse!.complete(
        const ConversationContent.initial().copyWith(
          id: 'thread',
          otherParticipant: const ChatParticipantContent(id: 'other'),
        ),
      );
      source.contactResponse = null;
      source.contactSnapshot = const ConversationContent.initial().copyWith(
        id: 'thread',
        otherParticipant: const ChatParticipantContent(
          id: 'other',
          phoneNumber: '+201001234567',
          isPhoneRevealed: true,
        ),
      );
      await Future.wait([first, queued]);
      await Future<void>.delayed(Duration.zero);
      expect(source.contactRequests, 2);
      expect(cubit.state.contact.revealedPhone, '+201001234567');
      await cubit.close();
      await realtime.close();
    },
  );

  test('a contact response from the previous account is ignored', () async {
    final realtime = _FakeChatRealtimeGateway();
    final source = _ReadTrackingDataSource();
    source.contactResponse = Completer<ConversationContent>();
    final cubit = ChatThreadCubit(
      conversationId: 'thread',
      otherParticipantId: 'other',
      realtimeService: realtime,
      dataSource: source,
    );
    final request = cubit.refreshContact();
    AccountSession.begin('another-account');
    source.contactResponse!.complete(
      const ConversationContent.initial().copyWith(
        id: 'thread',
        otherParticipant: const ChatParticipantContent(
          id: 'other',
          phoneNumber: '+201001234567',
          isPhoneRevealed: true,
        ),
      ),
    );
    await request;
    expect(cubit.state.contact.revealedPhone, isEmpty);
    await cubit.close();
    await realtime.close();
  });

  test(
    'fresh metadata replaces a grant and updates sending independently',
    () async {
      final realtime = _FakeChatRealtimeGateway();
      final source = _ReadTrackingDataSource()
        ..contactSnapshot = ConversationContent.fromJson({
          'id': 'thread',
          'other_participant': {
            'id': 'other',
            'is_phone_revealed': false,
            'phone_number': '',
            'can_send': false,
          },
        });
      final cubit = ChatThreadCubit(
        conversationId: 'thread',
        otherParticipantId: 'other',
        realtimeService: realtime,
        dataSource: source,
        localStore: _MemoryChatLocalStore(),
        initialContact: const ChatParticipantContent(
          id: 'other',
          isPhoneRevealed: true,
          phoneNumber: '+201001234567',
        ),
      );
      cubit.updateDraft('Keep this draft');
      await cubit.connect();
      await cubit.refreshContact();
      expect(cubit.state.contact.isPhoneRevealed, isFalse);
      expect(cubit.state.contact.revealedPhone, isEmpty);
      expect(cubit.canSend, isFalse);
      expect(
        (await cubit.sendTextMessage('Denied')).status,
        ChatSendStatus.failed,
      );
      expect(realtime.sentContents, isEmpty);

      source.contactSnapshot = ConversationContent.fromJson({
        'id': 'thread',
        'other_participant': {
          'id': 'other',
          'is_phone_revealed': true,
          'phone_number': null,
          'can_send': true,
        },
      });
      await cubit.refreshContact();
      expect(cubit.state.contact.isPhoneRevealed, isTrue);
      expect(cubit.state.contact.revealedPhone, isEmpty);
      expect(cubit.canSend, isTrue);
      expect(cubit.state.draft, 'Keep this draft');
      await cubit.close();
      await realtime.close();
    },
  );

  test('a refreshed sending denial pauses queued delivery', () async {
    final realtime = _FakeChatRealtimeGateway()..canConnect = false;
    final source = _ReadTrackingDataSource()
      ..contactSnapshot = const ConversationContent.initial().copyWith(
        id: 'thread',
        canSend: false,
      );
    final cubit = ChatThreadCubit(
      conversationId: 'thread',
      realtimeService: realtime,
      dataSource: source,
      localStore: _MemoryChatLocalStore(),
    );
    await cubit.connect();
    expect((await cubit.sendTextMessage('Wait for access')).isQueued, isTrue);
    await cubit.refreshContact();
    realtime.setConnected(true);
    await Future<void>.delayed(Duration.zero);
    expect(cubit.canSend, isFalse);
    expect(cubit.queuedMessageCount, 1);
    expect(realtime.sentContents, isEmpty);
    expect(source.sentClientIds, isEmpty);
    await cubit.close();
    await realtime.close();
  });

  test('read-only contact reads preserve the existing socket owner', () async {
    final realtime = _FakeChatRealtimeGateway()
      ..activeConversationId = 'thread'
      ..isConnected = true;
    final source = _ReadTrackingDataSource()
      ..contactSnapshot = ConversationContent.fromJson({
        'id': 'thread',
        'other_participant': {
          'id': 'other',
          'phone_number': '+201001234567',
          'is_phone_revealed': true,
          'can_send': true,
        },
      });
    final cubit = ChatThreadCubit(
      conversationId: 'thread',
      otherParticipantId: 'other',
      readOnly: true,
      realtimeService: realtime,
      dataSource: source,
    );
    await cubit.refreshContact();
    await cubit.connect();
    expect(cubit.state.contact.revealedPhone, '+201001234567');
    expect(cubit.canSend, isFalse);
    expect(realtime.connectCount, 0);
    await cubit.close();
    expect(realtime.activeConversationId, 'thread');
    expect(realtime.disconnectCount, 0);
    await realtime.close();
  });

  test(
    'recovered messages require explicit review and sending after restart',
    () async {
      final store = _MemoryChatLocalStore()
        ..state = const ChatLocalState(
          draft: 'New draft',
          messages: [
            SavedChatMessage(
              id: 'uncertain-send',
              content: 'Review before resending',
            ),
          ],
        );
      final realtime = _FakeChatRealtimeGateway()..echoSentMessages = true;
      final cubit = ChatThreadCubit(
        conversationId: 'conversation-1',
        localStore: store,
        realtimeService: realtime,
        dataSource: _ReadTrackingDataSource(),
      );
      await cubit.connect();
      expect(cubit.state.draft, 'New draft');
      expect(cubit.state.recoveredMessages, hasLength(1));
      expect(cubit.queuedMessageCount, 0);
      expect(realtime.sentContents, isEmpty);
      expect(
        await cubit.restoreMessageDraft(cubit.state.recoveredMessages.single),
        isFalse,
      );
      cubit.updateDraft('');
      expect(
        await cubit.restoreMessageDraft(cubit.state.recoveredMessages.single),
        isTrue,
      );
      expect(cubit.state.draft, 'Review before resending');
      expect(store.state.messages, isEmpty);
      final result = await cubit.sendTextMessage(cubit.state.draft);
      expect(result.isSent, isTrue);
      expect(realtime.sentContents, ['Review before resending']);
      expect(store.state.messages, isEmpty);
      cubit.updateDraft('');
      await cubit.close();
      await realtime.close();
      expect(store.state, const ChatLocalState.initial());
    },
  );

  test(
    'a server send restriction preserves history without opening a socket',
    () async {
      final realtime = _FakeChatRealtimeGateway();
      final cubit = ChatThreadCubit(
        conversationId: 'read-only',
        canSend: false,
        localStore: _MemoryChatLocalStore(),
        realtimeService: realtime,
      );
      await cubit.connect();
      expect(realtime.connectCount, 0);
      expect(
        (await cubit.sendTextMessage('Blocked')).status,
        ChatSendStatus.failed,
      );
      expect(realtime.sentContents, isEmpty);
      await cubit.close();
      await realtime.close();
    },
  );

  test(
    'an unverified account cannot connect or send despite conversation permission',
    () async {
      await CacheStorage.write('user', {
        'id': 'current-user-id',
        'is_verified': false,
      });
      final realtime = _FakeChatRealtimeGateway();
      final cubit = ChatThreadCubit(
        conversationId: 'thread',
        canSend: true,
        realtimeService: realtime,
        localStore: _MemoryChatLocalStore(),
      );
      expect(cubit.canSend, isFalse);
      await cubit.connect();
      expect(realtime.connectCount, 0);
      expect(
        (await cubit.sendTextMessage('Blocked')).status,
        ChatSendStatus.failed,
      );
      expect(realtime.sentContents, isEmpty);
      await cubit.close();
      await realtime.close();
    },
    skip: UserModel.bypassVerification,
  );

  test(
    'failed durable storage retains the composer and sends nothing',
    () async {
      final store = _MemoryChatLocalStore()..fail = true;
      final realtime = _FakeChatRealtimeGateway();
      final cubit = ChatThreadCubit(
        conversationId: 'conversation-1',
        localStore: store,
        realtimeService: realtime,
      );
      await cubit.connect();
      cubit.updateDraft('Keep my text');
      expect(
        (await cubit.sendTextMessage('Keep my text')).status,
        ChatSendStatus.failed,
      );
      expect(cubit.state.draft, 'Keep my text');
      expect(cubit.state.localSaveFailed, isTrue);
      expect(cubit.queuedMessageCount, 0);
      expect(realtime.sentContents, isEmpty);
      store.fail = false;
      await cubit.close();
      await realtime.close();
      expect(store.state.draft, 'Keep my text');
    },
  );

  test(
    'encrypted chat keys cannot collide between account and conversation pairs',
    () {
      expect(
        ChatLocalData.keyFor('a_b', 'c'),
        isNot(ChatLocalData.keyFor('a', 'b_c')),
      );
      expect(
        ChatLocalData.keyFor('alice', 'c'),
        isNot(ChatLocalData.keyFor('bob', 'c')),
      );
    },
  );

  test('closing a chat disconnects its socket', () async {
    final realtime = _FakeChatRealtimeGateway();
    final cubit = ChatThreadCubit(
      localStore: _MemoryChatLocalStore(),
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
        localStore: _MemoryChatLocalStore(),
        conversationId: 'conversation-1',
        realtimeService: realtime,
      );
      final second = ChatThreadCubit(
        localStore: _MemoryChatLocalStore(),
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
          localStore: _MemoryChatLocalStore(),
          conversationId: 'conversation-1',
          realtimeService: realtime,
          dataSource: data,
        );
        addTearDown(() async {
          if (!cubit.isClosed) await cubit.close();
          await realtime.close();
        });
        final connecting = cubit.connect();
        await pumpEventQueue();
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

  test('confirms an outgoing echo by client ID and conversation', () async {
    final _FakeChatRealtimeGateway realtime = _FakeChatRealtimeGateway();
    final ChatThreadCubit cubit = ChatThreadCubit(
      localStore: _MemoryChatLocalStore(),
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
      conversationId: 'conversation-uuid',
      senderId: 'current-user-id',
      content: 'Hello',
    );

    final ChatSendResult result = await cubit.sendTextMessage('Hello');

    expect(result.isSent, isTrue);
    expect(result.restMessage?.id, 'message-id');
    expect(cubit.state.receivedMessage?.id, 'message-id');
  });

  test('connects the socket before sending when it is disconnected', () async {
    final _FakeChatRealtimeGateway realtime = _FakeChatRealtimeGateway();
    final ChatThreadCubit cubit = ChatThreadCubit(
      localStore: _MemoryChatLocalStore(),
      conversationId: 'conversation-uuid',
      otherParticipantId: 'other-user-id',
      realtimeService: realtime,
    );
    addTearDown(() async {
      await cubit.close();
      await realtime.close();
    });

    realtime.messageToEcho = _message(
      conversationId: 'conversation-uuid',
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

  test('successful sends never show the queued-message notice', () async {
    final realtime = _FakeChatRealtimeGateway()..echoSentMessages = true;
    final cubit = ChatThreadCubit(
      localStore: _MemoryChatLocalStore(),
      conversationId: 'conversation-uuid',
      realtimeService: realtime,
    );
    final states = <ChatThreadState>[];
    final subscription = cubit.stream.listen(states.add);
    addTearDown(() async {
      await cubit.close();
      await subscription.cancel();
      await realtime.close();
    });
    final result = await cubit.sendTextMessage('Hello');
    await pumpEventQueue();
    expect(result.isSent, isTrue);
    expect(states.any((state) => state.queuedMessageCount > 0), isTrue);
    expect(states.any((state) => state.showQueuedMessages), isFalse);
  });

  testWidgets(
    'a pending send shows the notice after two seconds and clears on confirmation',
    (tester) async {
      final realtime = _FakeChatRealtimeGateway();
      final cubit = ChatThreadCubit(
        localStore: _MemoryChatLocalStore(),
        conversationId: 'conversation-uuid',
        realtimeService: realtime,
      );
      addTearDown(() async {
        final closing = cubit.close();
        await _flushWrites(tester);
        await closing;
        await realtime.close();
      });
      await cubit.connect();
      final sending = cubit.sendTextMessage('Slow message');
      await _flushWrites(tester);
      expect(cubit.state.queuedMessageCount, 1);
      expect(cubit.state.showQueuedMessages, isFalse);
      await tester.pump(const Duration(milliseconds: 1999));
      expect(cubit.state.showQueuedMessages, isFalse);
      await tester.pump(const Duration(milliseconds: 1));
      expect(cubit.state.showQueuedMessages, isTrue);
      realtime.addMessage(
        _message(
          conversationId: 'conversation-uuid',
          senderId: 'current-user-id',
          content: 'Slow message',
          clientMessageId: realtime.sentClientIds[0],
        ),
      );
      await _flushWrites(tester);
      expect((await sending).isSent, isTrue);
      expect(cubit.state.queuedMessageCount, 0);
      expect(cubit.state.showQueuedMessages, isFalse);
    },
  );

  testWidgets('the next pending message has its own two-second threshold', (
    tester,
  ) async {
    final realtime = _FakeChatRealtimeGateway();
    final cubit = ChatThreadCubit(
      localStore: _MemoryChatLocalStore(),
      conversationId: 'conversation-uuid',
      realtimeService: realtime,
    );
    addTearDown(() async {
      final closing = cubit.close();
      await _flushWrites(tester);
      await closing;
      await realtime.close();
    });
    await cubit.connect();
    final first = cubit.sendTextMessage('First');
    await tester.pump(const Duration(milliseconds: 1500));
    final second = cubit.sendTextMessage('Second');
    await tester.pump(const Duration(milliseconds: 500));
    expect(cubit.state.showQueuedMessages, isTrue);
    realtime.addMessage(
      _message(
        conversationId: 'conversation-uuid',
        senderId: 'current-user-id',
        content: 'First',
        clientMessageId: realtime.sentClientIds[0],
      ),
    );
    await _flushWrites(tester);
    expect(cubit.state.queuedMessageCount, 1);
    expect(cubit.state.showQueuedMessages, isFalse);
    await tester.pump(const Duration(milliseconds: 1499));
    expect(cubit.state.showQueuedMessages, isFalse);
    await tester.pump(const Duration(milliseconds: 1));
    expect(cubit.state.showQueuedMessages, isTrue);
    realtime.addMessage(
      _message(
        conversationId: 'conversation-uuid',
        senderId: 'current-user-id',
        content: 'Second',
        clientMessageId: realtime.sentClientIds[1],
      ),
    );
    await _flushWrites(tester);
    await Future.wait([first, second]);
    expect(cubit.state.showQueuedMessages, isFalse);
  });

  test('queues messages while disconnected and sends them in order', () async {
    final _FakeChatRealtimeGateway realtime = _FakeChatRealtimeGateway()
      ..canConnect = false
      ..echoSentMessages = true;
    final ChatThreadCubit cubit = ChatThreadCubit(
      localStore: _MemoryChatLocalStore(),
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
    expect(cubit.state.showQueuedMessages, isTrue);
    expect(realtime.sentContents, isEmpty);

    realtime.setConnected(true);
    await pumpEventQueue();

    expect(realtime.sentContents, <String>['First', 'Second']);
    expect(cubit.queuedMessageCount, 0);
    expect(cubit.state.queuedMessageCount, 0);
    expect(cubit.state.showQueuedMessages, isFalse);
    expect(cubit.state.confirmedLocalMessageId, 'local-second');
  });

  test(
    'rejects another conversation even from the active participant',
    () async {
      final _FakeChatRealtimeGateway realtime = _FakeChatRealtimeGateway();
      final ChatThreadCubit cubit = ChatThreadCubit(
        localStore: _MemoryChatLocalStore(),
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
          conversationId: 'another-conversation-uuid',
          senderId: 'other-user-id',
          content: 'Incoming',
        ),
      );

      expect(cubit.state.receivedMessage, isNull);
    },
  );

  test(
    'rejects numeric conversation messages from another participant',
    () async {
      final _FakeChatRealtimeGateway realtime = _FakeChatRealtimeGateway();
      final ChatThreadCubit cubit = ChatThreadCubit(
        localStore: _MemoryChatLocalStore(),
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

  test(
    'rejects a different numeric conversation from the active participant',
    () async {
      final realtime = _FakeChatRealtimeGateway();
      final cubit = ChatThreadCubit(
        localStore: _MemoryChatLocalStore(),
        conversationId: '5',
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
          conversationId: '6',
          senderId: 'other-user-id',
          content: 'Wrong thread',
        ),
      );

      expect(cubit.state.receivedMessage, isNull);
    },
  );

  test(
    'message ACK replaces only the pending client ID with the server ID',
    () async {
      final realtime = _FakeChatRealtimeGateway();
      final cubit = ChatThreadCubit(
        conversationId: 'conversation-1',
        realtimeService: realtime,
        localStore: _MemoryChatLocalStore(),
      );
      await cubit.connect();
      final sending = cubit.sendTextMessage(
        'Same message',
        localMessageId: 'local-pending',
      );
      await pumpEventQueue();
      realtime.acknowledge('unknown-client-id');
      expect(cubit.state.receivedMessage, isNull);
      final id = realtime.sentClientIds.single;
      expect(
        id,
        matches(
          RegExp(
            r'^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$',
          ),
        ),
      );
      realtime.acknowledge(id, id: 'authoritative-message');
      expect(cubit.state.receivedMessage?.id, 'authoritative-message');
      await pumpEventQueue();
      expect((await sending).isSent, isTrue);
      expect(cubit.state.confirmedLocalMessageId, 'local-pending');
      expect(cubit.state.receivedMessage?.id, 'authoritative-message');
      expect(cubit.state.receivedMessage?.clientMessageId, id);
      await cubit.close();
      await realtime.close();
    },
  );

  testWidgets('a lost socket ACK reuses the same UUID in the REST fallback', (
    tester,
  ) async {
    final realtime = _FakeChatRealtimeGateway();
    final source = _ReadTrackingDataSource();
    final store = _MemoryChatLocalStore();
    final cubit = ChatThreadCubit(
      durableReplay: true,
      conversationId: 'conversation-1',
      realtimeService: realtime,
      dataSource: source,
      localStore: store,
    );
    addTearDown(() async {
      final closing = cubit.close();
      await _flushWrites(tester);
      await closing;
      await realtime.close();
    });
    await cubit.connect();
    final sending = cubit.sendTextMessage(
      'Do not duplicate',
      localMessageId: 'local-fallback',
    );
    await _flushWrites(tester);
    final id = realtime.sentClientIds.single;
    expect(store.state.messages.single.clientMessageId, id);
    await tester.pump(const Duration(seconds: 5));
    await _flushWrites(tester);
    expect((await sending).isSent, isTrue);
    expect(source.sentClientIds, [id]);
    expect(cubit.state.receivedMessage?.clientMessageId, id);
    expect(cubit.state.confirmedLocalMessageId, 'local-fallback');
    expect(store.state.messages, isEmpty);
  });

  testWidgets(
    'a mismatched REST identity stays queued and retries its original UUID',
    (tester) async {
      final realtime = _FakeChatRealtimeGateway();
      final source = _ReadTrackingDataSource()..wrongIdentity = true;
      final cubit = ChatThreadCubit(
        durableReplay: true,
        conversationId: 'conversation-1',
        realtimeService: realtime,
        dataSource: source,
        localStore: _MemoryChatLocalStore(),
      );
      addTearDown(() async {
        final closing = cubit.close();
        await _flushWrites(tester);
        await closing;
        await realtime.close();
      });
      await cubit.connect();
      final sending = cubit.sendTextMessage('Keep pending');
      await _flushWrites(tester);
      final id = realtime.sentClientIds.single;
      await tester.pump(const Duration(seconds: 5));
      await _flushWrites(tester);
      expect((await sending).isQueued, isTrue);
      expect(cubit.state.receivedMessage, isNull);
      expect(cubit.queuedMessageCount, 1);
      await tester.pump(const Duration(seconds: 5));
      await _flushWrites(tester);
      expect(realtime.sentClientIds, [id, id]);
      realtime.acknowledge(id);
      await _flushWrites(tester);
      expect(cubit.queuedMessageCount, 0);
    },
  );

  for (final edit in [false, true]) {
    test(
      'recovery ${edit ? 'changes' : 'preserves'} the UUID when ${edit ? 'the content changes' : 'the content is unchanged'}',
      () async {
        const originalId = 'a8b9d21a-137b-40c0-af9d-b70f520b7373';
        final store = _MemoryChatLocalStore()
          ..state = const ChatLocalState(
            messages: [
              SavedChatMessage(
                id: 'local-recovered',
                content: 'Recover this',
                clientMessageId: originalId,
              ),
            ],
          );
        final firstRealtime = _FakeChatRealtimeGateway();
        final first = ChatThreadCubit(
          conversationId: 'conversation-1',
          realtimeService: firstRealtime,
          localStore: store,
        );
        await first.connect();
        await first.restoreMessageDraft(first.state.recoveredMessages.single);
        if (edit) first.updateDraft('Edited content');
        await first.close();
        await firstRealtime.close();
        final realtime = _FakeChatRealtimeGateway()..echoSentMessages = true;
        final recovered = ChatThreadCubit(
          conversationId: 'conversation-1',
          realtimeService: realtime,
          localStore: store,
        );
        await recovered.connect();
        expect(
          (await recovered.sendTextMessage(recovered.state.draft)).isSent,
          isTrue,
        );
        expect(
          realtime.sentClientIds.single,
          edit ? isNot(originalId) : originalId,
        );
        await recovered.close();
        await realtime.close();
      },
    );
  }

  testWidgets(
    'default replay keeps a lost ACK unknown until its matching late ACK',
    (tester) async {
      final realtime = _FakeChatRealtimeGateway();
      final source = _ReadTrackingDataSource();
      final store = _MemoryChatLocalStore();
      final cubit = ChatThreadCubit(
        conversationId: 'conversation-1',
        realtimeService: realtime,
        dataSource: source,
        localStore: store,
      );
      addTearDown(() async {
        final closing = cubit.close();
        await _flushWrites(tester);
        await closing;
        await realtime.close();
      });
      await cubit.connect();
      final sending = cubit.sendTextMessage('Preserve uncertain delivery');
      await _flushWrites(tester);
      final id = realtime.sentClientIds.single;
      await tester.pump(const Duration(seconds: 5));
      await _flushWrites(tester);
      expect((await sending).status, ChatSendStatus.unknown);
      expect(cubit.state.unknownDelivery, isTrue);
      expect(store.state.messages.single.delivery, ChatDeliveryState.unknown);
      await tester.pump(const Duration(seconds: 30));
      await _flushWrites(tester);
      expect(source.sentClientIds, isEmpty);
      expect(realtime.sentClientIds, [id]);
      realtime.acknowledge(id);
      await _flushWrites(tester);
      expect(cubit.queuedMessageCount, 0);
      expect(store.state.messages, isEmpty);
    },
  );

  test(
    'unknown delivery is recovered without restart transmission and settles from exact history',
    () async {
      const id = 'a8b9d21a-137b-40c0-af9d-b70f520b7373';
      final store = _MemoryChatLocalStore()
        ..state = ChatLocalState.fromJson(
          const ChatLocalState(
            messages: [
              SavedChatMessage(
                id: 'local-1',
                clientMessageId: id,
                content: 'Already delivered',
                delivery: ChatDeliveryState.awaitingConfirmation,
              ),
            ],
          ).toJson(),
        );
      final realtime = _FakeChatRealtimeGateway();
      final cubit = ChatThreadCubit(
        conversationId: 'conversation-1',
        realtimeService: realtime,
        dataSource: _ReadTrackingDataSource(),
        localStore: store,
      );
      await cubit.connect();
      expect(realtime.sentContents, isEmpty);
      expect(
        cubit.state.recoveredMessages.single.delivery,
        ChatDeliveryState.unknown,
      );
      final confirmed = ChatMessageContent.fromJson({
        'id': 'server-1',
        'conversation_id': 'conversation-1',
        'client_message_id': id,
        'content': 'Already delivered',
        'sender': {'id': 'current-user-id'},
      });
      await cubit.reconcileHistory([
        confirmed.copyWith(conversationId: 'another-conversation'),
      ]);
      expect(cubit.state.recoveredMessages, hasLength(1));
      await cubit.reconcileHistory([confirmed]);
      expect(cubit.state.recoveredMessages, isEmpty);
      expect(store.state.messages, isEmpty);
      await cubit.close();
      await realtime.close();
    },
  );

  test(
    'gated restart reads matching history before replaying an outgoing UUID',
    () async {
      const id = 'a8b9d21a-137b-40c0-af9d-b70f520b7373';
      final store = _MemoryChatLocalStore()
        ..state = const ChatLocalState(
          messages: [
            SavedChatMessage(
              id: 'local-1',
              clientMessageId: id,
              content: 'Already delivered',
              delivery: ChatDeliveryState.unknown,
            ),
          ],
        );
      final source = _ReadTrackingDataSource()
        ..history = [
          ChatMessageContent.fromJson({
            'id': 'server-1',
            'conversation_id': 'conversation-1',
            'client_message_id': id,
            'content': 'Already delivered',
            'sender': {'id': 'current-user-id'},
          }),
        ];
      final realtime = _FakeChatRealtimeGateway();
      final cubit = ChatThreadCubit(
        durableReplay: true,
        conversationId: 'conversation-1',
        realtimeService: realtime,
        dataSource: source,
        localStore: store,
      );
      await cubit.connect();
      expect(realtime.sentContents, isEmpty);
      expect(cubit.queuedMessageCount, 0);
      expect(store.state.messages, isEmpty);
      await cubit.close();
      await realtime.close();
    },
  );

  test(
    'restored composer asks for a choice and discard preserves separate outgoing recovery',
    () async {
      final store = _MemoryChatLocalStore()
        ..state = const ChatLocalState(
          draft: 'Unsubmitted text',
          messages: [
            SavedChatMessage(
              id: 'pending',
              content: 'Different outgoing text',
              delivery: ChatDeliveryState.unknown,
            ),
          ],
        );
      final realtime = _FakeChatRealtimeGateway();
      final cubit = ChatThreadCubit(
        conversationId: 'conversation-1',
        realtimeService: realtime,
        dataSource: _ReadTrackingDataSource(),
        localStore: store,
      );
      await cubit.connect();
      expect(cubit.state.needsDraftDecision, isTrue);
      await cubit.resolveComposerDraft(false);
      expect(cubit.state.draft, isEmpty);
      expect(store.state.draft, isEmpty);
      expect(store.state.messages.single.content, 'Different outgoing text');
      await cubit.close();
      await realtime.close();
    },
  );

  test('identical text sent twice has two independent send UUIDs', () async {
    final realtime = _FakeChatRealtimeGateway()..echoSentMessages = true;
    final cubit = ChatThreadCubit(
      conversationId: 'conversation-1',
      realtimeService: realtime,
      localStore: _MemoryChatLocalStore(),
    );
    await cubit.sendTextMessage('Hello', localMessageId: 'first');
    await cubit.sendTextMessage('Hello', localMessageId: 'second');
    expect(realtime.sentClientIds.toSet(), hasLength(2));
    expect(cubit.state.confirmedLocalMessageId, 'second');
    await cubit.close();
    await realtime.close();
  });
}

ChatSocketMessage _message({
  required String conversationId,
  required String senderId,
  required String content,
  String clientMessageId = '',
}) {
  return ChatSocketMessage(
    id: 'message-id',
    clientMessageId: clientMessageId,
    conversationId: conversationId,
    sender: ChatParticipantContent(
      id: senderId,
      fullName: 'Sender',
      avatarUrl: '',
      isOnline: true,
    ),
    content: content,
    createdAt: DateTime(2026),
  );
}

class _FakeChatRealtimeGateway implements ChatRealtimeGateway {
  final StreamController<ChatMessageAcknowledgement> _acknowledgements =
      StreamController<ChatMessageAcknowledgement>.broadcast(sync: true);
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
  final List<String> sentClientIds = [];

  @override
  String? activeConversationId;

  @override
  bool isConnected = false;

  @override
  Stream<ChatSocketMessage> get messages => _messages.stream;
  @override
  Stream<ChatMessageAcknowledgement> get acknowledgements =>
      _acknowledgements.stream;

  @override
  Stream<ChatReadReceipt> get readReceipts => _readReceipts.stream;

  @override
  ChatRealtimeStatus get status => isConnected
      ? ChatRealtimeStatus.connected
      : ChatRealtimeStatus.disconnected;

  @override
  Stream<ChatRealtimeStatus> get statuses => _statuses.stream;

  void addMessage(ChatSocketMessage message) => _messages.add(message);
  void acknowledge(String clientId, {String id = 'server-message'}) =>
      _acknowledgements.add(
        ChatMessageAcknowledgement(
          id: id,
          clientMessageId: clientId,
          status: 'sent',
        ),
      );

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
    String clientMessageId = '',
  }) async {
    sentContents.add(content);
    sentClientIds.add(clientMessageId);
    final ChatSocketMessage? echoedMessage = echoSentMessages
        ? ChatSocketMessage(
            id: 'message-${++_sentMessageCount}',
            clientMessageId: clientMessageId,
            conversationId: conversationId,
            sender: const ChatParticipantContent(
              id: 'current-user-id',
              fullName: 'Current User',
              avatarUrl: '',
              isOnline: true,
            ),
            content: content,
            createdAt: DateTime(2026),
          )
        : messageToEcho?.copyWith(clientMessageId: clientMessageId);
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
      _acknowledgements.close(),
      _readReceipts.close(),
      _statuses.close(),
    ]);
  }
}

class _ReadTrackingDataSource implements ChatDataSource {
  List<ChatMessageContent> history = const [];
  @override
  Future<(List<ChatMessageContent>, PaginationData)> getMessagesPage({
    required String conversationId,
    int page = 1,
  }) async => (history, PaginationData(perPage: 20, totalPages: 1));
  int readCount = 0;
  int contactRequests = 0;
  Completer<ConversationContent>? contactResponse;
  ConversationContent contactSnapshot = const ConversationContent.initial();

  @override
  Future<ConversationContent> getConversation(String conversationId) {
    contactRequests++;
    return contactResponse?.future ?? Future.value(contactSnapshot);
  }

  final List<String> sentClientIds = [];
  bool wrongIdentity = false;

  @override
  Future<ChatMessageContent> sendMessage({
    required String conversationId,
    required String content,
    String clientMessageId = '',
  }) async {
    sentClientIds.add(clientMessageId);
    return ChatMessageContent(
      id: 'rest-message',
      body: content,
      time: '',
      isFromMe: true,
      conversationId: conversationId,
      clientMessageId: wrongIdentity ? 'another-id' : clientMessageId,
      sender: const ChatParticipantContent.initial().copyWith(
        id: 'current-user-id',
      ),
    );
  }

  @override
  Future<ChatReadContent> markConversationAsRead(String conversationId) async {
    readCount++;
    return const ChatReadContent.initial();
  }

  @override
  dynamic noSuchMethod(Invocation invocation) => super.noSuchMethod(invocation);
}

class _MemoryChatLocalStore implements ChatLocalStore {
  bool fail = false;
  ChatLocalState state = const ChatLocalState.initial();
  @override
  Future<ChatLocalState> read() async => state;
  @override
  Future<void> write(ChatLocalState value) async {
    if (fail) throw StateError('Device storage is unavailable');
    state = value;
  }
}

Future<void> _flushWrites(WidgetTester tester) async {
  for (var step = 0; step < 5; step++) {
    await tester.pump();
  }
}
