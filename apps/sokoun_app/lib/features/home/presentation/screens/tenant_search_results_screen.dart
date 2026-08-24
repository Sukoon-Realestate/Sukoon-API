import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/core/widgets/app_pagify.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:pagify/helpers/data_and_pagination_data.dart';
import 'package:pagify/pagify.dart';
import 'package:sokoun_app/features/home/data/models/property_details_model.dart';
import 'package:sokoun_app/features/home/data/models/property_search_model.dart';
import 'package:sokoun_app/features/home/data/property_search_data.dart';
import 'package:sokoun_app/features/home/data/models/tenant_search_result_content.dart';

import '../widgets/tenant_filter/property_filter_options.dart';
import '../widgets/tenant_search_results/imports.dart';
import 'tenant_filter_screen.dart';
import 'tenant_property_details_screen.dart';

class TenantSearchResultsScreen extends StatefulWidget {
  const TenantSearchResultsScreen({super.key, required this.initialFilters});

  final PropertySearchFilters initialFilters;

  @override
  State<TenantSearchResultsScreen> createState() =>
      _TenantSearchResultsScreenState();
}

class _TenantSearchResultsScreenState extends State<TenantSearchResultsScreen> {
  late PropertySearchFilters _filters;
  late PropertySearchFilters _paginatedFilters;
  late final TextEditingController _queryController;
  late final PagifyController<PropertyDetailsModel> _pagifyController;
  int? _resultCount;
  int _searchVersion = 0;

  @override
  void initState() {
    super.initState();
    _filters = widget.initialFilters;
    _paginatedFilters = _filters;
    _queryController = TextEditingController(text: _filters.search);
    _pagifyController = PagifyController<PropertyDetailsModel>();
  }

  @override
  void dispose() {
    _queryController.dispose();
    super.dispose();
  }

  void _updateQuery(String value) {
    setState(() => _filters = _filters.copyWith(search: value, page: 1));
  }

  Future<void> _submitQuery(String value) async {
    final PropertySearchFilters updatedFilters = _filters.copyWith(
      search: value.trim(),
      page: 1,
    );
    await _search(updatedFilters);
  }

  Future<void> _removeFilter(ActiveFilterContent filter) async {
    await _search(_filters.removeFilter(filter.id));
  }

  Future<void> _clearFilters() async {
    await _search(_filters.clearFilters());
  }

  Future<void> _openFilters() async {
    final PropertySearchFilters? updatedFilters =
        await Go.to<PropertySearchFilters>(
          TenantFilterScreen(initialFilters: _filters),
        );
    if (updatedFilters == null || !mounted) return;

    _queryController.text = updatedFilters.search;
    await _search(updatedFilters);
  }

  Future<void> _search(PropertySearchFilters filters) async {
    setState(() {
      _filters = filters;
      _paginatedFilters = filters.copyWith(page: 1);
      _resultCount = null;
      _searchVersion++;
    });
    _pagifyController.clear();
    await _pagifyController.refresh();
  }

  Future<(List<PropertyDetailsModel>, PaginationData)> _getPropertiesPage(
    BuildContext context,
    int page,
  ) async {
    final int requestVersion = _searchVersion;
    final PropertySearchFilters requestFilters = _paginatedFilters.copyWith(
      page: page,
    );
    final PropertySearchResponseModel response =
        await PropertySearchData.getProperties(requestFilters);

    if (requestVersion != _searchVersion) {
      return (
        const <PropertyDetailsModel>[],
        PaginationData(perPage: requestFilters.pageSize, totalPages: 1),
      );
    }

    if (page == 1 && mounted) {
      setState(() => _resultCount = response.count);
    }

    final int totalPages = response.count == 0
        ? 1
        : (response.count + requestFilters.pageSize - 1) ~/
              requestFilters.pageSize;
    return (
      response.results,
      PaginationData(perPage: requestFilters.pageSize, totalPages: totalPages),
    );
  }

  void _openDetails(PropertyDetailsModel item) {
    if (item.id.isEmpty) return;
    Go.to(TenantPropertyDetailsScreen(propertyId: item.id));
  }

  List<ActiveFilterContent> get _activeFilters => _filters.activeFilters
      .map(
        (filter) => ActiveFilterContent(
          id: filter.id,
          label: TenantPropertyFilterOptions.labelFor(filter),
        ),
      )
      .toList(growable: false);

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.scaffoldBackground,
      body: SafeArea(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            ResultsSearchHeader(
              controller: _queryController,
              onChanged: _updateQuery,
              onSubmitted: _submitQuery,
              onFiltersTap: _openFilters,
            ),
            ActiveFiltersBar(
              filters: _activeFilters,
              onFilterRemoved: _removeFilter,
              onClearAll: _clearFilters,
            ),
            Padding(
              padding: EdgeInsets.symmetric(horizontal: 18.w, vertical: 10.h),
              child: AppText(
                _resultCount == null
                    ? LocaleKeys.tenantSearchResultsCount
                    : '$_resultCount ${LocaleKeys.tenantSearchResultsCount}',
                color: AppColors.sokoonGray,
                fontSize: 13.sp,
                fontWeight: FontWeight.w600,
              ),
            ),
            Expanded(
              child: Padding(
                padding: EdgeInsets.fromLTRB(16.w, 0, 16.w, 18.h),
                child: AppPagify<PropertyDetailsModel>(
                  pagifyController: _pagifyController,
                  asyncCall: _getPropertiesPage,
                  shrinkWrap: false,
                  itemBuilder: (context, data, index, item) => Padding(
                    padding: EdgeInsets.only(bottom: 14.h),
                    child: SearchResultCard(
                      item: item,
                      onDetailsTap: () => _openDetails(item),
                    ),
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
