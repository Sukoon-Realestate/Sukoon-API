import 'dart:async';
import 'dart:developer';
import 'package:socket_io_client/socket_io_client.dart' as IO;

import '../../config/language/locale_keys.g.dart';
import '../widgets/chat_builder/chat_message.dart';
import '../widgets/toast_messages/custom_messages.dart';

class MessageEvents {
  final String receiveMsgEvent;
  final String sendMsgEvent;

  MessageEvents({
    required this.receiveMsgEvent,
    required this.sendMsgEvent,
  });
}

class ChatEvents{
  final String enterChatEvent;
  final String exitChatEvent;

  ChatEvents({
    required this.enterChatEvent,
    required this.exitChatEvent,
  });
}

class EasyChatEvents{
  final MessageEvents messageEvents;
  final ChatEvents chatEvents;
  final List<String> otherEvents;

  EasyChatEvents({
    required this.chatEvents,
    required this.messageEvents,
    required this.otherEvents
  });
}



abstract interface class SocketHelper{
  final String url;
  final int roomId;
  final bool enableOfflineState;
  final dynamic Function(dynamic)? onConnect;
  final dynamic Function(dynamic)? onDisconnect;
  final dynamic Function(dynamic)? onReconnect;
  final ChatMessages Function(Map<String, dynamic> jsonMessage) jsonToChatMessage;
  final FutureOr<void> Function(ChatMessages message) onReceiveMessage;
  final FutureOr<void> Function(String event, dynamic data)? onReceiveAnyEvent;
  final EasyChatEvents events;

  FutureOr<void> initSocket();
  FutureOr<void> initConfig();
  FutureOr<void> connect();
  FutureOr<void> disconnect();
  FutureOr<void> reconnect();

  bool get isConnected;

  FutureOr<void> sendMessage(Map<String, dynamic> data);
  FutureOr<void> emitEvent({required String event, Map<String, dynamic>? data});

  SocketHelper({
    required this.url,
    required this.roomId,
    required this.jsonToChatMessage,
    required this.onReceiveMessage,
    required this.events,
    this.enableOfflineState = false,
    this.onReceiveAnyEvent,
    this.onConnect,
    this.onDisconnect,
    this.onReconnect,
  });
}

class ClientIOImpl extends SocketHelper{
  final Map<String, dynamic>? extraParams;
  final Map<String, String>? extraHeaders;

  ClientIOImpl({
    this.extraParams,
    this.extraHeaders,
    super.enableOfflineState,
    super.onConnect,
    super.onDisconnect,
    super.onReconnect,
    required super.url,
    required super.roomId,
    required super.jsonToChatMessage,
    required super.onReceiveMessage,
    required super.events,
    super.onReceiveAnyEvent,
  });

  late final IO.Socket socket;

  @override
  bool get isConnected => socket.connected;

  @override
  FutureOr<void> initSocket() {
    socket = IO.io(
        url,
        IO.OptionBuilder()
            .setTransports(['websocket'])
            .disableAutoConnect()
            // .enableReconnection()
            // .setReconnectionAttempts(double.infinity.toInt())
            // .setReconnectionDelay(1000)
            // .setReconnectionDelayMax(5000)
            .enableForceNew()
            .setExtraHeaders(extraHeaders ?? {})
            .setQuery(extraParams ?? {})
            .build()
    );
  }

  void initSocketStates(){
    socket.onConnect((d) {
      emitEvent(event: events.chatEvents.enterChatEvent, data: {'room_id' : roomId});
      onConnect?.call(d);
    });

    socket.onDisconnect((d) {
      onDisconnect?.call(d);
    });

    socket
      ..onReconnect((d) => onReconnect?.call(d))
      ..onReconnectAttempt((data) => log('Socket reconnection attempt: $data'))
      ..onReconnectError((data) => log('Socket reconnection error: $data'))
      ..onReconnectFailed((_) => log('Socket reconnection failed'));


    socket
      ..onConnectError((err) => log('❌ Socket connect error: $err'))
      ..onError((err) => log('❌ Socket error: $err'));
  }

