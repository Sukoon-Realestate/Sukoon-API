import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/features/shared/notifications/data/models/notification_setting_content.dart';

class NotificationSettingsTile extends StatelessWidget {
  const NotificationSettingsTile({
    super.key,
    required this.setting,
    required this.onChanged,
  });

  final NotificationSettingContent setting;
  final ValueChanged<bool> onChanged;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: EdgeInsets.symmetric(horizontal: 20.w, vertical: 14.h),
      decoration: const BoxDecoration(
        color: AppColors.white,
        border: Border(bottom: BorderSide(color: AppColors.sokoonBorder)),
      ),
      child: Row(
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                AppText(
                  setting.title,
                  color: AppColors.sokoonNavy,
                  fontSize: 14.sp,
                  fontWeight: FontWeight.w700,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
                3.szH,
                AppText(
                  setting.description,
                  color: AppColors.sokoonGray,
                  fontSize: 12.sp,
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                ),
              ],
            ),
          ),
          14.szW,
          Switch.adaptive(
            value: setting.isEnabled,
            onChanged: onChanged,
            activeThumbColor: AppColors.white,
            activeTrackColor: AppColors.sokoonTeal,
            inactiveThumbColor: AppColors.white,
            inactiveTrackColor: AppColors.grayPale,
          ),
        ],
      ),
    );
  }
}
