import 'package:flutter/material.dart';
import 'package:melos_core/core/helpers/text_style_manager.dart';
import 'package:sokoun_app/shared_widgets/localized_digits_formatter.dart';
import 'package:sokoun_app/shared_widgets/sokoun_motion.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
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
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Row(
            spacing: 10.w,
            children: [
              Expanded(
                child: FilterTextField(
                  label: LocaleKeys.tenantFilterFrom,
                  hint: LocaleKeys.tenantFilterFrom,
                  controller: minPriceController,
                  keyboardType: TextInputType.number,
                  inputFormatters: [const LocalizedDigitsFormatter()],
                  textAlign: TextAlign.center,
                  onChanged: (value) => onFiltersChanged(
                    filters.copyWith(priceMin: value, page: 1),
                  ),
                ),
              ),
              AppText(
                '—',
                style: AppTextStyles.bold16.copyWith(
                  color: AppColors.sokoonGray,
                  fontSize: 16.sp,
                  height: 1.45,
                ),
              ),
              Expanded(
                child: FilterTextField(
                  label: LocaleKeys.tenantFilterTo,
                  hint: LocaleKeys.tenantFilterTo,
                  controller: maxPriceController,
                  keyboardType: TextInputType.number,
                  inputFormatters: [const LocalizedDigitsFormatter()],
                  textAlign: TextAlign.center,
                  onChanged: (value) => onFiltersChanged(
                    filters.copyWith(priceMax: value, page: 1),
                  ),
                ),
              ),
            ],
          ),
          AnimatedSize(
            duration: SokounMotion.duration(context, milliseconds: 240),
            curve: SokounMotion.curve,
            alignment: AlignmentDirectional.topStart,
            child: filters.hasValidPriceRange
                ? const SizedBox(width: double.infinity)
                : Semantics(
                    liveRegion: true,
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const SizedBox(height: 8),
                        AppText(
                          LocaleKeys.searchPriceRangeError,
                          style: AppTextStyles.regular13.copyWith(
                            color: AppColors.sokoonRose,
                            fontSize: 13.sp,
                            height: 1.45,
                          ),
                        ),
                        TextButton.icon(
                          onPressed: () {
                            final minimum = minPriceController.text;
                            minPriceController.text = maxPriceController.text;
                            maxPriceController.text = minimum;
                            onFiltersChanged(
                              filters.copyWith(
                                priceMin: minPriceController.text,
                                priceMax: maxPriceController.text,
                                page: 1,
                              ),
                            );
                          },
                          icon: const Icon(Icons.swap_horiz_rounded, size: 18),
                          label: Text(
                            LocaleKeys.swapPriceRange,
                            style: AppTextStyles.base,
                          ),
                        ),
                      ],
                    ),
                  ),
          ),
        ],
      ),
    );
  }
}
