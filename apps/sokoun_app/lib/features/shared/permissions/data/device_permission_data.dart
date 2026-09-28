import 'package:melos_core/config/res/config_imports.dart' show injector;
import 'package:melos_core/core/helpers/cache_service.dart';
import 'package:permission_handler/permission_handler.dart';

import 'enums/device_permission.dart';

abstract interface class DevicePermissionDataSource {
  Future<DevicePermissionStatus> status(DevicePermission permission);
  Future<DevicePermissionStatus> request(DevicePermission permission);
  Future<bool> openSettings();
  bool get hasSeenNotificationPrompt;
  Future<void> markNotificationPromptSeen();
}

class NativeDevicePermissionDataSource implements DevicePermissionDataSource {
  const NativeDevicePermissionDataSource();

  static const notificationPromptKey = 'notification_permission_prompt_seen';

  Permission _nativePermission(DevicePermission permission) =>
      switch (permission) {
        DevicePermission.notifications => Permission.notification,
        DevicePermission.location => Permission.locationWhenInUse,
      };

  DevicePermissionStatus _mapStatus(PermissionStatus status) {
    if (status.isGranted || status.isProvisional || status.isLimited) {
      return DevicePermissionStatus.granted;
    }
    if (status.isPermanentlyDenied) return DevicePermissionStatus.blocked;
    if (status.isRestricted) return DevicePermissionStatus.restricted;
    return DevicePermissionStatus.denied;
  }

  @override
  Future<DevicePermissionStatus> status(DevicePermission permission) async =>
      _mapStatus(await _nativePermission(permission).status);

  @override
  Future<DevicePermissionStatus> request(DevicePermission permission) async =>
      _mapStatus(await _nativePermission(permission).request());

  @override
  Future<bool> openSettings() => openAppSettings();

  @override
  bool get hasSeenNotificationPrompt =>
      CacheStorage.read(notificationPromptKey) == true;

  @override
  Future<void> markNotificationPromptSeen() =>
      CacheStorage.write(notificationPromptKey, true);
}

abstract final class DevicePermissionData {
  static DevicePermissionDataSource get source =>
      injector.isRegistered<DevicePermissionDataSource>()
      ? injector<DevicePermissionDataSource>()
      : const NativeDevicePermissionDataSource();
}
