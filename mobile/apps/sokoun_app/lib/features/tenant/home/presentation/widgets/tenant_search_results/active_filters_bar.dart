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
    final Widget content = filters.isEmpty
        ? const SizedBox(width: double.infinity)
        : Container(
            padding: EdgeInsets.symmetric(horizontal: 14.w, vertical: 8.h),
            decoration: BoxDecoration(
              color: context.appColor(AppColors.white, surface: true),
              border: Border(
                bottom: BorderSide(color: context.appColor(AppColors.grayPale)),
              ),
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
          );
    final Duration duration = SokounMotion.duration(context, milliseconds: 240);
    if (duration == Duration.zero) return content;
    return AnimatedSize(
      duration: duration,
      curve: SokounMotion.curve,
      alignment: AlignmentDirectional.topStart,
      child: content,
    );
  }
}
