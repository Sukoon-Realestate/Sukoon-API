import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:melos_core/core/socket_service/web_socket_client.dart';

void main() {
  test('authenticates and exchanges raw chat JSON events', () async {
    final HttpServer server = await HttpServer.bind(
      InternetAddress.loopbackIPv4,
      0,
    );
    final Completer<Uri> requestUri = Completer<Uri>();
    final StreamController<Map<String, dynamic>> serverEvents =
        StreamController<Map<String, dynamic>>.broadcast();

    server.listen((HttpRequest request) async {
      if (!requestUri.isCompleted) requestUri.complete(request.uri);
      final WebSocket webSocket = await WebSocketTransformer.upgrade(request);
      webSocket.listen((dynamic rawData) {
        final Map<String, dynamic> event = Map<String, dynamic>.from(
          jsonDecode(rawData as String) as Map,
        );
        serverEvents.add(event);
        if (event['type'] == 'message.send') {
          webSocket.add(
            jsonEncode({
              'type': 'message.new',
              'payload': {
                'id': 'message-id',
                'conversation': event['conversation_id'],
                'content': event['content'],
              },
            }),
          );
        }
      });
    });

    final Completer<Map<String, dynamic>> receivedMessage =
        Completer<Map<String, dynamic>>();
    final WebSocketClientImpl<Map<String, dynamic>> client =
        WebSocketClientImpl<Map<String, dynamic>>(
          url: Uri.parse('ws://${server.address.host}:${server.port}/ws/chat/'),
          accessTokenProvider: () async => 'access-token',
          jsonToMessage: (json) => json,
          onReceiveMessage: receivedMessage.complete,
        );

    addTearDown(() async {
      await client.disconnect();
      await serverEvents.close();
      await server.close(force: true);
    });

    await client.connect();
    expect(client.isConnected, isTrue);
    expect((await requestUri.future).queryParameters['token'], 'access-token');

    final Future<Map<String, dynamic>> sentEvent = serverEvents.stream.first;
    await client.sendMessage({
      'conversation_id': 'conversation-id',
      'content': 'Hello',
    });
    expect(await sentEvent, {
      'conversation_id': 'conversation-id',
      'content': 'Hello',
      'type': 'message.send',
    });
    expect(await receivedMessage.future, {
      'id': 'message-id',
      'conversation': 'conversation-id',
      'content': 'Hello',
    });

    final Future<Map<String, dynamic>> readEvent = serverEvents.stream.first;
    await client.markConversationAsRead('conversation-id');
    expect(await readEvent, {
      'conversation_id': 'conversation-id',
      'type': 'message.read',
    });
  });

  test('refreshes the JWT and reconnects after close code 4401', () async {
    final HttpServer server = await HttpServer.bind(
      InternetAddress.loopbackIPv4,
      0,
    );
    final List<String?> receivedTokens = <String?>[];
    final Completer<void> reconnected = Completer<void>();
    String token = 'expired-token';
    int refreshCount = 0;

    server.listen((HttpRequest request) async {
      receivedTokens.add(request.uri.queryParameters['token']);
      final WebSocket webSocket = await WebSocketTransformer.upgrade(request);
      if (receivedTokens.length == 1) {
        await webSocket.close(4401, 'Token expired');
      }
    });

    final WebSocketClientImpl<Map<String, dynamic>> client =
        WebSocketClientImpl<Map<String, dynamic>>(
          url: Uri.parse('ws://${server.address.host}:${server.port}/ws/chat/'),
          accessTokenProvider: () async => token,
          refreshAccessToken: () async {
            refreshCount++;
            token = 'fresh-token';
            return true;
          },
          jsonToMessage: (json) => json,
          onReceiveMessage: (_) {},
          onReconnect: reconnected.complete,
          reconnectDelays: const [Duration.zero],
        );

    addTearDown(() async {
      await client.disconnect();
      await server.close(force: true);
    });

    await client.connect();
    await reconnected.future.timeout(const Duration(seconds: 5));

    expect(refreshCount, 1);
    expect(receivedTokens, ['expired-token', 'fresh-token']);
    expect(client.isConnected, isTrue);
  });
}
