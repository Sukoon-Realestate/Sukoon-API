import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/helpers/text_style_manager.dart';
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
        spacing: 12.w,
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
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              spacing: 4.h,
              children: [
                AppText(
                  LocaleKeys.recoveryLinkValidFor24Hours,
                  style: AppTextStyles.extraBold13.copyWith(
                    color: AppColors.sokoonNavy,
                    fontSize: 13.sp,
                    height: 1.45,
                  ),
                ),
                AppText(
                  LocaleKeys.recoverySecurityHint,
                  style: AppTextStyles.medium11.copyWith(
                    color: AppColors.sokoonGray,
                    fontSize: 11.sp,
                    height: 1.55,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
