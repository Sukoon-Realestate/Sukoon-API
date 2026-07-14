import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/features/home/data/models/tenant_search_result_content.dart';

import '../widgets/tenant_search_results/imports.dart';

class TenantSearchResultsScreen extends StatefulWidget {
  const TenantSearchResultsScreen({
    super.key,
    this.initialQuery,
    this.initialFilters,
  });

  final String? initialQuery;
  final Set<String>? initialFilters;

  @override
  State<TenantSearchResultsScreen> createState() =>
      _TenantSearchResultsScreenState();
}

class _TenantSearchResultsScreenState extends State<TenantSearchResultsScreen> {
  late TenantSearchResultsFilterState _filters;
  late final TextEditingController _queryController;

  @override
  void initState() {
    super.initState();
    _filters = TenantSearchResultsFilterState.initial(
      query: widget.initialQuery,
      selectedFilters: widget.initialFilters,
    );
    _queryController = TextEditingController(text: _filters.query);
  }

  @override
  void dispose() {
    _queryController.dispose();
    super.dispose();
  }

  void _updateQuery(String value) {
    setState(() => _filters = _filters.copyWith(query: value));
  }

  void _removeFilter(ActiveFilterContent filter) {
    final selectedFilters = Set<String>.from(_filters.selectedFilters)
      ..remove(filter.label);
    setState(() {
      _filters = _filters.copyWith(selectedFilters: selectedFilters);
    });
  }

  void _clearFilters() {
    setState(() {
      _filters = _filters.copyWith(selectedFilters: {});
    });
  }

  void _showFiltersSheet() {
    showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      backgroundColor: AppColors.white,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(22.r)),
      ),
      builder: (context) {
        return ResultsFilterSheet(
          groups: TenantSearchResultContent.filterGroups,
          selectedFilters: _filters.selectedFilters,
          onClear: () {
            setState(() {
              _filters = _filters.copyWith(selectedFilters: {});
            });
          },
          onApply: (selectedFilters) {
            setState(() {
              _filters = _filters.copyWith(selectedFilters: selectedFilters);
            });
            Navigator.of(context).pop();
          },
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    final results = TenantSearchResultContent.filterResults(_filters);

    return Directionality(
      textDirection: TextDirection.rtl,
      child: Scaffold(
        backgroundColor: AppColors.scaffoldBackground,
        body: SafeArea(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              ResultsSearchHeader(
                controller: _queryController,
                onChanged: _updateQuery,
                onSubmitted: _updateQuery,
                onFiltersTap: _showFiltersSheet,
              ),
              ActiveFiltersBar(
                filters: _filters.activeFilters,
                onFilterRemoved: _removeFilter,
                onClearAll: _clearFilters,
              ),
              Padding(
                padding: EdgeInsets.symmetric(horizontal: 18.w, vertical: 10.h),
                child: AppText(
                  '${results.length} نتيجة',
                  color: AppColors.sokoonGray,
                  fontSize: 13.sp,
                  fontWeight: FontWeight.w600,
                  textAlign: TextAlign.right,
                ),
              ),
              Expanded(
                child: results.isEmpty
                    ? const _EmptyResultsState()
                    : ListView.separated(
                        padding: EdgeInsets.fromLTRB(16.w, 0, 16.w, 18.h),
                        itemBuilder: (context, index) {
                          return SearchResultCard(item: results[index]);
                        },
                        separatorBuilder: (context, index) => 14.szH,
                        itemCount: results.length,
                      ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _EmptyResultsState extends StatelessWidget {
  const _EmptyResultsState();

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: EdgeInsets.symmetric(horizontal: 28.w),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              width: 78.r,
              height: 78.r,
              alignment: Alignment.center,
              decoration: const BoxDecoration(
                color: AppColors.tealAlpha07,
                shape: BoxShape.circle,
              ),
              child: Icon(
                Icons.search_off_rounded,
                color: AppColors.sokoonTeal,
                size: 34.r,
              ),
            ),
            14.szH,
            AppText(
              'لا توجد نتائج مطابقة',
              color: AppColors.sokoonNavy,
              fontSize: 17.sp,
              fontWeight: FontWeight.w900,
              textAlign: TextAlign.center,
            ),
            6.szH,
            AppText(
              'جرّب تغيير البحث أو إزالة بعض الفلاتر',
              color: AppColors.sokoonGray,
              fontSize: 13.sp,
              fontWeight: FontWeight.w500,
              textAlign: TextAlign.center,
            ),
          ],
        ),
      ),
    );
  }
}
