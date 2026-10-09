import 'package:sokoun_app/features/tenant/home/data/public_property_cache.dart';
import 'package:melos_core/core/local_db/read_cache_policy.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/core/extensions/padding_extension.dart';
import 'package:melos_core/core/widgets/app_pagify.dart';
import 'package:pagify/helpers/data_and_pagination_data.dart';
import 'package:pagify/pagify.dart';
import 'package:melos_core/core/shared/base_state.dart';
import 'package:melos_core/core/widgets/toast_messages/toast_message.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_details_model.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_filter_options_model.dart';
import 'package:sokoun_app/features/tenant/home/data/models/tenant_search_result_content.dart';

import 'empty_results_state.dart';
import 'search_refresh_notice.dart';
import 'search_results_header.dart';
import 'search_result_card.dart';
import '../../../data/models/property_search_model.dart';
import 'package:sokoun_app/features/shared/rental_offers/data/enums/rental_listing_category.dart';
import 'package:sokoun_app/features/shared/rental_offers/data/rental_collection_filter.dart';
import 'package:sokoun_app/features/shared/rental_offers/presentation/widgets/rental_collection_footer.dart';

typedef PropertySearchPageLoader =
    Future<(List<PropertyDetailsModel>, PaginationData)> Function(
      BuildContext context,
      int page,
    );

class TenantSearchResultsContent extends StatefulWidget {
  const TenantSearchResultsContent({
    super.key,
    required this.queryController,
    required this.pagifyController,
    required this.filterOptions,
    required this.activeFilters,
    required this.resultCount,
    required this.cacheKey,
    required this.loadPage,
    this.scrollController,
    this.preferences,
    required this.onQueryChanged,
    required this.onQuerySubmitted,
    required this.onFiltersPressed,
    required this.onFilterRemoved,
    required this.onClearFiltersPressed,
    required this.onResetSearchPressed,
    required this.onCategorySelected,
  });

  final TextEditingController queryController;
  final PagifyController<PropertyDetailsModel> pagifyController;
  final PropertyFilterOptionsModel filterOptions;
  final List<ActiveFilterContent> activeFilters;
  final ValueListenable<int?> resultCount;
  final String cacheKey;
  final PropertySearchPageLoader loadPage;
  final ScrollController? scrollController;
  final PropertySearchFilters? preferences;
  final ValueChanged<String> onQueryChanged;
  final ValueChanged<String> onQuerySubmitted;
  final VoidCallback onFiltersPressed;
  final ValueChanged<ActiveFilterContent> onFilterRemoved;
  final VoidCallback onClearFiltersPressed;
  final VoidCallback onResetSearchPressed;
  final ValueChanged<RentalListingCategory> onCategorySelected;

  @override
  State<TenantSearchResultsContent> createState() =>
      _TenantSearchResultsContentState();
}

class _TenantSearchResultsContentState
    extends State<TenantSearchResultsContent> {
  final ValueNotifier<String?> _errorMessage = ValueNotifier(null);

  @override
  void dispose() {
    _errorMessage.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AppPagify<PropertyDetailsModel>(
      scrollController: widget.scrollController,
      header: TenantSearchResultsHeader(
        queryController: widget.queryController,
        activeFilters: widget.activeFilters,
        resultCount: widget.resultCount,
        onQueryChanged: widget.onQueryChanged,
        onQuerySubmitted: widget.onQuerySubmitted,
        onFiltersPressed: widget.onFiltersPressed,
        onFilterRemoved: widget.onFilterRemoved,
        onClearFiltersPressed: widget.onClearFiltersPressed,
        category: RentalListingCategory.fromScope(
          widget.preferences?.rentalScope ?? '',
        ),
        onCategorySelected: widget.onCategorySelected,
      ),
      contentPadding: EdgeInsets.symmetric(horizontal: 16.w),
      enablePullRefresh: true,
      retainItemsOnRefresh: true,
      retainedItemsNotice: (isLoading, retry) =>
          ValueListenableBuilder<String?>(
            valueListenable: _errorMessage,
            builder: (context, message, _) => SearchRefreshNotice(
              isLoading: isLoading,
              errorMessage: message,
              onRetry: retry,
            ),
          ),
      onSuccess: (_, _) => _errorMessage.value = null,
      onError: (_, _, error) {
        _errorMessage.value = error.msg;
        if (error.msg.isNotEmpty) {
          Messages.showToast(msg: error.msg, status: BaseStatus.error);
        }
      },
      pagifyController: widget.pagifyController,
      rankingType: Ranking.adaptiveGrid,
      disposeController: false,
      asyncCall: widget.loadPage,
      shrinkWrap: false,
      cacheKey: widget.cacheKey,
      cachePolicy: ReadCachePolicy.publicListing,
      cacheToJson: (item) => PublicPropertyCache.sanitize(item.toJson()),
      cacheFromJson: PropertyDetailsModel.fromJson,
      emptyListView: EmptyResultsState(
        onResetSearchPressed: widget.onResetSearchPressed,
      ),
      filterItems: (items) => RentalCollectionFilter.properties(
        items,
        identity: (property) => property.id,
        matches: (_) => true,
      ),
      filteredFooterBuilder: (context, hasMore, isLoading, error, loadMore) =>
          RentalCollectionFooter(
            hasMorePages: hasMore,
            isLoading: isLoading,
            errorMessage: error,
            onLoadMore: loadMore,
          ),
      itemBuilder: (context, data, index, item) => SearchResultCard(
        item: item,
        filterOptions: widget.filterOptions,
        preferences: widget.preferences,
      ),
    ).paddingBottom(18.h);
  }
}
