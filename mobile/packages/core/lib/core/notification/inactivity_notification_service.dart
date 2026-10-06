import 'dart:io';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:timezone/data/latest_all.dart' as tz;
import 'package:timezone/timezone.dart' as tz;

class InactivityNotificationService {
  static const int _notificationId = 9001;
  static const String _channelId = 'inactivity_channel';
  static const String _channelName = 'Inactivity Reminders';

  static final FlutterLocalNotificationsPlugin _plugin =
      FlutterLocalNotificationsPlugin();

  static bool _initialized = false;

  static Future<void> init() async {
    if (_initialized) return;
    tz.initializeTimeZones();

    const androidSettings = AndroidInitializationSettings(
      '@mipmap/ic_launcher',
    );
    const iosSettings = DarwinInitializationSettings(
      requestAlertPermission: false,
      requestBadgePermission: false,
      requestSoundPermission: false,
    );
    await _plugin.initialize(
      const InitializationSettings(android: androidSettings, iOS: iosSettings),
    );

    if (Platform.isAndroid) {
      await _plugin
          .resolvePlatformSpecificImplementation<
            AndroidFlutterLocalNotificationsPlugin
          >()
          ?.createNotificationChannel(
            const AndroidNotificationChannel(
              _channelId,
              _channelName,
              description: 'Reminds users to return to the app',
              importance: Importance.high,
            ),
          );
    }
    _initialized = true;
  }

  /// Cancels any pending reminder and schedules a fresh one 24h from now.
  /// Call this on every successful API request and on app foreground.
  static Future<void> scheduleInactivityReminder() async {
    await init();
    await _plugin.cancel(_notificationId);

    final scheduledDate =
        // tz.TZDateTime.now(tz.local).add(const Duration(minutes: 1));
        tz.TZDateTime.now(tz.local).add(const Duration(hours: 24));

    const androidDetails = AndroidNotificationDetails(
      _channelId,
      _channelName,
      channelDescription: 'Reminds users to return to the app',
      importance: Importance.high,
      priority: Priority.high,
      icon: '@mipmap/ic_launcher',
    );

    const iosDetails = DarwinNotificationDetails(
      presentAlert: true,
      presentBadge: true,
      presentSound: true,
    );

    const details = NotificationDetails(
      android: androidDetails,
      iOS: iosDetails,
    );

    await _plugin.zonedSchedule(
      _notificationId,
      'اشتاقنا إليك!',
      'لديك محادثات تنتظرك، تفضل بالدخول الآن',
      scheduledDate,
      details,
      androidScheduleMode: AndroidScheduleMode.inexactAllowWhileIdle,
      payload: 'inactivity_reminder',
    );
  }
}
