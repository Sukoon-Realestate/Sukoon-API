import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/widgets/app_text.dart';

class OwnerRequestVerifiedBadge extends StatelessWidget {
  const OwnerRequestVerifiedBadge({super.key});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: EdgeInsets.symmetric(horizontal: 7.w, vertical: 3.h),
      decoration: BoxDecoration(
        color: AppColors.goldPale,
        borderRadius: BorderRadius.circular(999.r),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(Icons.verified_rounded, color: AppColors.gold, size: 11.r),
          3.szW,
          AppText(
            'موثّق',
            color: AppColors.gold,
            fontSize: 11.sp,
            fontWeight: FontWeight.w600,
          ),
        ],
      ),
    );
  }
}
