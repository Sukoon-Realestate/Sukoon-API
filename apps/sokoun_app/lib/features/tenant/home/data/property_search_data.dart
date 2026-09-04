import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/network/api_endpoints.dart';
import 'package:melos_core/core/network/network_request.dart';
import 'package:melos_core/core/network/network_service.dart';
import 'package:pagify/helpers/data_and_pagination_data.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_search_model.dart';

abstract final class PropertySearchData {
  static String cacheKeyFor(PropertySearchFilters filters) => filters.cacheKey;

  static Future<(PropertySearchResponseModel, PaginationData)>
  getPropertiesPage(PropertySearchFilters filters) async {
    final response = await injector<NetworkService>().callApi(
      NetworkRequest(
        method: RequestMethod.get,
        path: ApiConstants.properties,
        queryParameters: filters.toQueryParameters(),
      ),
      mapper: (json) => PropertySearchResponseModel.fromJson(json),
    );

    final PropertySearchResponseModel data = response.data;
    final int totalPages = data.count == 0
        ? 1
        : (data.count + filters.pageSize - 1) ~/ filters.pageSize;
    return (
      data,
      PaginationData(perPage: filters.pageSize, totalPages: totalPages),
    );
  }
}
