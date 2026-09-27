import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/widgets/app_text.dart';

class ForgotPasswordSecurityHint extends StatelessWidget {
  const ForgotPasswordSecurityHint({super.key});

  @override
  Widget build(BuildContext context) {
    final Color accentColor = AppColors.sokoonTeal;

    return Container(
      padding: EdgeInsets.symmetric(horizontal: 16.w, vertical: 14.h),
      decoration: BoxDecoration(
        color: AppColors.mintLight,
        borderRadius: BorderRadius.circular(14.r),
        border: Border.all(color: accentColor.withValues(alpha: .2)),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            width: 34.r,
            height: 34.r,
            decoration: BoxDecoration(
              color: accentColor.withValues(alpha: .12),
              borderRadius: BorderRadius.circular(10.r),
            ),
            child: Icon(Icons.shield_outlined, color: accentColor, size: 19.r),
          ),
          12.szW,
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                AppText(
                  LocaleKeys.recoveryLinkValidTitle,
                  color: AppColors.sokoonNavy,
                  fontSize: 13.sp,
                  fontWeight: FontWeight.w800,
                ),
                4.szH,
                AppText(
                  LocaleKeys.recoverySecurityHint,
                  color: AppColors.sokoonGray,
                  fontSize: 11.sp,
                  fontWeight: FontWeight.w500,
                  height: 1.55,
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
