import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:sokoun_app/features/tenant/favorites/data/models/favorites_content.dart';

import 'favorite_property_card.dart';
import 'favorites_empty_state.dart';

class FavoritesList extends StatelessWidget {
  const FavoritesList({
    super.key,
    required this.items,
    required this.onFavoriteRemoved,
    required this.isFiltered,
    required this.onClearFiltersPressed,
  });

  final List<FavoritePropertyContent> items;
  final void Function(FavoritePropertyContent item) onFavoriteRemoved;
  final bool isFiltered;
  final VoidCallback onClearFiltersPressed;

  @override
  Widget build(BuildContext context) {
    return AnimatedSwitcher(
      duration: const Duration(milliseconds: 220),
      child: items.isEmpty
          ? FavoritesEmptyState(
              key: const ValueKey('favorites-empty'),
              isFiltered: isFiltered,
              onClearFiltersTap: onClearFiltersPressed,
            )
          : ListView.separated(
              key: const PageStorageKey('favorites-list'),
              padding: EdgeInsets.fromLTRB(20.w, 0, 20.w, 16.h),
              itemBuilder: (context, index) {
                final FavoritePropertyContent item = items[index];
                return FavoritePropertyCard(
                  key: ValueKey(item.id),
                  item: item,
                  onRemove: () => onFavoriteRemoved(item),
                );
              },
              separatorBuilder: (context, index) => 12.szH,
              itemCount: items.length,
            ),
    );
  }
}
