import 'helpers/favorites_fixtures.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:sokoun_app/features/tenant/favorites/data/favorite_property_filter.dart';
import 'package:sokoun_app/features/tenant/favorites/data/models/favorites_content.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_search_model.dart';

void main() {
  group('FavoritePropertyFilter', () {
    final List<FavoritePropertyContent> favorites = [
      FavoritesFixtures.initialItems[0].copyWith(
        city: 'cairo',
        district: 'nasr-city',
        suitableFor: 'families',
        isVerified: true,
        smokingAllowed: false,
        amenities: const {'wifi', 'parking'},
        savedAt: '2026-08-01',
      ),
      FavoritesFixtures.initialItems[1].copyWith(
        city: 'cairo',
        district: 'new-cairo',
        suitableFor: 'students',
        isVerified: false,
        smokingAllowed: true,
        amenities: const {'wifi'},
        savedAt: '2026-08-03',
      ),
      FavoritesFixtures.initialItems[2].copyWith(
        city: 'giza',
        district: 'mohandessin',
        suitableFor: 'families',
        isVerified: true,
        smokingAllowed: false,
        amenities: const {'wifi', 'parking', 'elevator'},
        savedAt: '2026-08-02',
      ),
    ];

    test('filters the loaded favorites without mutating the source', () {
      const PropertySearchFilters filters = PropertySearchFilters.initial(
        propertyType: 'studio',
        priceMax: '5,000',
        isFurnished: 'true',
        bedrooms: '1',
      );

      final List<FavoritePropertyContent> result = FavoritePropertyFilter.apply(
        favorites,
        filters,
      );

      expect(result.map((item) => item.id), ['2']);
      expect(favorites.map((item) => item.id), ['1', '2', '3']);
    });

    test('supports location, flags, amenities, and three-plus counts', () {
      const PropertySearchFilters filters = PropertySearchFilters.initial(
        city: 'giza',
        district: 'mohandessin',
        suitableFor: 'families',
        isVerified: 'true',
        smokingAllowed: 'false',
        bedrooms: '3+',
        amenities: {'has_wifi', 'has_elevator'},
      );

      final List<FavoritePropertyContent> result = FavoritePropertyFilter.apply(
        favorites,
        filters,
      );

      expect(result.map((item) => item.id), ['3']);
    });

    test('sorts numeric prices locally', () {
      const PropertySearchFilters filters = PropertySearchFilters.initial(
        ordering: '-price',
      );

      final List<FavoritePropertyContent> result = FavoritePropertyFilter.apply(
        favorites,
        filters,
      );

      expect(result.map((item) => item.id), ['3', '1', '2']);
    });

    test('parses optional local-filter fields from saved-property JSON', () {
      final FavoritePropertyContent item = FavoritePropertyContent.fromJson({
        'id': 'favorite-id',
        'city': {'id': 'city-id', 'name': 'Cairo', 'slug': 'cairo'},
        'location': {'district': 'maadi'},
        'is_furnished': 'true',
        'is_verified': 1,
        'smoking_allowed': 'false',
        'amenities': [
          {'value': 'wifi', 'query_parameter': 'has_wifi'},
          {'slug': 'parking'},
        ],
      });

      expect(item.city, 'cairo');
      expect(item.district, 'maadi');
      expect(item.isFurnished, isTrue);
      expect(item.isVerified, isTrue);
      expect(item.smokingAllowed, isFalse);
      expect(item.amenities, {'has_wifi', 'parking'});
    });
  });
}
