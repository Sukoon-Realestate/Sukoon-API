import 'package:sokoun_app/shared_widgets/sokoun_motion.dart';
import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:sokoun_app/shared_widgets/sokoun_layout.dart';
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
      duration: SokounMotion.duration(context, milliseconds: 220),
      child: items.isEmpty
          ? FavoritesEmptyState(
              isFiltered: isFiltered,
              onClearFiltersTap: onClearFiltersPressed,
            )
          : SingleChildScrollView(
              key: const PageStorageKey('favorites-list'),
              padding: EdgeInsets.fromLTRB(20.w, 0, 20.w, 16.h),
              child: SokounAdaptiveGrid(
                children: [
                  for (final item in items)
                    FavoritePropertyCard(
                      key: ValueKey(item.id),
                      item: item,
                      onRemove: () => onFavoriteRemoved(item),
                    ),
                ],
              ),
            ),
    );
  }
}
