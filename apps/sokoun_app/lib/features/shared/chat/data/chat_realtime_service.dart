import 'dart:async';
import 'dart:developer';

import 'package:melos_core/core/socket_service/web_socket_client.dart';

import 'chat_socket_data.dart';
import 'models/chat_socket_message.dart';
import 'models/message_params_model.dart';
import 'socket_events.dart';

enum ChatRealtimeStatus { disconnected, connecting, connected, error }

abstract interface class ChatRealtimeGateway {
  Stream<ChatSocketMessage> get messages;

  Stream<ChatReadReceipt> get readReceipts;

  Stream<ChatRealtimeStatus> get statuses;

  ChatRealtimeStatus get status;

  bool get isConnected;

  String? get activeConversationId;

  void setActiveConversation(String? conversationId);

  Future<void> connect();

  Future<void> disconnect();

  Future<void> sendMessage({
    required String conversationId,
    required String content,
  });

  Future<void> markConversationAsRead(String conversationId);
}

class ChatReadReceipt {
  const ChatReadReceipt({required this.conversationId, required this.readerId});

  factory ChatReadReceipt.fromJson(Map<String, dynamic> json) {
    return ChatReadReceipt(
      conversationId: json['conversation_id']?.toString() ?? '',
      readerId: json['reader_id']?.toString() ?? '',
    );
  }

  final String conversationId;
  final String readerId;
}

/// Owns the one personal `/ws/chat/` connection shared by all conversations.
final class ChatRealtimeService implements ChatRealtimeGateway {
  ChatRealtimeService._();

  static final ChatRealtimeService instance = ChatRealtimeService._();

  final StreamController<ChatSocketMessage> _messages =
      StreamController<ChatSocketMessage>.broadcast(sync: true);
  final StreamController<ChatReadReceipt> _readReceipts =
      StreamController<ChatReadReceipt>.broadcast(sync: true);
  final StreamController<ChatRealtimeStatus> _statuses =
      StreamController<ChatRealtimeStatus>.broadcast(sync: true);

  WebSocketHelper<ChatSocketMessage>? _socket;
  Future<void>? _connectionRequest;
  ChatRealtimeStatus _status = ChatRealtimeStatus.disconnected;
  @override
  String? activeConversationId;

  @override
  Stream<ChatSocketMessage> get messages => _messages.stream;

  @override
  Stream<ChatReadReceipt> get readReceipts => _readReceipts.stream;

  @override
  Stream<ChatRealtimeStatus> get statuses => _statuses.stream;

  @override
  ChatRealtimeStatus get status => _status;

  @override
  bool get isConnected => _socket?.isConnected ?? false;

  @override
  void setActiveConversation(String? conversationId) {
    activeConversationId = conversationId;
  }

  @override
  Future<void> connect() {
    if (isConnected) return Future<void>.value();
    final Future<void>? pending = _connectionRequest;
    if (pending != null) return pending;

    final Future<void> request = _connect();
    _connectionRequest = request;
    return request.whenComplete(() {
      if (identical(_connectionRequest, request)) _connectionRequest = null;
    });
  }

  Future<void> _connect() async {
    _setStatus(ChatRealtimeStatus.connecting);
    try {
      final WebSocketHelper<ChatSocketMessage> socket =
          _socket ??
          await ChatSocketData.create(
            onReceiveMessage: (message) async => _messages.add(message),
            onReceiveAnyEvent: _receiveEvent,
            onConnect: () => _setStatus(ChatRealtimeStatus.connected),
            onReconnect: () => _setStatus(ChatRealtimeStatus.connected),
            onDisconnect: (_, _) => _setStatus(ChatRealtimeStatus.disconnected),
            onError: _handleError,
          );
      _socket = socket;
      await socket.connect();
    } catch (error, stackTrace) {
      await _handleError(error, stackTrace);
    }
  }

  @override
  Future<void> disconnect() async {
    await _socket?.disconnect();
    _setStatus(ChatRealtimeStatus.disconnected);
  }

  @override
  Future<void> sendMessage({
    required String conversationId,
    required String content,
  }) async {
    final WebSocketHelper<ChatSocketMessage>? socket = _socket;
    if (socket == null || !socket.isConnected) {
      throw const SocketNotConnectedException();
    }
    await socket.sendMessage(
      MessageParamsModel(
        conversationId: conversationId,
        content: content,
      ).toSocketJson(),
    );
  }

  @override
  Future<void> markConversationAsRead(String conversationId) async {
    final WebSocketHelper<ChatSocketMessage>? socket = _socket;
    if (socket == null || !socket.isConnected) {
      throw const SocketNotConnectedException();
    }
    await socket.markConversationAsRead(conversationId);
  }

  Future<void> _receiveEvent(
    String event,
    Map<String, dynamic> eventData,
  ) async {
    log('the data is $eventData');
    if (event != SocketEvents.readMessage) return;
    final Object? payload = eventData['payload'];
    if (payload is! Map) return;
    _readReceipts.add(
      ChatReadReceipt.fromJson(Map<String, dynamic>.from(payload)),
    );
  }

  Future<void> _handleError(Object error, StackTrace stackTrace) async {
    log('Chat realtime connection error: $error', stackTrace: stackTrace);
    _setStatus(ChatRealtimeStatus.error);
  }

  void _setStatus(ChatRealtimeStatus status) {
    _status = status;
    _statuses.add(status);
  }
}
