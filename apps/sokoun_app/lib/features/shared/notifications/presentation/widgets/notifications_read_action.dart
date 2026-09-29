import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/padding_extension.dart';
import 'package:melos_core/core/helpers/text_style_manager.dart';
import 'package:melos_core/core/widgets/app_text.dart';

import '../../data/enums/notification_role.dart';

class NotificationsReadAction extends StatelessWidget {
  const NotificationsReadAction({
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
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        TextButton(
          onPressed: canMarkAll ? onMarkAllPressed : null,
          style: TextButton.styleFrom(
            foregroundColor: AppColors.sokoonTeal,
            padding: EdgeInsets.symmetric(horizontal: 6.w),
            minimumSize: const Size(48, 48),
          ),
          child: AppText(
            role.isOwner
                ? LocaleKeys.notificationsMarkAll
                : LocaleKeys.notificationsMarkAllRead,
            style: AppTextStyles.semiBold.copyWith(
              color: canMarkAll ? AppColors.sokoonTeal : AppColors.sokoonMuted,
              fontSize: 14.sp,
            ),
          ),
        ),
      ],
    ).padding(EdgeInsetsDirectional.fromSTEB(20.w, 4.h, 14.w, 12.h));
  }
}
