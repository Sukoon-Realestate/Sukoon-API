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

class TenantSearchScreen extends StatefulWidget {
  const TenantSearchScreen({super.key});

  @override
  State<TenantSearchScreen> createState() => _TenantSearchScreenState();
}

class _TenantSearchScreenState extends State<TenantSearchScreen> {
  late TenantSearchFormState _form;
  late PropertySearchFilters _filters;
  late final TextEditingController _searchController;
  late final PropertyTypesCubit _propertyTypesCubit;
  late final Future<void> _propertyTypesRequest;
  late final AvailablePlacesCubit _availablePlacesCubit;
  late final TenantRecentSearchesCubit _recentSearchesCubit;
  Future<void>? _availablePlacesRequest;

  @override
  void initState() {
    super.initState();
    _form = const TenantSearchFormState.initial();
    _searchController = TextEditingController();
    _filters = PropertySearchFilters.initial();
    _propertyTypesCubit = PropertyTypesCubit();
    _propertyTypesRequest = _propertyTypesCubit.getPropertyTypes();
    _availablePlacesCubit = AvailablePlacesCubit();
    _recentSearchesCubit = TenantRecentSearchesCubit();
    _recentSearchesCubit.loadRecentSearches();
  }

  @override
  void dispose() {
    _searchController.dispose();
    _propertyTypesCubit.close();
    _availablePlacesCubit.close();
    _recentSearchesCubit.close();
    super.dispose();
  }

  void _updateQuery(String value) {
    setState(() {
      _filters = _filters.copyWith(search: value, page: 1);
      if (_form.selectedArea != null) {
        _form = _form.copyWith(clearSelectedArea: true);
      }
    });
  }

  void _selectCategory(PropertyTypeModel propertyType) {
    final Future<void> request = _availablePlacesCubit.getAvailablePlaces(
      propertyType.id,
    );
    setState(() {
      _form = _form.copyWith(
        selectedCategory: propertyType.slug,
        clearSelectedArea: true,
      );
      _filters = _filters.copyWith(propertyType: propertyType.slug, page: 1);
      _availablePlacesRequest = request;
    });
  }

  void _selectArea(AvailablePlaceModel area) {
    final String query = area.searchQuery;
    _searchController.text = query;
    setState(() {
      _form = _form.copyWith(selectedArea: query);
      _filters = _filters.copyWith(search: query, page: 1);
    });
  }

  Future<void> _selectRecent(RecentSearchContent search) async {
    _searchController.text = search.title;
    _form = _form.copyWith(clearSelectedArea: true);
    await _submitSearch(search.title);
  }

  Future<void> _submitSearch([String? submittedQuery]) async {
    final String query = (submittedQuery ?? _searchController.text).trim();
    if (query.isEmpty &&
        _form.selectedCategory.isEmpty &&
        _form.selectedArea == null) {
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
          propertyType: _form.selectedCategory,
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
          propertyType: _form.selectedCategory,
          page: 1,
        ),
        onFiltersApplied: _applyFilters,
      ),
    );
  }

  Future<void> _applyFilters(PropertySearchFilters filters) async {
    if (!mounted) return;
    _searchController.text = filters.search;
    setState(() {
      _filters = filters;
      _form = _form.copyWith(
        selectedCategory: filters.propertyType,
        clearSelectedArea: true,
      );
    });
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
        builder: (context, recentSearches) => Scaffold(
          backgroundColor: AppColors.scaffoldBackground,
          body: SafeArea(
            child: TenantSearchContentView(
              searchController: _searchController,
              form: _form,
              recentSearches: recentSearches,
              propertyTypesRequest: _propertyTypesRequest,
              availablePlacesRequest: _availablePlacesRequest,
              onQueryChanged: _updateQuery,
              onQuerySubmitted: _submitSearch,
              onSearchPressed: _submitSearch,
              onCategorySelected: _selectCategory,
              onAreaSelected: _selectArea,
              onRecentSearchSelected: _selectRecent,
              onFiltersPressed: _openFilters,
              activeFilterCount: _filters.activeCount,
            ),
          ),
        ),
      ),
    );
  }
}
