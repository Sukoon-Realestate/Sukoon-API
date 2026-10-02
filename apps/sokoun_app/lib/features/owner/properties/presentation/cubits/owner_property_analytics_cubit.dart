part of '../../imports.dart';

class OwnerPropertyAnalyticsCubit
    extends AsyncCubit<OwnerPropertyAnalyticsContent> {
  OwnerPropertyAnalyticsCubit()
    : super(const OwnerPropertyAnalyticsContent.initial());
  int _version = 0;
  CancelToken? _cancelToken;

  Future<void> load({
    required String propertyId,
    required String period,
  }) async {
    if (isClosed) return;
    _cancelToken?.cancel();
    final token = _cancelToken = CancelToken();
    final version = ++_version;
    await executeAsyncWithBaseModel(
      shouldApplyResult: () => version == _version,
      operation: () => baseCrudUseCase.call(
        CrudBaseParmas<OwnerPropertyAnalyticsContent>(
          api: ApiConstants.propertyStatistics(propertyId),
          httpRequestType: HttpRequestType.get,
          cancelToken: token,
          queryParameters: {'period': period},
          cacheKey: 'owner_statistics_${propertyId}_$period',
          mapper: (json) => OwnerPropertyAnalyticsContent.fromJson(
            json is Map ? Map<String, dynamic>.from(json) : const {},
          ),
          fromCacheJson: OwnerPropertyAnalyticsContent.fromJson,
          toJson: (data) => data.toJson(),
        ),
      ),
      withInternetInterceptor: true,
    );
  }

  @override
  Future<void> close() {
    _version++;
    _cancelToken?.cancel();
    return super.close();
  }
}
