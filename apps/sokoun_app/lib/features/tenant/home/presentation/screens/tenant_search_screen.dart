import 'package:sokoun_app/shared_widgets/app_scaffold.dart';
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:sokoun_app/features/tenant/home/data/models/available_places_model.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_search_model.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_types_model.dart';
import 'package:sokoun_app/features/tenant/home/data/models/tenant_search_content.dart';
import 'package:sokoun_app/features/tenant/home/presentation/cubits/available_places_cubit.dart';
import 'package:sokoun_app/features/tenant/home/presentation/cubits/property_types_cubit.dart';
import 'package:sokoun_app/features/tenant/home/presentation/cubits/tenant_recent_searches_cubit.dart';

import '../widgets/tenant_search/imports.dart';
import 'tenant_filter_screen.dart';
import 'tenant_search_results_screen.dart';
import '../../data/models/current_location_area.dart';

class TenantSearchScreen extends StatefulWidget {
  const TenantSearchScreen({super.key});

  @override
  State<TenantSearchScreen> createState() => _TenantSearchScreenState();
}

class _TenantSearchScreenState extends State<TenantSearchScreen> {
  late final ValueNotifier<
    ({
      TenantSearchFormState form,
      int activeFilterCount,
      Future<void>? availablePlacesRequest,
    })
  >
  _viewState;
  late PropertySearchFilters _filters;
  late final TextEditingController _searchController;
  late final PropertyTypesCubit _propertyTypesCubit;
  late final Future<void> _propertyTypesRequest;
  late final AvailablePlacesCubit _availablePlacesCubit;
  late final TenantRecentSearchesCubit _recentSearchesCubit;

  @override
  void initState() {
    super.initState();
    _searchController = TextEditingController();
    _filters = PropertySearchFilters.initial();
    _viewState = ValueNotifier((
      form: const TenantSearchFormState.initial(),
      activeFilterCount: _filters.activeCount,
      availablePlacesRequest: null,
    ));
    _propertyTypesCubit = PropertyTypesCubit();
    _propertyTypesRequest = _propertyTypesCubit.getPropertyTypes();
    _availablePlacesCubit = AvailablePlacesCubit();
    _recentSearchesCubit = TenantRecentSearchesCubit();
    _recentSearchesCubit.loadRecentSearches();
  }

  @override
  void dispose() {
    _searchController.dispose();
    _viewState.dispose();
    _propertyTypesCubit.close();
    _availablePlacesCubit.close();
    _recentSearchesCubit.close();
    super.dispose();
  }

  void _updateQuery(String value) {
    _filters = _filters.copyWith(search: value, page: 1);
    final current = _viewState.value;
    if (current.form.selectedArea != null) {
      _viewState.value = (
        form: current.form.copyWith(clearSelectedArea: true),
        activeFilterCount: current.activeFilterCount,
        availablePlacesRequest: current.availablePlacesRequest,
      );
    }
  }

  void _selectCategory(PropertyTypeModel propertyType) {
    final Future<void> request = _availablePlacesCubit.getAvailablePlaces(
      propertyType.id,
    );
    _filters = _filters.copyWith(propertyType: propertyType.slug, page: 1);
    _viewState.value = (
      form: _viewState.value.form.copyWith(
        selectedCategory: propertyType.slug,
        clearSelectedArea: true,
      ),
      activeFilterCount: _filters.activeCount,
      availablePlacesRequest: request,
    );
  }

  void _selectArea(AvailablePlaceModel area) {
    final String query = area.searchQuery;
    _searchController.text = query;
    _filters = _filters.copyWith(search: query, page: 1);
    final current = _viewState.value;
    _viewState.value = (
      form: current.form.copyWith(selectedArea: query),
      activeFilterCount: current.activeFilterCount,
      availablePlacesRequest: current.availablePlacesRequest,
    );
  }

