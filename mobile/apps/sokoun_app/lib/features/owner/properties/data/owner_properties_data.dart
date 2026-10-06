import 'models/owner_properties_response.dart';
import 'enums/owner_property_filter.dart';
import 'models/owner_property_content.dart';
import 'models/owner_property_location_model.dart';
import 'package:melos_core/config/res/config_imports.dart' show injector;
import 'package:melos_core/core/network/api_endpoints.dart';
import 'package:melos_core/core/network/network_request.dart';
import 'package:melos_core/core/network/network_service.dart';
import 'package:pagify/helpers/data_and_pagination_data.dart';

abstract interface class OwnerPropertiesDataSource {
  String get cacheKey;

  String get governoratesCacheKey;

  String citiesCacheKey(String governorateId);

  Future<OwnerPropertyLocationsResponse> getGovernorates();

  Future<OwnerPropertyLocationsResponse> getCities({
    required String governorateId,
    required String search,
  });

  Future<(List<OwnerPropertyContent>, PaginationData)> getOwnedPropertiesPage({
    required int page,
    required OwnerPropertyFilter filter,
  });
}

final class OwnerPropertiesApiDataSource implements OwnerPropertiesDataSource {
  const OwnerPropertiesApiDataSource();

  @override
  String get cacheKey => OwnerPropertiesData.cacheKey;

  @override
  String get governoratesCacheKey => OwnerPropertiesData.governoratesCacheKey;

  @override
  String citiesCacheKey(String governorateId) =>
      'owner_property_cities_$governorateId';

  @override
  Future<OwnerPropertyLocationsResponse> getGovernorates() async {
    final response = await injector<NetworkService>().callApi(
      NetworkRequest(
        method: RequestMethod.get,
        path: ApiConstants.propertyGovernorates,
      ),
      mapper: (json) => OwnerPropertyLocationsResponse.fromJson(
        json is Map<String, dynamic> ? json : const {},
      ),
    );

    return response.data;
  }

  @override
  Future<OwnerPropertyLocationsResponse> getCities({
    required String governorateId,
    required String search,
  }) async {
    final response = await injector<NetworkService>().callApi(
      NetworkRequest(
        method: RequestMethod.get,
        path: ApiConstants.propertyCities,
        queryParameters: {
          'search': search.trim(),
          'governorate': governorateId,
        },
      ),
      mapper: (json) => OwnerPropertyLocationsResponse.fromJson(
        json is Map<String, dynamic> ? json : const {},
      ),
    );

    return response.data;
  }

  @override
  Future<(List<OwnerPropertyContent>, PaginationData)> getOwnedPropertiesPage({
    required int page,
    required OwnerPropertyFilter filter,
  }) async {
    final response = await injector<NetworkService>().callApi(
      NetworkRequest(
        method: RequestMethod.get,
        path: ApiConstants.ownedProperties,
        queryParameters: {
          'status': filter.apiValue,
          'page': page,
          'page_size': OwnerPropertiesData.pageSize,
        },
      ),
      mapper: (json) => OwnerPropertiesResponse.fromJson(json),
    );

    final OwnerPropertiesResponse data = response.data;
    return (
      data.results,
      PaginationData(perPage: data.perPage, totalPages: data.totalPages),
    );
  }
}

abstract final class OwnerPropertiesData {
  static const int pageSize = OwnerPropertiesResponse.defaultPerPage;
  static const String cacheKey = 'owner_properties';
  static const String governoratesCacheKey = 'owner_property_governorates';

  static OwnerPropertiesDataSource get source =>
      injector.isRegistered<OwnerPropertiesDataSource>()
      ? injector<OwnerPropertiesDataSource>()
      : const OwnerPropertiesApiDataSource();

  static String citiesCacheKey(String governorateId) =>
      source.citiesCacheKey(governorateId);

  static String cacheKeyFor(OwnerPropertyFilter filter) =>
      '${source.cacheKey}_${filter.apiValue}';

  static Future<OwnerPropertyLocationsResponse> getGovernorates() =>
      source.getGovernorates();

  static Future<OwnerPropertyLocationsResponse> getCities({
    required String governorateId,
    required String search,
  }) => source.getCities(governorateId: governorateId, search: search);

  static Future<(List<OwnerPropertyContent>, PaginationData)>
  getOwnedPropertiesPage({
    required int page,
    required OwnerPropertyFilter filter,
  }) => source.getOwnedPropertiesPage(page: page, filter: filter);
}
