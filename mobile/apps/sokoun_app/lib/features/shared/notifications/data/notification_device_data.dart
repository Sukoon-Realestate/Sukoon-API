import 'dart:async';
import 'dart:developer' show log;
import 'dart:io';

import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/network/api_endpoints.dart';
import 'package:melos_core/core/network/account_session.dart';
import 'package:melos_core/core/network/network_request.dart';
import 'package:melos_core/core/network/network_service.dart';
import 'package:melos_core/core/notification/notification_service.dart';

import 'models/notification_device_body.dart';

abstract interface class NotificationDeviceDataSource {
  Future<void> start();

  Future<void> registerCurrentDevice();

  Future<void> registerToken(String token);

  Future<void> unregisterCurrentDevice({bool notifyServer = true});
}

final class NotificationDeviceApiDataSource
    implements NotificationDeviceDataSource {
  StreamSubscription<String>? _tokenRefreshSubscription;
  Future<void>? _registration;
  ({String token, int generation})? _pendingRegistration;
  ({String token, int generation})? _activeRegistration;
  ({String token, int generation})? _registered;
  int _registrationEpoch = 0;

  @override
  Future<void> start() async {
    final int epoch = _registrationEpoch;
    try {
      await registerCurrentDevice();
      if (epoch != _registrationEpoch) return;
      _tokenRefreshSubscription ??= injector<NotificationService>()
          .onTokenRefresh
          .listen(registerToken);
    } catch (error, stackTrace) {
      _logDeviceFailure('initialize', error, stackTrace);
    }
  }

  @override
  Future<void> registerCurrentDevice() async {
    final int epoch = _registrationEpoch;
    final int generation = AccountSession.generation;
    try {
      final NetworkService networkService = injector<NetworkService>();
      if (!await networkService.hasSessionCookies() ||
          epoch != _registrationEpoch ||
          generation != AccountSession.generation) {
        return;
      }

      final String? token = await injector<NotificationService>().getFcmToken();
      if (token == null ||
          token.isEmpty ||
          epoch != _registrationEpoch ||
          generation != AccountSession.generation) {
        return;
      }
      await registerToken(token);
    } catch (error, stackTrace) {
      _logDeviceFailure('register', error, stackTrace);
    }
  }

  @override
  Future<void> registerToken(String token) {
    final String normalizedToken = token.trim();
    if (normalizedToken.isEmpty) return Future<void>.value();
    final ({String token, int generation}) registration = (
      token: normalizedToken,
      generation: AccountSession.generation,
    );
    if (registration == _registered) return Future<void>.value();
    if (registration != _activeRegistration) {
      _pendingRegistration = registration;
    }
    final Future<void>? pending = _registration;
    if (pending != null) return pending;
    late final Future<void> request;
    request = _drainRegistrations(_registrationEpoch).whenComplete(() {
      if (identical(_registration, request)) _registration = null;
    });
    _registration = request;
    return request;
  }

  Future<void> _drainRegistrations(int epoch) async {
    while (_pendingRegistration != null && epoch == _registrationEpoch) {
      final ({String token, int generation}) registration =
          _pendingRegistration!;
      _pendingRegistration = null;
      _activeRegistration = registration;
      try {
        final NetworkService networkService = injector<NetworkService>();
        if (!await networkService.hasSessionCookies() ||
            registration.generation != AccountSession.generation ||
            epoch != _registrationEpoch) {
          continue;
        }
        final NotificationDeviceBody body = NotificationDeviceBody(
          token: registration.token,
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
        if (registration.generation == AccountSession.generation &&
            epoch == _registrationEpoch) {
          _registered = registration;
        }
      } catch (error, stackTrace) {
        _logDeviceFailure('register', error, stackTrace);
      } finally {
        if (epoch == _registrationEpoch) _activeRegistration = null;
      }
    }
  }

  @override
  Future<void> unregisterCurrentDevice({bool notifyServer = true}) async {
    final int generation = AccountSession.generation;
    _registrationEpoch++;
    _pendingRegistration = null;
    _activeRegistration = null;
    _registered = null;
    final Future<void>? pending = _registration;
    _registration = null;
    final subscription = _tokenRefreshSubscription;
    _tokenRefreshSubscription = null;
    await subscription?.cancel();
    if (!notifyServer) return;
    await pending;
    if (generation != AccountSession.generation) return;

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

  static Future<void> stop() =>
      source.unregisterCurrentDevice(notifyServer: false);
}
