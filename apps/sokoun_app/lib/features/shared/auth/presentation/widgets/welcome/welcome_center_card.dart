import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/widgets/app_text.dart';

class WelcomeCenterCard extends StatelessWidget {
  const WelcomeCenterCard({
    super.key,
    required this.icon,
    required this.iconBackgroundColor,
    required this.iconColor,
    required this.title,
    required this.subtitle,
  });

  final IconData icon;
  final Color iconBackgroundColor;
  final Color iconColor;
  final String title;
  final String subtitle;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: EdgeInsets.symmetric(horizontal: 17.w, vertical: 13.h),
      decoration: BoxDecoration(
        color: AppColors.white,
        borderRadius: BorderRadius.circular(8.r),
        border: Border.all(color: AppColors.sokoonBorder),
      ),
      child: Row(
        children: [
          Container(
            width: 40.r,
            height: 40.r,
            decoration: BoxDecoration(
              color: iconBackgroundColor,
              borderRadius: BorderRadius.circular(8.r),
            ),
            child: Icon(icon, color: iconColor, size: 19.r),
          ),
          14.szW,
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              mainAxisSize: MainAxisSize.min,
              children: [
                AppText(
                  title,
                  color: AppColors.sokoonNavy,
                  fontSize: 14.sp,
                  fontWeight: FontWeight.w900,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
                3.szH,
                AppText(
                  subtitle,
                  color: AppColors.sokoonGray,
                  fontSize: 12.sp,
                  fontWeight: FontWeight.w400,
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
