import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/helpers/text_style_manager.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/features/shared/notifications/data/models/notification_setting_content.dart';

class NotificationSettingsTile extends StatelessWidget {
  const NotificationSettingsTile({
    super.key,
    required this.setting,
    required this.isUpdating,
    required this.onChanged,
  });

  final NotificationSettingContent setting;
  final bool isUpdating;
  final ValueChanged<bool> onChanged;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: EdgeInsets.symmetric(horizontal: 20.w, vertical: 14.h),
      decoration: BoxDecoration(
        color: context.appColor(AppColors.white, surface: true),
        border: Border(
          bottom: BorderSide(color: context.appColor(AppColors.sokoonBorder)),
        ),
      ),
      child: Row(
        spacing: 14.w,
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              spacing: 3.h,
              children: [
                AppText(
                  setting.title,
                  style: AppTextStyles.bold14.copyWith(
                    color: context.appColor(AppColors.sokoonNavy),
                    fontSize: 14.sp,
                    height: 1.45,
                  ),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
                AppText(
                  setting.description,
                  style: AppTextStyles.regular12.copyWith(
                    color: context.appColor(AppColors.sokoonGray),
                    fontSize: 12.sp,
                    height: 1.45,
                  ),
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                ),
              ],
            ),
          ),
          Switch.adaptive(
            value: setting.isEnabled,
            onChanged: setting.canChange && !isUpdating ? onChanged : null,
            activeThumbColor: AppColors.white,
            activeTrackColor: context.appColor(AppColors.sokoonTeal),
            inactiveThumbColor: AppColors.white,
            inactiveTrackColor: context.appColor(AppColors.grayPale),
          ),
        ],
      ),
    );
  }
}
