import 'dart:async';
import 'dart:developer';
import 'package:permission_handler/permission_handler.dart';
import 'model.dart';

class PermissionHandler{
  late Permission permission;

  Future<void> checkPermission({
    required PermissionModel permissionManagerModel,
    bool openSetting = false
  }) async {
    for(Permission permission in permissionManagerModel.permissions){
      await _checkOnePermission(
          selectedPermission: permission,
          onGranted: permissionManagerModel.onGranted,
          onDenied: permissionManagerModel.onDenied,
          onPermissionDeniedForever: permissionManagerModel.onDeniedForever,
          onPermissionLimited: permissionManagerModel.onPermissionLimited,
          openSetting: openSetting
      );
    }
  }

  Future<void> _checkOnePermission({
    required Permission selectedPermission,
    FutureOr<void> Function(Permission permission)? onGranted,
    FutureOr<void> Function(Permission permission)? onDenied,
    FutureOr<void> Function(Permission permission)? onPermissionDeniedForever,
    FutureOr<void> Function(Permission permission)? onPermissionLimited,
    bool openSetting = false
  })async{
    permission = selectedPermission;

    await _askForPermission(
      onPermissionGranted: onGranted,
      onPermissionDenied: onDenied,
      onPermissionDeniedForever: onPermissionDeniedForever,
      onPermissionLimited: onPermissionLimited,
      openSetting: openSetting,
    );
  }

  Future<void> _askForPermission({
    FutureOr<void> Function(Permission permission)? onPermissionGranted,
    FutureOr<void> Function(Permission permission)? onPermissionDenied,
    FutureOr<void> Function(Permission permission)? onPermissionDeniedForever,
    FutureOr<void> Function(Permission permission)? onPermissionLimited,
    bool openSetting = false
  })async {
    final PermissionStatus permissionStatus = await permission.status;
    log('Initial permission status: $permissionStatus');

    // Handle already granted permission
    if(permissionStatus == PermissionStatus.granted) {
      log('Permission already granted');
      await onPermissionGranted?.call(permission);
      return;
    }

    // Handle limited permission (iOS photos)
    if(permissionStatus == PermissionStatus.limited) {
      log('Permission limited (iOS photos)');
      await onPermissionLimited?.call(permission);
      return;
    }

    // Handle permanently denied - don't request again, just notify
    if(permissionStatus == PermissionStatus.permanentlyDenied) {
      log('Permission permanently denied');
      await onPermissionDeniedForever?.call(permission);
      if(openSetting){
        await openAppSettings();
      }
      return;
    }

    // iOS-specific: If permission is denied, treat as permanently denied
    // because requesting again will immediately return permanentlyDenied
    if(permissionStatus == PermissionStatus.denied) {
      log('Requesting permission...');
      final PermissionStatus status = await permission.request();
      log('Permission request result: $status');

      switch(status) {
        case PermissionStatus.granted:
          await onPermissionGranted?.call(permission);
          break;

        case PermissionStatus.denied:
        // First denial - on Android this is normal, on iOS this shouldn't happen
        // because we handle denied status above
          await onPermissionDenied?.call(permission);
          break;

        case PermissionStatus.permanentlyDenied:
          await onPermissionDeniedForever?.call(permission);
          if(openSetting){
            await openAppSettings();
          }
          break;

        case PermissionStatus.limited:
          await onPermissionLimited?.call(permission);
          break;

        case PermissionStatus.restricted:
        // iOS: Permission restricted by parental controls or device management
          await onPermissionDeniedForever?.call(permission);
          break;

        default:
          return;
      }
    }
  }
}