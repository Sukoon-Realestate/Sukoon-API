import 'package:flutter/material.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/helpers/text_style_manager.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/shared_widgets/sokoun_selection_chip.dart';
import '../../data/enums/rental_listing_category.dart';

class RentalListingCategories extends StatelessWidget {
  const RentalListingCategories({
    super.key,
    required this.selected,
    required this.onSelected,
    this.includeUnspecified = true,
    this.loadedPropertiesOnly = false,
    this.scopeSearchUnavailable = false,
  });

  final RentalListingCategory selected;
  final ValueChanged<RentalListingCategory> onSelected;
  final bool includeUnspecified;
  final bool loadedPropertiesOnly;
  final bool scopeSearchUnavailable;

  static String label(RentalListingCategory category) => switch (category) {
    RentalListingCategory.all => LocaleKeys.rentalCategoryAll,
    RentalListingCategory.unspecified => LocaleKeys.rentalCategoryUnspecified,
    _ => category.scope!.label,
  };

  @override
  Widget build(BuildContext context) => Column(
    crossAxisAlignment: CrossAxisAlignment.stretch,
    spacing: 8,
    children: [
      AppText(
        LocaleKeys.rentalAccommodationCategories,
        style: AppTextStyles.bold14,
      ),
      Wrap(
        spacing: 8,
        runSpacing: 8,
        children: [
          for (final category in RentalListingCategory.values)
            if (includeUnspecified ||
                category != RentalListingCategory.unspecified)
              SokounSelectionChip(
                label: label(category),
                selected: selected == category,
                onPressed:
                    scopeSearchUnavailable &&
                        category != RentalListingCategory.all
                    ? null
                    : () => onSelected(category),
              ),
        ],
      ),
      if (selected == RentalListingCategory.unspecified)
        AppText(
          LocaleKeys.rentalCategoryUnspecifiedHint,
          style: AppTextStyles.regular12.copyWith(
            color: context.appColor(AppColors.sokoonGray),
            height: 1.45,
          ),
        ),
      if (loadedPropertiesOnly || scopeSearchUnavailable)
        AppText(
          scopeSearchUnavailable
              ? LocaleKeys.rentalCategorySearchUnavailable
              : LocaleKeys.rentalCategoryLoadedHint,
          style: AppTextStyles.regular12.copyWith(
            color: context.appColor(AppColors.sokoonGray),
            height: 1.45,
          ),
        ),
    ],
  );
}
