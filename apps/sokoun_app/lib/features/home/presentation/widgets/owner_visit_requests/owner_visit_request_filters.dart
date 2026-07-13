import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/features/home/data/models/owner_visit_request_content.dart';

class OwnerVisitRequestFilters extends StatelessWidget {
  const OwnerVisitRequestFilters({super.key, required this.filters});

  final List<OwnerVisitRequestFilterContent> filters;

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      scrollDirection: Axis.horizontal,
      child: Row(
        textDirection: TextDirection.ltr,
        children: [
          for (int index = 0; index < filters.length; index++) ...[
            _FilterChip(filter: filters[index]),
            if (index < filters.length - 1) 8.szW,
          ],
        ],
      ),
    );
  }
}

class _FilterChip extends StatelessWidget {
  const _FilterChip({required this.filter});

  final OwnerVisitRequestFilterContent filter;

  @override
  Widget build(BuildContext context) {
    return Container(
      height: 36.h,
      padding: EdgeInsets.symmetric(horizontal: 13.w),
      decoration: BoxDecoration(
        color: filter.isSelected ? AppColors.sokoonTeal : AppColors.white,
        borderRadius: BorderRadius.circular(999.r),
        border: Border.all(
          color: filter.isSelected ? AppColors.sokoonTeal : AppColors.grayPale,
        ),
      ),
      child: Row(
        children: [
          AppText(
            filter.label,
            color: filter.isSelected ? AppColors.white : AppColors.sokoonNavy,
            fontSize: 12.sp,
            fontWeight: FontWeight.w700,
          ),
          if (filter.count != null) ...[
            6.szW,
            Container(
              padding: EdgeInsets.symmetric(horizontal: 6.w, vertical: 1.h),
              decoration: BoxDecoration(
                color: filter.isSelected
                    ? AppColors.whiteAlpha40
                    : AppColors.grayPale,
                borderRadius: BorderRadius.circular(8.r),
              ),
              child: AppText(
                filter.count!,
                color: filter.isSelected
                    ? AppColors.white
                    : AppColors.sokoonGray,
                fontSize: 10.sp,
                fontWeight: FontWeight.w900,
              ),
            ),
          ],
        ],
      ),
    );
  }
}
