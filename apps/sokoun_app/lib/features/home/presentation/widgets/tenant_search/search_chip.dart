import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/features/home/data/models/tenant_search_content.dart';

class SearchChip extends StatelessWidget {
  const SearchChip({super.key, required this.category, this.onTap});

  final SearchCategoryContent category;
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
          color: category.isSelected ? AppColors.sokoonTeal : AppColors.white,
          borderRadius: BorderRadius.circular(999.r),
          border: Border.all(
            color: category.isSelected
                ? AppColors.sokoonTeal
                : AppColors.sokoonBorder,
          ),
        ),
        child: AppText(
          category.label,
          color: category.isSelected ? AppColors.white : AppColors.sokoonNavy,
          fontSize: 12.sp,
          fontWeight: FontWeight.w800,
        ),
      ),
    );
  }
}
