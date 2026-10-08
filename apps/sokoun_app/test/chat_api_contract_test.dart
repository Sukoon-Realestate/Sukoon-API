import 'helpers/account_test_dependencies.dart';
import 'package:melos_core/core/shared/models/user_models/user_model.dart';
import 'package:melos_core/core/shared/user_cubit/user_cubit.dart';
import 'package:sokoun_app/features/shared/unread_counts/data/models/unread_counts.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/base_crud/code/domain/usecases/pagination_response.dart';
import 'package:melos_core/core/network/api_endpoints.dart';
import 'package:melos_core/core/network/network_request.dart';
import 'package:melos_core/core/network/network_service.dart';
import 'package:sokoun_app/features/shared/chat/data/chat_data.dart';
import 'package:sokoun_app/features/shared/chat/data/chat_realtime_service.dart';
import 'package:sokoun_app/features/shared/chat/data/chat_socket_data.dart';
import 'helpers/recording_chat_socket.dart';
import 'package:sokoun_app/features/shared/chat/data/models/chat_content.dart';
import 'package:sokoun_app/features/shared/chat/data/models/chat_socket_message.dart';
import 'package:sokoun_app/features/shared/notifications/data/models/notification_payload_content.dart';

void main() {
  late _RecordingNetworkService network;

  setUp(() async {
    if (injector.isRegistered<UserCubit>()) {
      await injector.unregister<UserCubit>();
    }
    injector.registerSingleton<UserCubit>(
      TestAccountCubit(
        const UserModel(
          id: 'verified-test-account',
          name: '',
          phone: '',
          email: '',
          isVerified: true,
        ),
      ),
      dispose: (cubit) => cubit.close(),
    );
    if (injector.isRegistered<NetworkService>()) {
      await injector.unregister<NetworkService>();
    }
    network = _RecordingNetworkService();
    injector.registerSingleton<NetworkService>(network);
  });

  tearDown(() async {
    await injector.unregister<UserCubit>();
    if (injector.isRegistered<NetworkService>()) {
      await injector.unregister<NetworkService>();
    }
  });

  test('loads the documented paginated conversations endpoint', () async {
    expect(ApiConstants.refreshToken, 'auth/refresh/');

    final page = await ChatData.getConversationsPage(page: 2);

    expect(network.lastRequest?.path, ApiConstants.chatConversations);
    expect(network.lastRequest?.method, RequestMethod.get);
    expect(network.lastRequest?.queryParameters, {
      'page': 2,
      'page_size': ChatData.conversationsPageSize,
    });
    expect(page.$1.single.id, 'conversation-uuid');
    expect(page.$1.single.name, 'أحمد عمارة');
    expect(page.$1.single.unreadCount, 2);
    expect(page.$2.totalPages, 3);
  });

  test('creates a direct conversation with user_id', () async {
    final ConversationContent conversation = await ChatData.createConversation(
      'owner-uuid',
    );

    expect(network.lastRequest?.path, ApiConstants.createChatConversation);
    expect(network.lastRequest?.method, RequestMethod.post);
    expect(network.lastRequest?.body, {'user_id': 'owner-uuid'});
    expect(conversation.id, 'conversation-uuid');
  });

  test('refreshes participant contact through conversation details', () async {
    final conversation = await const ChatApiDataSource().getConversation(
      'conversation-uuid',
    );
    expect(network.lastRequest?.path, 'chat/conversations/conversation-uuid/');
    expect(network.lastRequest?.method, RequestMethod.get);
    expect(conversation.otherParticipant.id, 'owner-uuid');
  });

  test('online presence survives cached conversation snapshots', () {
    final ConversationContent conversation = ConversationContent.fromJson({
      'id': 'online-conversation',
      'other_participant': {
        'id': 'other-user',
        'full_name': 'Online account',
        'is_online': true,
      },
    });
    expect(conversation.isOnline, isTrue);
    expect(ConversationContent.fromJson(conversation.toJson()), conversation);

    final cached = const ConversationContent.initial().copyWith(isOnline: true);
    expect(ConversationContent.fromJson(cached.toJson()).isOnline, isTrue);
  });

  test('conversation permissions read the returned counterpart contract', () {
    for (final allowed in [false, true]) {
      final conversation = ConversationContent.fromJson({
        'id': 'conversation',
        'other_participant': {'id': 'owner', 'can_send': allowed},
      });
      expect(conversation.canSend, allowed);
      expect(ConversationContent.fromJson(conversation.toJson()), conversation);
    }
    // Older payloads still supply the current-account permission at the root.
    final denied = ConversationContent.fromJson({
      'can_send': false,
      'other_participant': {'can_send': true},
    });
    expect(denied.canSend, isFalse);
  });

  test('REST and socket messages share sparse participant parsing', () {
    final sender = {'id': 'other-user', 'name': 'Chat account'};
    final rest = ChatMessageContent.fromJson({'sender': sender});
    final socket = ChatSocketMessage.fromJson({'sender': sender});

    expect(rest.sender, socket.sender);
    expect(socket.sender.fullName, 'Chat account');
    expect(socket.sender.isOnline, isFalse);
    expect(ChatSocketMessage.fromJson(socket.toJson()), socket);
  });

  test('loads history and calls both REST fallback actions', () async {
    final history = await ChatData.getMessagesPage(
      conversationId: 'conversation-uuid',
      page: 1,
    );
    expect(
      network.lastRequest?.path,
      ApiConstants.chatMessages('conversation-uuid'),
    );
    expect(network.lastRequest?.queryParameters, {
      'page': 1,
      'page_size': ChatData.messagesPageSize,
    });
    expect(history.$1.single.body, 'السلام عليكم');
    expect(history.$1.single.sender.email, 'sender@example.com');

    final sent = await ChatData.sendMessage(
      conversationId: 'conversation-uuid',
      content: 'شكراً',
    );
    expect(
      network.lastRequest?.path,
      ApiConstants.createChatMessage('conversation-uuid'),
    );
    expect(network.lastRequest?.body, {'content': 'شكراً'});
    expect(sent.body, 'السلام عليكم');

    final read = await ChatData.markConversationAsRead('conversation-uuid');
    expect(
      network.lastRequest?.path,
      ApiConstants.markChatConversationRead('conversation-uuid'),
    );
    expect(network.lastRequest?.method, RequestMethod.post);
    expect(read.status, 'read');
  });

  test('maps FCM chat deep links and account unread totals', () {
    final NotificationPayloadContent payload =
        NotificationPayloadContent.fromJson({
          'conversation_id': 'conversation-uuid',
          'message_id': 'message-uuid',
          'sender_id': 'owner-uuid',
        });
    final UnreadCounts unread = UnreadCounts.fromJson({
      'unread_chat_messages_count': 5,
    });

    expect(payload.chatId, 'conversation-uuid');
    expect(payload.messageId, 'message-uuid');
    expect(payload.senderId, 'owner-uuid');
    expect(unread.chatCount, 5);
  });
  test(
    'client UUID is carried through REST and the personal socket ACK stream',
    () async {
      const clientId = 'a8b9d21a-137b-40c0-af9d-b70f520b7373';
      await ChatData.sendMessage(
        conversationId: 'conversation-uuid',
        content: 'Hello',
        clientMessageId: clientId,
      );
      expect(network.lastRequest?.body, {
        'content': 'Hello',
        'client_message_id': clientId,
      });
      final source = RecordingChatSocketSource();
      final service = ChatRealtimeService.instance;
      await service.disconnect();
      injector.registerSingleton<ChatSocketDataSource>(source);
      addTearDown(() async {
        await service.disconnect();
        await injector.unregister<ChatSocketDataSource>();
      });
      await service.connect();
      await service.sendMessage(
        conversationId: 'conversation-uuid',
        content: 'Hello',
        clientMessageId: clientId,
      );
      expect(source.lastSentData, {
        'conversation_id': 'conversation-uuid',
        'content': 'Hello',
        'client_message_id': clientId,
      });
      final received = service.acknowledgements.first;
      await source.receiveEvent('message.ack', {
        'payload': {
          'id': 'server-message',
          'client_message_id': clientId,
          'status': 'sent',
        },
      });
      final acknowledgement = await received;
      expect(acknowledgement.isSent, isTrue);
      expect(acknowledgement.clientMessageId, clientId);
    },
  );
}

