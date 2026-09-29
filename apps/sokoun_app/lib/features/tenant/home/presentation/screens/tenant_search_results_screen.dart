import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:sokoun_app/shared_widgets/sokoun_layout.dart';
import 'package:sokoun_app/shared_widgets/app_scaffold.dart';
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/helpers/status_builder.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:pagify/helpers/data_and_pagination_data.dart';
import 'package:pagify/pagify.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_details_model.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_filter_options_model.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_search_model.dart';
import 'package:sokoun_app/features/tenant/home/data/models/tenant_search_result_content.dart';
import 'package:sokoun_app/features/tenant/home/data/property_search_data.dart';
import 'package:sokoun_app/features/tenant/home/presentation/cubits/property_filter_options_cubit.dart';

import '../widgets/tenant_filter/property_filter_label_resolver.dart';
import '../widgets/tenant_search_results/imports.dart';
import 'tenant_filter_screen.dart';

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
  late final PropertyFilterOptionsCubit _propertyFilterOptionsCubit;
  late final Future<void> _propertyFilterOptionsRequest;
  final ValueNotifier<int?> _resultCount = ValueNotifier<int?>(null);
  int _searchVersion = 0;

  @override
  void initState() {
    super.initState();
    _filters = widget.initialFilters;
    _paginatedFilters = _filters;
    _queryController = TextEditingController(text: _filters.search);
    _pagifyController = PagifyController<PropertyDetailsModel>();
    _propertyFilterOptionsCubit = PropertyFilterOptionsCubit();
    _propertyFilterOptionsRequest = _propertyFilterOptionsCubit
        .getFilterOptions();
  }

  @override
  void dispose() {
    _queryController.dispose();
    _pagifyController.dispose();
    _resultCount.dispose();
    _propertyFilterOptionsCubit.close();
    super.dispose();
  }

  void _updateQuery(String value) {
    _filters = _filters.copyWith(search: value, page: 1);
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
    final PropertySearchFilters clearedFilters = _filters.clearFilters();
    final String defaultOrdering =
        _propertyFilterOptionsCubit.state.data.defaultOrdering;
    await _search(
      defaultOrdering.isEmpty
          ? clearedFilters
          : clearedFilters.copyWith(ordering: defaultOrdering),
    );
  }

  Future<void> _openFilters() async {
    await Go.to<void>(
      TenantFilterScreen(
        initialFilters: _filters,
        onFiltersApplied: _applyFilters,
      ),
    );
  }

  Future<void> _applyFilters(PropertySearchFilters filters) async {
    if (!mounted) return;
    _queryController.text = filters.search;
    await _search(filters);
  }

  Future<void> _search(PropertySearchFilters filters) async {
    // A submitted search replaces filters, cache identity, and list together.
    setState(() {
      _filters = filters;
      _paginatedFilters = filters.copyWith(page: 1);
      _searchVersion++;
    });
    _resultCount.value = null;
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
    final (PropertySearchResponseModel response, PaginationData pagination) =
        await PropertySearchData.getPropertiesPage(requestFilters);

    if (requestVersion != _searchVersion) {
      return (
        const <PropertyDetailsModel>[],
        PaginationData(perPage: requestFilters.pageSize, totalPages: 1),
      );
    }

    if (page == 1 && mounted) {
      _resultCount.value = response.count;
    }

    return (response.results, pagination);
  }

  List<ActiveFilterContent> _activeFilters(
    PropertyFilterOptionsModel filterOptions,
  ) {
    final PropertyFilterLabelResolver labelResolver =
        PropertyFilterLabelResolver(filterOptions);
    return _filters.activeFilters
        .map(
          (filter) => ActiveFilterContent(
            id: filter.id,
            label: labelResolver.labelFor(filter),
          ),
        )
        .toList(growable: false);
  }

  Future<void> _resetSearchAndFilters() async {
    final String defaultOrdering =
        _propertyFilterOptionsCubit.state.data.defaultOrdering;
    PropertySearchFilters resetFilters = PropertySearchFilters.initial(
      pageSize: _filters.pageSize,
    );
    if (defaultOrdering.isNotEmpty) {
      resetFilters = resetFilters.copyWith(ordering: defaultOrdering);
    }
    _queryController.clear();
    await _search(resetFilters);
  }

  @override
  Widget build(BuildContext context) {
    return BlocProvider<PropertyFilterOptionsCubit>.value(
      value: _propertyFilterOptionsCubit,
      child:
          StatusBuilder<
            PropertyFilterOptionsCubit,
            PropertyFilterOptionsModel
          >.withShimmer(
            initialDataForShimmer: const PropertyFilterOptionsModel.initial(),
            requestToTryAgainWhenError: _propertyFilterOptionsRequest,
            onRetry: _propertyFilterOptionsCubit.getFilterOptions,
            errorType: ErrorType.defaultView,
            builder: (filterOptions) => AppScaffold(
              title: LocaleKeys.searchResult,
              showBackButton: true,
              backgroundColor: AppColors.scaffoldBackground,
              contentWidth: SokounContentWidth.wide,
              body: SafeArea(
                child: TenantSearchResultsContent(
                  queryController: _queryController,
                  pagifyController: _pagifyController,
                  filterOptions: filterOptions,
                  activeFilters: _activeFilters(filterOptions),
                  resultCount: _resultCount,
                  cacheKey: PropertySearchData.cacheKeyFor(_paginatedFilters),
                  loadPage: _getPropertiesPage,
                  onQueryChanged: _updateQuery,
                  onQuerySubmitted: _submitQuery,
                  onFiltersPressed: _openFilters,
                  onFilterRemoved: _removeFilter,
                  onClearFiltersPressed: _clearFilters,
                  onResetSearchPressed: _resetSearchAndFilters,
                ),
              ),
            ),
          ),
    );
  }
}
