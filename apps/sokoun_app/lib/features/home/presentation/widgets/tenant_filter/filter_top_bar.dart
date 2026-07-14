import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/widgets/app_text.dart';

class FilterTopBar extends StatelessWidget {
  const FilterTopBar({
    super.key,
    required this.activeCount,
    required this.onReset,
  });

  final int activeCount;
  final VoidCallback onReset;

  @override
  Widget build(BuildContext context) {
    return Container(
      height: 56.h,
      padding: EdgeInsets.symmetric(horizontal: 16.w),
      decoration: const BoxDecoration(
        color: AppColors.white,
        border: Border(bottom: BorderSide(color: AppColors.grayPale)),
      ),
      child: Row(
        children: [
          Container(
            width: 22.r,
            height: 22.r,
            alignment: Alignment.center,
            decoration: const BoxDecoration(
              color: AppColors.sokoonTeal,
              shape: BoxShape.circle,
            ),
            child: AppText(
              '$activeCount',
              color: AppColors.white,
              fontSize: 12.sp,
              fontWeight: FontWeight.w900,
            ),
          ),
          8.szW,
          AppText(
            'فلتر البحث',
            color: AppColors.sokoonNavy,
            fontSize: 17.sp,
            fontWeight: FontWeight.w900,
          ),
          const Spacer(),
          GestureDetector(
            onTap: onReset,
            behavior: HitTestBehavior.opaque,
            child: AppText(
              'إعادة تعيين',
              color: AppColors.sokoonTeal,
              fontSize: 13.sp,
              fontWeight: FontWeight.w800,
            ),
          ),
        ],
      ),
    );
  }
}
