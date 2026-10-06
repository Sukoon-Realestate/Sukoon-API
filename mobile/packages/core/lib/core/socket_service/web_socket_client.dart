import 'dart:async';
import 'dart:convert';
import 'dart:developer';

import 'package:web_socket_channel/status.dart' as socket_status;
import 'package:web_socket_channel/web_socket_channel.dart';

typedef SocketChannelConnector = WebSocketChannel Function(Uri uri);
typedef SocketCallback = FutureOr<void> Function();
typedef SocketDisconnectCallback =
    FutureOr<void> Function(int? closeCode, String? closeReason);
typedef SocketErrorCallback =
    FutureOr<void> Function(Object error, StackTrace stackTrace);
typedef SocketEventCallback =
    FutureOr<void> Function(String event, Map<String, dynamic> data);

class WebSocketMessageEvents {
  const WebSocketMessageEvents({
    this.receiveMsgEvent = 'message.new',
    this.sendMsgEvent = 'message.send',
    this.readMsgEvent = 'message.read',
  });

  final String receiveMsgEvent;
  final String sendMsgEvent;
  final String readMsgEvent;
}

class WebSocketEvents {
  const WebSocketEvents({this.messageEvents = const WebSocketMessageEvents()});

  final WebSocketMessageEvents messageEvents;
}

abstract interface class WebSocketHelper<MessageModel> {
  bool get isConnected;

  Future<void> connect();

  Future<void> disconnect();

  Future<void> reconnect();

  Future<void> sendMessage(Map<String, dynamic> data);

  Future<void> markConversationAsRead(String conversationId);

  Future<void> emitEvent({required String event, Map<String, dynamic>? data});
}

