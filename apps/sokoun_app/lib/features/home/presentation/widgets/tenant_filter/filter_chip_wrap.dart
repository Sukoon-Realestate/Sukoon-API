import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/widgets/app_text.dart';

class FilterChipWrap extends StatelessWidget {
  const FilterChipWrap({
    super.key,
    required this.options,
    required this.selectedValues,
    required this.onSelected,
  });

  final List<String> options;
  final Set<String> selectedValues;
  final ValueChanged<String> onSelected;

  @override
  Widget build(BuildContext context) {
    return Wrap(
      alignment: WrapAlignment.end,
      spacing: 8.w,
      runSpacing: 8.h,
      children: [
        for (final option in options)
          _FilterChip(
            label: option,
            isSelected: selectedValues.contains(option),
            onTap: () => onSelected(option),
          ),
      ],
    );
  }
}

class _FilterChip extends StatelessWidget {
  const _FilterChip({
    required this.label,
    required this.isSelected,
    required this.onTap,
  });

  final String label;
  final bool isSelected;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      behavior: HitTestBehavior.opaque,
      child: Container(
        height: 34.h,
        padding: EdgeInsets.symmetric(horizontal: 14.w),
        alignment: Alignment.center,
        decoration: BoxDecoration(
          color: isSelected ? AppColors.tealAlpha07 : AppColors.white,
          borderRadius: BorderRadius.circular(999.r),
          border: Border.all(
            color: isSelected ? AppColors.sokoonTeal : AppColors.grayPale,
          ),
        ),
        child: AppText(
          label,
          color: isSelected ? AppColors.sokoonTeal : AppColors.sokoonNavy,
          fontSize: 12.sp,
          fontWeight: FontWeight.w700,
        ),
      ),
    );
  }
}
