import '../favorite_projection.dart';
import 'package:melos_core/core/local_db/read_cache_policy.dart';
import 'package:sokoun_app/features/shared/rental_offers/data/rental_offer_capabilities.dart';
import 'package:sokoun_app/features/shared/rental_offers/data/enums/rental_listing_category.dart';
import 'package:sokoun_app/features/shared/rental_offers/presentation/widgets/rental_listing_categories.dart';
import 'package:sokoun_app/features/shared/rental_offers/presentation/widgets/rental_collection_footer.dart';
import '../../data/favorite_property_filter.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_search_model.dart';
import 'package:flutter/foundation.dart';
import 'package:melos_core/core/helpers/text_style_manager.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/core/extensions/padding_extension.dart';
import 'package:melos_core/core/widgets/app_pagify.dart';
import 'package:pagify/helpers/data_and_pagination_data.dart';
import 'package:pagify/helpers/status_stream.dart';
import 'package:pagify/pagify.dart';
import 'package:sokoun_app/features/tenant/favorites/data/favorites_data.dart';
import 'package:sokoun_app/features/tenant/favorites/data/models/favorites_content.dart';

import 'favorite_property_card.dart';
import 'favorites_empty_state.dart';
import 'favorites_list.dart';

typedef FavoritesPageLoader =
    Future<(List<FavoritePropertyContent>, PaginationData)> Function(
      BuildContext context,
      int page,
    );

class FavoritesContentView extends StatelessWidget {
  const FavoritesContentView({
    super.key,
    required this.itemCount,
    this.onOfferRemoved,
    this.filters = const PropertySearchFilters.initial(),
    required this.initialItems,
    required this.pagifyController,
    required this.loadPage,
    required this.onFavoriteRemoved,
    required this.activeFilterCount,
    required this.onClearFiltersPressed,
    required this.onPagifyStatusChanged,
    this.category = RentalListingCategory.all,
    required this.onCategorySelected,
    this.usesLocalFiltering = false,
  });

  final VoidCallback? onOfferRemoved;
  final PropertySearchFilters filters;
  final ValueListenable<int> itemCount;
  final List<FavoritePropertyContent>? initialItems;
  final PagifyController<FavoritePropertyContent> pagifyController;
  final FavoritesPageLoader loadPage;
  final ValueChanged<FavoritePropertyContent> onFavoriteRemoved;
  final int activeFilterCount;
  final VoidCallback onClearFiltersPressed;
  final ValueChanged<PagifyAsyncCallStatus> onPagifyStatusChanged;
  final RentalListingCategory category;
  final ValueChanged<RentalListingCategory> onCategorySelected;
  final bool usesLocalFiltering;

  @override
  Widget build(BuildContext context) {
    final List<FavoritePropertyContent>? fixtureItems = initialItems;
    final Widget header = Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        RentalListingCategories(
          selected: category,
          onSelected: onCategorySelected,
          loadedPropertiesOnly: usesLocalFiltering,
        ).paddingSymmetric(horizontal: 20, vertical: 12),
        ValueListenableBuilder<int>(
          valueListenable: itemCount,
          builder: (context, count, _) => AppText(
            usesLocalFiltering
                ? LocaleKeys.rentalCategoryLoadedCount.replaceAll(
                    '{count}',
                    '$count',
                  )
                : '$count ${LocaleKeys.favoritesSavedPropertiesCount}',
            style: AppTextStyles.regular12.copyWith(
              color: context.appColor(AppColors.sokoonGray),
            ),
          ).paddingSymmetric(horizontal: 20, vertical: 12),
        ),
      ],
    );
    return fixtureItems != null
        ? FavoritesList(
            header: header,
            items: fixtureItems,
            onFavoriteRemoved: onFavoriteRemoved,
            isFiltered: activeFilterCount > 0,
            onClearFiltersPressed: onClearFiltersPressed,
            category: category,
            onOfferRemoved: onOfferRemoved,
          )
        : AppPagify<FavoritePropertyContent>(
            header: header,
            contentPadding: EdgeInsets.symmetric(horizontal: 20.w),
            enablePullRefresh: true,
            pagifyController: pagifyController,
            disposeController: false,
            rankingType: Ranking.adaptiveGrid,
            asyncCall: loadPage,
            shrinkWrap: false,
            cacheKey: RentalOfferCapabilities.configured.canFavorite
                ? FavoritesData.filteredCacheKey(filters)
                : FavoritesData.cacheKey,
            cachePolicy: ReadCachePolicy.privateMemory,
            cacheToJson: (item) => item.toJson(),
            cacheFromJson: FavoritePropertyContent.fromJson,
            onUpdateStatus: onPagifyStatusChanged,
            emptyListView: FavoritesEmptyState(
              isFiltered: activeFilterCount > 0,
              categoryFiltered: category != RentalListingCategory.all,
              onClearFiltersTap: onClearFiltersPressed,
            ),
            filterItems: (items) => FavoritePropertyFilter.apply(
              FavoriteProjection.apply(items),
              RentalOfferCapabilities.configured.canFavorite
                  ? const PropertySearchFilters.initial()
                  : filters,
              category: category,
            ),
            filteredFooterBuilder:
                (context, hasMore, isLoading, error, loadMore) =>
                    RentalCollectionFooter(
                      hasMorePages: hasMore,
                      isLoading: isLoading,
                      errorMessage: error,
                      onLoadMore: loadMore,
                    ),
            itemBuilder: (context, data, index, item) => FavoritePropertyCard(
              key: ValueKey(item.id),
              item: item,
              onRemove: () => onFavoriteRemoved(item),
              onOfferRemoved: onOfferRemoved,
              category: category,
            ),
          ).paddingBottom(16.h);
  }
}