  Future<void> _selectRecent(RecentSearchContent search) async {
    _searchController.text = search.title;
    final current = _viewState.value;
    _viewState.value = (
      form: current.form.copyWith(clearSelectedArea: true),
      activeFilterCount: current.activeFilterCount,
      availablePlacesRequest: current.availablePlacesRequest,
    );
    await _submitSearch(search.title);
  }

  Future<void> _searchCurrentArea(CurrentLocationArea area) async {
    final query = area.searchQuery;
    _searchController.text = query;
    _filters = _filters.copyWith(
      search: query,
      city: '',
      district: '',
      page: 1,
    );
    final current = _viewState.value;
    _viewState.value = (
      form: current.form.copyWith(selectedArea: query),
      activeFilterCount: _filters.activeCount,
      availablePlacesRequest: current.availablePlacesRequest,
    );
    await _submitSearch(query);
  }

  Future<void> _submitSearch([String? submittedQuery]) async {
    final String query = (submittedQuery ?? _searchController.text).trim();
    if (query.isEmpty &&
        _viewState.value.form.selectedCategory.isEmpty &&
        _viewState.value.form.selectedArea == null) {
      return;
    }

    await _recentSearchesCubit.addRecentSearch(query);
    if (!mounted) {
      return;
    }

    await Go.to(
      TenantSearchResultsScreen(
        initialFilters: _filters.copyWith(
          search: query,
          propertyType: _viewState.value.form.selectedCategory,
          page: 1,
        ),
      ),
    );
  }

  Future<void> _openFilters() async {
    await Go.to<void>(
      TenantFilterScreen(
        initialFilters: _filters.copyWith(
          search: _searchController.text.trim(),
          propertyType: _viewState.value.form.selectedCategory,
          page: 1,
        ),
        onFiltersApplied: _applyFilters,
      ),
    );
  }

  Future<void> _applyFilters(PropertySearchFilters filters) async {
    if (!mounted) return;
    _searchController.text = filters.search;
    _filters = filters;
    final current = _viewState.value;
    _viewState.value = (
      form: current.form.copyWith(
        selectedCategory: filters.propertyType,
        clearSelectedArea: true,
      ),
      activeFilterCount: filters.activeCount,
      availablePlacesRequest: current.availablePlacesRequest,
    );
    if (filters.search.isNotEmpty) {
      await _recentSearchesCubit.addRecentSearch(filters.search);
    }
    if (!mounted) return;
    await Go.to(TenantSearchResultsScreen(initialFilters: filters));
  }

  @override
  Widget build(BuildContext context) {
    return MultiBlocProvider(
      providers: [
        BlocProvider<PropertyTypesCubit>.value(value: _propertyTypesCubit),
        BlocProvider<AvailablePlacesCubit>.value(value: _availablePlacesCubit),
        BlocProvider<TenantRecentSearchesCubit>.value(
          value: _recentSearchesCubit,
        ),
      ],
      child: BlocBuilder<TenantRecentSearchesCubit, List<RecentSearchContent>>(
        builder: (context, recentSearches) =>
            ValueListenableBuilder<
              ({
                TenantSearchFormState form,
                int activeFilterCount,
                Future<void>? availablePlacesRequest,
              })
            >(
              valueListenable: _viewState,
              builder: (context, viewState, _) => AppScaffold(
                showBackButton: false,
                backgroundColor: AppColors.scaffoldBackground,
                body: SafeArea(
                  child: TenantSearchContentView(
                    searchController: _searchController,
                    form: viewState.form,
                    recentSearches: recentSearches,
                    propertyTypesRequest: _propertyTypesRequest,
                    availablePlacesRequest: viewState.availablePlacesRequest,
                    onQueryChanged: _updateQuery,
                    onQuerySubmitted: _submitSearch,
                    onSearchPressed: _submitSearch,
                    onCategorySelected: _selectCategory,
                    onAreaSelected: _selectArea,
                    onRecentSearchSelected: _selectRecent,
                    onFiltersPressed: _openFilters,
                    activeFilterCount: viewState.activeFilterCount,
                    onCurrentAreaResolved: _searchCurrentArea,
                  ),
                ),
              ),
            ),
      ),
    );
  }
}
