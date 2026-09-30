import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/languages.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/helpers/text_style_manager.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:melos_core/core/widgets/toast_messages/custom_messages.dart';

import '../../../../../shared/permissions/data/enums/device_permission.dart';
import '../../../../../shared/permissions/presentation/device_permission_flow.dart';
import '../../../../../shared/permissions/presentation/widgets/permission_settings_dialog.dart';
import '../../../data/current_location_data.dart';
import '../../../data/models/current_location_area.dart';

class UseCurrentLocationButton extends StatefulWidget {
  const UseCurrentLocationButton({super.key, required this.onAreaResolved});

  // The search screen owns the filters and submitted query.
  final ValueChanged<CurrentLocationArea> onAreaResolved;

  @override
  State<UseCurrentLocationButton> createState() =>
      _UseCurrentLocationButtonState();
}

class _UseCurrentLocationButtonState extends State<UseCurrentLocationButton> {
  final _isLocating = ValueNotifier(false);

  Future<void> _locate() async {
    if (_isLocating.value) return;
    _isLocating.value = true;
    final source = CurrentLocationData.source;
    try {
      final enabled = await source.isServiceEnabled();
      if (!mounted || ModalRoute.of(context)?.isCurrent != true) return;
      if (!enabled) {
        final open = await PermissionSettingsDialog.show(
          context,
          LocaleKeys.locationServicesDisabled,
        );
        if (!mounted ||
            ModalRoute.of(context)?.isCurrent != true ||
            open != true) {
          return;
        }
        if (!await source.openLocationSettings() && mounted) {
          MessageUtils.showTopMsg(LocaleKeys.permissionSettingsUnavailable);
        }
        return;
      }
      final granted = await DevicePermissionFlow.ensureGranted(
        context,
        DevicePermission.location,
      );
      if (!mounted || !granted) return;
      final area = await source.resolveArea(
        languageCode: Languages.currentLanguage.languageCode,
      );
      if (!mounted || ModalRoute.of(context)?.isCurrent != true) return;
      widget.onAreaResolved(area);
    } catch (_) {
      if (mounted && ModalRoute.of(context)?.isCurrent == true) {
        MessageUtils.showTopMsg(LocaleKeys.currentLocationUnavailable);
      }
    } finally {
      if (mounted) _isLocating.value = false;
    }
  }

  @override
  void dispose() {
    _isLocating.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => ValueListenableBuilder<bool>(
    valueListenable: _isLocating,
    builder: (context, busy, _) => TextButton(
      onPressed: busy ? null : _locate,
      style: TextButton.styleFrom(
        minimumSize: Size(0, 44.h),
        foregroundColor: AppColors.sokoonTeal,
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.center,
        spacing: 8.w,
        children: [
          if (busy)
            SizedBox.square(
              dimension: 18.r,
              child: const CircularProgressIndicator(
                strokeWidth: 2,
                color: AppColors.sokoonTeal,
              ),
            )
          else
            Icon(Icons.my_location_rounded, size: 18.r),
          Flexible(
            child: AppText(
              busy
                  ? LocaleKeys.currentLocationLoading
                  : LocaleKeys.useMyLocation,
              style: AppTextStyles.bold14.copyWith(
                color: AppColors.sokoonTeal,
                fontSize: 14.sp,
                height: 1.45,
              ),
              textAlign: TextAlign.center,
            ),
          ),
        ],
      ),
    ),
  );
}
