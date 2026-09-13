import 'dart:async';
import 'dart:developer' show log;
import 'dart:io';

import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/network/api_endpoints.dart';
import 'package:melos_core/core/network/network_request.dart';
import 'package:melos_core/core/network/network_service.dart';
import 'package:melos_core/core/notification/notification_service.dart';

import 'models/notification_device_body.dart';

abstract final class NotificationDeviceData {
  static StreamSubscription<String>? _tokenRefreshSubscription;
  static bool _isRegistering = false;

  static Future<void> start() async {
    try {
      await registerCurrentDevice();
      _tokenRefreshSubscription ??= injector<NotificationService>()
          .onTokenRefresh
          .listen(registerToken);
    } catch (error, stackTrace) {
      _logDeviceFailure('initialize', error, stackTrace);
    }
  }

  static Future<void> registerCurrentDevice() async {
    try {
      final NetworkService networkService = injector<NetworkService>();
      if (!await networkService.hasSessionCookies()) return;

      final String? token = await injector<NotificationService>().getFcmToken();
      if (token == null || token.isEmpty) return;
      await registerToken(token);
    } catch (error, stackTrace) {
      _logDeviceFailure('register', error, stackTrace);
    }
  }

  static Future<void> registerToken(String token) async {
    if (_isRegistering || token.trim().isEmpty) return;
    try {
      final NetworkService networkService = injector<NetworkService>();
      if (!await networkService.hasSessionCookies()) return;
      _isRegistering = true;
      final NotificationDeviceBody body = NotificationDeviceBody(
        token: token,
        deviceType: Platform.isIOS ? 'ios' : 'android',
        deviceName: Platform.operatingSystemVersion,
      );
      await networkService.callApi<Map<String, dynamic>>(
        NetworkRequest(
          method: RequestMethod.post,
          path: ApiConstants.notificationDevices,
          body: body.toJson(),
        ),
        mapper: _mapResponse,
      );
    } catch (error, stackTrace) {
      _logDeviceFailure('register', error, stackTrace);
    } finally {
      _isRegistering = false;
    }
  }

  static Future<void> unregisterCurrentDevice() async {
    await _tokenRefreshSubscription?.cancel();
    _tokenRefreshSubscription = null;

    try {
      final NetworkService networkService = injector<NetworkService>();
      if (!await networkService.hasSessionCookies()) return;

      final String? token = await injector<NotificationService>().getFcmToken();
      if (token == null || token.isEmpty) return;
      await networkService.callApi<Map<String, dynamic>>(
        NetworkRequest(
          method: RequestMethod.post,
          path: ApiConstants.unregisterNotificationDevice,
          body: {'token': token},
        ),
        mapper: _mapResponse,
      );
    } catch (error, stackTrace) {
      _logDeviceFailure('unregister', error, stackTrace);
    }
  }

  static Map<String, dynamic> _mapResponse(dynamic json) {
    if (json is! Map) return const {};
    return Map<String, dynamic>.from(json);
  }

  static void _logDeviceFailure(
    String operation,
    Object error,
    StackTrace stackTrace,
  ) {
    log(
      'Unable to $operation the notification device.',
      error: error,
      stackTrace: stackTrace,
    );
  }
}
