import 'package:sokoun_app/features/tenant/home/data/models/property_details_model.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_search_model.dart';
import 'package:sokoun_app/features/shared/finance/data/egyptian_pound.dart';

enum PropertyMatchReason { price, period, type, amenities, bedrooms, verified }

abstract final class PropertyMatchData {
  static Set<PropertyMatchReason> reasons(
    PropertyDetailsModel property,
    PropertySearchFilters filters,
  ) {
    final price = EgyptianPound.parseAmount(property.price);
    final minimum = EgyptianPound.parseAmount(filters.priceMin);
    final maximum = EgyptianPound.parseAmount(filters.priceMax);
    return {
      if ((minimum != null || maximum != null) &&
          price != null &&
          (filters.pricePeriod.isEmpty ||
              filters.pricePeriod == property.pricePeriod) &&
          (minimum == null || price >= minimum) &&
          (maximum == null || price <= maximum))
        PropertyMatchReason.price,
      if (filters.pricePeriod.isNotEmpty &&
          property.pricePeriod == filters.pricePeriod)
        PropertyMatchReason.period,
      if (filters.propertyType.isNotEmpty &&
          property.propertyType == filters.propertyType)
        PropertyMatchReason.type,
      if (filters.amenities.isNotEmpty &&
          filters.amenities.every(property.amenities.contains))
        PropertyMatchReason.amenities,
      if (filters.bedrooms.isNotEmpty &&
          int.tryParse(filters.bedrooms) == property.bedrooms)
        PropertyMatchReason.bedrooms,
      if (filters.isVerified == 'true' && property.isVerified)
        PropertyMatchReason.verified,
    };
  }
}
