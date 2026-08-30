part of '../imports.dart';

abstract final class TenantVisitsData {
  static const int _fallbackPageSize = 20;

  static String cacheKeyFor(TenantVisitFilter filter) {
    return 'tenant_visits_${filter.name}';
  }

  static Future<(List<TenantVisitContent>, PaginationData)> getVisitsPage({
    required int page,
    required TenantVisitFilter filter,
  }) async {
    final TenantVisitsResponse response = await getVisits(
      page: page,
      filter: filter,
    );
    return (
      response.results,
      PaginationData(
        perPage: response.perPage < 1 ? _fallbackPageSize : response.perPage,
        totalPages: response.totalPages < 1 ? 1 : response.totalPages,
      ),
    );
  }

  static Future<TenantVisitsResponse> getVisits({
    required int page,
    required TenantVisitFilter filter,
  }) async {
    final Map<String, dynamic> queryParameters = {'page': page};
    final String? status = filter.apiValue;
    if (status != null) queryParameters['status'] = status;

    final response = await injector<NetworkService>().callApi(
      NetworkRequest(
        method: RequestMethod.get,
        path: ApiConstants.tenantVisits,
        queryParameters: queryParameters,
      ),
      mapper: (json) => TenantVisitsResponse.fromJson(
        json is Map<String, dynamic> ? json : const {},
      ),
    );

    return response.data;
  }
}
