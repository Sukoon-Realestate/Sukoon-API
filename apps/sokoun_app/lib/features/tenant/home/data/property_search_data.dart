import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/network/api_endpoints.dart';
import 'package:melos_core/core/network/network_request.dart';
import 'package:melos_core/core/network/network_service.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_search_model.dart';

abstract final class PropertySearchData {
  static Future<PropertySearchResponseModel> getProperties(
    PropertySearchFilters filters,
  ) async {
    final response = await injector<NetworkService>().callApi(
      NetworkRequest(
        method: RequestMethod.get,
        path: ApiConstants.properties,
        queryParameters: filters.toQueryParameters(),
      ),
      mapper: (json) => PropertySearchResponseModel.fromJson(json),
    );

    return response.data;
  }
}
