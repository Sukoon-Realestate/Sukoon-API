part of '../imports.dart';

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
  }) async {
    final response = await injector<NetworkService>().callApi(
      NetworkRequest(
        method: RequestMethod.get,
        path: ApiConstants.ownedProperties,
        queryParameters: {
          'page': page,
          'page_size': OwnerPropertiesData.pageSize,
        },
      ),
      mapper: (json) => OwnerPropertiesResponse.fromJson(json),
    );

    final OwnerPropertiesResponse data = response.data;
    final int totalPages = data.count == 0
        ? 1
        : (data.count + OwnerPropertiesData.pageSize - 1) ~/
              OwnerPropertiesData.pageSize;
    return (
      data.results,
      PaginationData(
        perPage: OwnerPropertiesData.pageSize,
        totalPages: totalPages,
      ),
    );
  }
}

abstract final class OwnerPropertiesData {
  static const int pageSize = 10;
  static const String cacheKey = 'owner_properties';
  static const String governoratesCacheKey = 'owner_property_governorates';

  static OwnerPropertiesDataSource get source =>
      injector.isRegistered<OwnerPropertiesDataSource>()
      ? injector<OwnerPropertiesDataSource>()
      : const OwnerPropertiesApiDataSource();

  static String citiesCacheKey(String governorateId) =>
      source.citiesCacheKey(governorateId);

  static Future<OwnerPropertyLocationsResponse> getGovernorates() =>
      source.getGovernorates();

  static Future<OwnerPropertyLocationsResponse> getCities({
    required String governorateId,
    required String search,
  }) => source.getCities(governorateId: governorateId, search: search);

  static Future<(List<OwnerPropertyContent>, PaginationData)>
  getOwnedPropertiesPage({required int page}) =>
      source.getOwnedPropertiesPage(page: page);
}
