import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/padding_extension.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:melos_core/core/widgets/buttons/default_button.dart';

import '../../../permissions/data/device_permission_data.dart';
import '../../../permissions/data/enums/device_permission.dart';
import '../../../permissions/presentation/device_permission_flow.dart';
import '../../data/notification_device_data.dart';

class DeviceNotificationPermissionTile extends StatefulWidget {
  const DeviceNotificationPermissionTile({super.key});

  @override
  State<DeviceNotificationPermissionTile> createState() =>
      _DeviceNotificationPermissionTileState();
}

class _DeviceNotificationPermissionTileState
    extends State<DeviceNotificationPermissionTile>
    with WidgetsBindingObserver {
  final _status = ValueNotifier<DevicePermissionStatus?>(null);
  final _isRequesting = ValueNotifier(false);

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    unawaited(_refresh());
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.resumed) unawaited(_refresh());
  }

  Future<void> _refresh() async {
    try {
      final status = await DevicePermissionData.source.status(
        DevicePermission.notifications,
      );
      if (mounted) {
        final previouslyGranted =
            _status.value == DevicePermissionStatus.granted;
        _status.value = status;
        if (!previouslyGranted && status == DevicePermissionStatus.granted) {
          unawaited(NotificationDeviceData.registerCurrentDevice());
        }
      }
    } catch (_) {
      if (mounted) _status.value = null;
    }
  }

  Future<void> _enable() async {
    if (_isRequesting.value) return;
    _isRequesting.value = true;
    try {
      await DevicePermissionFlow.ensureGranted(
        context,
        DevicePermission.notifications,
      );
      if (mounted) await _refresh();
    } finally {
      if (mounted) _isRequesting.value = false;
    }
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    _status.dispose();
    _isRequesting.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => Container(
    padding: EdgeInsets.all(16.r),
    decoration: BoxDecoration(
      color: AppColors.grayOffWhite,
      borderRadius: BorderRadius.circular(14.r),
    ),
    child: ValueListenableBuilder<DevicePermissionStatus?>(
      valueListenable: _status,
      builder: (context, status, _) {
        final enabled = status == DevicePermissionStatus.granted;
        return Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          mainAxisSize: MainAxisSize.min,
          children: [
            AppText(
              LocaleKeys.deviceNotificationsTitle,
              color: AppColors.sokoonNavy,
              fontSize: 14.sp,
              fontWeight: FontWeight.w700,
            ),
            6.szH,
            AppText(
              status == null
                  ? LocaleKeys.permissionUnavailable
                  : enabled
                  ? LocaleKeys.deviceNotificationsEnabled
                  : LocaleKeys.deviceNotificationsDisabled,
              color: AppColors.sokoonGray,
              fontSize: 12.sp,
              height: 1.5,
            ),
            if (!enabled) ...[
              12.szH,
              ValueListenableBuilder<bool>(
                valueListenable: _isRequesting,
                builder: (context, busy, _) => DefaultButton(
                  onTap: busy ? null : _enable,
                  title: status == DevicePermissionStatus.blocked
                      ? LocaleKeys.permissionOpenSettings
                      : LocaleKeys.notificationPermissionTitle,
                  minHeight: 44.h,
                  width: double.infinity,
                  fontSize: 14.sp,
                  borderRadius: BorderRadius.circular(12.r),
                  color: AppColors.blue,
                  customChild: busy
                      ? SizedBox.square(
                          dimension: 18.r,
                          child: const CircularProgressIndicator(
                            color: AppColors.white,
                            strokeWidth: 2,
                          ),
                        )
                      : null,
                ),
              ),
            ],
          ],
        );
      },
    ),
  ).paddingSymmetric(horizontal: 20.w, vertical: 12.h);
}
