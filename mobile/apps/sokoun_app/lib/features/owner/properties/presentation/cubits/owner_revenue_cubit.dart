part of '../../imports.dart';

class OwnerRevenueCubit extends AsyncCubit<OwnerRevenueContent> {
  OwnerRevenueCubit() : super(const OwnerRevenueContent.initial());
  Future<void> load() async {
    if (isClosed || isLoading) return;
    await executeAsyncWithBaseModel(
      operation: () => baseCrudUseCase.call(
        CrudBaseParmas<OwnerRevenueContent>(
          api: ApiConstants.ownerRevenues,
          httpRequestType: HttpRequestType.get,
          cacheKey: 'owner_revenue',
          mapper: (json) => OwnerRevenueContent.fromJson(
            json is Map ? Map<String, dynamic>.from(json) : const {},
          ),
          fromCacheJson: OwnerRevenueContent.fromJson,
          toJson: (data) => data.toJson(),
        ),
      ),
      withInternetInterceptor: true,
    );
  }
}
