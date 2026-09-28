import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/features/owner/visits/imports.dart';

class OwnerVisitRequestFilters extends StatelessWidget {
  const OwnerVisitRequestFilters({
    super.key,
    required this.filters,
    required this.selectedFilter,
    required this.countForFilter,
    required this.onFilterSelected,
  });

  final List<OwnerVisitRequestFilter> filters;
  final OwnerVisitRequestFilter selectedFilter;
  final int Function(OwnerVisitRequestFilter filter) countForFilter;
  final ValueChanged<OwnerVisitRequestFilter> onFilterSelected;

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        for (int index = 0; index < filters.length; index++) ...[
          _FilterChip(
            filter: filters[index],
            count: countForFilter(filters[index]),
            isSelected: filters[index].isSame(selectedFilter),
            onPressed: () => onFilterSelected(filters[index]),
          ),
          if (index < filters.length - 1) 8.szW,
        ],
      ],
    );
  }
}

class _FilterChip extends StatelessWidget {
  const _FilterChip({
    required this.filter,
    required this.count,
    required this.isSelected,
    required this.onPressed,
  });

  final OwnerVisitRequestFilter filter;
  final int count;
  final bool isSelected;
  final VoidCallback onPressed;

  @override
  Widget build(BuildContext context) {
    return Expanded(
      child: Material(
        color: AppColors.transparent,
        child: InkWell(
          onTap: onPressed,
          borderRadius: BorderRadius.circular(999.r),
          child: Container(
            height: 36.h,
            padding: EdgeInsets.symmetric(horizontal: 13.w),
            decoration: BoxDecoration(
              color: isSelected ? AppColors.sokoonTeal : AppColors.white,
              borderRadius: BorderRadius.circular(999.r),
              border: Border.all(
                color: isSelected ? AppColors.sokoonTeal : AppColors.grayPale,
              ),
            ),
            child: FittedBox(
              child: Row(
                children: [
                  AppText(
                    filter.label,
                    color: isSelected ? AppColors.white : AppColors.sokoonNavy,
                    fontSize: 12.sp,
                    fontWeight: FontWeight.w700,
                  ),
                  if (count > 0) ...[
                    6.szW,
                    Container(
                      padding: EdgeInsets.symmetric(horizontal: 6.w, vertical: 1.h),
                      decoration: BoxDecoration(
                        color: isSelected
                            ? AppColors.whiteAlpha40
                            : AppColors.grayPale,
                        borderRadius: BorderRadius.circular(8.r),
                      ),
                      child: AppText(
                        '$count',
                        color: isSelected ? AppColors.white : AppColors.sokoonGray,
                        fontSize: 10.sp,
                        fontWeight: FontWeight.w900,
                      ),
                    ),
                  ],
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}
