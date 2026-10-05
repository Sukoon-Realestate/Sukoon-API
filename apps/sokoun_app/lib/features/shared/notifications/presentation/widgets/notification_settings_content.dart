import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:melos_core/core/base_crud/code/presentation/cubit/base_cubit/async_cubit.dart';
import '../cubits/notification_settings_cubit.dart';
import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/padding_extension.dart';
import 'package:melos_core/core/helpers/text_style_manager.dart';
import 'package:melos_core/core/widgets/app_text.dart';

import '../../data/models/notification_setting_content.dart';
import 'notification_settings_tile.dart';

class NotificationSettingsContentView extends StatelessWidget {
  const NotificationSettingsContentView({
    super.key,
    required this.settings,
    this.observeChanges = false,
    required this.onSettingChanged,
  });

  final NotificationSettingsContent settings;
  final bool observeChanges;
  final void Function(NotificationSettingContent setting, bool value)
  onSettingChanged;

  @override
  Widget build(BuildContext context) {
    return ListView(
      padding: EdgeInsets.only(top: 12.h, bottom: 24.h),
      children: [
        for (final NotificationSettingContent setting in settings.items)
          _NotificationSettingRow(
            key: ValueKey(setting.id),
            initialSetting: setting,
            observeChanges: observeChanges,
            onSettingChanged: onSettingChanged,
          ),
        Container(
          padding: EdgeInsets.symmetric(horizontal: 16.w, vertical: 14.h),
          decoration: BoxDecoration(
            color: context.appColor(AppColors.mintLight, surface: true),
            borderRadius: BorderRadius.circular(14.r),
          ),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            spacing: 10.w,
            children: [
              Icon(
                Icons.info_outline_rounded,
                color: context.appColor(AppColors.sokoonTeal),
                size: 18.r,
              ),
              Expanded(
                child: AppText(
                  settings.footerNote.isEmpty
                      ? LocaleKeys.notificationSettingsInfo
                      : settings.footerNote,
                  style: AppTextStyles.regular12.copyWith(
                    color: context.appColor(AppColors.sokoonTeal),
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
}

class _NotificationSettingRow extends StatelessWidget {
  const _NotificationSettingRow({
    super.key,
    required this.initialSetting,
    required this.observeChanges,
    required this.onSettingChanged,
  });

  final NotificationSettingContent initialSetting;
  final bool observeChanges;
  final void Function(NotificationSettingContent, bool) onSettingChanged;

  @override
  Widget build(BuildContext context) {
    if (!observeChanges) return _tile(initialSetting, false);
    return BlocSelector<
      NotificationSettingsCubit,
      AsyncState<NotificationSettingsContent>,
      NotificationSettingContent
    >(
      selector: (state) => state.data.items.firstWhere(
        (item) => item.id == initialSetting.id,
        orElse: () => initialSetting,
      ),
      builder: (context, setting) =>
          BlocSelector<
            NotificationSettingUpdateCubit,
            AsyncState<String>,
            bool
          >(
            selector: (state) => state.isLoading && state.data == setting.id,
            builder: (context, isUpdating) => _tile(setting, isUpdating),
          ),
    );
  }

  Widget _tile(NotificationSettingContent setting, bool isUpdating) {
    return NotificationSettingsTile(
      setting: setting.copyWith(
        title: setting.title.isEmpty ? _titleFor(setting.id) : null,
        description: setting.description.isEmpty
            ? _descriptionFor(setting.id)
            : null,
      ),
      isUpdating: isUpdating,
      onChanged: (value) => onSettingChanged(setting, value),
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
