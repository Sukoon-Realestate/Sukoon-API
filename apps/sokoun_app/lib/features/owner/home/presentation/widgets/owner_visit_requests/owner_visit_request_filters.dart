import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/helpers/text_style_manager.dart';
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
      spacing: 8.w,
      children: [
        for (int index = 0; index < filters.length; index++)
          _FilterChip(
            filter: filters[index],
            count: countForFilter(filters[index]),
            isSelected: filters[index].isSame(selectedFilter),
            onPressed: () => onFilterSelected(filters[index]),
          ),
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
                spacing: 6.w,
                children: [
                  AppText(
                    filter.label,
                    style: AppTextStyles.bold12.copyWith(
                      color: isSelected
                          ? AppColors.white
                          : AppColors.sokoonNavy,
                      fontSize: 12.sp,
                      height: 1.45,
                    ),
                  ),
                  if (count > 0)
                    Container(
                      padding: EdgeInsets.symmetric(
                        horizontal: 6.w,
                        vertical: 1.h,
                      ),
                      decoration: BoxDecoration(
                        color: isSelected
                            ? AppColors.whiteAlpha40
                            : AppColors.grayPale,
                        borderRadius: BorderRadius.circular(8.r),
                      ),
                      child: AppText(
                        '$count',
                        style: AppTextStyles.bold10.copyWith(
                          color: isSelected
                              ? AppColors.white
                              : AppColors.sokoonGray,
                          fontSize: 10.sp,
                          height: 1.45,
                        ),
                      ),
                    ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}
