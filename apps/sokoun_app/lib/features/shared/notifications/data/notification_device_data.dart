import 'dart:async';
import 'dart:developer' show log;
import 'dart:io';

import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/network/api_endpoints.dart';
import 'package:melos_core/core/network/network_request.dart';
import 'package:melos_core/core/network/network_service.dart';
import 'package:melos_core/core/notification/notification_service.dart';

import 'models/notification_device_body.dart';

abstract interface class NotificationDeviceDataSource {
  Future<void> start();

  Future<void> registerCurrentDevice();

  Future<void> registerToken(String token);

  Future<void> unregisterCurrentDevice();
}

final class NotificationDeviceApiDataSource
    implements NotificationDeviceDataSource {
  StreamSubscription<String>? _tokenRefreshSubscription;
  bool _isRegistering = false;

  @override
  Future<void> start() async {
    try {
      await registerCurrentDevice();
      _tokenRefreshSubscription ??= injector<NotificationService>()
          .onTokenRefresh
          .listen(registerToken);
    } catch (error, stackTrace) {
      _logDeviceFailure('initialize', error, stackTrace);
    }
  }

  @override
  Future<void> registerCurrentDevice() async {
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

  @override
  Future<void> registerToken(String token) async {
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

  @override
  Future<void> unregisterCurrentDevice() async {
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

  Map<String, dynamic> _mapResponse(dynamic json) {
    if (json is! Map) return const {};
    return Map<String, dynamic>.from(json);
  }

  void _logDeviceFailure(
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

abstract final class NotificationDeviceData {
  static final NotificationDeviceDataSource _defaultSource =
      NotificationDeviceApiDataSource();

  static NotificationDeviceDataSource get source =>
      injector.isRegistered<NotificationDeviceDataSource>()
      ? injector<NotificationDeviceDataSource>()
      : _defaultSource;

  static Future<void> start() => source.start();

  static Future<void> registerCurrentDevice() => source.registerCurrentDevice();

  static Future<void> registerToken(String token) =>
      source.registerToken(token);

  static Future<void> unregisterCurrentDevice() =>
      source.unregisterCurrentDevice();
}
