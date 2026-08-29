import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/helpers/status_builder.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/features/tenant/home/data/models/available_places_model.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_types_model.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_search_model.dart';
import 'package:sokoun_app/features/tenant/home/data/models/tenant_search_content.dart';
import 'package:sokoun_app/features/tenant/home/presentation/cubits/available_places_cubit.dart';

import '../widgets/tenant_search/imports.dart';
import 'tenant_search_results_screen.dart';

class TenantSearchScreen extends StatefulWidget {
  const TenantSearchScreen({super.key});

  @override
  State<TenantSearchScreen> createState() => _TenantSearchScreenState();
}

class _TenantSearchScreenState extends State<TenantSearchScreen> {
  static const String _initialQuery = 'مدينة نصر، القاهرة';

  late TenantSearchFormState _form;
  late final TextEditingController _searchController;
  late final AvailablePlacesCubit _availablePlacesCubit;
  Future<void>? _availablePlacesRequest;

  @override
  void initState() {
    super.initState();
    _form = TenantSearchFormState.initial();
    _searchController = TextEditingController(text: _initialQuery);
    _availablePlacesCubit = AvailablePlacesCubit();
  }

  @override
  void dispose() {
    _searchController.dispose();
    _availablePlacesCubit.close();
    super.dispose();
  }

  void _clearSelectedArea(String _) {
    if (_form.selectedArea == null) return;
    setState(() => _form = _form.copyWith(clearSelectedArea: true));
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
      _availablePlacesRequest = request;
    });
  }

  void _selectArea(AvailablePlaceModel area) {
    final String query = area.searchQuery;
    _searchController.text = query;
    setState(() => _form = _form.copyWith(selectedArea: query));
  }

  Widget _buildAvailablePlaces() {
    final Future<void>? request = _availablePlacesRequest;
    if (request == null) {
      return AppText(
        LocaleKeys.tenantSearchSelectPropertyType,
        color: AppColors.sokoonMuted,
        fontSize: 12.sp,
        textAlign: TextAlign.right,
      );
    }

    return BlocProvider<AvailablePlacesCubit>.value(
      value: _availablePlacesCubit,
      child:
          StatusBuilder<AvailablePlacesCubit, AvailablePlacesModel>.withShimmer(
            initialDataForShimmer: const AvailablePlacesModel.initial(),
            requestToTryAgainWhenError: request,
            errorType: ErrorType.defaultView,
            builder: (data) {
              if (data.places.isEmpty) {
                return AppText(
                  LocaleKeys.tenantSearchNoAvailablePlaces,
                  color: AppColors.sokoonMuted,
                  fontSize: 12.sp,
                  textAlign: TextAlign.right,
                );
              }

              return SuggestedAreasGrid(
                places: data.places,
                selectedArea: _form.selectedArea,
                onAreaSelected: _selectArea,
              );
            },
          ),
    );
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

    final TenantSearchFormState updatedForm = _form.withRecentSearch(query);
    setState(() => _form = updatedForm);
    await TenantSearchContent.saveRecentSearches(updatedForm.recentSearches);
    if (!mounted) {
      return;
    }

    await Go.to(
      TenantSearchResultsScreen(
        initialFilters: PropertySearchFilters.initial(
          search: query,
          propertyType: updatedForm.selectedCategory,
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.scaffoldBackground,
      body: SafeArea(
        child: SingleChildScrollView(
          padding: EdgeInsets.symmetric(horizontal: 20.w, vertical: 12.h),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              AppText(
                LocaleKeys.tenantSearchTitle,
                color: AppColors.sokoonNavy,
                fontSize: 20.sp,
                fontWeight: FontWeight.w900,
                textAlign: TextAlign.right,
              ),
              14.szH,
              TenantSearchField(
                controller: _searchController,
                onChanged: _clearSelectedArea,
                onSubmitted: (value) => _submitSearch(value),
                onSearchTap: () => _submitSearch(),
              ),
              14.szH,
              SearchCategoryChips(
                selectedCategory: _form.selectedCategory,
                onCategorySelected: _selectCategory,
              ),
              18.szH,
              SearchSectionTitle(LocaleKeys.tenantSearchSuggestedAreas),
              10.szH,
              _buildAvailablePlaces(),
              18.szH,
              SearchSectionTitle(LocaleKeys.tenantSearchRecentSearches),
              6.szH,
              for (final search in _form.recentSearches)
                RecentSearchRow(
                  search: search,
                  onTap: () => _selectRecent(search),
                ),
              24.szH,
            ],
          ),
        ),
      ),
    );
  }
}
