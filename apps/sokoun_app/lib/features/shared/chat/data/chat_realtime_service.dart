import 'dart:async';
import 'dart:developer';

import 'package:melos_core/core/socket_service/web_socket_client.dart';
import 'package:melos_core/core/shared/models/user_models/user_model.dart';

import 'chat_socket_data.dart';
import 'models/chat_socket_message.dart';

enum ChatRealtimeStatus { disconnected, connecting, connected, error }

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
final class ChatRealtimeService {
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
  String? activeConversationId;

  Stream<ChatSocketMessage> get messages => _messages.stream;
  Stream<ChatReadReceipt> get readReceipts => _readReceipts.stream;
  Stream<ChatRealtimeStatus> get statuses => _statuses.stream;
  ChatRealtimeStatus get status => _status;
  bool get isConnected => _socket?.isConnected ?? false;

  void setActiveConversation(String? conversationId) {
    activeConversationId = conversationId;
  }

  Future<void> connect() {
    if (!UserModel.isAuthenticated) return Future<void>.value();
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

  Future<void> disconnect() async {
    await _socket?.disconnect();
    _setStatus(ChatRealtimeStatus.disconnected);
  }

  Future<void> sendMessage({
    required String conversationId,
    required String content,
  }) async {
    final WebSocketHelper<ChatSocketMessage>? socket = _socket;
    if (socket == null || !socket.isConnected) {
      throw const SocketNotConnectedException();
    }
    await socket.sendMessage({
      'conversation_id': conversationId,
      'content': content,
    });
  }

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
    if (event != 'message.read') return;
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
