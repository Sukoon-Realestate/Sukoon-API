import 'package:sokoun_app/features/tenant/home/data/public_property_cache.dart';
import 'package:sokoun_app/features/shared/rental_offers/data/rental_offer_capabilities.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/base_crud/code/domain/base_domain_imports.dart';
import 'package:melos_core/core/network/api_endpoints.dart';
import 'package:pagify/helpers/data_and_pagination_data.dart';
import 'package:pagify/helpers/errors.dart';
import 'models/home_page_model.dart';
import 'package:melos_core/core/local_db/objectbox_cache_service.dart';

/// Endpoint paging metadata only; AppPagify owns collection and scroll state.
class TenantHomeData {
  static String get cacheKey => RentalOfferCapabilities.configured.canSearch
      ? 'tenant_home_properties_offers_v1'
      : 'tenant_home_properties';
  static String get _pageKey => RentalOfferCapabilities.configured.canSearch
      ? 'tenant_home_page_offers_v1'
      : 'tenant_home_page';

  HomePageModel? readCachedPage() {
    final json = ObjectBoxCacheService.read(
      _pageKey,
      policy: ReadCachePolicy.publicListing,
    );
    if (json == null) return null;
    return HomePageModel.fromJson(json);
  }

  bool fromCache = false;
  final Map<int, int> _serverPages = {1: 1};
  int _generation = 0;

  Future<(HomePageModel, PaginationData)> getPage({required int page}) async {
    if (page == 1) {
      _generation++;
      fromCache = false;
      _serverPages
        ..clear()
        ..[1] = 1;
    }
    final int generation = _generation;
    final int serverPage = _serverPages[page] ?? page;
    final result = await injector<BaseCrudUseCase>().call(
      CrudBaseParmas<HomePageModel>(
        api: ApiConstants.homePage,
        httpRequestType: HttpRequestType.get,
        cachePolicy: ReadCachePolicy.publicListing,
        queryParameters: {
          'page': serverPage,
          if (RentalOfferCapabilities.configured.canSearch)
            'rental_offers_version': 1,
        },
        cacheKey: serverPage == 1 ? _pageKey : '${_pageKey}_$serverPage',
        mapper: (json) => HomePageModel.fromJson(json),
        fromCacheJson: HomePageModel.fromJson,
        toJson: (model) => PublicPropertyCache.sanitize(model.toJson()),
      ),
    );
    if (generation == _generation) {
      fromCache = fromCache || result.tryGetSuccess()?.key == 'fromCache';
    }
    final HomePageModel model = result.when(
      (response) => response.data,
      (failure) => throw PagifyApiRequestException(
        failure.message,
        pagifyFailure: RequestFailureData(
          statusCode: failure.statusCode,
          statusMsg: failure.message,
        ),
      ),
    );
    final String? next = model.next;
    final int? nextPage = next == null
        ? null
        : int.tryParse(Uri.tryParse(next)?.queryParameters['page'] ?? '');
    final bool hasMore =
        next?.trim().isNotEmpty == true &&
        (nextPage == null || nextPage > serverPage);
    if (generation == _generation && hasMore) {
      _serverPages[page + 1] = nextPage ?? serverPage + 1;
    }
    return (
      model,
      PaginationData(
        perPage: model.results.isEmpty ? 20 : model.results.length,
        totalPages: hasMore ? page + 1 : page,
      ),
    );
  }
}