  void onReceiveEvent(){
    socket.on(
        events.messageEvents.receiveMsgEvent,
            (data) => onReceiveMessage.call(jsonToChatMessage.call(data))
    );

    socket.onAny(
            (event, data) => onReceiveAnyEvent?.call(event, data)
    );
  }

  @override
  FutureOr<void> initConfig(){
    initSocketStates();
    onReceiveEvent();
  }

  @override
  FutureOr<void> connect() {
    socket.connect();
  }

  @override
  FutureOr<void> reconnect() {
    socket..disconnect()..connect();
  }

  @override
  FutureOr<void> disconnect() {
    if(socket.connected){
      emitEvent(event: events.chatEvents.exitChatEvent, data: {'room_id' : roomId});
      socket.disconnect();
      socket.dispose();
    }
  }

  // Future<void> _checkAndEmit({
  //   required FutureOr<void> Function() onConnected,
  //   required FutureOr<void> Function() onDisconnected,
  // })async{
  //   final connectivityResult = await Connectivity().checkConnectivity();
  //   if(connectivityResult.contains(ConnectivityResult.none)){
  //     await onDisconnected.call();
  //
  //   }else{
  //     await onConnected.call();
  //   }
  // }

  @override
  FutureOr<void> sendMessage(Map<String, dynamic> data) {
    _emit(event: events.messageEvents.sendMsgEvent, data: data);
  }

  @override
  FutureOr<void> emitEvent({required String event, Map<String, dynamic>? data}) {
    _emit(event: event, data: data);
  }

  void _emit({required String event, Map<String, dynamic>? data}){
    if(socket.connected){
      socket.emitWithAck(
          event, [data],
        ack: () => log('Server acknowledged: $data'),
      );

    }else{
      MessageUtils.showSnackBar(LocaleKeys.waitingForConnection);
      // throw Exception('the socket is not connected');
    }
  }
}

