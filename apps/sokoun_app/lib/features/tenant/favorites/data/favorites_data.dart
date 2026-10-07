import 'package:sokoun_app/features/tenant/home/data/models/property_search_model.dart';
import 'package:sokoun_app/features/shared/rental_offers/data/rental_offer_capabilities.dart';
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
  static String filteredCacheKey(PropertySearchFilters filters) =>
      '${cacheKey}_v1_${filters.cacheKey}';

  static FavoritesDataSource get source =>
      injector.isRegistered<FavoritesDataSource>()
      ? injector<FavoritesDataSource>()
      : const FavoritesApiDataSource();

  static Future<SavedPropertiesResponse> getSavedProperties({
    required int page,
  }) => source.getSavedProperties(page: page);

  static Future<(SavedPropertiesResponse, PaginationData)>
  getSavedPropertiesPage({
    required int page,
    PropertySearchFilters? filters,
  }) async {
    if (!RentalOfferCapabilities.configured.canFavorite) {
      return source.getSavedPropertiesPage(page: page);
    }
    // Proposed v1 grouped favorite search. Legacy data sources remain unchanged.
    final query = (filters ?? const PropertySearchFilters.initial())
        .copyWith(page: page)
        .toQueryParameters(
          capabilities: const RentalOfferCapabilities(
            contractVersion: 1,
            search: true,
          ),
        );
    final response = await injector<NetworkService>().callApi(
      NetworkRequest(
        method: RequestMethod.get,
        path: ApiConstants.savedProperties,
        queryParameters: query,
      ),
      mapper: (json) => SavedPropertiesResponse.fromJson(
        Map<String, dynamic>.from(json as Map),
      ),
    );
    final data = response.data;
    return (
      data,
      PaginationData(
        perPage: data.perPage < 1 ? 9 : data.perPage,
        totalPages: data.totalPages < 1 ? 1 : data.totalPages,
      ),
    );
  }
}
