import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/padding_extension.dart';
import 'package:melos_core/core/helpers/text_style_manager.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/features/tenant/home/data/models/tenant_search_result_content.dart';

import 'active_filters_bar.dart';
import 'results_search_header.dart';
import 'package:sokoun_app/features/shared/rental_offers/data/enums/rental_listing_category.dart';
import 'package:sokoun_app/features/shared/rental_offers/data/rental_offer_capabilities.dart';
import 'package:sokoun_app/features/shared/rental_offers/presentation/widgets/rental_listing_categories.dart';

class TenantSearchResultsHeader extends StatelessWidget {
  const TenantSearchResultsHeader({
    super.key,
    required this.queryController,
    required this.activeFilters,
    required this.resultCount,
    required this.onQueryChanged,
    required this.onQuerySubmitted,
    required this.onFiltersPressed,
    required this.onFilterRemoved,
    required this.onClearFiltersPressed,
    required this.category,
    required this.onCategorySelected,
  });

  final TextEditingController queryController;
  final List<ActiveFilterContent> activeFilters;
  final ValueListenable<int?> resultCount;
  final ValueChanged<String> onQueryChanged;
  final ValueChanged<String> onQuerySubmitted;
  final VoidCallback onFiltersPressed;
  final ValueChanged<ActiveFilterContent> onFilterRemoved;
  final VoidCallback onClearFiltersPressed;
  final RentalListingCategory category;
  final ValueChanged<RentalListingCategory> onCategorySelected;

  @override
  Widget build(BuildContext context) => Column(
    crossAxisAlignment: CrossAxisAlignment.stretch,
    children: [
      ResultsSearchHeader(
        controller: queryController,
        onChanged: onQueryChanged,
        onSubmitted: onQuerySubmitted,
        onFiltersTap: onFiltersPressed,
      ),
      RentalListingCategories(
        selected: category,
        onSelected: onCategorySelected,
        includeUnspecified: false,
        scopeSearchUnavailable: !RentalOfferCapabilities.configured.canSearch,
      ).paddingSymmetric(horizontal: 18, vertical: 12),
      ActiveFiltersBar(
        filters: activeFilters,
        onFilterRemoved: onFilterRemoved,
        onClearAll: onClearFiltersPressed,
      ),
      ValueListenableBuilder<int?>(
        valueListenable: resultCount,
        builder: (context, count, _) => AppText(
          count == null
              ? LocaleKeys.tenantSearchResultsCount
              : '$count ${LocaleKeys.tenantSearchResultsCount}',
          style: AppTextStyles.semiBold.copyWith(
            color: context.appColor(AppColors.sokoonGray),
            fontSize: 13.sp,
          ),
        ).paddingSymmetric(horizontal: 18.w, vertical: 10.h),
      ),
    ],
  );
}