// class MessageEvents {
//   final String receiveMsgEvent;
//   final String sendMsgEvent;
//
//   MessageEvents({
//     required this.receiveMsgEvent,
//     required this.sendMsgEvent,
//   });
// }
//
// class ChatEvents{
//   final String enterChatEvent;
//   final String exitChatEvent;
//
//   ChatEvents({
//     required this.enterChatEvent,
//     required this.exitChatEvent,
//   });
// }
//
// class EasyChatEvents{
//   final MessageEvents messageEvents;
//   final ChatEvents chatEvents;
//   final List<String> otherEvents;
//
//   EasyChatEvents({
//     required this.chatEvents,
//     required this.messageEvents,
//     required this.otherEvents
//   });
// }
//
//
//
// abstract interface class SocketHelper<T>{
//   final String url;
//   final int roomId;
//   final bool enableOfflineState;
//   final dynamic Function(dynamic)? onConnect;
//   final dynamic Function(dynamic)? onDisconnect;
//   final dynamic Function(dynamic)? onReconnect;
//   final T Function(Map<String, dynamic> json) mapper;
//   final FutureOr<void> Function(T message) onReceiveMessage;
//   final FutureOr<void> Function(String event, dynamic data)? onReceiveAnyEvent;
//   final EasyChatEvents events;
//
//   FutureOr<void> initSocket();
//   FutureOr<void> initConfig();
//   FutureOr<void> connect();
//   FutureOr<void> disconnect();
//   FutureOr<void> reconnect();
//
//   bool get isConnected;
//
//   FutureOr<void> sendMessage(Map<String, dynamic> data);
//   FutureOr<void> emitEvent({required String event, Map<String, dynamic>? data});
//
//   SocketHelper({
//     required this.url,
//     required this.roomId,
//     required this.mapper,
//     required this.onReceiveMessage,
//     required this.events,
//     this.enableOfflineState = false,
//     this.onReceiveAnyEvent,
//     this.onConnect,
//     this.onDisconnect,
//     this.onReconnect,
//   });
// }
//
// class ClientIOImpl<T> extends SocketHelper<T>{
//   final Map<String, dynamic>? extraParams;
//   final Map<String, dynamic>? extraHeaders;
//
//   ClientIOImpl({
//     this.extraParams,
//     this.extraHeaders,
//     super.enableOfflineState,
//     super.onConnect,
//     super.onDisconnect,
//     super.onReconnect,
//     required super.url,
//     required super.roomId,
//     required super.mapper,
//     required super.onReceiveMessage,
//     required super.events,
//     super.onReceiveAnyEvent,
//   });
//
//   late final IO.Socket socket;
//
//   @override
//   bool get isConnected => socket.connected;
//
//   @override
//   FutureOr<void> initSocket() {
//     socket = IO.io(
//         url,
//         IO.OptionBuilder()
//             .setTransports(['websocket'])
//             .disableAutoConnect()
//         // .enableReconnection()
//         // .setReconnectionAttempts(double.infinity.toInt())
//         // .setReconnectionDelay(1000)
//         // .setReconnectionDelayMax(5000)
//             .enableForceNew()
//             .setExtraHeaders(extraHeaders ?? {})
//             .setQuery(extraParams ?? {})
//             .build()
//     );
//   }
//
//   void initSocketStates(){
//     socket.onConnect((d) {
//       emitEvent(event: events.chatEvents.enterChatEvent, data: {'room_id' : roomId});
//       onConnect?.call(d);
//     });
//
//     socket.onDisconnect((d) {
//       onDisconnect?.call(d);
//     });
//
//     socket
//       ..onReconnect((d) => onReconnect?.call(d))
//       ..onReconnectAttempt((data) => log('Socket reconnection attempt: $data'))
//       ..onReconnectError((data) => log('Socket reconnection error: $data'))
//       ..onReconnectFailed((_) => log('Socket reconnection failed'));
//
//
//     socket
//       ..onConnectError((err) => log('❌ Socket connect error: $err'))
//       ..onError((err) => log('❌ Socket error: $err'));
//   }
//
//   void onReceiveEvent(){
//     socket.on(
//         events.messageEvents.receiveMsgEvent,
//             (data) => onReceiveMessage.call(mapper.call(data))
//     );
//
//     socket.onAny(
//             (event, data) => onReceiveAnyEvent?.call(event, data)
//     );
//   }
//
//   @override
//   FutureOr<void> initConfig(){
//     initSocketStates();
//     onReceiveEvent();
//   }
//
//   @override
//   FutureOr<void> connect() {
//     socket.connect();
//   }
//
//   @override
//   FutureOr<void> reconnect() {
//     socket..disconnect()..connect();
//   }
//
//   @override
//   FutureOr<void> disconnect() {
//     emitEvent(event: events.chatEvents.exitChatEvent, data: {'room_id' : roomId});
//     socket.disconnect();
//     socket.dispose();
//   }
//
//   // Future<void> _checkAndEmit({
//   //   required FutureOr<void> Function() onConnected,
//   //   required FutureOr<void> Function() onDisconnected,
//   // })async{
//   //   final connectivityResult = await Connectivity().checkConnectivity();
//   //   if(connectivityResult.contains(ConnectivityResult.none)){
//   //     await onDisconnected.call();
//   //
//   //   }else{
//   //     await onConnected.call();
//   //   }
//   // }
//
//   @override
//   FutureOr<void> sendMessage(Map<String, dynamic> data) {
//     _emit(event: events.messageEvents.sendMsgEvent, data: data);
//   }
//
//   @override
//   FutureOr<void> emitEvent({required String event, Map<String, dynamic>? data}) {
//     _emit(event: event, data: data);
//   }
//
//   void _emit({required String event, Map<String, dynamic>? data}){
//     if(socket.connected){
//       socket.emitWithAck(
//         event, [data],
//         ack: () => log('Server acknowledged: $data'),
//       );
//
//     }else{
//       MessageUtils.showSnackBar(LocaleKeys.waitingForConnection);
//       // throw Exception('the socket is not connected');
//     }
//   }
// }