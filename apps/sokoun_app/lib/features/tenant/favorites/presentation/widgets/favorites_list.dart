import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:sokoun_app/features/tenant/favorites/data/models/favorites_content.dart';

import 'favorite_property_card.dart';
import 'favorites_empty_state.dart';

class FavoritesList extends StatelessWidget {
  const FavoritesList({
    super.key,
    required this.items,
    required this.onFavoriteRemoved,
    required this.onBrowsePressed,
  });

  final List<FavoritePropertyContent> items;
  final void Function(FavoritePropertyContent item) onFavoriteRemoved;
  final VoidCallback onBrowsePressed;

  @override
  Widget build(BuildContext context) {
    return AnimatedSwitcher(
      duration: const Duration(milliseconds: 220),
      child: items.isEmpty
          ? FavoritesEmptyState(
              key: const ValueKey('favorites-empty'),
              onBrowseTap: onBrowsePressed,
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
              separatorBuilder: (context, index) => SizedBox(height: 12.h),
              itemCount: items.length,
            ),
    );
  }
}
