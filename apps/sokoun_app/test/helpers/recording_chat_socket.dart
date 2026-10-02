import 'package:melos_core/core/socket_service/web_socket_client.dart';
import 'package:sokoun_app/features/shared/chat/data/chat_socket_data.dart';
import 'package:sokoun_app/features/shared/chat/data/models/chat_socket_message.dart';

class RecordingChatSocketSource implements ChatSocketDataSource {
  int creations = 0;
  int connections = 0;
  int disconnections = 0;
  int readRequests = 0;

  @override
  Future<WebSocketHelper<ChatSocketMessage>> create({
    required Future<void> Function(ChatSocketMessage message) onReceiveMessage,
    Future<void> Function(String event, Map<String, dynamic> data)?
    onReceiveAnyEvent,
    SocketCallback? onConnect,
    SocketDisconnectCallback? onDisconnect,
    SocketCallback? onReconnect,
    SocketErrorCallback? onError,
  }) async {
    creations++;
    return _RecordingChatSocket(this, onConnect, onDisconnect);
  }
}

class _RecordingChatSocket implements WebSocketHelper<ChatSocketMessage> {
  _RecordingChatSocket(this.source, this.onConnect, this.onDisconnect);

  final RecordingChatSocketSource source;
  final SocketCallback? onConnect;
  final SocketDisconnectCallback? onDisconnect;

  @override
  bool isConnected = false;

  @override
  Future<void> connect() async {
    source.connections++;
    isConnected = true;
    await onConnect?.call();
  }

  @override
  Future<void> disconnect() async {
    source.disconnections++;
    isConnected = false;
    await onDisconnect?.call(null, null);
  }

  @override
  Future<void> reconnect() async {
    await disconnect();
    await connect();
  }

  @override
  Future<void> markConversationAsRead(String conversationId) async {
    source.readRequests++;
  }

  @override
  Future<void> sendMessage(Map<String, dynamic> data) async {}

  @override
  Future<void> emitEvent({
    required String event,
    Map<String, dynamic>? data,
  }) async {}
}
