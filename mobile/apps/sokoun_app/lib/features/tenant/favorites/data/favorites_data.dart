import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/network/api_endpoints.dart';
import 'package:melos_core/core/network/network_request.dart';
import 'package:melos_core/core/network/network_service.dart';
import 'package:pagify/helpers/data_and_pagination_data.dart';
import 'package:sokoun_app/features/tenant/favorites/data/models/saved_properties_response.dart';

abstract interface class FavoritesDataSource {
  String get cacheKey;

  Future<SavedPropertiesResponse> getSavedProperties({required int page});

  Future<(SavedPropertiesResponse, PaginationData)> getSavedPropertiesPage({
    required int page,
  });
}

final class FavoritesApiDataSource implements FavoritesDataSource {
  const FavoritesApiDataSource();

  @override
  String get cacheKey => FavoritesData.cacheKey;

  @override
  Future<SavedPropertiesResponse> getSavedProperties({
    required int page,
  }) async {
    return (await getSavedPropertiesPage(page: page)).$1;
  }

  @override
  Future<(SavedPropertiesResponse, PaginationData)> getSavedPropertiesPage({
    required int page,
  }) async {
    final response = await injector<NetworkService>().callApi(
      NetworkRequest(
        method: RequestMethod.get,
        path: ApiConstants.savedProperties,
        queryParameters: {'page': page},
      ),
      mapper: (json) => SavedPropertiesResponse.fromJson(
        json is Map<String, dynamic> ? json : const {},
      ),
    );

    final SavedPropertiesResponse data = response.data;
    return (
      data,
      PaginationData(
        perPage: data.perPage < 1 ? 9 : data.perPage,
        totalPages: data.totalPages < 1 ? 1 : data.totalPages,
      ),
    );
  }
}

abstract final class FavoritesData {
  static const String cacheKey = 'tenant_saved_properties';

  static FavoritesDataSource get source =>
      injector.isRegistered<FavoritesDataSource>()
      ? injector<FavoritesDataSource>()
      : const FavoritesApiDataSource();

  static Future<SavedPropertiesResponse> getSavedProperties({
    required int page,
  }) => source.getSavedProperties(page: page);

  static Future<(SavedPropertiesResponse, PaginationData)>
  getSavedPropertiesPage({required int page}) =>
      source.getSavedPropertiesPage(page: page);
}
