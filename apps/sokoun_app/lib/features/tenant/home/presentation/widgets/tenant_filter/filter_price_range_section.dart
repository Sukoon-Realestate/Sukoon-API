import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_search_model.dart';

import 'filter_card.dart';
import 'filter_text_field.dart';

class FilterPriceRangeSection extends StatelessWidget {
  const FilterPriceRangeSection({
    super.key,
    required this.filters,
    required this.minPriceController,
    required this.maxPriceController,
    required this.onFiltersChanged,
  });

  final PropertySearchFilters filters;
  final TextEditingController minPriceController;
  final TextEditingController maxPriceController;
  final ValueChanged<PropertySearchFilters> onFiltersChanged;

  @override
  Widget build(BuildContext context) {
    return FilterCard(
      title: LocaleKeys.tenantFilterPriceRange,
      child: Row(
        children: [
          Expanded(
            child: FilterTextField(
              label: LocaleKeys.tenantFilterFrom,
              hint: LocaleKeys.tenantFilterFrom,
              controller: minPriceController,
              keyboardType: TextInputType.number,
              inputFormatters: [FilteringTextInputFormatter.digitsOnly],
              textAlign: TextAlign.center,
              onChanged: (value) =>
                  onFiltersChanged(filters.copyWith(priceMin: value, page: 1)),
            ),
          ),
          10.szW,
          AppText(
            '—',
            color: AppColors.sokoonGray,
            fontSize: 16.sp,
            fontWeight: FontWeight.w700,
          ),
          10.szW,
          Expanded(
            child: FilterTextField(
              label: LocaleKeys.tenantFilterTo,
              hint: LocaleKeys.tenantFilterTo,
              controller: maxPriceController,
              keyboardType: TextInputType.number,
              inputFormatters: [FilteringTextInputFormatter.digitsOnly],
              textAlign: TextAlign.center,
              onChanged: (value) =>
                  onFiltersChanged(filters.copyWith(priceMax: value, page: 1)),
            ),
          ),
        ],
      ),
    );
  }
}
