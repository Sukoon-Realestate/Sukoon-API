import '../data/models/favorites_content.dart';
import '../../home/data/models/favorite_target.dart';
import '../../home/presentation/cubits/favorite_coordinator.dart';

/// Keep each saved offer consistent with the latest shared user intention.
abstract final class FavoriteProjection {
  static List<FavoritePropertyContent> apply(
    List<FavoritePropertyContent> items,
  ) => [
    for (final item in items)
      if (!item.hasRentalOffers &&
          FavoriteCoordinator.instance
                  .value(FavoriteTarget(item.id))
                  ?.desired !=
              false)
        item
      else if (item.hasRentalOffers)
        if (item.savedOffers.isEmpty)
          item
        else if (item.savedOffers.any(
          (offer) =>
              FavoriteCoordinator.instance
                  .value(FavoriteTarget(item.id, offer.offerId))
                  ?.desired !=
              false,
        ))
          item.copyWith(
            savedOffers: item.savedOffers
                .where(
                  (offer) =>
                      FavoriteCoordinator.instance
                          .value(FavoriteTarget(item.id, offer.offerId))
                          ?.desired !=
                      false,
                )
                .toList(),
          ),
  ];
}
