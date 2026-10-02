import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:sokoun_app/features/tenant/favorites/data/models/favorites_content.dart';

abstract final class FavoritesFixtures {
  static List<FavoritePropertyContent> get initialItems => [
    FavoritePropertyContent(
      id: '1',
      mainImage: '',
      title: LocaleKeys.ownerPropertyNasrCityTitle,
      propertyType: 'apartment',
      isFurnished: true,
      bedrooms: 3,
      bathrooms: 2,
      area: 90,
      price: '6,500',
      pricePeriod: 'monthly',
      rating: 4.8,
      savedAt: '',
      isSaved: true,
    ),
    FavoritePropertyContent(
      id: '2',
      mainImage: '',
      title: LocaleKeys.favoritesModernStudioTitle,
      propertyType: 'studio',
      isFurnished: true,
      bedrooms: 1,
      bathrooms: 1,
      area: 55,
      price: '4,200',
      pricePeriod: 'monthly',
      rating: 4.6,
      savedAt: '',
      isSaved: true,
    ),
    FavoritePropertyContent(
      id: '3',
      mainImage: '',
      title: LocaleKeys.ownerPropertyMohandessinTitle,
      propertyType: 'apartment',
      isFurnished: false,
      bedrooms: 3,
      bathrooms: 2,
      area: 120,
      price: '8,800',
      pricePeriod: 'monthly',
      rating: 4.9,
      savedAt: '',
      isSaved: true,
    ),
  ];
}
