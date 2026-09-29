import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/padding_extension.dart';
import 'package:melos_core/core/helpers/text_style_manager.dart';
import 'package:melos_core/core/widgets/app_pagify.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:pagify/helpers/data_and_pagination_data.dart';
import 'package:pagify/pagify.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_details_model.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_filter_options_model.dart';
import 'package:sokoun_app/features/tenant/home/data/models/tenant_search_result_content.dart';

import 'active_filters_bar.dart';
import 'empty_results_state.dart';
import 'results_search_header.dart';
import 'search_result_card.dart';

typedef PropertySearchPageLoader =
    Future<(List<PropertyDetailsModel>, PaginationData)> Function(
      BuildContext context,
      int page,
    );

class TenantSearchResultsContent extends StatelessWidget {
  const TenantSearchResultsContent({
    super.key,
    required this.queryController,
    required this.pagifyController,
    required this.filterOptions,
    required this.activeFilters,
    required this.resultCount,
    required this.cacheKey,
    required this.loadPage,
    required this.onQueryChanged,
    required this.onQuerySubmitted,
    required this.onFiltersPressed,
    required this.onFilterRemoved,
    required this.onClearFiltersPressed,
    required this.onResetSearchPressed,
  });

  final TextEditingController queryController;
  final PagifyController<PropertyDetailsModel> pagifyController;
  final PropertyFilterOptionsModel filterOptions;
  final List<ActiveFilterContent> activeFilters;
  final ValueListenable<int?> resultCount;
  final String cacheKey;
  final PropertySearchPageLoader loadPage;
  final ValueChanged<String> onQueryChanged;
  final ValueChanged<String> onQuerySubmitted;
  final VoidCallback onFiltersPressed;
  final ValueChanged<ActiveFilterContent> onFilterRemoved;
  final VoidCallback onClearFiltersPressed;
  final VoidCallback onResetSearchPressed;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        ResultsSearchHeader(
          controller: queryController,
          onChanged: onQueryChanged,
          onSubmitted: onQuerySubmitted,
          onFiltersTap: onFiltersPressed,
        ),
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
              color: AppColors.sokoonGray,
              fontSize: 13.sp,
            ),
          ).paddingSymmetric(horizontal: 18.w, vertical: 10.h),
        ),
        Expanded(
          child: AppPagify<PropertyDetailsModel>(
            pagifyController: pagifyController,
            rankingType: Ranking.adaptiveGrid,
            disposeController: false,
            asyncCall: loadPage,
            shrinkWrap: false,
            cacheKey: cacheKey,
            cacheToJson: (item) => item.toJson(),
            cacheFromJson: PropertyDetailsModel.fromJson,
            emptyListView: EmptyResultsState(
              onResetSearchPressed: onResetSearchPressed,
            ),
            itemBuilder: (context, data, index, item) =>
                SearchResultCard(item: item, filterOptions: filterOptions),
          ).padding(EdgeInsets.fromLTRB(16.w, 0, 16.w, 18.h)),
        ),
      ],
    );
  }
}
