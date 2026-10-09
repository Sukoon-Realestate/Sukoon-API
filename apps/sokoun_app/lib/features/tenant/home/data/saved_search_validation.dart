import 'models/property_filter_options_model.dart';
import 'models/property_search_model.dart';

abstract final class SavedSearchValidation {
  static ({PropertySearchFilters filters, bool changed}) against(
    PropertySearchFilters filters,
    PropertyFilterOptionsModel catalog,
  ) {
    bool changed = false;
    String choice(String selected, List<TenantFilterOption> available) {
      if (selected.isEmpty ||
          available.isEmpty ||
          available.any(
            (option) =>
                selected == option.id ||
                selected == option.value ||
                selected == option.selectionValue,
          )) {
        return selected;
      }
      changed = true;
      return '';
    }

    final Set<String> amenities = {
      for (final selected in filters.amenities)
        if (choice(selected, catalog.amenities).isNotEmpty) selected,
    };
    final PropertySearchFilters result = filters.copyWith(
      propertyType: choice(filters.propertyType, catalog.propertyTypes),
      pricePeriod: choice(filters.pricePeriod, catalog.pricePeriods),
      suitableFor: choice(filters.suitableFor, catalog.suitableFor),
      bedrooms: choice(filters.bedrooms, catalog.bedrooms),
      bathrooms: choice(filters.bathrooms, catalog.bathrooms),
      ordering: choice(filters.ordering, catalog.ordering),
      amenities: amenities,
      page: 1,
    );
    return (filters: result, changed: changed);
  }
}
