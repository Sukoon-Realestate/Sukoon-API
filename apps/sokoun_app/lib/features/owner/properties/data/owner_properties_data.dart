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

  static Future<(OwnerPropertiesResponse, PaginationData)>
  getOwnedPropertiesPage({required int page, required int pageSize}) async {
    final response = await injector<NetworkService>().callApi(
      NetworkRequest(
        method: RequestMethod.get,
        path: ApiConstants.ownedProperties,
        queryParameters: {'page': page, 'page_size': pageSize},
      ),
      mapper: (json) => OwnerPropertiesResponse.fromJson(json),
    );

    final OwnerPropertiesResponse data = response.data;
    final int totalPages = data.count == 0
        ? 1
        : (data.count + pageSize - 1) ~/ pageSize;
    return (data, PaginationData(perPage: pageSize, totalPages: totalPages));
  }
}
