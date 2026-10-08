import 'package:sokoun_app/features/shared/rental_offers/data/enums/rental_scope.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:sokoun_app/features/shared/finance/presentation/egyptian_pound_text.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_details_model.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_filter_options_model.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_search_model.dart';

class PropertyFilterLabelResolver {
  const PropertyFilterLabelResolver(this.options);

  final PropertyFilterOptionsModel options;

  String labelFor(PropertySearchFilterEntry filter) {
    switch (filter.id) {
      case 'city':
      case 'district':
        return filter.value;
      case 'price_min':
        return '${LocaleKeys.tenantFilterFrom} ${EgyptianPoundText.format(filter.value)}';
      case 'price_max':
        return '${LocaleKeys.tenantFilterTo} ${EgyptianPoundText.format(filter.value)}';
      case 'rental_scope':
        return RentalScope.fromValue(filter.value)?.label ??
            LocaleKeys.rentalUnknownScope;
      case 'property_type':
        return propertyTypeLabel(filter.value);
      case 'price_period':
        return pricePeriodLabel(filter.value);
      case 'suitable_for':
        return suitableForLabel(filter.value);
      case 'is_furnished':
        return '${LocaleKeys.tenantFilterFurnished}: ${_booleanLabel(filter.value)}';
      case 'is_verified':
        return '${LocaleKeys.tenantFilterVerified}: ${_booleanLabel(filter.value)}';
      case 'smoking_allowed':
        return '${LocaleKeys.tenantFilterSmoking}: ${_booleanLabel(filter.value)}';
      case 'bedrooms':
        return '${LocaleKeys.tenantFilterBedrooms}: ${filter.value}';
      case 'bathrooms':
        return '${LocaleKeys.tenantFilterBathrooms}: ${filter.value}';
      case 'ordering':
        return _label(options.ordering, filter.value);
      default:
        return amenityLabel(filter.id);
    }
  }

  String propertyTypeLabel(String value) {
    final label = _label(options.propertyTypes, value);
    return label == value
        ? PropertyDetailsModel.propertyTypeLabelFor(value)
        : label;
  }

  String suitableForLabel(String value) => _label(options.suitableFor, value);

  String pricePeriodLabel(String value) => _label(options.pricePeriods, value);

  String amenityLabel(String value) =>
      _label(options.amenities, value, matchQueryParameter: true);

  String _booleanLabel(String value) {
    final label = _label(options.booleanOptions, value);
    if (label != value) return label;
    return switch (value) {
      'true' => LocaleKeys.featureFilterYes,
      'false' => LocaleKeys.featureFilterNo,
      _ => value,
    };
  }

  List<String> amenityLabels(PropertyDetailsModel property) =>
      property.amenities.map(amenityLabel).toList(growable: false);

  String _label(
    List<TenantFilterOption> availableOptions,
    String value, {
    bool matchQueryParameter = false,
  }) {
    for (final TenantFilterOption option in availableOptions) {
      if (option.value == value ||
          (matchQueryParameter && option.queryParameter == value)) {
        return option.label;
      }
    }
    return value;
  }
}
