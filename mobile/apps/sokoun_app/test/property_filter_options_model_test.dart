import 'package:flutter_test/flutter_test.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_filter_options_model.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_search_model.dart';
import 'package:sokoun_app/features/tenant/home/presentation/widgets/tenant_filter/property_filter_label_resolver.dart';

void main() {
  group('PropertyFilterOptionsModel', () {
    test('parses the backend filter-options contract', () {
      final PropertyFilterOptionsModel options =
          PropertyFilterOptionsModel.fromJson({
            'property_types': [
              {
                'id': 'property-type-id',
                'value': 'apartment',
                'label': 'Apartment',
              },
            ],
            'ordering': [
              {'value': '-created_at', 'label': 'Newest'},
            ],
            'bedrooms': [1],
            'bathrooms': [
              {'value': 2, 'label': '2'},
            ],
            'price_periods': [
              {'value': 'monthly', 'label': 'Monthly'},
            ],
            'suitable_for': [
              {'value': 'families', 'label': 'Families'},
            ],
            'boolean_options': [
              {'value': true, 'label': 'Yes'},
              {'value': false, 'label': 'No'},
            ],
            'amenities': [
              {
                'value': 'wifi',
                'query_parameter': 'has_wifi',
                'label': 'Wi-Fi',
              },
            ],
            'defaults': {'ordering': '-created_at'},
          });

      expect(options.propertyTypes.single.id, 'property-type-id');
      expect(options.bedrooms.single.value, '1');
      expect(options.booleanOptions.map((option) => option.value), [
        'true',
        'false',
      ]);
      expect(options.amenities.single.value, 'wifi');
      expect(options.amenities.single.selectionValue, 'has_wifi');
      expect(options.defaultOrdering, '-created_at');
    });

    test('resolves labels using option values and query parameters', () {
      const PropertyFilterOptionsModel options = PropertyFilterOptionsModel(
        propertyTypes: [
          TenantFilterOption(value: 'apartment', label: 'Apartment'),
        ],
        ordering: [],
        bedrooms: [],
        bathrooms: [],
        pricePeriods: [],
        suitableFor: [],
        booleanOptions: [],
        amenities: [
          TenantFilterOption(
            value: 'wifi',
            queryParameter: 'has_wifi',
            label: 'Wi-Fi',
          ),
        ],
        defaultOrdering: '',
      );
      const PropertyFilterLabelResolver resolver = PropertyFilterLabelResolver(
        options,
      );

      expect(resolver.propertyTypeLabel('apartment'), 'Apartment');
      expect(resolver.amenityLabel('wifi'), 'Wi-Fi');
      expect(
        resolver.labelFor(
          const PropertySearchFilterEntry(id: 'has_wifi', value: 'true'),
        ),
        'Wi-Fi',
      );
    });

    test('builds stable pagination cache keys from every search dimension', () {
      const PropertySearchFilters firstPage = PropertySearchFilters.initial(
        search: 'Nasr City',
        propertyType: 'apartment',
        amenities: {'has_wifi', 'has_elevator'},
      );
      final PropertySearchFilters laterPage = firstPage.copyWith(page: 3);
      final PropertySearchFilters reorderedAmenities = firstPage.copyWith(
        amenities: {'has_elevator', 'has_wifi'},
      );
      final PropertySearchFilters differentType = firstPage.copyWith(
        propertyType: 'studio',
      );

      expect(laterPage.cacheKey, firstPage.cacheKey);
      expect(reorderedAmenities.cacheKey, firstPage.cacheKey);
      expect(differentType.cacheKey, isNot(firstPage.cacheKey));
    });
  });
}
