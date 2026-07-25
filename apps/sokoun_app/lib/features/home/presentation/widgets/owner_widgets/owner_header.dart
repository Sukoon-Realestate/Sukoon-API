import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/widgets/app_text.dart';

import 'home_avatar.dart';
import 'home_circle_button.dart';

class OwnerHeader extends StatelessWidget {
  const OwnerHeader({super.key, this.onNotificationsPressed});

  final VoidCallback? onNotificationsPressed;

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        const HomeAvatar(
          icon: Icons.key_rounded,
          backgroundColor: AppColors.goldPale,
          iconColor: AppColors.gold,
        ),
        10.szW,
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              AppText(
                'أهلاً أحمد 👋',
                color: AppColors.sokoonNavy,
                fontSize: 18.sp,
                fontWeight: FontWeight.w900,
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
              ),
              4.szH,
              Container(
                padding: EdgeInsets.symmetric(horizontal: 8.w, vertical: 3.h),
                decoration: BoxDecoration(
                  color: AppColors.goldPale,
                  borderRadius: BorderRadius.circular(999.r),
                ),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(
                      Icons.verified_rounded,
                      color: AppColors.gold,
                      size: 12.r,
                    ),
                    3.szW,
                    AppText(
                      'موثّق',
                      color: AppColors.gold,
                      fontSize: 12.sp,
                      fontWeight: FontWeight.w600,
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
        10.szW,
        HomeCircleButton(
          key: const ValueKey('owner-open-notifications'),
          icon: Icons.notifications_none_rounded,
          iconColor: AppColors.sokoonNavy,
          showBadge: true,
          onPressed: onNotificationsPressed,
        ),
      ],
    );
  }
}
