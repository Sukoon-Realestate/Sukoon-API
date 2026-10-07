import 'enums/rental_listing_category.dart';
import 'enums/rental_scope.dart';
import 'models/rental_inventory.dart';
import 'models/rental_listing_summary.dart';

abstract final class RentalCollectionFilter {
  static bool matchesProperty({
    required RentalListingCategory category,
    RentalInventory? inventory,
    RentalListingSummary? summary,
  }) => category.acceptsScopes(
    inventory != null
        ? inventory.offers.map((offer) => offer.scope)
        : summary?.scopes.map(RentalScope.fromValue) ?? const [],
  );

  /// The discovery and management unit remains a physical property.
  /// Never generate a card for each matching offer or count an ID twice.
  static List<T> properties<T>(
    Iterable<T> items, {
    required String Function(T) identity,
    required bool Function(T) matches,
  }) {
    final Map<String, T> unique = {};
    for (final T item in items) {
      if (matches(item)) unique[identity(item)] = item;
    }
    return unique.values.toList(growable: false);
  }
}
