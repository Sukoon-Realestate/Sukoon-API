import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/core/base_crud/code/domain/base_domain_imports.dart';
import 'package:melos_core/core/network/api_endpoints.dart';
import 'package:sokoun_app/features/owner/home/data/enums/property_price_period.dart';
import 'package:sokoun_app/features/shared/rental_offers/data/enums/rental_scope.dart';
import 'package:sokoun_app/features/shared/rental_offers/data/rental_offer_capabilities.dart';
import 'models/property_search_model.dart';
import 'rental_property_discovery_data.dart';

abstract final class RentalHomeSectionData {
  static PropertySearchFilters filters(
    RentalScope scope,
    PropertyPricePeriod period, {
    bool preview = false,
  }) => PropertySearchFilters.initial(
    rentalScope: scope.value,
    pricePeriod: period.value,
    pageSize: preview ? 2 : 10,
  );

  static CrudBaseParmas<PropertySearchResponseModel> request({
    required RentalScope scope,
    required PropertyPricePeriod period,
    RentalOfferCapabilities capabilities = RentalOfferCapabilities.configured,
  }) {
    if (!capabilities.canSearch) {
      throw StateError(LocaleKeys.rentalScopeFilterUnavailable);
    }
    final query = filters(scope, period, preview: true);
    PropertySearchResponseModel read(Map<String, dynamic> json) =>
        RentalPropertyDiscoveryData.read(json, query);
    return CrudBaseParmas<PropertySearchResponseModel>(
      api: ApiConstants.properties,
      httpRequestType: HttpRequestType.get,
      queryParameters: query.toQueryParameters(capabilities: capabilities),
      cacheKey: 'rental_home_v1_${scope.value}_${period.value}',
      mapper: (json) => read(Map<String, dynamic>.from(json as Map)),
      fromCacheJson: read,
      toJson: (model) => model.toJson(),
    );
  }
}
