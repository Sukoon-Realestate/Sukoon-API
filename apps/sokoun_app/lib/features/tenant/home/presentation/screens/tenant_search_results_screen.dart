import '../cubits/search_restoration_cubit.dart';
import '../../data/models/search_restoration_snapshot.dart';
import 'package:melos_core/core/widgets/toast_messages/toast_message.dart';
import 'dart:async';
import 'package:melos_core/config/language/languages.dart';
import 'package:melos_core/core/network/account_session.dart';
import '../../data/saved_search_validation.dart';
import 'package:sokoun_app/features/tenant/premium_alerts/presentation/widgets/premium_alert_entry.dart';
import 'package:melos_core/core/network/network_request.dart';
import 'package:melos_core/core/error/exceptions.dart';
import 'package:melos_core/core/shared/base_state.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:sokoun_app/shared_widgets/sokoun_layout.dart';
import 'package:sokoun_app/shared_widgets/app_scaffold.dart';
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/base_crud/code/presentation/cubit/base_cubit/async_cubit.dart';
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
import 'property_map_screen.dart';
import 'package:sokoun_app/features/tenant/decision_tools/presentation/widgets/save_search_button.dart';
import 'package:sokoun_app/features/tenant/decision_tools/presentation/screens/decision_tools_screen.dart';
import 'package:sokoun_app/features/shared/rental_offers/data/enums/rental_listing_category.dart';

class TenantSearchResultsScreen extends StatefulWidget {
  const TenantSearchResultsScreen({
    super.key,
    required this.initialFilters,
    this.initialFilterOptions,
    this.validateSavedFilters = false,
  });

  final PropertySearchFilters initialFilters;
  final PropertyFilterOptionsModel? initialFilterOptions;
  final bool validateSavedFilters;

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
  final ValueNotifier<int?> _resultCount = ValueNotifier<int?>(null);
  int _searchVersion = 0;
  Timer? _queryDebounce;
  late final SearchRestorationCubit _restoration;
  final ScrollController _scroll = ScrollController();
  int _loadedPages = 1;
  double? _restoreOffset;
  int _restorePages = 1;
  CancelToken _searchCancellation = CancelToken();

  @override
  void initState() {
    super.initState();
    _filters = widget.initialFilters;
    _paginatedFilters = _filters;
    _queryController = TextEditingController(text: _filters.search);
    _pagifyController = PagifyController<PropertyDetailsModel>();
    _restoration = SearchRestorationCubit();
    _scroll.addListener(_saveSnapshot);
    unawaited(_restoreSearch());
    _propertyFilterOptionsCubit = PropertyFilterOptionsCubit(
      initialOptions: widget.initialFilterOptions,
    );
    if (widget.initialFilterOptions == null) {
      unawaited(_prepareFilterOptions());
    }
  }

  Future<void> _restoreSearch() async {
    await _restoration.load();
    if (!mounted) return;
    final snapshot = _restoration.state.record?.value;
    if (snapshot == null ||
        snapshot.filters.cacheKey !=
            _paginatedFilters.copyWith(page: 1).cacheKey) {
      return;
    }
    _restorePages = snapshot.loadedPages;
    _restoreOffset = snapshot.offset;
    if (_pagifyController.items.isNotEmpty) _applyRestoreOffset();
  }

  void _saveSnapshot() {
    if (!mounted) return;
    _restoration.schedule(
      SearchRestorationSnapshot(
        filters: _paginatedFilters,
        loadedPages: _loadedPages,
        anchorId: _pagifyController.items.firstOrNull?.id ?? '',
        offset: _restoreOffset ?? (_scroll.hasClients ? _scroll.offset : 0),
      ),
    );
  }

  void _applyRestoreOffset({bool hasMore = true}) {
    final offset = _restoreOffset;
    if (!mounted || offset == null) return;
    if (!_scroll.hasClients) {
      WidgetsBinding.instance.addPostFrameCallback((_) {
        if (mounted && _scroll.hasClients) {
          _applyRestoreOffset(hasMore: hasMore);
        }
      });
      return;
    }
    final position = _scroll.position;
    final target = offset.clamp(0, position.maxScrollExtent);
    _scroll.jumpTo(target.toDouble());
    if (!hasMore || _loadedPages >= _restorePages || target == offset) {
      _restoreOffset = null;
      _saveSnapshot();
    }
  }

  Future<void> _prepareFilterOptions() async {
    await _propertyFilterOptionsCubit.getFilterOptions();
    if (!mounted ||
        !widget.validateSavedFilters ||
        !_propertyFilterOptionsCubit.state.isSuccess ||
        _propertyFilterOptionsCubit.state.fromCache) {
      return;
    }
    final checked = SavedSearchValidation.against(
      _filters,
      _propertyFilterOptionsCubit.data,
    );
    if (checked.changed) {
      Messages.showToast(
        msg: LocaleKeys.professionalRemovedFilters,
        status: BaseStatus.error,
      );
      await _search(checked.filters);
    }
  }

