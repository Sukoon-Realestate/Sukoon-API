import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/padding_extension.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/helpers/text_style_manager.dart';
import 'package:melos_core/core/widgets/app_text.dart';

import '../../data/models/notification_setting_content.dart';
import 'notification_settings_tile.dart';

class NotificationSettingsContentView extends StatelessWidget {
  const NotificationSettingsContentView({
    super.key,
    required this.settings,
    required this.updatingKey,
    required this.onSettingChanged,
  });

  final NotificationSettingsContent settings;
  final String? updatingKey;
  final void Function(NotificationSettingContent setting, bool value)
  onSettingChanged;

  @override
  Widget build(BuildContext context) {
    return ListView(
      padding: EdgeInsets.only(top: 12.h, bottom: 24.h),
      children: [
        for (final NotificationSettingContent setting in settings.items)
          NotificationSettingsTile(
            key: ValueKey(setting.id),
            setting: setting.copyWith(
              title: setting.title.isEmpty ? _titleFor(setting.id) : null,
              description: setting.description.isEmpty
                  ? _descriptionFor(setting.id)
                  : null,
            ),
            isUpdating: updatingKey == setting.id,
            onChanged: (value) => onSettingChanged(setting, value),
          ),
        Container(
          padding: EdgeInsets.symmetric(horizontal: 16.w, vertical: 14.h),
          decoration: BoxDecoration(
            color: AppColors.mintLight,
            borderRadius: BorderRadius.circular(14.r),
          ),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Icon(
                Icons.info_outline_rounded,
                color: AppColors.sokoonTeal,
                size: 18.r,
              ),
              10.szW,
              Expanded(
                child: AppText(
                  settings.footerNote.isEmpty
                      ? LocaleKeys.notificationSettingsInfo
                      : settings.footerNote,
                  style: AppTextStyles.regular12.copyWith(
                    color: AppColors.sokoonTeal,
                    fontSize: 12.sp,
                    height: 1.6,
                  ),
                  maxLines: 4,
                ),
              ),
            ],
          ),
        ).paddingOnly(left: 20.w, top: 24.h, right: 20.w),
      ],
    );
  }

  String _titleFor(String key) {
    return switch (key) {
      'visit_notifications' => LocaleKeys.notificationSettingVisitRequests,
      'owner_messages' => LocaleKeys.notificationSettingNewMessages,
      'property_updates' => LocaleKeys.notificationSettingPropertyUpdates,
      'security_alerts' => LocaleKeys.notificationSettingSecurityAlerts,
      'promotions_and_updates' => LocaleKeys.notificationSettingPromotions,
      _ => key,
    };
  }

  String _descriptionFor(String key) {
    return switch (key) {
      'visit_notifications' =>
        LocaleKeys.notificationSettingVisitRequestsDescription,
      'owner_messages' => LocaleKeys.notificationSettingNewMessagesDescription,
      'property_updates' =>
        LocaleKeys.notificationSettingPropertyUpdatesDescription,
      'security_alerts' =>
        LocaleKeys.notificationSettingSecurityAlertsDescription,
      'promotions_and_updates' =>
        LocaleKeys.notificationSettingPromotionsDescription,
      _ => '',
    };
  }
}
