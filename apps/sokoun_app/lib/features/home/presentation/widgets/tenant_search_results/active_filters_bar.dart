import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:sokoun_app/features/home/data/models/tenant_search_result_content.dart';

import 'active_filter_chip.dart';
import 'clear_filters_chip.dart';

class ActiveFiltersBar extends StatelessWidget {
  const ActiveFiltersBar({
    super.key,
    required this.filters,
    this.onFilterRemoved,
    this.onClearAll,
  });

  final List<ActiveFilterContent> filters;
  final ValueChanged<ActiveFilterContent>? onFilterRemoved;
  final VoidCallback? onClearAll;

  @override
  Widget build(BuildContext context) {
    return Container(
      height: 48.h,
      padding: EdgeInsets.symmetric(horizontal: 14.w, vertical: 8.h),
      decoration: const BoxDecoration(
        color: AppColors.white,
        border: Border(bottom: BorderSide(color: AppColors.grayPale)),
      ),
      child: SingleChildScrollView(
        scrollDirection: Axis.horizontal,
        child: Row(
          textDirection: TextDirection.ltr,
          children: [
            for (final filter in filters) ...[
              ActiveFilterChip(
                filter: filter,
                onRemove: onFilterRemoved == null
                    ? null
                    : () => onFilterRemoved!(filter),
              ),
              8.szW,
            ],
            if (filters.isNotEmpty) ClearFiltersChip(onTap: onClearAll),
          ],
        ),
      ),
    );
  }
}
