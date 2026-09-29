import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
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
                ? AppColors.white
                : AppColors.scaffoldBackground,
            borderRadius: BorderRadius.circular(16.r),
            border: Border.all(
              color: notification.isUnread
                  ? AppColors.tealAlpha19
                  : AppColors.sokoonBorder,
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
            children: [
              NotificationIconBadge(iconType: notification.resolvedIconType),
              12.szW,
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Expanded(
                          child: AppText(
                            notification.title,
                            color: AppColors.sokoonNavy,
                            fontSize: 14.sp,
                            fontWeight: FontWeight.w700,
                            maxLines: 2,
                            overflow: TextOverflow.ellipsis,
                          ),
                        ),
                        if (notification.isUnread) ...[
                          8.szW,
                          Container(
                            width: 8.r,
                            height: 8.r,
                            margin: EdgeInsets.only(top: 4.h),
                            decoration: const BoxDecoration(
                              color: AppColors.sokoonTeal,
                              shape: BoxShape.circle,
                            ),
                          ),
                        ],
                      ],
                    ),
                    3.szH,
                    AppText(
                      notification.description,
                      color: AppColors.sokoonGray,
                      fontSize: 12.sp,
                      height: 1.45,
                      maxLines: 3,
                      overflow: TextOverflow.ellipsis,
                    ),
                    5.szH,
                    AppText(
                      notification.time,
                      color: AppColors.graySoft,
                      fontSize: 11.sp,
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
