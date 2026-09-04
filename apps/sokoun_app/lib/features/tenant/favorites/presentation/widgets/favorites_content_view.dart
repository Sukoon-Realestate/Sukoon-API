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
import 'favorites_header.dart';
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
    required this.initialItems,
    required this.pagifyController,
    required this.loadPage,
    required this.onFavoriteRemoved,
    required this.activeFilterCount,
    required this.onFiltersPressed,
    required this.onClearFiltersPressed,
    required this.onPagifyStatusChanged,
  });

  final int itemCount;
  final List<FavoritePropertyContent>? initialItems;
  final PagifyController<FavoritePropertyContent> pagifyController;
  final FavoritesPageLoader loadPage;
  final ValueChanged<FavoritePropertyContent> onFavoriteRemoved;
  final int activeFilterCount;
  final VoidCallback onFiltersPressed;
  final VoidCallback onClearFiltersPressed;
  final ValueChanged<PagifyAsyncCallStatus> onPagifyStatusChanged;

  @override
  Widget build(BuildContext context) {
    final List<FavoritePropertyContent>? fixtureItems = initialItems;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        FavoritesHeader(
          itemCount: itemCount,
          activeFilterCount: activeFilterCount,
          onFiltersPressed: onFiltersPressed,
        ),
        Expanded(
          child: fixtureItems != null
              ? FavoritesList(
                  items: fixtureItems,
                  onFavoriteRemoved: onFavoriteRemoved,
                  isFiltered: activeFilterCount > 0,
                  onClearFiltersPressed: onClearFiltersPressed,
                )
              : AppPagify<FavoritePropertyContent>(
                  pagifyController: pagifyController,
                  asyncCall: loadPage,
                  shrinkWrap: false,
                  cacheKey: activeFilterCount == 0
                      ? FavoritesData.cacheKey
                      : null,
                  cacheToJson: (item) => item.toJson(),
                  cacheFromJson: FavoritePropertyContent.fromJson,
                  onUpdateStatus: onPagifyStatusChanged,
                  emptyListView: FavoritesEmptyState(
                    isFiltered: activeFilterCount > 0,
                    onClearFiltersTap: onClearFiltersPressed,
                  ),
                  itemBuilder: (context, data, index, item) =>
                      FavoritePropertyCard(
                        key: ValueKey(item.id),
                        item: item,
                        onRemove: () => onFavoriteRemoved(item),
                      ).paddingBottom(12.h),
                ).padding(EdgeInsets.fromLTRB(20.w, 0, 20.w, 16.h)),
        ),
      ],
    );
  }
}