class _RecordingNetworkService implements NetworkService {
  NetworkRequest? lastRequest;

  @override
  Future<BaseModel<Model>> callApi<Model>(
    NetworkRequest networkRequest, {
    Model Function(dynamic json)? mapper,
  }) async {
    lastRequest = networkRequest;
    final Map<String, dynamic> data = switch (networkRequest.path) {
      ApiConstants.chatConversations => _conversationPage,
      ApiConstants.createChatConversation => _conversation,
      'chat/conversations/conversation-uuid/' => _conversation,
      final String path when path.endsWith('/messages/') => _messagePage,
      final String path when path.endsWith('/messages/create/') => _message,
      final String path when path.endsWith('/read/') => const {
        'status': 'read',
      },
      _ => const {},
    };
    final Model value = mapper != null ? mapper(data) : data as Model;
    return BaseModel<Model>(key: '', msg: 'ok', data: value);
  }

  @override
  Future<void> clearSessionCookies() async {}

  @override
  Future<bool> hasSessionCookies() async => true;

  @override
  Future<void> updateBaseUrl() async {}

  static const Map<String, dynamic> _participant = {
    'id': 'owner-uuid',
    'first_name': 'أحمد',
    'last_name': 'عمارة',
    'full_name': 'أحمد عمارة',
    'email': 'sender@example.com',
    'avatar_url': 'https://example.com/avatar.jpg',
    'is_online': true,
  };

  static const Map<String, dynamic> _conversation = {
    'id': 'conversation-uuid',
    'other_participant': _participant,
    'last_message_preview': 'مرحباً',
    'last_message_at': '2026-09-15T02:37:04Z',
    'unread_count': 2,
    'updated_at': '2026-09-15T02:37:04Z',
  };

  static const Map<String, dynamic> _conversationPage = {
    'count': 41,
    'next': 'page-3',
    'previous': 'page-1',
    'results': [_conversation],
  };

  static const Map<String, dynamic> _message = {
    'id': 'message-uuid',
    'conversation': 'conversation-uuid',
    'sender': _participant,
    'content': 'السلام عليكم',
    'created_at': '2026-09-15T02:35:00Z',
  };

  static const Map<String, dynamic> _messagePage = {
    'count': 1,
    'next': null,
    'previous': null,
    'results': [_message],
  };
}
