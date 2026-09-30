import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:flutter/material.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_filter_options_model.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_search_model.dart';

import 'filter_card.dart';
import 'single_select_group.dart';

class FilterPropertyDetailsSection extends StatelessWidget {
  const FilterPropertyDetailsSection({
    super.key,
    required this.filters,
    required this.filterOptions,
    required this.onFiltersChanged,
  });

  final PropertySearchFilters filters;
  final PropertyFilterOptionsModel filterOptions;
  final ValueChanged<PropertySearchFilters> onFiltersChanged;

  List<TenantFilterOption> _withAll(List<TenantFilterOption> options) => [
    TenantFilterOption(value: '', label: LocaleKeys.tenantSearchAll),
    ...options.where((option) => option.selectionValue.isNotEmpty),
  ];

  @override
  Widget build(BuildContext context) {
    return FilterCard(
      title: LocaleKeys.tenantFilterPropertyDetails,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        spacing: 12.h,
        children: [
          SingleSelectGroup(
            title: LocaleKeys.tenantFilterBedrooms,
            options: _withAll(filterOptions.bedrooms),
            selectedValue: filters.bedrooms,
            onSelected: (value) =>
                onFiltersChanged(filters.copyWith(bedrooms: value, page: 1)),
          ),
          SingleSelectGroup(
            title: LocaleKeys.tenantFilterBathrooms,
            options: _withAll(filterOptions.bathrooms),
            selectedValue: filters.bathrooms,
            onSelected: (value) =>
                onFiltersChanged(filters.copyWith(bathrooms: value, page: 1)),
          ),
          SingleSelectGroup(
            title: LocaleKeys.tenantFilterPricePeriod,
            options: _withAll(filterOptions.pricePeriods),
            selectedValue: filters.pricePeriod,
            onSelected: (value) =>
                onFiltersChanged(filters.copyWith(pricePeriod: value, page: 1)),
          ),
          SingleSelectGroup(
            title: LocaleKeys.tenantFilterSuitableFor,
            options: _withAll(filterOptions.suitableFor),
            selectedValue: filters.suitableFor,
            onSelected: (value) =>
                onFiltersChanged(filters.copyWith(suitableFor: value, page: 1)),
          ),
          SingleSelectGroup(
            title: LocaleKeys.tenantFilterFurnished,
            options: _withAll(filterOptions.booleanOptions),
            selectedValue: filters.isFurnished,
            onSelected: (value) =>
                onFiltersChanged(filters.copyWith(isFurnished: value, page: 1)),
          ),
          SingleSelectGroup(
            title: LocaleKeys.tenantFilterSmoking,
            options: _withAll(filterOptions.booleanOptions),
            selectedValue: filters.smokingAllowed,
            onSelected: (value) => onFiltersChanged(
              filters.copyWith(smokingAllowed: value, page: 1),
            ),
          ),
        ],
      ),
    );
  }
}
