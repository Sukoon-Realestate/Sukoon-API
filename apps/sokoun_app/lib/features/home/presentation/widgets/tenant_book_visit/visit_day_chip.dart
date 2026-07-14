import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/features/home/data/models/tenant_property_content.dart';

class VisitDayChip extends StatelessWidget {
  const VisitDayChip({
    super.key,
    required this.day,
    required this.isSelected,
    required this.onTap,
  });

  final TenantVisitDayContent day;
  final bool isSelected;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      behavior: HitTestBehavior.opaque,
      child: Container(
        width: 66.w,
        padding: EdgeInsets.symmetric(vertical: 10.h),
        decoration: BoxDecoration(
          color: isSelected ? AppColors.sokoonTeal : AppColors.white,
          borderRadius: BorderRadius.circular(16.r),
          border: Border.all(
            color: isSelected ? AppColors.sokoonTeal : AppColors.sokoonBorder,
          ),
        ),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            AppText(
              day.weekday,
              color: isSelected ? AppColors.white : AppColors.sokoonGray,
              fontSize: 12.sp,
              fontWeight: FontWeight.w700,
            ),
            3.szH,
            AppText(
              day.day,
              color: isSelected ? AppColors.white : AppColors.sokoonNavy,
              fontSize: 20.sp,
              fontWeight: FontWeight.w900,
            ),
          ],
        ),
      ),
    );
  }
}
