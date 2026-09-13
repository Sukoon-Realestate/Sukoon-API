import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/features/shared/notifications/data/enums/notification_role.dart';
import 'package:sokoun_app/features/shared/notifications/presentation/widgets/notification_bell_button.dart';

import 'home_avatar.dart';

class TenantHeader extends StatelessWidget {
  const TenantHeader({super.key});

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        const HomeAvatar(
          icon: Icons.person_outline_rounded,
          backgroundColor: AppColors.mintLight,
          iconColor: AppColors.sokoonTeal,
        ),
        10.szW,
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              AppText(
                LocaleKeys.tenantHomeGreeting,
                color: AppColors.sokoonNavy,
                fontSize: 18.sp,
                fontWeight: FontWeight.w900,
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
              ),
              2.szH,
              AppText(
                LocaleKeys.tenantHomeCurrentArea,
                color: AppColors.sokoonGray,
                fontSize: 12.sp,
                fontWeight: FontWeight.w400,
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
              ),
            ],
          ),
        ),
        10.szW,
        const NotificationBellButton(role: NotificationRole.tenant),
      ],
    );
  }
}
