import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/features/home/data/models/property_types_model.dart';
import 'package:sokoun_app/features/home/data/models/property_search_model.dart';
import 'package:sokoun_app/features/home/data/models/tenant_search_content.dart';

import '../widgets/tenant_search/imports.dart';
import 'tenant_search_results_screen.dart';

class TenantSearchScreen extends StatefulWidget {
  const TenantSearchScreen({super.key});

  @override
  State<TenantSearchScreen> createState() => _TenantSearchScreenState();
}

class _TenantSearchScreenState extends State<TenantSearchScreen> {
  late TenantSearchFormState _form;
  late final TextEditingController _searchController;

  @override
  void initState() {
    super.initState();
    _form = TenantSearchFormState.initial();
    _searchController = TextEditingController(text: _form.query);
  }

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  void _updateQuery(String value) {
    setState(() {
      _form = _form.copyWith(query: value, clearSelectedArea: true);
    });
  }

  void _selectCategory(PropertyTypeModel? propertyType) {
    setState(() {
      _form = _form.copyWith(selectedCategory: propertyType?.slug ?? '');
    });
  }

  void _selectArea(SuggestedAreaContent area) {
    final String query = area.title;
    _searchController.text = query;
    setState(() {
      _form = _form.copyWith(query: query, selectedArea: area.title);
    });
  }

  Future<void> _selectRecent(RecentSearchContent search) async {
    _searchController.text = search.title;
    _form = _form.copyWith(query: search.title, clearSelectedArea: true);
    await _submitSearch();
  }

  Future<void> _submitSearch([String? submittedQuery]) async {
    final String query = (submittedQuery ?? _searchController.text).trim();
    if (query.isEmpty && !_form.canSearch) {
      return;
    }

    final TenantSearchFormState updatedForm = _form
        .copyWith(query: query)
        .withRecentSearch(query);
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
                onChanged: _updateQuery,
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
              SuggestedAreasGrid(
                areas: TenantSearchContent.suggestedAreas,
                selectedArea: _form.selectedArea,
                onAreaSelected: _selectArea,
              ),
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
