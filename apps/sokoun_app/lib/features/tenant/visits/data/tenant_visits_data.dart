import 'enums/visit_status.dart';
import 'models/tenant_visit_content.dart';
import 'models/tenant_visits_response.dart';
import 'package:melos_core/config/res/config_imports.dart' show injector;
import 'package:melos_core/core/network/api_endpoints.dart';
import 'package:melos_core/core/network/network_request.dart';
import 'package:melos_core/core/network/network_service.dart';
import 'package:pagify/helpers/data_and_pagination_data.dart';

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
  const TenantVisitsApiDataSource({this.requests = false});

  final bool requests;

  @override
  String cacheKeyFor(TenantVisitFilter filter) {
    return '${requests ? 'tenant_visit_requests' : 'tenant_visits'}_${filter.name}';
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
        path: requests
            ? ApiConstants.tenantVisitRequests
            : ApiConstants.tenantVisits,
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

  static TenantVisitsDataSource _sourceFor(bool requests) =>
      injector.isRegistered<TenantVisitsDataSource>()
      ? source
      : TenantVisitsApiDataSource(requests: requests);

  static String cacheKeyFor(
    TenantVisitFilter filter, {
    bool requests = false,
  }) => _sourceFor(requests).cacheKeyFor(filter);

  static Future<(List<TenantVisitContent>, PaginationData)> getVisitsPage({
    required int page,
    required TenantVisitFilter filter,
    bool requests = false,
  }) => _sourceFor(requests).getVisitsPage(page: page, filter: filter);

  static Future<TenantVisitsResponse> getVisits({
    required int page,
    required TenantVisitFilter filter,
  }) => source.getVisits(page: page, filter: filter);
}
