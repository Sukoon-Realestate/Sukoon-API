import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
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
        children: [
          Container(
            padding: EdgeInsets.all(24.r),
            decoration: BoxDecoration(
              color: AppColors.white,
              borderRadius: BorderRadius.circular(20.r),
              border: Border.all(color: AppColors.sokoonBorder),
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
                    color: AppColors.sokoonGray,
                    fontSize: 11.sp,
                    fontWeight: FontWeight.w700,
                    maxLines: 1,
                  ),
                  8.szH,
                ],
                AppText(
                  notification.title,
                  color: AppColors.sokoonNavy,
                  fontSize: 20.sp,
                  fontWeight: FontWeight.w700,
                  maxLines: 3,
                ),
                12.szH,
                AppText(
                  notification.description,
                  color: AppColors.sokoonGray,
                  fontSize: 14.sp,
                  height: 1.7,
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
                    color: AppColors.sokoonGray,
                    fontSize: 11.sp,
                    maxLines: 1,
                  ),
                ],
              ],
            ),
          ),
          20.szH,
          Row(
            children: [
              Expanded(
                child: DefaultButton(
                  onTap: onPrimaryPressed,
                  title: _primaryActionLabel,
                  color: AppColors.sokoonTeal,
                  textColor: AppColors.white,
                  borderRadius: BorderRadius.circular(16.r),
                  height: 50.h,
                  fontSize: 14.sp,
                  fontWeight: FontWeight.w800,
                ),
              ),
              12.szW,
              Expanded(
                child: DefaultButton(
                  onTap: onDismissPressed,
                  title: _secondaryActionLabel,
                  color: AppColors.white,
                  textColor: AppColors.sokoonNavy,
                  borderColor: AppColors.sokoonBorder,
                  borderRadius: BorderRadius.circular(16.r),
                  height: 50.h,
                  fontSize: 14.sp,
                  fontWeight: FontWeight.w800,
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
        color: AppColors.mintLight,
        borderRadius: BorderRadius.circular(12.r),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (notification.detailLabel.isNotEmpty) ...[
            AppText(
              notification.detailLabel,
              color: AppColors.sokoonTeal,
              fontSize: 13.sp,
              fontWeight: FontWeight.w800,
              maxLines: 1,
            ),
            4.szH,
          ],
          if (notification.detailDate.isNotEmpty)
            AppText(
              notification.detailDate,
              color: AppColors.sokoonNavy,
              fontSize: 13.sp,
              maxLines: 2,
            ),
          if (notification.detailLocation.isNotEmpty) ...[
            4.szH,
            AppText(
              notification.detailLocation,
              color: AppColors.sokoonGray,
              fontSize: 12.sp,
              maxLines: 2,
            ),
          ],
        ],
      ),
    );
  }
}
