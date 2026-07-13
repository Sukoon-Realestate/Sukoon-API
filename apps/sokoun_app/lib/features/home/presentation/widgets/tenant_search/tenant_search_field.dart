import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/widgets/app_text.dart';

class TenantSearchField extends StatelessWidget {
  const TenantSearchField({super.key});

  @override
  Widget build(BuildContext context) {
    return Container(
      height: 52.h,
      padding: EdgeInsetsDirectional.only(start: 14.w, end: 8.w),
      decoration: BoxDecoration(
        color: AppColors.white,
        borderRadius: BorderRadius.circular(16.r),
        border: Border.all(color: AppColors.sokoonTeal, width: 1.4),
      ),
      child: Row(
        textDirection: TextDirection.ltr,
        children: [
          Icon(Icons.search_rounded, color: AppColors.sokoonMuted, size: 20.r),
          10.szW,
          Expanded(
            child: AppText(
              'مدينة نصر، القاهرة…',
              color: AppColors.sokoonMuted,
              fontSize: 14.sp,
              fontWeight: FontWeight.w400,
              overflow: TextOverflow.ellipsis,
            ),
          ),
          Container(
            padding: EdgeInsets.symmetric(horizontal: 12.w, vertical: 6.h),
            decoration: BoxDecoration(
              color: AppColors.mintLight,
              borderRadius: BorderRadius.circular(12.r),
            ),
            child: AppText(
              'بحث',
              color: AppColors.sokoonTeal,
              fontSize: 12.sp,
              fontWeight: FontWeight.w800,
            ),
          ),
        ],
      ),
    );
  }
}
