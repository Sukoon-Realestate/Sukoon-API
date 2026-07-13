import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/features/home/data/models/tenant_search_result_content.dart';

class ResultImageHeader extends StatelessWidget {
  const ResultImageHeader({super.key, required this.item});

  final SearchResultContent item;

  @override
  Widget build(BuildContext context) {
    return Container(
      height: 140.h,
      decoration: BoxDecoration(
        gradient: LinearGradient(
          begin: AlignmentDirectional.topStart,
          end: AlignmentDirectional.bottomEnd,
          colors: [item.imageColor.withValues(alpha: .78), item.imageColorEnd],
        ),
      ),
      child: Stack(
        children: [
          Center(
            child: Icon(
              Icons.image_outlined,
              color: AppColors.whiteAlpha60,
              size: 36.r,
            ),
          ),
          if (item.isVerified)
            PositionedDirectional(
              top: 10.h,
              end: 10.w,
              child: Container(
                padding: EdgeInsets.symmetric(horizontal: 8.w, vertical: 4.h),
                decoration: BoxDecoration(
                  color: AppColors.sokoonTeal,
                  borderRadius: BorderRadius.circular(7.r),
                ),
                child: AppText(
                  'موثّق ✓',
                  color: AppColors.white,
                  fontSize: 10.sp,
                  fontWeight: FontWeight.w800,
                ),
              ),
            ),
          PositionedDirectional(
            start: 10.w,
            bottom: 10.h,
            child: Container(
              padding: EdgeInsets.symmetric(horizontal: 8.w, vertical: 4.h),
              decoration: BoxDecoration(
                color: AppColors.blackAlpha45,
                borderRadius: BorderRadius.circular(7.r),
              ),
              child: AppText(
                '8 صور',
                color: AppColors.white,
                fontSize: 10.sp,
                fontWeight: FontWeight.w600,
              ),
            ),
          ),
        ],
      ),
    );
  }
}
