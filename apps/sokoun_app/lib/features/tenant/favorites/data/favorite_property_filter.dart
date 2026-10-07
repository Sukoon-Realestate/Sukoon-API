import 'package:sokoun_app/features/tenant/favorites/data/models/favorites_content.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_search_model.dart';
import 'package:sokoun_app/features/shared/rental_offers/data/enums/rental_listing_category.dart';
import 'package:sokoun_app/features/shared/rental_offers/data/models/rental_selection.dart';
import 'package:sokoun_app/features/shared/rental_offers/data/rental_collection_filter.dart';

abstract final class FavoritePropertyFilter {
  static List<FavoritePropertyContent> apply(
    Iterable<FavoritePropertyContent> items,
    PropertySearchFilters filters, {
    RentalListingCategory category = RentalListingCategory.all,
  }) {
    final List<FavoritePropertyContent> results =
        RentalCollectionFilter.properties(
              items,
              identity: (item) => item.id,
              matches: (item) => category.acceptsScopes(
                item.savedOffers.map((offer) => offer.scope),
              ),
            )
            .map((item) {
              if (item.savedOffers.isEmpty) return item;
              return item.copyWith(
                savedOffers: item.savedOffers
                    .where(
                      (offer) =>
                          category.accepts(offer.scope) &&
                          _matchesOffer(offer, item, filters),
                    )
                    .toList(growable: false),
              );
            })
            .where((item) => _matches(item, filters))
            .toList(growable: true);
    if (!results.any((item) => item.hasRentalOffers)) {
      _sort(results, filters.ordering);
    }
    return results;
  }

  static bool _matches(
    FavoritePropertyContent item,
    PropertySearchFilters filters,
  ) {
    if (item.hasRentalOffers) {
      if (!_matchesPropertyContext(item, filters)) return false;
      if (item.savedOffers.isNotEmpty) return true;
      // A missing saved snapshot cannot inherit a discovery offer's scope,
      // price or terms. Keep it accessible only without offer-specific filters.
      return filters.rentalScope.isEmpty &&
          filters.pricePeriod.isEmpty &&
          filters.priceMin.isEmpty &&
          filters.priceMax.isEmpty &&
          filters.suitableFor.isEmpty &&
          filters.smokingAllowed.isEmpty &&
          _contains(_normalize(item.title), filters.search);
    }
    if (filters.rentalScope.isNotEmpty) return false;
    final String title = _normalize(item.title);
    if (!_contains(title, filters.search) ||
        !_matchesLocation(item.city, title, filters.city) ||
        !_matchesLocation(item.district, title, filters.district) ||
        !_equals(item.propertyType, filters.propertyType) ||
        !_equals(item.pricePeriod, filters.pricePeriod) ||
        !_equals(item.suitableFor, filters.suitableFor) ||
        !_matchesBoolean(item.isFurnished, filters.isFurnished) ||
        !_matchesNullableBoolean(item.isVerified, filters.isVerified) ||
        !_matchesNullableBoolean(item.smokingAllowed, filters.smokingAllowed) ||
        !_matchesCount(item.bedrooms, filters.bedrooms) ||
        !_matchesCount(item.bathrooms, filters.bathrooms) ||
        !_matchesAmenities(item.amenities, filters.amenities)) {
      return false;
    }

    final double? price = _number(item.price);
    final double? minimumPrice = _number(filters.priceMin);
    final double? maximumPrice = _number(filters.priceMax);
    if (minimumPrice != null && (price == null || price < minimumPrice)) {
      return false;
    }
    if (maximumPrice != null && (price == null || price > maximumPrice)) {
      return false;
    }
    return true;
  }

  static bool _matchesPropertyContext(
    FavoritePropertyContent item,
    PropertySearchFilters filters,
  ) =>
      _matchesLocation(item.city, _normalize(item.title), filters.city) &&
      _matchesLocation(
        item.district,
        _normalize(item.title),
        filters.district,
      ) &&
      _equals(item.propertyType, filters.propertyType) &&
      _matchesBoolean(item.isFurnished, filters.isFurnished) &&
      _matchesNullableBoolean(item.isVerified, filters.isVerified) &&
      _matchesCount(item.bedrooms, filters.bedrooms) &&
      _matchesCount(item.bathrooms, filters.bathrooms) &&
      _matchesAmenities(item.amenities, filters.amenities);

