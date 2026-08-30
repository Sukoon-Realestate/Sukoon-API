import 'package:melos_core/core/base_crud/code/domain/base_domain_imports.dart';
import 'package:melos_core/core/base_crud/code/domain/usecases/pagination_response.dart';
import 'package:melos_core/core/base_crud/code/presentation/cubit/base_cubit/async_cubit.dart';
import 'package:melos_core/core/network/api_endpoints.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_search_model.dart';

class PropertySearchCubit extends AsyncCubit<PropertySearchResponseModel> {
  PropertySearchCubit() : super(const PropertySearchResponseModel.initial());

  late PropertySearchFilters _filters;
  bool _isLoadingMore = false;

  PropertySearchFilters get filters => _filters;
  bool get canLoadMore => state.data.next?.isNotEmpty ?? false;
  bool get isLoadingMore => _isLoadingMore;

  Future<void> getProperties(PropertySearchFilters filters) async {
    _filters = filters.copyWith(page: 1);
    await executeAsyncWithBaseModel(
      operation: () => baseCrudUseCase.call(
        CrudBaseParmas<PropertySearchResponseModel>(
          api: ApiConstants.properties,
          httpRequestType: HttpRequestType.get,
          cacheKey: _filters.cacheKey,
          queryParameters: _filters.toQueryParameters(),
          mapper: (json) => PropertySearchResponseModel.fromJson(json),
          fromCacheJson: PropertySearchResponseModel.fromJson,
          toJson: (model) => model.toJson(),
        ),
      ),
    );
  }

  Future<void> loadMore() async {
    if (_isLoadingMore || !canLoadMore) return;

    _isLoadingMore = true;
    final PropertySearchResponseModel currentData = state.data;
    final PropertySearchFilters nextFilters = _filters.copyWith(
      page: _filters.page + 1,
    );
    setLoadingMore();
    final result = await baseCrudUseCase.call(
      CrudBaseParmas<PropertySearchResponseModel>(
        api: ApiConstants.properties,
        httpRequestType: HttpRequestType.get,
        cacheKey: '${nextFilters.cacheKey}_page_${nextFilters.page}',
        queryParameters: nextFilters.toQueryParameters(),
        mapper: (json) => PropertySearchResponseModel.fromJson(json),
        fromCacheJson: PropertySearchResponseModel.fromJson,
        toJson: (model) => model.toJson(),
      ),
    );
    result.when(
      (success) {
        _filters = nextFilters;
        setSuccess(
          BaseModel<PropertySearchResponseModel>(
            key: success.key,
            msg: success.msg,
            data: success.data.copyWith(
              results: [...currentData.results, ...success.data.results],
            ),
          ),
        );
      },
      (failure) {
        setSuccess(
          BaseModel<PropertySearchResponseModel>(
            key: '',
            msg: failure.message,
            data: currentData,
          ),
        );
      },
    );
    _isLoadingMore = false;
  }
}
