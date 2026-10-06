import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/helpers/text_style_manager.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:melos_core/core/widgets/buttons/default_button.dart';

import '../../data/enums/app_notification_kind.dart';
import '../../data/models/app_notification_content.dart';
import 'notification_icon_badge.dart';

class NotificationDetailsContent extends StatelessWidget {
  const NotificationDetailsContent({
    super.key,
    required this.notification,
    required this.onPrimaryPressed,
    required this.onDismissPressed,
  });

  final AppNotificationContent notification;
  final VoidCallback onPrimaryPressed;
  final VoidCallback onDismissPressed;

  String get _primaryActionLabel {
    final String apiLabel =
        notification.actions.primary?.label ?? notification.payload.actionLabel;
    if (apiLabel.trim().isNotEmpty) return apiLabel;
    if (notification.kind == AppNotificationKind.visitRequest) {
      return LocaleKeys.notificationViewRequest;
    }
    if (notification.kind == AppNotificationKind.visitAccepted) {
      return LocaleKeys.notificationViewVisit;
    }
    return LocaleKeys.notificationOpenRelated;
  }

  String get _secondaryActionLabel {
    final String apiLabel = notification.actions.secondary?.label ?? '';
    return apiLabel.trim().isEmpty ? LocaleKeys.notificationDismiss : apiLabel;
  }

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      padding: EdgeInsets.fromLTRB(20.w, 28.h, 20.w, 24.h),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        spacing: 20.h,
        children: [
          Container(
            padding: EdgeInsets.all(24.r),
            decoration: BoxDecoration(
              color: context.appColor(AppColors.white, surface: true),
              borderRadius: BorderRadius.circular(20.r),
              border: Border.all(
                color: context.appColor(AppColors.sokoonBorder),
              ),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                NotificationIconBadge(
                  iconType: notification.resolvedIconType,
                  size: 56,
                  iconSize: 28,
                ),
                20.szH,
                if (notification.category.isNotEmpty) ...[
                  AppText(
                    notification.category,
                    style: AppTextStyles.bold11.copyWith(
                      color: context.appColor(AppColors.sokoonGray),
                      fontSize: 11.sp,
                      height: 1.45,
                    ),
                    maxLines: 1,
                  ),
                  8.szH,
                ],
                AppText(
                  notification.title,
                  style: AppTextStyles.bold.copyWith(
                    color: context.appColor(AppColors.sokoonNavy),
                    fontSize: 20.sp,
                  ),
                  maxLines: 3,
                ),
                12.szH,
                AppText(
                  notification.description,
                  style: AppTextStyles.regular14.copyWith(
                    color: context.appColor(AppColors.sokoonGray),
                    fontSize: 14.sp,
                    height: 1.7,
                  ),
                  maxLines: 8,
                ),
                if (notification.hasDetailCard) ...[
                  20.szH,
                  _NotificationContextCard(notification: notification),
                ],
                if (notification.time.isNotEmpty ||
                    notification.formattedTime.isNotEmpty) ...[
                  20.szH,
                  AppText(
                    notification.formattedTime.isNotEmpty
                        ? notification.formattedTime
                        : notification.time,
                    style: AppTextStyles.regular11.copyWith(
                      color: context.appColor(AppColors.sokoonGray),
                      fontSize: 11.sp,
                      height: 1.45,
                    ),
                    maxLines: 1,
                  ),
                ],
              ],
            ),
          ),
          Row(
            spacing: 12.w,
            children: [
              Expanded(
                child: DefaultButton(
                  onTap: onPrimaryPressed,
                  title: _primaryActionLabel,
                  color: context.appColor(AppColors.sokoonTeal, surface: true),
                  textColor: AppColors.white,
                  borderRadius: BorderRadius.circular(16.r),
                  height: 50.h,
                  textStyle: AppTextStyles.extraBold.copyWith(fontSize: 14.sp),
                ),
              ),
              Expanded(
                child: DefaultButton(
                  onTap: onDismissPressed,
                  title: _secondaryActionLabel,
                  color: context.appColor(AppColors.white, surface: true),
                  textColor: context.appColor(AppColors.sokoonNavy),
                  borderColor: context.appColor(AppColors.sokoonBorder),
                  borderRadius: BorderRadius.circular(16.r),
                  height: 50.h,
                  textStyle: AppTextStyles.extraBold.copyWith(fontSize: 14.sp),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

class _NotificationContextCard extends StatelessWidget {
  const _NotificationContextCard({required this.notification});

  final AppNotificationContent notification;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: EdgeInsets.symmetric(horizontal: 16.w, vertical: 14.h),
      decoration: BoxDecoration(
        color: context.appColor(AppColors.mintLight, surface: true),
        borderRadius: BorderRadius.circular(12.r),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (notification.detailLabel.isNotEmpty) ...[
            AppText(
              notification.detailLabel,
              style: AppTextStyles.extraBold13.copyWith(
                color: context.appColor(AppColors.sokoonTeal),
                fontSize: 13.sp,
                height: 1.45,
              ),
              maxLines: 1,
            ),
            4.szH,
          ],
          if (notification.detailDate.isNotEmpty)
            AppText(
              notification.detailDate,
              style: AppTextStyles.regular13.copyWith(
                color: context.appColor(AppColors.sokoonNavy),
                fontSize: 13.sp,
                height: 1.45,
              ),
              maxLines: 2,
            ),
          if (notification.detailLocation.isNotEmpty) ...[
            4.szH,
            AppText(
              notification.detailLocation,
              style: AppTextStyles.regular12.copyWith(
                color: context.appColor(AppColors.sokoonGray),
                fontSize: 12.sp,
                height: 1.45,
              ),
              maxLines: 2,
            ),
          ],
        ],
      ),
    );
  }
}
