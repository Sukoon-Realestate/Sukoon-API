import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/widgets/app_text.dart';

class OwnerListingsHeader extends StatelessWidget {
  const OwnerListingsHeader({super.key});

  @override
  Widget build(BuildContext context) {
    return Row(
      textDirection: TextDirection.ltr,
      children: [
        Container(
          height: 38.h,
          padding: EdgeInsets.symmetric(horizontal: 12.w),
          decoration: BoxDecoration(
            color: AppColors.sokoonTeal,
            borderRadius: BorderRadius.circular(14.r),
          ),
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(Icons.add_rounded, color: AppColors.white, size: 18.r),
              5.szW,
              AppText(
                'إضافة عقار',
                color: AppColors.white,
                fontSize: 13.sp,
                fontWeight: FontWeight.w900,
              ),
            ],
          ),
        ),
        const Spacer(),
        AppText(
          'عقاراتي',
          color: AppColors.sokoonNavy,
          fontSize: 20.sp,
          fontWeight: FontWeight.w900,
          textAlign: TextAlign.right,
        ),
      ],
    );
  }
}
