import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/features/home/data/models/tenant_search_result_content.dart';

import '../widgets/tenant_search_results/imports.dart';
import 'tenant_filter_screen.dart';
import 'tenant_property_details_screen.dart';

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

  Future<void> _openFilters() async {
    final updatedFilters = await Navigator.of(context)
        .push<TenantSearchResultsFilterState>(
          MaterialPageRoute(
            builder: (_) => TenantFilterScreen(initialFilters: _filters),
          ),
        );
    if (updatedFilters == null) {
      return;
    }

    setState(() {
      _filters = updatedFilters;
      _queryController.text = updatedFilters.query;
    });
  }

  void _openDetails(SearchResultContent item) {
    Navigator.of(context).push(
      MaterialPageRoute<void>(
        builder: (_) => TenantPropertyDetailsScreen(item: item),
      ),
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
                onFiltersTap: _openFilters,
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
                    ? const EmptyResultsState()
                    : ListView.separated(
                        padding: EdgeInsets.fromLTRB(16.w, 0, 16.w, 18.h),
                        itemBuilder: (context, index) {
                          return SearchResultCard(
                            item: results[index],
                            onDetailsTap: () => _openDetails(results[index]),
                          );
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
