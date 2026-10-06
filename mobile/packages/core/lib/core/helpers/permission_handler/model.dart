import 'dart:async';
import 'package:permission_handler/permission_handler.dart';

class PermissionModel{
  final List<Permission> permissions;
  final FutureOr<void> Function(Permission permission)? onGranted;
  final FutureOr<void> Function(Permission permission)? onDenied;
  final FutureOr<void> Function(Permission permission)? onDeniedForever;
  final FutureOr<void> Function(Permission permission)? onPermissionLimited;

  PermissionModel({
    required this.permissions,
    this.onGranted,
    this.onDenied,
    this.onDeniedForever,
    this.onPermissionLimited
  });
}