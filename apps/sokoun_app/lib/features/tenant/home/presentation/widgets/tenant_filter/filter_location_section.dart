import 'package:flutter/material.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_search_model.dart';

import 'filter_card.dart';
import 'filter_text_field.dart';

class FilterLocationSection extends StatelessWidget {
  const FilterLocationSection({
    super.key,
    required this.filters,
    required this.cityController,
    required this.districtController,
    required this.onFiltersChanged,
  });

  final PropertySearchFilters filters;
  final TextEditingController cityController;
  final TextEditingController districtController;
  final ValueChanged<PropertySearchFilters> onFiltersChanged;

  @override
  Widget build(BuildContext context) {
    return FilterCard(
      title: LocaleKeys.tenantFilterLocation,
      child: Column(
        children: [
          FilterTextField(
            label: LocaleKeys.tenantFilterCity,
            hint: LocaleKeys.tenantFilterCityHint,
            controller: cityController,
            onChanged: (value) =>
                onFiltersChanged(filters.copyWith(city: value, page: 1)),
          ),
          10.szH,
          FilterTextField(
            label: LocaleKeys.tenantFilterDistrict,
            hint: LocaleKeys.tenantFilterDistrictHint,
            controller: districtController,
            onChanged: (value) =>
                onFiltersChanged(filters.copyWith(district: value, page: 1)),
          ),
        ],
      ),
    );
  }
}
