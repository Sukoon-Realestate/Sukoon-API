part of '../imports.dart';

abstract interface class TenantVisitsDataSource {
  String cacheKeyFor(TenantVisitFilter filter);

  Future<(List<TenantVisitContent>, PaginationData)> getVisitsPage({
    required int page,
    required TenantVisitFilter filter,
  });

  Future<TenantVisitsResponse> getVisits({
    required int page,
    required TenantVisitFilter filter,
  });
}

final class TenantVisitsApiDataSource implements TenantVisitsDataSource {
  const TenantVisitsApiDataSource();

  @override
  String cacheKeyFor(TenantVisitFilter filter) {
    return 'tenant_visits_${filter.name}';
  }

  @override
  Future<(List<TenantVisitContent>, PaginationData)> getVisitsPage({
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
        perPage: response.perPage < 1
            ? TenantVisitsData._fallbackPageSize
            : response.perPage,
        totalPages: response.totalPages < 1 ? 1 : response.totalPages,
      ),
    );
  }

  @override
  Future<TenantVisitsResponse> getVisits({
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

abstract final class TenantVisitsData {
  static const int _fallbackPageSize = 20;

  static TenantVisitsDataSource get source =>
      injector.isRegistered<TenantVisitsDataSource>()
      ? injector<TenantVisitsDataSource>()
      : const TenantVisitsApiDataSource();

  static String cacheKeyFor(TenantVisitFilter filter) =>
      source.cacheKeyFor(filter);

  static Future<(List<TenantVisitContent>, PaginationData)> getVisitsPage({
    required int page,
    required TenantVisitFilter filter,
  }) => source.getVisitsPage(page: page, filter: filter);

  static Future<TenantVisitsResponse> getVisits({
    required int page,
    required TenantVisitFilter filter,
  }) => source.getVisits(page: page, filter: filter);
}
