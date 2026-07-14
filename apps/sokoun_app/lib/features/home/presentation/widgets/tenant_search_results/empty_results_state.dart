import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/widgets/app_text.dart';

class EmptyResultsState extends StatelessWidget {
  const EmptyResultsState({super.key});

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: EdgeInsets.symmetric(horizontal: 28.w),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              width: 78.r,
              height: 78.r,
              alignment: Alignment.center,
              decoration: const BoxDecoration(
                color: AppColors.tealAlpha07,
                shape: BoxShape.circle,
              ),
              child: Icon(
                Icons.search_off_rounded,
                color: AppColors.sokoonTeal,
                size: 34.r,
              ),
            ),
            14.szH,
            AppText(
              'لا توجد نتائج مطابقة',
              color: AppColors.sokoonNavy,
              fontSize: 17.sp,
              fontWeight: FontWeight.w900,
              textAlign: TextAlign.center,
            ),
            6.szH,
            AppText(
              'جرّب تغيير البحث أو إزالة بعض الفلاتر',
              color: AppColors.sokoonGray,
              fontSize: 13.sp,
              fontWeight: FontWeight.w500,
              textAlign: TextAlign.center,
            ),
          ],
        ),
      ),
    );
  }
}
