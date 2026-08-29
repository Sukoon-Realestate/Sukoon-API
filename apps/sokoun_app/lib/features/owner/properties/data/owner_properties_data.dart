part of '../imports.dart';

abstract final class OwnerPropertiesData {
  static Future<OwnerPropertyLocationsResponse> getGovernorates() async {
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

  static Future<OwnerPropertyLocationsResponse> getCities({
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

  static Future<OwnerPropertiesResponse> getOwnedProperties({
    required int page,
    required int pageSize,
  }) async {
    final response = await injector<NetworkService>().callApi(
      NetworkRequest(
        method: RequestMethod.get,
        path: ApiConstants.ownedProperties,
        queryParameters: {'page': page, 'page_size': pageSize},
      ),
      mapper: (json) => OwnerPropertiesResponse.fromJson(json),
    );

    return response.data;
  }
}
