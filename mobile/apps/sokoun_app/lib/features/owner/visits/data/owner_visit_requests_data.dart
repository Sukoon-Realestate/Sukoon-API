import 'package:melos_core/config/res/config_imports.dart' show injector;
import 'package:melos_core/core/base_crud/code/domain/base_domain_imports.dart';
import 'package:melos_core/core/error/exceptions.dart';
import 'package:melos_core/core/local_db/objectbox_cache_service.dart';
import 'package:melos_core/core/network/api_endpoints.dart';
import 'package:pagify/helpers/data_and_pagination_data.dart';
import 'package:pagify/helpers/errors.dart';

import 'enums/owner_visit_request_state.dart';
import 'models/owner_visit_requests_response.dart';

/// Resolves server page links; AppPagify owns the displayed collection.
class OwnerVisitRequestsData {
  OwnerVisitRequestsData({required this.requests});

  final bool requests;
  final Map<int, int> _serverPages = {1: 1};
  int _generation = 0;

  String get _cachePrefix =>
      requests ? 'owner_visit_requests' : 'owner_received_visits';

  String cacheKeyFor(OwnerVisitRequestFilter filter) =>
      '${_cachePrefix}_paginated_${filter.name}';

  OwnerVisitRequestsResponse? readCachedPage() {
    final json = ObjectBoxCacheService.read('${_cachePrefix}_page_1');
    return json == null ? null : OwnerVisitRequestsResponse.fromJson(json);
  }

  Future<(OwnerVisitRequestsResponse, PaginationData)> getPage({
    required int page,
    required OwnerVisitRequestFilter filter,
  }) async {
    if (page == 1) {
      _generation++;
      _serverPages
        ..clear()
        ..[1] = 1;
    }
    final int generation = _generation;
    int serverPage = _serverPages[page] ?? page;
    OwnerVisitRequestsResponse? firstResponse;
    while (true) {
      final result = await injector<BaseCrudUseCase>().call(
        CrudBaseParmas<OwnerVisitRequestsResponse>(
          api: requests
              ? ApiConstants.ownerVisitRequests
              : ApiConstants.receivedPropertyVisits,
          httpRequestType: HttpRequestType.get,
          queryParameters: {'page': serverPage},
          cacheKey: '${_cachePrefix}_page_$serverPage',
          mapper: OwnerVisitRequestsResponse.fromJson,
          fromCacheJson: OwnerVisitRequestsResponse.fromJson,
          toJson: (response) => response.toJson(),
        ),
      );
      if (generation != _generation) throw const RequestCancelledException();
      final OwnerVisitRequestsResponse response = result.when(
        (model) => model.data,
        (failure) => throw PagifyApiRequestException(
          failure.message,
          pagifyFailure: RequestFailureData(
            statusCode: null,
            statusMsg: failure.message,
          ),
        ),
      );
      firstResponse ??= response;
      final int? linkedPage = int.tryParse(
        Uri.tryParse(response.next ?? '')?.queryParameters['page'] ?? '',
      );
      final bool hasMore =
          response.next?.trim().isNotEmpty == true &&
          (linkedPage == null || linkedPage > serverPage);
      final int nextPage = linkedPage ?? serverPage + 1;
      final visible = response.results
          .where((request) => filter.accepts(request.status))
          .toList(growable: false);
      // A local filter must not stop at an empty page when later pages match.
      if (visible.isEmpty && hasMore && !filter.isAll) {
        serverPage = nextPage;
        continue;
      }
      if (hasMore) _serverPages[page + 1] = nextPage;
      return (
        response.copyWith(
          results: visible,
          tabs: response.tabs.isEmpty ? firstResponse.tabs : response.tabs,
        ),
        PaginationData(
          perPage: response.results.isEmpty ? 20 : response.results.length,
          totalPages: hasMore ? page + 1 : page,
        ),
      );
    }
  }
}
