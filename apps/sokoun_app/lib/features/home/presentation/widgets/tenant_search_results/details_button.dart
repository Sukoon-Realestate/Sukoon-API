import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/widgets/app_text.dart';

class DetailsButton extends StatelessWidget {
  const DetailsButton({super.key, this.onTap});

  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      behavior: HitTestBehavior.opaque,
      child: Container(
        height: 34.h,
        padding: EdgeInsets.symmetric(horizontal: 16.w),
        alignment: Alignment.center,
        decoration: BoxDecoration(
          color: AppColors.sokoonTeal,
          borderRadius: BorderRadius.circular(10.r),
        ),
        child: AppText(
          'تفاصيل',
          color: AppColors.white,
          fontSize: 13.sp,
          fontWeight: FontWeight.w800,
        ),
      ),
    );
  }
}
