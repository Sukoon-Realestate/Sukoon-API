import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:sokoun_app/features/home/data/models/property_details_model.dart';
import 'package:sokoun_app/features/home/data/models/property_search_model.dart';

class TenantFilterOption {
  final String value;
  final String label;

  const TenantFilterOption({required this.value, required this.label});
}

abstract final class TenantPropertyFilterOptions {
  static List<TenantFilterOption> get propertyTypes => [
    TenantFilterOption(
      value: 'apartment',
      label: LocaleKeys.tenantFilterApartment,
    ),
    TenantFilterOption(value: 'house', label: LocaleKeys.tenantFilterHouse),
    TenantFilterOption(value: 'villa', label: LocaleKeys.tenantFilterVilla),
    TenantFilterOption(value: 'studio', label: LocaleKeys.tenantFilterStudio),
    TenantFilterOption(
      value: 'penthouse',
      label: LocaleKeys.tenantFilterPenthouse,
    ),
  ];

  static List<TenantFilterOption> get counts => [
    TenantFilterOption(value: '', label: LocaleKeys.tenantSearchAll),
    for (int count = 1; count <= 5; count++)
      TenantFilterOption(value: '$count', label: '$count'),
  ];

  static List<TenantFilterOption> get pricePeriods => [
    TenantFilterOption(value: '', label: LocaleKeys.tenantSearchAll),
    TenantFilterOption(value: 'daily', label: LocaleKeys.tenantFilterDaily),
    TenantFilterOption(value: 'weekly', label: LocaleKeys.tenantFilterWeekly),
    TenantFilterOption(value: 'monthly', label: LocaleKeys.tenantFilterMonthly),
    TenantFilterOption(value: 'yearly', label: LocaleKeys.tenantFilterYearly),
  ];

  static List<TenantFilterOption> get suitableFor => [
    TenantFilterOption(value: '', label: LocaleKeys.tenantSearchAll),
    TenantFilterOption(
      value: 'families',
      label: LocaleKeys.tenantFilterFamilies,
    ),
    TenantFilterOption(value: 'singles', label: LocaleKeys.tenantFilterSingles),
    TenantFilterOption(
      value: 'students',
      label: LocaleKeys.tenantFilterStudents,
    ),
    TenantFilterOption(
      value: 'female_students',
      label: LocaleKeys.tenantFilterFemaleStudents,
    ),
    TenantFilterOption(value: 'all', label: LocaleKeys.tenantFilterEveryone),
  ];

  static List<TenantFilterOption> get booleanOptions => [
    TenantFilterOption(value: '', label: LocaleKeys.tenantSearchAll),
    TenantFilterOption(value: 'true', label: LocaleKeys.tenantFilterYes),
    TenantFilterOption(value: 'false', label: LocaleKeys.tenantFilterNo),
  ];

  static List<TenantFilterOption> get ordering => [
    TenantFilterOption(
      value: '-created_at',
      label: LocaleKeys.tenantFilterNewest,
    ),
    TenantFilterOption(
      value: 'created_at',
      label: LocaleKeys.tenantFilterOldest,
    ),
    TenantFilterOption(
      value: 'price',
      label: LocaleKeys.tenantFilterLowestPrice,
    ),
    TenantFilterOption(
      value: '-price',
      label: LocaleKeys.tenantFilterHighestPrice,
    ),
  ];

  static List<TenantFilterOption> get amenities => [
    TenantFilterOption(value: 'has_wifi', label: LocaleKeys.tenantFilterWifi),
    TenantFilterOption(
      value: 'has_elevator',
      label: LocaleKeys.tenantFilterElevator,
    ),
    TenantFilterOption(
      value: 'has_garage',
      label: LocaleKeys.tenantFilterGarage,
    ),
    TenantFilterOption(
      value: 'has_security',
      label: LocaleKeys.tenantFilterSecurity,
    ),
    TenantFilterOption(
      value: 'has_balcony',
      label: LocaleKeys.tenantFilterBalcony,
    ),
    TenantFilterOption(
      value: 'has_air_conditioning',
      label: LocaleKeys.tenantFilterAirConditioning,
    ),
    TenantFilterOption(
      value: 'near_metro',
      label: LocaleKeys.tenantFilterNearMetro,
    ),
    TenantFilterOption(
      value: 'has_natural_gas',
      label: LocaleKeys.tenantFilterNaturalGas,
    ),
  ];

  static String labelFor(PropertySearchFilterEntry filter) {
    switch (filter.id) {
      case 'city':
      case 'district':
        return filter.value;
      case 'price_min':
        return '${LocaleKeys.tenantFilterFrom} ${filter.value}';
      case 'price_max':
        return '${LocaleKeys.tenantFilterTo} ${filter.value}';
      case 'property_type':
        return _label(propertyTypes, filter.value);
      case 'price_period':
        return _label(pricePeriods, filter.value);
      case 'suitable_for':
        return _label(suitableFor, filter.value);
      case 'is_furnished':
        return '${LocaleKeys.tenantFilterFurnished}: ${_label(booleanOptions, filter.value)}';
      case 'is_verified':
        return '${LocaleKeys.tenantFilterVerified}: ${_label(booleanOptions, filter.value)}';
      case 'smoking_allowed':
        return '${LocaleKeys.tenantFilterSmoking}: ${_label(booleanOptions, filter.value)}';
      case 'bedrooms':
        return '${LocaleKeys.tenantFilterBedrooms}: ${filter.value}';
      case 'bathrooms':
        return '${LocaleKeys.tenantFilterBathrooms}: ${filter.value}';
      case 'ordering':
        return _label(ordering, filter.value);
      default:
        return _label(amenities, filter.id);
    }
  }

  static String propertyTypeLabel(String value) => _label(propertyTypes, value);

  static String suitableForLabel(String value) => _label(suitableFor, value);

  static String pricePeriodLabel(String value) => _label(pricePeriods, value);

  static String amenityLabel(String value) => _label(amenities, value);

  static List<String> amenityLabels(PropertyDetailsModel property) => [
    if (property.hasWifi) amenityLabel('has_wifi'),
    if (property.hasElevator) amenityLabel('has_elevator'),
    if (property.hasGarage) amenityLabel('has_garage'),
    if (property.hasSecurity) amenityLabel('has_security'),
    if (property.hasBalcony) amenityLabel('has_balcony'),
    if (property.hasAirConditioning) amenityLabel('has_air_conditioning'),
    if (property.nearMetro) amenityLabel('near_metro'),
    if (property.hasNaturalGas) amenityLabel('has_natural_gas'),
  ];

  static String _label(List<TenantFilterOption> options, String value) {
    for (final TenantFilterOption option in options) {
      if (option.value == value) return option.label;
    }
    return value;
  }
}
