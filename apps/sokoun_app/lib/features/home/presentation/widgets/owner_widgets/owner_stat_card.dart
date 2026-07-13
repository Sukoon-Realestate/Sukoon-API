import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
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
      height: 118.h,
      padding: EdgeInsets.all(16.w),
      decoration: BoxDecoration(
        color: AppColors.white,
        borderRadius: BorderRadius.circular(16.r),
        border: Border.all(color: AppColors.sokoonBorder),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            width: 34.r,
            height: 34.r,
            decoration: BoxDecoration(
              color: iconBackgroundColor,
              borderRadius: BorderRadius.circular(12.r),
            ),
            child: Icon(icon, color: iconColor, size: 18.r),
          ),
          const Spacer(),
          AppText(
            value,
            color: AppColors.sokoonNavy,
            fontSize: 20.sp,
            fontWeight: FontWeight.w900,
          ),
          2.szH,
          AppText(
            label,
            color: AppColors.sokoonGray,
            fontSize: 12.sp,
            fontWeight: FontWeight.w400,
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
          ),
        ],
      ),
    );
  }
}
