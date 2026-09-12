import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:melos_core/core/widgets/buttons/default_button.dart';
import 'package:sokoun_app/features/shared/notifications/data/enums/notification_role.dart';
import 'package:sokoun_app/features/shared/notifications/data/models/app_notification_content.dart';

import '../widgets/notification_icon_badge.dart';

class NotificationDetailScreen extends StatelessWidget {
  const NotificationDetailScreen({
    super.key,
    required this.role,
    required this.notification,
  });

  final NotificationRole role;
  final AppNotificationContent notification;

  String get _primaryAction {
    if (notification.kind == AppNotificationKind.visitRequest) {
      return LocaleKeys.notificationViewRequest;
    }
    if (notification.kind == AppNotificationKind.visitAccepted) {
      return LocaleKeys.notificationViewVisit;
    }
    return LocaleKeys.notificationOpenRelated;
  }

  @override
  Widget build(BuildContext context) {
    return Directionality(
      textDirection: TextDirection.rtl,
      child: Scaffold(
        backgroundColor: AppColors.scaffoldBackground,
        body: SafeArea(
          child: Column(
            children: [
              const _NotificationDetailHeader(),
              Expanded(
                child: SingleChildScrollView(
                  padding: EdgeInsets.fromLTRB(20.w, 28.h, 20.w, 24.h),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      Container(
                        padding: EdgeInsets.all(24.r),
                        decoration: BoxDecoration(
                          color: AppColors.white,
                          borderRadius: BorderRadius.circular(20.r),
                          boxShadow: const [
                            BoxShadow(
                              color: AppColors.shadowBlack04,
                              blurRadius: 12,
                              offset: Offset(0, 2),
                            ),
                          ],
                        ),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            NotificationIconBadge(
                              kind: notification.kind,
                              size: 56,
                              iconSize: 28,
                            ),
                            20.szH,
                            AppText(
                              notification.category,
                              color: AppColors.sokoonGray,
                              fontSize: 11.sp,
                              fontWeight: FontWeight.w700,
                              maxLines: 1,
                            ),
                            8.szH,
                            AppText(
                              notification.title,
                              color: AppColors.sokoonNavy,
                              fontSize: 20.sp,
                              fontWeight: FontWeight.w900,
                              maxLines: 3,
                            ),
                            12.szH,
                            AppText(
                              notification.detailDescription ??
                                  notification.description,
                              color: AppColors.sokoonGray,
                              fontSize: 14.sp,
                              height: 1.7,
                              maxLines: 8,
                            ),
                            if (notification.hasDetailCard) ...[
                              20.szH,
                              _NotificationContextCard(
                                notification: notification,
                              ),
                            ],
                            20.szH,
                            AppText(
                              notification.time,
                              color: AppColors.sokoonGray,
                              fontSize: 11.sp,
                              maxLines: 1,
                            ),
                          ],
                        ),
                      ),
                      20.szH,
                      Row(
                        children: [
                          Expanded(
                            child: DefaultButton(
                              onTap: () => Go.back(),
                              title: _primaryAction,
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
                              onTap: () => Go.back(),
                              title: LocaleKeys.notificationDismiss,
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
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _NotificationDetailHeader extends StatelessWidget {
  const _NotificationDetailHeader();

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
            onPressed: () => Go.back(),
            icon: Icon(
              Icons.arrow_back_ios_new_rounded,
              color: AppColors.sokoonNavy,
              size: 20.r,
            ),
          ),
          Expanded(
            child: AppText(
              LocaleKeys.notificationDetailsTitle,
              color: AppColors.sokoonNavy,
              fontSize: 17.sp,
              fontWeight: FontWeight.w800,
              textAlign: TextAlign.center,
              maxLines: 1,
            ),
          ),
          SizedBox(width: 48.r),
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
          if (notification.detailLabel != null) ...[
            AppText(
              notification.detailLabel!,
              color: AppColors.sokoonTeal,
              fontSize: 13.sp,
              fontWeight: FontWeight.w800,
              maxLines: 1,
            ),
            4.szH,
          ],
          if (notification.detailDate != null)
            AppText(
              notification.detailDate!,
              color: AppColors.sokoonNavy,
              fontSize: 13.sp,
              maxLines: 2,
            ),
          if (notification.detailLocation != null) ...[
            4.szH,
            AppText(
              notification.detailLocation!,
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
