import 'dart:async';
import 'dart:convert';
import 'dart:developer' show log;
import 'dart:io';
import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';

import '../../config/res/config_imports.dart';

part 'navigation_types.dart';
part 'notification_payload.dart';
part 'notification_routes.dart';

Future<void> backgroundHandler(RemoteMessage message) async {
  await Firebase.initializeApp();
  log('========= >>> backGroundMessage ${message.data}');
}

class NotificationService {
  final FlutterLocalNotificationsPlugin _flutterLocalNotificationsPlugin =
      FlutterLocalNotificationsPlugin();

  static const AndroidNotificationChannel _channel = AndroidNotificationChannel(
    'high_importance_channel', // id
    'High Importance Notifications', // title
    importance: Importance.high,
  );

  static String deviceToken = '1234';
  bool _isConfigured = false;

  Stream<String> get onTokenRefresh =>
      FirebaseMessaging.instance.onTokenRefresh;

  Future<void> _createAndroidChannel() async {
    await _flutterLocalNotificationsPlugin
        .resolvePlatformSpecificImplementation<
          AndroidFlutterLocalNotificationsPlugin
        >()
        ?.createNotificationChannel(_channel);
  }

  void _showNotification(RemoteMessage message) async {
    if (Platform.isIOS) return;
    const DarwinNotificationDetails iOSPlatformChannelSpecifics =
        DarwinNotificationDetails(
          presentAlert: true,
          presentBadge: true,
          presentSound: true,
        );
    final AndroidNotificationDetails androidPlatformChannelSpecifics =
        AndroidNotificationDetails(
          _channel.id,
          _channel.name,
          channelDescription: ConstantManager.projectName,
          enableVibration: true,
          playSound: true,
          icon: '@mipmap/ic_launcher',
          importance: Importance.high,
          priority: Priority.max,
        );
    final notificationDetails = NotificationDetails(
      android: androidPlatformChannelSpecifics,
      iOS: iOSPlatformChannelSpecifics,
    );
    final notification = message.notification;
    await _flutterLocalNotificationsPlugin.show(
      notification.hashCode,
      notification?.title ?? '',
      notification?.body,
      notificationDetails,
      payload: json.encode(message.toMap()),
    );
  }

  Future<void> _initLocalNotification() async {
    const AndroidInitializationSettings initializationSettingsAndroid =
        AndroidInitializationSettings('@mipmap/ic_launcher');

    const DarwinInitializationSettings initializationSettingsIOS =
        DarwinInitializationSettings(
          requestAlertPermission: false,
          requestBadgePermission: false,
          requestSoundPermission: false,
        );

    const InitializationSettings initializationSettings =
        InitializationSettings(
          android: initializationSettingsAndroid,
          iOS: initializationSettingsIOS,
        );
    await _flutterLocalNotificationsPlugin.initialize(
      initializationSettings,
      onDidReceiveNotificationResponse: (NotificationResponse? payload) {
        if (payload?.payload != null) {
          _handleNotificationsTap(
            RemoteMessage.fromMap(json.decode(payload?.payload ?? '')),
          );
        }
      },
    );
  }

  void _handleNotificationsTap(RemoteMessage? message) async {
    if (message == null) return;
    NotificationNavigator._instance?.onRoutingMessage(message);
  }

  Future<String?> getFcmToken() async {
    try {
      final String? deviceToken = await FirebaseMessaging.instance.getToken();
      return deviceToken;
    } on Exception catch (e) {
      deviceToken = '1234';
    }
  }

  Future<void> saveFcmToken() async {
    final String? token = await getFcmToken();
    log('Firebase FCM token is ${token == null ? 'unavailable' : 'ready'}');
  }

  Future<void> _setForegroundNotificationOptions() async {
    FirebaseMessaging.instance.setForegroundNotificationPresentationOptions(
      alert: true,
      badge: true,
      sound: true,
    );
  }

  Future<void> setupNotifications({
    void Function(RemoteMessage message)? onForegroundMessage,
  }) async {
    if (_isConfigured) return;
    // Native permission is requested by the app's explanation flow. Listeners
    // and notification routing must work even when that prompt is skipped.
    await _initLocalNotification();
    if (Platform.isAndroid) await _createAndroidChannel();
    await Future.wait([
      _setForegroundNotificationOptions(),
      NotificationNavigator._instance!.init(),
    ]);
    _configureNotification(onForegroundMessage: onForegroundMessage);
    _isConfigured = true;
  }

  void _configureNotification({
    void Function(RemoteMessage message)? onForegroundMessage,
  }) {
    FirebaseMessaging.onBackgroundMessage(backgroundHandler);
    FirebaseMessaging.onMessage.listen((RemoteMessage event) {
      _showNotification(event);
      onForegroundMessage?.call(event);
    });
    FirebaseMessaging.onMessageOpenedApp.listen((RemoteMessage event) {
      _handleNotificationsTap(event);
    });
  }
}

class NotificationNavigator {
  NotificationNavigator._({
    required this.onRoutingMessage,
    required this.onNoInitialMessage,
  });

  static NotificationNavigator? _instance;
  RemoteMessage? _message;

  factory NotificationNavigator({
    required void Function(RemoteMessage message) onRoutingMessage,
    required void Function() onNoInitialMessage,
  }) {
    return _instance ??= NotificationNavigator._(
      onRoutingMessage: onRoutingMessage,
      onNoInitialMessage: onNoInitialMessage,
    );
  }

  Future<void> init() async {
    _message = await FirebaseMessaging.instance.getInitialMessage();
    if (_message != null) {
      onRoutingMessage(_message!);
    } else {
      onNoInitialMessage();
    }
  }

  final void Function(RemoteMessage message) onRoutingMessage;
  final void Function() onNoInitialMessage;
}
