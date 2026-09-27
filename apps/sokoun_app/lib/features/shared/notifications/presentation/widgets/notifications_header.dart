import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/padding_extension.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/core/widgets/app_text.dart';

import '../../data/enums/notification_role.dart';
import '../screens/notification_settings_screen.dart';

class NotificationsHeader extends StatelessWidget {
  const NotificationsHeader({
    super.key,
    required this.role,
    required this.hasUnread,
    required this.isMarkingAll,
    required this.onMarkAllPressed,
  });

  final NotificationRole role;
  final bool hasUnread;
  final bool isMarkingAll;
  final VoidCallback onMarkAllPressed;

  @override
  Widget build(BuildContext context) {
    final bool canMarkAll = hasUnread && !isMarkingAll;
    return Row(
      children: [
        Expanded(
          child: AppText(
            LocaleKeys.workspaceAllNotifications,
            color: AppColors.sokoonNavy,
            fontSize: 20.sp,
            fontWeight: FontWeight.w900,
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
          ),
        ),
        TextButton(
          onPressed: canMarkAll ? onMarkAllPressed : null,
          style: TextButton.styleFrom(
            foregroundColor: AppColors.sokoonTeal,
            padding: EdgeInsets.symmetric(horizontal: 6.w),
            minimumSize: Size.zero,
            tapTargetSize: MaterialTapTargetSize.shrinkWrap,
          ),
          child: AppText(
            role.isOwner
                ? LocaleKeys.notificationsMarkAll
                : LocaleKeys.notificationsMarkAllRead,
            color: canMarkAll ? AppColors.sokoonTeal : AppColors.sokoonMuted,
            fontSize: 12.sp,
            fontWeight: FontWeight.w800,
          ),
        ),
        IconButton(
          tooltip: LocaleKeys.notificationSettingsTitle,
          onPressed: isMarkingAll
              ? null
              : () => Go.to(NotificationSettingsScreen(role: role)),
          visualDensity: VisualDensity.compact,
          constraints: BoxConstraints.tightFor(width: 38.r, height: 38.r),
          padding: EdgeInsets.zero,
          icon: Icon(
            Icons.settings_outlined,
            color: isMarkingAll ? AppColors.sokoonMuted : AppColors.sokoonNavy,
            size: 20.r,
          ),
        ),
      ],
    ).padding(EdgeInsetsDirectional.fromSTEB(20.w, 4.h, 14.w, 12.h));
  }
}
