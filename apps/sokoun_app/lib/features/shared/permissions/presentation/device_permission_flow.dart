import 'dart:async';
import 'dart:developer' show log;

import 'package:flutter/material.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/core/shared/base_state.dart';
import 'package:melos_core/core/widgets/location_permission_view.dart';
import 'package:melos_core/core/widgets/notification_permission_view.dart';
import 'package:melos_core/core/widgets/toast_messages/toast_message.dart';

import '../../notifications/data/notification_device_data.dart';
import '../data/device_permission_data.dart';
import '../data/enums/device_permission.dart';
import 'widgets/permission_settings_dialog.dart';

abstract final class DevicePermissionFlow {
  static bool _isRequesting = false;

  static bool _isCurrent(BuildContext context) =>
      ModalRoute.of(context)?.isCurrent == true;

  /// Requests native access only after the matching explanation is accepted.
  /// Automatic notification prompts are remembered across launches and logins.
  static Future<bool> ensureGranted(
    BuildContext context,
    DevicePermission permission, {
    bool promptOnce = false,
  }) async {
    if (_isRequesting || !context.mounted || !_isCurrent(context)) return false;
    _isRequesting = true;
    final source = DevicePermissionData.source;
    final bool automatic =
        promptOnce && permission == DevicePermission.notifications;
    try {
      if (automatic && source.hasSeenNotificationPrompt) return false;
      final status = await source.status(permission);
      if (!context.mounted || !_isCurrent(context)) return false;
      if (status == DevicePermissionStatus.granted) return true;
      if (status == DevicePermissionStatus.restricted) {
        if (!automatic) {
          Messages.showToast(
            status: BaseStatus.error,
            msg: LocaleKeys.permissionRestricted,
          );
        }
        return false;
      }
      if (status == DevicePermissionStatus.blocked) {
        if (automatic) return false;
        final open = await PermissionSettingsDialog.show(
          context,
          permission == DevicePermission.notifications
              ? LocaleKeys.notificationPermissionBlocked
              : LocaleKeys.locationPermissionBlocked,
        );
        if (!context.mounted || !_isCurrent(context) || open != true) {
          return false;
        }
        if (!await source.openSettings() &&
            context.mounted &&
            _isCurrent(context)) {
          Messages.showToast(
            status: BaseStatus.error,
            msg: LocaleKeys.permissionSettingsUnavailable,
          );
        }
        // Opening settings is not a permission grant. The next action/resume
        // checks the actual OS status again.
        return false;
      }

      final decision = permission == DevicePermission.notifications
          ? NotificationPermissionView.show(context: context)
          : LocationPermissionView.show(context: context);
      if (permission == DevicePermission.notifications) {
        try {
          await source.markNotificationPromptSeen();
        } catch (error, stackTrace) {
          log(
            'Unable to remember the notification prompt.',
            error: error,
            stackTrace: stackTrace,
          );
        }
      }
      final accepted = await decision;
      if (!context.mounted || !_isCurrent(context) || accepted != true) {
        return false;
      }

      final result = await source.request(permission);
      if (!context.mounted || !_isCurrent(context)) return false;
      if (result != DevicePermissionStatus.granted) {
        Messages.showToast(
          status: BaseStatus.error,
          msg: result == DevicePermissionStatus.restricted
              ? LocaleKeys.permissionRestricted
              : LocaleKeys.permissionDenied,
        );

        return false;
      }
      if (permission == DevicePermission.notifications) {
        unawaited(NotificationDeviceData.registerCurrentDevice());
      }
      return context.mounted && _isCurrent(context);
    } catch (error, stackTrace) {
      log('Permission flow failed.', error: error, stackTrace: stackTrace);
      if (!automatic && context.mounted && _isCurrent(context)) {
        Messages.showToast(
          status: BaseStatus.error,
          msg: LocaleKeys.permissionUnavailable,
        );
      }
      return false;
    } finally {
      _isRequesting = false;
    }
  }
}
