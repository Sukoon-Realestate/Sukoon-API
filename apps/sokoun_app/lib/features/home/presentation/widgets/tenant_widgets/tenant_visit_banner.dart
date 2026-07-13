import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/widgets/app_text.dart';

class TenantVisitBanner extends StatelessWidget {
  const TenantVisitBanner({super.key});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: EdgeInsets.symmetric(horizontal: 14.w, vertical: 13.h),
      decoration: BoxDecoration(
        color: AppColors.mintLight,
        borderRadius: BorderRadius.circular(16.r),
        border: Border.all(color: AppColors.tealAlpha19),
      ),
      child: Row(
        children: [
          Container(
            width: 34.r,
            height: 34.r,
            decoration: const BoxDecoration(
              color: AppColors.whiteAlpha60,
              shape: BoxShape.circle,
            ),
            child: Icon(
              Icons.calendar_today_outlined,
              color: AppColors.sokoonTeal,
              size: 17.r,
            ),
          ),
          12.szW,
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                AppText(
                  'عندك زيارة النهارده 3:00 م',
                  color: AppColors.sokoonTeal,
                  fontSize: 14.sp,
                  fontWeight: FontWeight.w900,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
                3.szH,
                AppText(
                  'شقة مدينة نصر',
                  color: AppColors.sokoonTeal,
                  fontSize: 12.sp,
                  fontWeight: FontWeight.w500,
                ),
              ],
            ),
          ),
          Icon(Icons.chevron_left_rounded, color: AppColors.sokoonTeal),
        ],
      ),
    );
  }
}
