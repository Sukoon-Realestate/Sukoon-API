import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/helpers/text_style_manager.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/features/shared/notifications/data/models/app_notification_content.dart';

import 'notification_icon_badge.dart';

class NotificationCard extends StatelessWidget {
  const NotificationCard({
    super.key,
    required this.notification,
    required this.onPressed,
  });

  final AppNotificationContent notification;
  final VoidCallback onPressed;

  @override
  Widget build(BuildContext context) {
    return Material(
      color: AppColors.transparent,
      child: InkWell(
        onTap: onPressed,
        borderRadius: BorderRadius.circular(16.r),
        child: Ink(
          padding: EdgeInsets.all(16.r),
          decoration: BoxDecoration(
            color: notification.isUnread
                ? context.appColor(AppColors.white, surface: true)
                : context.appColor(AppColors.scaffoldBackground, surface: true),
            borderRadius: BorderRadius.circular(16.r),
            border: Border.all(
              color: notification.isUnread
                  ? AppColors.tealAlpha19
                  : context.appColor(AppColors.sokoonBorder),
            ),
            boxShadow: notification.isUnread
                ? const [
                    BoxShadow(
                      color: AppColors.shadowBlack04,
                      blurRadius: 8,
                      offset: Offset(0, 2),
                    ),
                  ]
                : null,
          ),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            spacing: 12.w,
            children: [
              NotificationIconBadge(iconType: notification.resolvedIconType),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      spacing: 8.w,
                      children: [
                        Expanded(
                          child: AppText(
                            notification.title,
                            style: AppTextStyles.bold14.copyWith(
                              color: context.appColor(AppColors.sokoonNavy),
                              fontSize: 14.sp,
                              height: 1.45,
                            ),
                            maxLines: 2,
                            overflow: TextOverflow.ellipsis,
                          ),
                        ),
                        if (notification.isUnread)
                          Container(
                            width: 8.r,
                            height: 8.r,
                            margin: EdgeInsets.only(top: 4.h),
                            decoration: BoxDecoration(
                              color: context.appColor(
                                AppColors.sokoonTeal,
                                surface: true,
                              ),
                              shape: BoxShape.circle,
                            ),
                          ),
                      ],
                    ),
                    3.szH,
                    AppText(
                      notification.description,
                      style: AppTextStyles.regular12.copyWith(
                        color: context.appColor(AppColors.sokoonGray),
                        fontSize: 12.sp,
                        height: 1.45,
                      ),
                      maxLines: 3,
                      overflow: TextOverflow.ellipsis,
                    ),
                    5.szH,
                    AppText(
                      notification.time,
                      style: AppTextStyles.regular11.copyWith(
                        color: context.appColor(AppColors.graySoft),
                        fontSize: 11.sp,
                        height: 1.45,
                      ),
                      maxLines: 1,
                    ),
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
