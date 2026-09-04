import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/padding_extension.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/features/shared/notifications/data/enums/notification_role.dart';
import 'package:sokoun_app/features/shared/notifications/data/models/notification_setting_content.dart';

import '../widgets/notification_settings_tile.dart';

class NotificationSettingsScreen extends StatefulWidget {
  const NotificationSettingsScreen({super.key, required this.role});

  final NotificationRole role;

  @override
  State<NotificationSettingsScreen> createState() =>
      _NotificationSettingsScreenState();
}

class _NotificationSettingsScreenState
    extends State<NotificationSettingsScreen> {
  late List<NotificationSettingContent> _settings;
  bool _didInitializeSettings = false;

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    if (_didInitializeSettings) {
      return;
    }

    _settings = [
      NotificationSettingContent(
        id: 'visit-requests',
        title: LocaleKeys.notificationSettingVisitRequests,
        description: LocaleKeys.notificationSettingVisitRequestsDescription,
        isEnabled: true,
      ),
      NotificationSettingContent(
        id: 'new-messages',
        title: LocaleKeys.notificationSettingNewMessages,
        description: LocaleKeys.notificationSettingNewMessagesDescription,
        isEnabled: true,
      ),
      NotificationSettingContent(
        id: 'property-updates',
        title: LocaleKeys.notificationSettingPropertyUpdates,
        description: LocaleKeys.notificationSettingPropertyUpdatesDescription,
        isEnabled: false,
      ),
      NotificationSettingContent(
        id: 'security-alerts',
        title: LocaleKeys.notificationSettingSecurityAlerts,
        description: LocaleKeys.notificationSettingSecurityAlertsDescription,
        isEnabled: true,
      ),
      NotificationSettingContent(
        id: 'promotions',
        title: LocaleKeys.notificationSettingPromotions,
        description: LocaleKeys.notificationSettingPromotionsDescription,
        isEnabled: false,
      ),
    ];
    _didInitializeSettings = true;
  }

  void _toggleSetting(int index, bool value) {
    setState(() {
      _settings[index] = _settings[index].copyWith(isEnabled: value);
    });
  }

  @override
  Widget build(BuildContext context) {
    return Directionality(
      textDirection: TextDirection.rtl,
      child: Scaffold(
        backgroundColor: AppColors.scaffoldBackground,
        body: SafeArea(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              const _NotificationSettingsHeader(),
              Expanded(
                child: ListView(
                  padding: EdgeInsets.only(top: 12.h, bottom: 24.h),
                  children: [
                    for (int index = 0; index < _settings.length; index++)
                      NotificationSettingsTile(
                        setting: _settings[index],
                        onChanged: (value) => _toggleSetting(index, value),
                      ),
                    Container(
                      padding: EdgeInsets.symmetric(
                        horizontal: 16.w,
                        vertical: 14.h,
                      ),
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
                              LocaleKeys.notificationSettingsInfo,
                              color: AppColors.sokoonTeal,
                              fontSize: 12.sp,
                              height: 1.6,
                              maxLines: 4,
                            ),
                          ),
                        ],
                      ),
                    ).paddingOnly(left: 20.w, top: 24.h, right: 20.w),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _NotificationSettingsHeader extends StatelessWidget {
  const _NotificationSettingsHeader();

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: EdgeInsets.symmetric(horizontal: 14.w, vertical: 10.h),
      decoration: const BoxDecoration(
        color: AppColors.white,
        border: Border(bottom: BorderSide(color: AppColors.sokoonBorder)),
      ),
      child: Row(
        children: [
          IconButton(
            key: const ValueKey('notification-settings-back'),
            onPressed: Go.back,
            icon: Icon(
              Icons.arrow_back_ios_new_rounded,
              color: AppColors.sokoonNavy,
              size: 20.r,
            ),
          ),
          8.szW,
          Expanded(
            child: AppText(
              LocaleKeys.notificationSettingsTitle,
              color: AppColors.sokoonNavy,
              fontSize: 17.sp,
              fontWeight: FontWeight.w800,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
            ),
          ),
        ],
      ),
    );
  }
}
