import 'package:flutter_test/flutter_test.dart';
import 'package:melos_core/config/res/config_imports.dart' show injector;
import 'package:melos_core/core/base_crud/code/domain/usecases/pagination_response.dart';
import 'package:melos_core/core/network/api_endpoints.dart';
import 'package:melos_core/core/network/network_request.dart';
import 'package:melos_core/core/network/network_service.dart';
import 'package:sokoun_app/features/tenant/visits/imports.dart';

void main() {
  late _FakeNetworkService networkService;

  setUp(() async {
    await injector.reset();
    networkService = _FakeNetworkService();
    injector.registerSingleton<NetworkService>(networkService);
  });

  tearDown(() => injector.reset());

  test('loads and maps a tenant visits page', () async {
    final (
      List<TenantVisitContent> visits,
      pagination,
    ) = await TenantVisitsData.getVisitsPage(
      page: 2,
      filter: TenantVisitFilter.all,
    );

    expect(networkService.lastRequest.path, ApiConstants.tenantVisits);
    expect(networkService.lastRequest.method, RequestMethod.get);
    expect(networkService.lastRequest.queryParameters, {'page': 2});
    expect(pagination.totalPages, 5);
    expect(pagination.perPage, 20);
    expect(visits, hasLength(1));
    expect(visits.single.id, '6ab0ee4c-5981-4224-8421-f365e70b0274');
    expect(
      visits.single.propertyTitle,
      'Cozy Studio Near Metro Station 1 - Maadi',
    );
    expect(visits.single.day, 'الخميس 20 أغسطس');
    expect(visits.single.time, '2:00 م');
    expect(visits.single.status.isPending, isTrue);
  });

  test('adds the selected status filter to the request', () async {
    await TenantVisitsData.getVisits(
      page: 1,
      filter: TenantVisitFilter.rejected,
    );

    expect(networkService.lastRequest.queryParameters, {
      'page': 1,
      'status': 'rejected',
    });
  });

  test('maps an unknown backend status to the rejected fail state', () {
    final TenantVisitContent visit = TenantVisitContent.fromJson(const {
      'status': 'unknown-status',
    });

    expect(visit.status.isRejected, isTrue);
  });

  test('builds a filter-specific stable cache key', () {
    expect(
      TenantVisitsData.cacheKeyFor(TenantVisitFilter.all),
      'tenant_visits_all',
    );
    expect(
      TenantVisitsData.cacheKeyFor(TenantVisitFilter.pending),
      'tenant_visits_pending',
    );
  });
}

class _FakeNetworkService implements NetworkService {
  late NetworkRequest lastRequest;

  @override
  Future<BaseModel<Model>> callApi<Model>(
    NetworkRequest networkRequest, {
    Model Function(dynamic json)? mapper,
  }) async {
    lastRequest = networkRequest;
    final Model data = mapper!(const {
      'total_pages': 5,
      'per_page': 20,
      'results': [
        {
          'id': '6ab0ee4c-5981-4224-8421-f365e70b0274',
          'title': 'Cozy Studio Near Metro Station 1 - Maadi',
          'day': 'الخميس 20 أغسطس',
          'time': '2:00 م',
          'status': 'بانتظار رد المالك',
        },
      ],
    });
    return BaseModel<Model>(key: '', msg: '', data: data);
  }

  @override
  Future<void> clearSessionCookies() async {}

  @override
  Future<bool> hasSessionCookies() async => false;

  @override
  Future<void> updateBaseUrl() async {}
}
