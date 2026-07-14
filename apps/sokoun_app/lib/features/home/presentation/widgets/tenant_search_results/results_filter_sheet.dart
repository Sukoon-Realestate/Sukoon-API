import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/features/home/data/models/tenant_search_result_content.dart';

class ResultsFilterSheet extends StatefulWidget {
  const ResultsFilterSheet({
    super.key,
    required this.groups,
    required this.selectedFilters,
    required this.onApply,
    required this.onClear,
  });

  final List<TenantResultsFilterGroupContent> groups;
  final Set<String> selectedFilters;
  final ValueChanged<Set<String>> onApply;
  final VoidCallback onClear;

  @override
  State<ResultsFilterSheet> createState() => _ResultsFilterSheetState();
}

class _ResultsFilterSheetState extends State<ResultsFilterSheet> {
  late Set<String> _selectedFilters;

  @override
  void initState() {
    super.initState();
    _selectedFilters = Set<String>.from(widget.selectedFilters);
  }

  void _toggleFilter(String filter) {
    setState(() {
      if (_selectedFilters.contains(filter)) {
        _selectedFilters.remove(filter);
      } else {
        _selectedFilters.add(filter);
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    return Directionality(
      textDirection: TextDirection.rtl,
      child: SafeArea(
        top: false,
        child: Padding(
          padding: EdgeInsets.fromLTRB(18.w, 14.h, 18.w, 18.h),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Center(
                child: Container(
                  width: 42.w,
                  height: 4.h,
                  decoration: BoxDecoration(
                    color: AppColors.graySoft,
                    borderRadius: BorderRadius.circular(999.r),
                  ),
                ),
              ),
              16.szH,
              Row(
                children: [
                  AppText(
                    'فلترة النتائج',
                    color: AppColors.sokoonNavy,
                    fontSize: 17.sp,
                    fontWeight: FontWeight.w900,
                  ),
                  const Spacer(),
                  GestureDetector(
                    onTap: () {
                      setState(_selectedFilters.clear);
                      widget.onClear();
                    },
                    behavior: HitTestBehavior.opaque,
                    child: AppText(
                      'مسح',
                      color: AppColors.sokoonRose,
                      fontSize: 13.sp,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                ],
              ),
              16.szH,
              ConstrainedBox(
                constraints: BoxConstraints(maxHeight: 420.h),
                child: SingleChildScrollView(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      for (final group in widget.groups) ...[
                        _FilterGroup(
                          group: group,
                          selectedFilters: _selectedFilters,
                          onToggle: _toggleFilter,
                        ),
                        14.szH,
                      ],
                    ],
                  ),
                ),
              ),
              10.szH,
              GestureDetector(
                onTap: () => widget.onApply(_selectedFilters),
                behavior: HitTestBehavior.opaque,
                child: Container(
                  height: 48.h,
                  alignment: Alignment.center,
                  decoration: BoxDecoration(
                    color: AppColors.sokoonTeal,
                    borderRadius: BorderRadius.circular(14.r),
                  ),
                  child: AppText(
                    'تطبيق الفلاتر',
                    color: AppColors.white,
                    fontSize: 15.sp,
                    fontWeight: FontWeight.w900,
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _FilterGroup extends StatelessWidget {
  const _FilterGroup({
    required this.group,
    required this.selectedFilters,
    required this.onToggle,
  });

  final TenantResultsFilterGroupContent group;
  final Set<String> selectedFilters;
  final ValueChanged<String> onToggle;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        AppText(
          group.title,
          color: AppColors.sokoonNavy,
          fontSize: 13.sp,
          fontWeight: FontWeight.w900,
          textAlign: TextAlign.right,
        ),
        9.szH,
        Wrap(
          alignment: WrapAlignment.end,
          spacing: 8.w,
          runSpacing: 8.h,
          children: [
            for (final option in group.options)
              _FilterOptionChip(
                label: option,
                isSelected: selectedFilters.contains(option),
                onTap: () => onToggle(option),
              ),
          ],
        ),
      ],
    );
  }
}

class _FilterOptionChip extends StatelessWidget {
  const _FilterOptionChip({
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
        padding: EdgeInsets.symmetric(horizontal: 13.w),
        alignment: Alignment.center,
        decoration: BoxDecoration(
          color: isSelected ? AppColors.tealAlpha07 : AppColors.white,
          borderRadius: BorderRadius.circular(999.r),
          border: Border.all(
            color: isSelected ? AppColors.sokoonTeal : AppColors.grayPale,
          ),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            if (isSelected) ...[
              Icon(
                Icons.check_rounded,
                color: AppColors.sokoonTeal,
                size: 14.r,
              ),
              4.szW,
            ],
            AppText(
              label,
              color: isSelected ? AppColors.sokoonTeal : AppColors.sokoonNavy,
              fontSize: 12.sp,
              fontWeight: FontWeight.w700,
            ),
          ],
        ),
      ),
    );
  }
}
