import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:sokoun_app/features/shared/notifications/data/models/app_notification_content.dart';

class NotificationIconBadge extends StatelessWidget {
  const NotificationIconBadge({
    super.key,
    required this.kind,
    this.size = 40,
    this.iconSize = 18,
  });

  final AppNotificationKind kind;
  final double size;
  final double iconSize;

  @override
  Widget build(BuildContext context) {
    final _NotificationVisual visual = _visual;

    return Container(
      width: size.r,
      height: size.r,
      alignment: Alignment.center,
      decoration: BoxDecoration(
        color: visual.backgroundColor,
        borderRadius: BorderRadius.circular(size >= 50 ? 16.r : 14.r),
      ),
      child: Icon(visual.icon, color: visual.color, size: iconSize.r),
    );
  }

  _NotificationVisual get _visual {
    return switch (kind) {
      AppNotificationKind.visitAccepted => const _NotificationVisual(
        icon: Icons.check_circle_outline_rounded,
        color: AppColors.green,
        backgroundColor: AppColors.greenPale,
      ),
      AppNotificationKind.newProperty => const _NotificationVisual(
        icon: Icons.notifications_none_rounded,
        color: AppColors.sokoonTeal,
        backgroundColor: AppColors.mintLight,
      ),
      AppNotificationKind.accountVerification => const _NotificationVisual(
        icon: Icons.warning_amber_rounded,
        color: AppColors.amber,
        backgroundColor: AppColors.amberPale,
      ),
      AppNotificationKind.rateVisit => const _NotificationVisual(
        icon: Icons.star_outline_rounded,
        color: AppColors.gold,
        backgroundColor: AppColors.goldPale,
      ),
      AppNotificationKind.ownerMessage ||
      AppNotificationKind.tenantMessage => const _NotificationVisual(
        icon: Icons.chat_bubble_outline_rounded,
        color: AppColors.blue,
        backgroundColor: AppColors.bluePale,
      ),
      AppNotificationKind.visitRequest => const _NotificationVisual(
        icon: Icons.calendar_month_outlined,
        color: AppColors.green,
        backgroundColor: AppColors.greenPale,
      ),
      AppNotificationKind.propertyViews => const _NotificationVisual(
        icon: Icons.visibility_outlined,
        color: AppColors.sokoonTeal,
        backgroundColor: AppColors.mintLight,
      ),
      AppNotificationKind.propertyVerified => const _NotificationVisual(
        icon: Icons.verified_outlined,
        color: AppColors.gold,
        backgroundColor: AppColors.goldPale,
      ),
      AppNotificationKind.dailyVisibility => const _NotificationVisual(
        icon: Icons.warning_amber_rounded,
        color: AppColors.amber,
        backgroundColor: AppColors.amberPale,
      ),
    };
  }
}

class _NotificationVisual {
  const _NotificationVisual({
    required this.icon,
    required this.color,
    required this.backgroundColor,
  });

  final IconData icon;
  final Color color;
  final Color backgroundColor;
}
