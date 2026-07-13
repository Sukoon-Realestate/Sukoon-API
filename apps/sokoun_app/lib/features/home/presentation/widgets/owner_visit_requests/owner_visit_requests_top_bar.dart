import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/widgets/app_text.dart';

class OwnerVisitRequestsTopBar extends StatelessWidget {
  const OwnerVisitRequestsTopBar({super.key});

  @override
  Widget build(BuildContext context) {
    return Container(
      height: 52.h,
      padding: EdgeInsets.symmetric(horizontal: 16.w),
      decoration: const BoxDecoration(
        color: AppColors.white,
        border: Border(bottom: BorderSide(color: AppColors.grayPale)),
      ),
      child: Row(
        textDirection: TextDirection.ltr,
        children: [
          Container(
            width: 36.r,
            height: 36.r,
            alignment: Alignment.center,
            decoration: BoxDecoration(
              color: AppColors.grayBackground,
              borderRadius: BorderRadius.circular(12.r),
            ),
            child: Icon(
              Icons.chevron_left_rounded,
              color: AppColors.sokoonNavy,
              size: 22.r,
            ),
          ),
          const Spacer(),
          AppText(
            'طلبات الزيارة',
            color: AppColors.sokoonNavy,
            fontSize: 16.sp,
            fontWeight: FontWeight.w900,
            textAlign: TextAlign.center,
          ),
          const Spacer(),
          SizedBox(width: 36.r),
        ],
      ),
    );
  }
}
