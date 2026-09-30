import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_filter_options_model.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_search_model.dart';

import 'filter_card.dart';
import 'filter_chip_wrap.dart';
import 'filter_location_section.dart';
import 'filter_price_range_section.dart';
import 'filter_property_details_section.dart';
import 'single_select_group.dart';

class TenantFilterContent extends StatelessWidget {
  const TenantFilterContent({
    super.key,
    required this.filters,
    required this.filterOptions,
    required this.cityController,
    required this.districtController,
    required this.minPriceController,
    required this.maxPriceController,
    required this.onFiltersChanged,
  });

  final PropertySearchFilters filters;
  final PropertyFilterOptionsModel filterOptions;
  final TextEditingController cityController;
  final TextEditingController districtController;
  final TextEditingController minPriceController;
  final TextEditingController maxPriceController;
  final ValueChanged<PropertySearchFilters> onFiltersChanged;

  List<TenantFilterOption> _withAll(List<TenantFilterOption> options) => [
    TenantFilterOption(value: '', label: LocaleKeys.tenantSearchAll),
    ...options.where((option) => option.selectionValue.isNotEmpty),
  ];

  void _selectPropertyType(String value) {
    onFiltersChanged(
      filters.copyWith(
        propertyType: filters.propertyType == value ? '' : value,
        page: 1,
      ),
    );
  }

  void _toggleAmenity(String value) {
    final Set<String> selectedAmenities = Set<String>.from(filters.amenities);
    selectedAmenities.contains(value)
        ? selectedAmenities.remove(value)
        : selectedAmenities.add(value);
    onFiltersChanged(filters.copyWith(amenities: selectedAmenities, page: 1));
  }

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      padding: EdgeInsets.fromLTRB(16.w, 12.h, 16.w, 20.h),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        spacing: 12.h,
        children: [
          FilterCard(
            title: LocaleKeys.tenantFilterOrdering,
            child: SingleSelectGroup(
              title: LocaleKeys.tenantFilterSortListings,
              options: filterOptions.ordering,
              selectedValue: filters.ordering,
              onSelected: (value) =>
                  onFiltersChanged(filters.copyWith(ordering: value, page: 1)),
            ),
          ),
          FilterCard(
            title: LocaleKeys.tenantFilterPropertyType,
            child: FilterChipWrap(
              options: filterOptions.propertyTypes,
              selectedValues: {filters.propertyType},
              onSelected: _selectPropertyType,
            ),
          ),
          FilterLocationSection(
            filters: filters,
            cityController: cityController,
            districtController: districtController,
            onFiltersChanged: onFiltersChanged,
          ),
          FilterPriceRangeSection(
            filters: filters,
            minPriceController: minPriceController,
            maxPriceController: maxPriceController,
            onFiltersChanged: onFiltersChanged,
          ),
          FilterPropertyDetailsSection(
            filters: filters,
            filterOptions: filterOptions,
            onFiltersChanged: onFiltersChanged,
          ),
          FilterCard(
            title: LocaleKeys.tenantFilterAmenities,
            child: FilterChipWrap(
              options: filterOptions.amenities,
              selectedValues: filters.amenities,
              onSelected: _toggleAmenity,
            ),
          ),
          FilterCard(
            title: LocaleKeys.tenantFilterVerification,
            child: SingleSelectGroup(
              title: LocaleKeys.tenantFilterVerified,
              options: _withAll(filterOptions.booleanOptions),
              selectedValue: filters.isVerified,
              onSelected: (value) => onFiltersChanged(
                filters.copyWith(isVerified: value, page: 1),
              ),
            ),
          ),
        ],
      ),
    );
  }
}