class WebSocketClientImpl<MessageModel>
    implements WebSocketHelper<MessageModel> {
  WebSocketClientImpl({
    required this.url,
    required this.accessTokenProvider,
    required this.jsonToMessage,
    required this.onReceiveMessage,
    this.refreshAccessToken,
    this.onConnect,
    this.onDisconnect,
    this.onReconnect,
    this.onError,
    this.onReceiveAnyEvent,
    this.events = const WebSocketEvents(),
    this.reconnectDelays = const [
      Duration(seconds: 1),
      Duration(seconds: 2),
      Duration(seconds: 4),
      Duration(seconds: 8),
      Duration(seconds: 10),
    ],
    SocketChannelConnector? connector,
  }) : _connector = connector ?? WebSocketChannel.connect;

  final Uri url;
  final Future<String?> Function() accessTokenProvider;
  final Future<bool> Function()? refreshAccessToken;
  final MessageModel Function(Map<String, dynamic> json) jsonToMessage;
  final FutureOr<void> Function(MessageModel message) onReceiveMessage;
  final SocketCallback? onConnect;
  final SocketDisconnectCallback? onDisconnect;
  final SocketCallback? onReconnect;
  final SocketErrorCallback? onError;
  final SocketEventCallback? onReceiveAnyEvent;
  final WebSocketEvents events;
  final List<Duration> reconnectDelays;
  final SocketChannelConnector _connector;

  WebSocketChannel? _channel;
  StreamSubscription<dynamic>? _subscription;
  Timer? _reconnectTimer;
  Future<void>? _connectionRequest;
  bool _isConnected = false;
  bool _allowReconnect = false;
  bool _hasConnected = false;
  int _reconnectAttempt = 0;
  int _generation = 0;
  int? _handledGeneration;

  @override
  bool get isConnected => _isConnected;

  @override
  Future<void> connect() {
    _allowReconnect = true;
    if (_isConnected) return Future<void>.value();

    final Future<void>? pendingConnection = _connectionRequest;
    if (pendingConnection != null) return pendingConnection;

    final Future<void> request = _openConnection();
    _connectionRequest = request;
    return request.whenComplete(() {
      if (identical(_connectionRequest, request)) {
        _connectionRequest = null;
      }
    });
  }

  Future<void> _openConnection() async {
    _reconnectTimer?.cancel();
    final int generation = ++_generation;
    _handledGeneration = null;

    try {
      String token = (await accessTokenProvider())?.trim() ?? '';
      final Future<bool> Function()? refresh = refreshAccessToken;
      if (token.isEmpty && refresh != null) {
        if (!_allowReconnect || generation != _generation) return;
        if (await refresh()) {
          token = (await accessTokenProvider())?.trim() ?? '';
        }
      }
      if (token.isEmpty) {
        throw const SocketAuthenticationException(
          'A JWT access token is required to open the chat socket.',
        );
      }

      if (!_allowReconnect || generation != _generation) return;

      final Uri authenticatedUrl = url.replace(
        queryParameters: {...url.queryParameters, 'token': token},
      );
      final WebSocketChannel channel = _connector(authenticatedUrl);
      _channel = channel;
      _subscription = channel.stream.listen(
        _handleIncomingData,
        onError: (Object error, StackTrace stackTrace) {
          unawaited(
            _handleConnectionEnded(
              generation: generation,
              error: error,
              stackTrace: stackTrace,
            ),
          );
        },
        onDone: () {
          unawaited(
            _handleConnectionEnded(
              generation: generation,
              closeCode: channel.closeCode,
              closeReason: channel.closeReason,
            ),
          );
        },
        cancelOnError: false,
      );

      await channel.ready;
      if (!_allowReconnect || generation != _generation) {
        await channel.sink.close(socket_status.normalClosure);
        return;
      }

      _isConnected = true;
      _reconnectAttempt = 0;
      if (_hasConnected) {
        await _invokeCallback(onReconnect);
      } else {
        _hasConnected = true;
        await _invokeCallback(onConnect);
      }
    } catch (error, stackTrace) {
      await _handleConnectionEnded(
        generation: generation,
        error: error,
        stackTrace: stackTrace,
      );
    }
  }

  void _handleIncomingData(dynamic rawData) {
    try {
      if (rawData is! String) {
        throw const FormatException(
          'Chat socket only accepts JSON text frames.',
        );
      }

      final dynamic decoded = jsonDecode(rawData);
      if (decoded is! Map) {
        throw const FormatException('Chat socket event must be a JSON object.');
      }

      final Map<String, dynamic> eventData = Map<String, dynamic>.from(decoded);
      final String event = eventData['type']?.toString() ?? '';
      if (event.isEmpty) {
        throw const FormatException('Chat socket event is missing its type.');
      }

      if (event == events.messageEvents.receiveMsgEvent) {
        final dynamic payload = eventData['payload'];
        log('the payload is $payload');
        if (payload is! Map) {
          throw const FormatException('message.new is missing its payload.');
        }
        final MessageModel message = jsonToMessage(
          Map<String, dynamic>.from(payload),
        );
        unawaited(_invokeMessageCallback(message));
      }

      final SocketEventCallback? eventCallback = onReceiveAnyEvent;
      if (eventCallback != null) {
        unawaited(_invokeEventCallback(eventCallback, event, eventData));
      }
    } catch (error, stackTrace) {
      unawaited(_reportError(error, stackTrace));
    }
  }

  Future<void> _handleConnectionEnded({
    required int generation,
    Object? error,
    StackTrace? stackTrace,
    int? closeCode,
    String? closeReason,
  }) async {
    if (generation != _generation || _handledGeneration == generation) return;
    _handledGeneration = generation;
    _isConnected = false;
    _channel = null;
    await _subscription?.cancel();
    _subscription = null;

    if (error != null) {
      await _reportError(error, stackTrace ?? StackTrace.current);
    }
    await _invokeDisconnectCallback(closeCode, closeReason);
    if (!_allowReconnect || error is SocketAuthenticationException) return;

    if (closeCode == 4401 || _isForbiddenHandshake(error)) {
      final Future<bool> Function()? refresh = refreshAccessToken;
      if (refresh == null || !await refresh()) {
        return;
      }
      _scheduleReconnect(Duration.zero);
      return;
    }

    _scheduleReconnect(_nextReconnectDelay());
  }

  bool _isForbiddenHandshake(Object? error) {
    if (error == null) return false;
    final String description = error.toString().toLowerCase();
    return description.contains('403') || description.contains('forbidden');
  }

  Duration _nextReconnectDelay() {
    if (reconnectDelays.isEmpty) return Duration.zero;
    final int index = _reconnectAttempt.clamp(0, reconnectDelays.length - 1);
    _reconnectAttempt++;
    return reconnectDelays[index];
  }

  void _scheduleReconnect(Duration delay) {
    _reconnectTimer?.cancel();
    _reconnectTimer = Timer(delay, () {
      if (_allowReconnect) unawaited(connect());
    });
  }

  @override
  Future<void> reconnect() async {
    await _closeCurrentConnection(notify: false);
    _allowReconnect = true;
    await connect();
  }

  @override
  Future<void> disconnect() async {
    _allowReconnect = false;
    _reconnectTimer?.cancel();
    await _closeCurrentConnection(notify: true);
  }

  Future<void> _closeCurrentConnection({required bool notify}) async {
    ++_generation;
    _handledGeneration = null;
    _isConnected = false;
    final StreamSubscription<dynamic>? subscription = _subscription;
    final WebSocketChannel? channel = _channel;
    _subscription = null;
    _channel = null;
    await subscription?.cancel();
    await channel?.sink.close(socket_status.normalClosure);
    if (notify && (subscription != null || channel != null)) {
      await _invokeDisconnectCallback(
        socket_status.normalClosure,
        'Client disconnected',
      );
    }
  }

  @override
  Future<void> sendMessage(Map<String, dynamic> data) {
    return emitEvent(event: events.messageEvents.sendMsgEvent, data: data);
  }

  @override
  Future<void> markConversationAsRead(String conversationId) {
    return emitEvent(
      event: events.messageEvents.readMsgEvent,
      data: {'conversation_id': conversationId},
    );
  }

  @override
  Future<void> emitEvent({
    required String event,
    Map<String, dynamic>? data,
  }) async {
    final WebSocketChannel? channel = _channel;
    if (!_isConnected || channel == null) {
      throw const SocketNotConnectedException();
    }

    channel.sink.add(jsonEncode({...?data, 'type': event}));
  }

  Future<void> _invokeCallback(SocketCallback? callback) async {
    if (callback == null) return;
    try {
      await callback();
    } catch (error, stackTrace) {
      await _reportError(error, stackTrace);
    }
  }

  Future<void> _invokeDisconnectCallback(
    int? closeCode,
    String? closeReason,
  ) async {
    final SocketDisconnectCallback? callback = onDisconnect;
    if (callback == null) return;
    try {
      await callback(closeCode, closeReason);
    } catch (error, stackTrace) {
      await _reportError(error, stackTrace);
    }
  }

  Future<void> _invokeMessageCallback(MessageModel message) async {
    try {
      await onReceiveMessage(message);
    } catch (error, stackTrace) {
      await _reportError(error, stackTrace);
    }
  }

  Future<void> _invokeEventCallback(
    SocketEventCallback callback,
    String event,
    Map<String, dynamic> data,
  ) async {
    try {
      await callback(event, data);
    } catch (error, stackTrace) {
      await _reportError(error, stackTrace);
    }
  }

  Future<void> _reportError(Object error, StackTrace stackTrace) async {
    log('Chat socket error: $error', stackTrace: stackTrace);
    final SocketErrorCallback? callback = onError;
    if (callback == null) return;
    try {
      await callback(error, stackTrace);
    } catch (callbackError, callbackStackTrace) {
      log(
        'Chat socket error callback failed: $callbackError',
        stackTrace: callbackStackTrace,
      );
    }
  }
}

class SocketNotConnectedException implements Exception {
  const SocketNotConnectedException();

  @override
  String toString() => 'The chat socket is not connected.';
}

class SocketAuthenticationException implements Exception {
  const SocketAuthenticationException(this.message);

  final String message;

  @override
  String toString() => message;
}