  static bool _matchesOffer(
    RentalSelection offer,
    FavoritePropertyContent property,
    PropertySearchFilters filters,
  ) {
    if (!_equals(offer.scopeValue ?? '', filters.rentalScope) ||
        !_equals(offer.terms.pricePeriod, filters.pricePeriod) ||
        !_equals(offer.terms.suitableFor, filters.suitableFor) ||
        !_matchesNullableBoolean(
          offer.terms.smokingAllowed,
          filters.smokingAllowed,
        ) ||
        !_contains(
          _normalize(
            [
              property.title,
              offer.name,
              ...offer.roomNames,
              offer.bedName,
            ].join(' '),
          ),
          filters.search,
        )) {
      return false;
    }
    final double? minimum = _number(filters.priceMin);
    final double? maximum = _number(filters.priceMax);
    final double? price = _number(offer.terms.price);
    if (minimum != null || maximum != null) {
      // Weekly and monthly amounts are not interchangeable.
      if (filters.pricePeriod.isEmpty || price == null) return false;
      if (minimum != null && price < minimum) return false;
      if (maximum != null && price > maximum) return false;
    }
    return true;
  }

  static bool _contains(String source, String filter) {
    final String normalizedFilter = _normalize(filter);
    return normalizedFilter.isEmpty || source.contains(normalizedFilter);
  }

  static bool _matchesLocation(
    String value,
    String normalizedTitle,
    String filter,
  ) {
    final String normalizedFilter = _normalize(filter);
    if (normalizedFilter.isEmpty) return true;
    return _normalize(value).contains(normalizedFilter) ||
        normalizedTitle.contains(normalizedFilter);
  }

  static bool _equals(String value, String filter) {
    final String normalizedFilter = _normalize(filter);
    return normalizedFilter.isEmpty || _normalize(value) == normalizedFilter;
  }

  static bool _matchesBoolean(bool value, String filter) {
    final bool? expected = _boolean(filter);
    return expected == null || value == expected;
  }

  static bool _matchesNullableBoolean(bool? value, String filter) {
    final bool? expected = _boolean(filter);
    return expected == null || value == expected;
  }

  static bool _matchesCount(int value, String filter) {
    if (filter.isEmpty) return true;
    final int? expected = int.tryParse(
      RegExp(r'\d+').firstMatch(filter)?.group(0) ?? '',
    );
    if (expected == null) return true;
    return filter.contains('+') ? value >= expected : value == expected;
  }

  static bool _matchesAmenities(
    Set<String> itemAmenities,
    Set<String> filters,
  ) {
    if (filters.isEmpty) return true;
    final Set<String> normalizedAmenities = itemAmenities
        .map(_normalizeAmenity)
        .toSet();
    return filters.map(_normalizeAmenity).every(normalizedAmenities.contains);
  }

  static bool? _boolean(String value) {
    switch (_normalize(value)) {
      case 'true':
      case '1':
      case 'yes':
        return true;
      case 'false':
      case '0':
      case 'no':
        return false;
      default:
        return null;
    }
  }

  static double? _number(String value) {
    final String normalized = value.replaceAll(RegExp(r'[^0-9.]'), '');
    return normalized.isEmpty ? null : double.tryParse(normalized);
  }

  static String _normalize(String value) => value.trim().toLowerCase();

  static String _normalizeAmenity(String value) {
    final String normalized = _normalize(value);
    return normalized.startsWith('has_') ? normalized.substring(4) : normalized;
  }

  static void _sort(List<FavoritePropertyContent> items, String ordering) {
    switch (ordering) {
      case 'price':
        items.sort(
          (a, b) => (_number(a.price) ?? 0).compareTo(_number(b.price) ?? 0),
        );
      case '-price':
        items.sort(
          (a, b) => (_number(b.price) ?? 0).compareTo(_number(a.price) ?? 0),
        );
      case 'rating':
        items.sort((a, b) => a.rating.compareTo(b.rating));
      case '-rating':
        items.sort((a, b) => b.rating.compareTo(a.rating));
      case 'saved_at':
        items.sort((a, b) => a.savedAt.compareTo(b.savedAt));
      case '-saved_at':
        items.sort((a, b) => b.savedAt.compareTo(a.savedAt));
    }
  }
}
