import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:sokoun_app/features/tenant/home/data/models/tenant_search_result_content.dart';

import 'active_filter_chip.dart';
import 'package:sokoun_app/shared_widgets/sokoun_motion.dart';
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
    return AnimatedSize(
      duration: SokounMotion.duration(context, milliseconds: 240),
      curve: SokounMotion.curve,
      alignment: AlignmentDirectional.topStart,
      child: filters.isEmpty
          ? const SizedBox(width: double.infinity)
          : Container(
              padding: EdgeInsets.symmetric(horizontal: 14.w, vertical: 8.h),
              decoration: const BoxDecoration(
                color: AppColors.white,
                border: Border(bottom: BorderSide(color: AppColors.grayPale)),
              ),
              child: SingleChildScrollView(
                scrollDirection: Axis.horizontal,
                child: Row(
                  spacing: 8.w,
                  children: [
                    for (final filter in filters)
                      ActiveFilterChip(
                        filter: filter,
                        onRemove: onFilterRemoved == null
                            ? null
                            : () => onFilterRemoved!(filter),
                      ),
                    if (filters.isNotEmpty) ClearFiltersChip(onTap: onClearAll),
                  ],
                ),
              ),
            ),
    );
  }
}
