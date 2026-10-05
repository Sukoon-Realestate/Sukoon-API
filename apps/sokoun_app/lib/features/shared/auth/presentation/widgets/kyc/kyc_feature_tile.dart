import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/helpers/text_style_manager.dart';
import 'package:melos_core/core/widgets/app_text.dart';

class KycFeatureTile extends StatelessWidget {
  const KycFeatureTile({super.key, required this.icon, required this.title});

  final IconData icon;
  final String title;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: EdgeInsets.symmetric(horizontal: 16.w, vertical: 13.h),
      decoration: BoxDecoration(
        color: context.appColor(AppColors.white, surface: true),
        borderRadius: BorderRadius.circular(10.r),
        border: Border.all(color: context.appColor(AppColors.sokoonBorder)),
      ),
      child: Row(
        spacing: 10.w,
        children: [
          Icon(icon, color: context.appColor(AppColors.sokoonTeal), size: 18.r),
          Expanded(
            child: AppText(
              title,
              style: AppTextStyles.extraBold.copyWith(
                color: context.appColor(AppColors.sokoonNavy),
                fontSize: 14.sp,
              ),
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
            ),
          ),
        ],
      ),
    );
  }
}