  @override
  void dispose() {
    _queryDebounce?.cancel();
    _searchCancellation.cancel();
    _scroll.removeListener(_saveSnapshot);
    _scroll.dispose();
    unawaited(_restoration.close());
    _queryController.dispose();
    _pagifyController.dispose();
    _resultCount.dispose();
    _propertyFilterOptionsCubit.close();
    super.dispose();
  }

  void _updateQuery(String value) {
    _filters = _filters.copyWith(search: value, page: 1);
    _queryDebounce?.cancel();
    _queryDebounce = Timer(const Duration(milliseconds: 300), () {
      if (mounted) unawaited(_submitQuery(value));
    });
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

  Future<void> _selectCategory(RentalListingCategory category) => _search(
    _filters.copyWith(rentalScope: category.scope?.value ?? '', page: 1),
  );

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
        initialFilterOptions: _propertyFilterOptionsCubit.state.status.isSuccess
            ? _propertyFilterOptionsCubit.data
            : null,
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
    _queryDebounce?.cancel();
    _searchCancellation.cancel();
    // A submitted search replaces filters, cache identity, and list together.
    setState(() {
      _filters = filters;
      _paginatedFilters = filters.copyWith(page: 1);
      _searchVersion++;
      _loadedPages = 1;
      _restoreOffset = null;
    });
    _saveSnapshot();
    final int version = _searchVersion;
    _resultCount.value = null;
    // Let the collection receive the submitted filters before refreshing it.
    await WidgetsBinding.instance.endOfFrame;
    if (mounted && version == _searchVersion) await _pagifyController.refresh();
  }

  Future<(List<PropertyDetailsModel>, PaginationData)> _getPropertiesPage(
    BuildContext context,
    int page,
  ) async {
    if (page == 1) {
      _searchCancellation.cancel();
      _searchCancellation = CancelToken();
    }
    final int requestVersion = _searchVersion;
    final int session = AccountSession.generation;
    final String language = Languages.currentLanguage.languageCode;
    final PropertySearchFilters requestFilters = _paginatedFilters.copyWith(
      page: page,
    );
    final (
      PropertySearchResponseModel response,
      PaginationData pagination,
    ) = await PropertySearchData.getPropertiesPage(
      requestFilters,
      cancelToken: _searchCancellation,
    );

    if (!mounted ||
        requestVersion != _searchVersion ||
        session != AccountSession.generation ||
        language != Languages.currentLanguage.languageCode) {
      throw const RequestCancelledException();
    }

    if (page == 1 && mounted) {
      _resultCount.value = response.count;
    }

    _loadedPages = page > _loadedPages ? page : _loadedPages;
    if (_restoreOffset != null) {
      WidgetsBinding.instance.addPostFrameCallback(
        (_) => _applyRestoreOffset(hasMore: page < pagination.totalPages),
      );
    }
    _saveSnapshot();
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
      child: AppScaffold(
        title: LocaleKeys.searchResult,
        actions: [
          PremiumAlertEntry(filters: _paginatedFilters, compact: true),
          SaveSearchButton(filters: _filters),
          IconButton(
            tooltip: LocaleKeys.freeMapResults,
            icon: const Icon(Icons.map_outlined),
            onPressed: () => Go.to(PropertyMapScreen(filters: _filters)),
          ),
          IconButton(
            tooltip: LocaleKeys.freeDecisionTools,
            icon: const Icon(Icons.checklist),
            onPressed: () => Go.to(const DecisionToolsScreen()),
          ),
        ],
        showBackButton: true,
        backgroundColor: context.appColor(
          AppColors.scaffoldBackground,
          surface: true,
        ),
        contentWidth: SokounContentWidth.wide,
        body: SafeArea(
          child:
              BlocSelector<
                PropertyFilterOptionsCubit,
                AsyncState<PropertyFilterOptionsModel>,
                PropertyFilterOptionsModel
              >(
                selector: (state) => state.data,
                builder: (context, filterOptions) => TenantSearchResultsContent(
                  queryController: _queryController,
                  preferences: _filters,
                  pagifyController: _pagifyController,
                  filterOptions: filterOptions,
                  activeFilters: _activeFilters(filterOptions),
                  resultCount: _resultCount,
                  cacheKey: PropertySearchData.cacheKeyFor(_paginatedFilters),
                  loadPage: _getPropertiesPage,
                  scrollController: _scroll,
                  onQueryChanged: _updateQuery,
                  onQuerySubmitted: _submitQuery,
                  onFiltersPressed: _openFilters,
                  onFilterRemoved: _removeFilter,
                  onClearFiltersPressed: _clearFilters,
                  onResetSearchPressed: _resetSearchAndFilters,
                  onCategorySelected: _selectCategory,
                ),
              ),
        ),
      ),
    );
  }
}
