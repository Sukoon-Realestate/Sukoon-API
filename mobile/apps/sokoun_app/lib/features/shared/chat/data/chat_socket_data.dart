import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/helpers/cache_service.dart';
import 'package:melos_core/core/network/dio_service.dart';
import 'package:melos_core/core/network/session_auth_service.dart';
import 'package:melos_core/core/socket_service/web_socket_client.dart';

import 'models/chat_socket_message.dart';
import 'socket_events.dart';

abstract interface class ChatSocketDataSource {
  Future<WebSocketHelper<ChatSocketMessage>> create({
    required Future<void> Function(ChatSocketMessage message) onReceiveMessage,
    Future<void> Function(String event, Map<String, dynamic> data)?
    onReceiveAnyEvent,
    SocketCallback? onConnect,
    SocketDisconnectCallback? onDisconnect,
    SocketCallback? onReconnect,
    SocketErrorCallback? onError,
  });
}

final class ChatSocketApiDataSource implements ChatSocketDataSource {
  const ChatSocketApiDataSource();

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
    final SessionAuthService sessionAuth = injector<SessionAuthService>();
    final Uri socketUri = await _resolveSocketUri(sessionAuth);

    return WebSocketClientImpl<ChatSocketMessage>(
      url: socketUri,
      accessTokenProvider: sessionAuth.getAccessToken,
      refreshAccessToken: sessionAuth.refreshSession,
      jsonToMessage: ChatSocketMessage.fromJson,
      onReceiveMessage: onReceiveMessage,
      onReceiveAnyEvent: onReceiveAnyEvent,
      onConnect: onConnect,
      onDisconnect: onDisconnect,
      onReconnect: onReconnect,
      onError: onError,
      events: const WebSocketEvents(
        messageEvents: WebSocketMessageEvents(
          receiveMsgEvent: SocketEvents.receiveMessage,
          sendMsgEvent: SocketEvents.sendMessage,
          readMsgEvent: SocketEvents.readMessage,
        ),
      ),
    );
  }

  Future<Uri> _resolveSocketUri(SessionAuthService sessionAuth) async {
    final String configuredUrl =
        (await SecureStorage.read(
          SecureLocalVariableKeys.socetIoUrl,
        ))?.trim() ??
        '';
    final Uri? configuredUri = Uri.tryParse(configuredUrl);
    if (configuredUri != null &&
        configuredUri.hasScheme &&
        configuredUri.host.isNotEmpty) {
      return _withSocketScheme(
        configuredUri.replace(path: '/ws/chat/', query: null, fragment: null),
      );
    }

    final Uri? baseUri = await sessionAuth.getBaseUri();
    if (baseUri == null) {
      throw StateError('Chat socket URL is not configured.');
    }
    return _withSocketScheme(
      baseUri.replace(path: '/ws/chat/', query: null, fragment: null),
    );
  }

  Uri _withSocketScheme(Uri uri) {
    final String scheme = switch (uri.scheme) {
      'https' => 'wss',
      'http' => 'ws',
      _ => uri.scheme,
    };
    return uri.replace(scheme: scheme, query: null, fragment: null);
  }
}

abstract final class ChatSocketData {
  static ChatSocketDataSource get source =>
      injector.isRegistered<ChatSocketDataSource>()
      ? injector<ChatSocketDataSource>()
      : const ChatSocketApiDataSource();

  static Future<WebSocketHelper<ChatSocketMessage>> create({
    required Future<void> Function(ChatSocketMessage message) onReceiveMessage,
    Future<void> Function(String event, Map<String, dynamic> data)?
    onReceiveAnyEvent,
    SocketCallback? onConnect,
    SocketDisconnectCallback? onDisconnect,
    SocketCallback? onReconnect,
    SocketErrorCallback? onError,
  }) => source.create(
    onReceiveMessage: onReceiveMessage,
    onReceiveAnyEvent: onReceiveAnyEvent,
    onConnect: onConnect,
    onDisconnect: onDisconnect,
    onReconnect: onReconnect,
    onError: onError,
  );
}
