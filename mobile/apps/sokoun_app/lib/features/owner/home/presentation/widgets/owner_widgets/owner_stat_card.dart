import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/helpers/text_style_manager.dart';
import 'package:melos_core/core/widgets/app_text.dart';

class OwnerStatCard extends StatelessWidget {
  const OwnerStatCard({
    super.key,
    required this.value,
    required this.label,
    required this.icon,
    required this.iconColor,
    required this.iconBackgroundColor,
  });

  final String value;
  final String label;
  final IconData icon;
  final Color iconColor;
  final Color iconBackgroundColor;

  @override
  Widget build(BuildContext context) {
    return Container(
      constraints: BoxConstraints(minHeight: 108.h),
      padding: EdgeInsets.all(12.w),
      decoration: BoxDecoration(
        color: context.appColor(AppColors.white, surface: true),
        borderRadius: BorderRadius.circular(16.r),
        border: Border.all(color: context.appColor(AppColors.sokoonBorder)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            spacing: 10.w,
            children: [
              Container(
                width: 32.r,
                height: 32.r,
                decoration: BoxDecoration(
                  color: context.appColor(iconBackgroundColor, surface: true),
                  borderRadius: BorderRadius.circular(10.r),
                ),
                child: Icon(
                  icon,
                  color: context.appColor(iconColor),
                  size: 18.r,
                ),
              ),
              Expanded(
                child: AppText(
                  value,
                  style: AppTextStyles.bold.copyWith(
                    color: context.appColor(AppColors.sokoonNavy),
                    fontSize: 22.sp,
                  ),
                ),
              ),
            ],
          ),
          12.szH,
          AppText(
            label,
            style: AppTextStyles.regular13.copyWith(
              color: context.appColor(AppColors.sokoonGray),
              fontSize: 13.sp,
              height: 1.45,
            ),
          ),
        ],
      ),
    );
  }
}
