import 'package:sokoun_app/features/shared/chat/data/models/chat_participant_content.dart';
import 'package:melos_core/core/socket_service/web_socket_client.dart';
import 'package:melos_core/core/shared/models/user_models/user_model.dart';
import 'package:sokoun_app/features/shared/chat/data/chat_socket_data.dart';
import 'package:sokoun_app/features/shared/chat/data/models/chat_socket_message.dart';

class RecordingChatSocketSource implements ChatSocketDataSource {
  int creations = 0;
  int connections = 0;
  int disconnections = 0;
  int readRequests = 0;
  int sentMessages = 0;
  bool echoSentMessages = false;
  Future<void> Function(ChatSocketMessage)? _onReceiveMessage;
  Future<void> Function(String, Map<String, dynamic>)? _onReceiveAnyEvent;
  Map<String, dynamic>? lastSentData;

  Future<void> receive(ChatSocketMessage message) async {
    await _onReceiveMessage?.call(message);
  }

  Future<void> receiveEvent(String event, Map<String, dynamic> data) async {
    await _onReceiveAnyEvent?.call(event, data);
  }

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
    _onReceiveMessage = onReceiveMessage;
    _onReceiveAnyEvent = onReceiveAnyEvent;
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
  Future<void> sendMessage(Map<String, dynamic> data) async {
    source.sentMessages++;
    source.lastSentData = Map.of(data);
    if (!source.echoSentMessages) return;
    await source.receive(
      const ChatSocketMessage.initial().copyWith(
        id: 'socket-message-${source.sentMessages}',
        conversationId: data['conversation_id'].toString(),
        content: data['content'].toString(),
        clientMessageId: data['client_message_id']?.toString() ?? '',
        sender: const ChatParticipantContent.initial().copyWith(
          id: UserModel.currentUser?.id ?? '',
        ),
      ),
    );
  }

  @override
  Future<void> emitEvent({
    required String event,
    Map<String, dynamic>? data,
  }) async {}
}
