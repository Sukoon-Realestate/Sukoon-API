import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/helpers/text_style_manager.dart';
import 'package:melos_core/core/widgets/app_text.dart';

class KycPrivacyCard extends StatelessWidget {
  const KycPrivacyCard({
    super.key,
    required this.title,
    required this.subtitle,
  });

  final String title;
  final String subtitle;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: EdgeInsets.symmetric(horizontal: 16.w, vertical: 14.h),
      decoration: BoxDecoration(
        color: AppColors.mintPale,
        borderRadius: BorderRadius.circular(12.r),
        border: Border.all(color: AppColors.tealAlpha13),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        spacing: 12.w,
        children: [
          Container(
            width: 36.r,
            height: 36.r,
            decoration: BoxDecoration(
              color: AppColors.tealAlpha09,
              borderRadius: BorderRadius.circular(10.r),
            ),
            child: Icon(
              Icons.lock_outline_rounded,
              color: AppColors.sokoonTeal,
              size: 18.r,
            ),
          ),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              mainAxisSize: MainAxisSize.min,
              spacing: 4.h,
              children: [
                AppText(
                  title,
                  style: AppTextStyles.extraBold13.copyWith(
                    color: AppColors.sokoonNavy,
                    fontSize: 13.sp,
                    height: 1.45,
                  ),
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                ),
                AppText(
                  subtitle,
                  style: AppTextStyles.regular11.copyWith(
                    color: AppColors.sokoonGray,
                    fontSize: 11.sp,
                    height: 1.45,
                  ),
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
