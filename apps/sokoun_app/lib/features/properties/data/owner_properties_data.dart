part of '../imports.dart';

abstract final class OwnerPropertiesData {
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
