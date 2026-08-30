import 'package:sokoun_app/features/tenant/favorites/data/models/favorites_content.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_search_model.dart';

abstract final class FavoritePropertyFilter {
  static List<FavoritePropertyContent> apply(
    Iterable<FavoritePropertyContent> items,
    PropertySearchFilters filters,
  ) {
    final List<FavoritePropertyContent> results = items
        .where((item) => _matches(item, filters))
        .toList(growable: true);
    _sort(results, filters.ordering);
    return results;
  }

  static bool _matches(
    FavoritePropertyContent item,
    PropertySearchFilters filters,
  ) {
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
