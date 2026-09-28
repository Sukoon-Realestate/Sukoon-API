import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/features/tenant/home/data/models/available_places_model.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_types_model.dart';
import 'package:sokoun_app/features/tenant/home/data/models/tenant_search_content.dart';
import 'package:sokoun_app/shared_widgets/property_filter_button.dart';

import 'available_places_section.dart';
import 'recent_search_row.dart';
import 'search_property_types_section.dart';
import 'search_section_title.dart';
import 'tenant_search_field.dart';
import 'use_current_location_button.dart';
import '../../../data/models/current_location_area.dart';

class TenantSearchContentView extends StatelessWidget {
  const TenantSearchContentView({
    super.key,
    required this.searchController,
    required this.form,
    required this.recentSearches,
    required this.propertyTypesRequest,
    required this.availablePlacesRequest,
    required this.onQueryChanged,
    required this.onQuerySubmitted,
    required this.onSearchPressed,
    required this.onCategorySelected,
    required this.onAreaSelected,
    required this.onRecentSearchSelected,
    required this.onFiltersPressed,
    required this.activeFilterCount,
    required this.onCurrentAreaResolved,
  });

  final TextEditingController searchController;
  final TenantSearchFormState form;
  final List<RecentSearchContent> recentSearches;
  final Future<void> propertyTypesRequest;
  final Future<void>? availablePlacesRequest;
  final ValueChanged<String> onQueryChanged;
  final ValueChanged<String> onQuerySubmitted;
  final VoidCallback onSearchPressed;
  final ValueChanged<PropertyTypeModel> onCategorySelected;
  final ValueChanged<AvailablePlaceModel> onAreaSelected;
  final ValueChanged<RecentSearchContent> onRecentSearchSelected;
  final VoidCallback onFiltersPressed;
  final int activeFilterCount;
  final ValueChanged<CurrentLocationArea> onCurrentAreaResolved;

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      padding: EdgeInsets.symmetric(horizontal: 20.w, vertical: 12.h),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          AppText(
            LocaleKeys.tenantSearchTitle,
            color: AppColors.sokoonNavy,
            fontSize: 20.sp,
            fontWeight: FontWeight.w900,
            textAlign: TextAlign.start,
          ),
          14.szH,
          Row(
            children: [
              Expanded(
                child: TenantSearchField(
                  controller: searchController,
                  onChanged: onQueryChanged,
                  onSubmitted: onQuerySubmitted,
                  onSearchTap: onSearchPressed,
                ),
              ),
              10.szW,
              PropertyFilterButton(
                activeCount: activeFilterCount,
                onPressed: onFiltersPressed,
              ),
            ],
          ),
          UseCurrentLocationButton(onAreaResolved: onCurrentAreaResolved),
          14.szH,
          SearchPropertyTypesSection(
            requestToTryAgainWhenError: propertyTypesRequest,
            selectedCategory: form.selectedCategory,
            onCategorySelected: onCategorySelected,
          ),
          18.szH,
          SearchSectionTitle(LocaleKeys.tenantSearchSuggestedAreas),
          10.szH,
          AvailablePlacesSection(
            requestToTryAgainWhenError: availablePlacesRequest,
            selectedArea: form.selectedArea,
            onAreaSelected: onAreaSelected,
          ),
          18.szH,
          SearchSectionTitle(LocaleKeys.tenantSearchRecentSearches),
          6.szH,
          for (final search in recentSearches)
            RecentSearchRow(
              search: search,
              onTap: () => onRecentSearchSelected(search),
            ),
          24.szH,
        ],
      ),
    );
  }
}
