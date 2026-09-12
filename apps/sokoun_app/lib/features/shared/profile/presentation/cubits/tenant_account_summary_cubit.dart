part of '../../imports.dart';

class TenantAccountSummaryCubit
    extends AsyncCubit<TenantAccountSummaryContent> {
  TenantAccountSummaryCubit()
    : super(const TenantAccountSummaryContent.initial());

  Future<void> getSummary() async {
    await executeAsyncWithBaseModel(
      operation: () => baseCrudUseCase.call(
        CrudBaseParmas<TenantAccountSummaryContent>(
          api: ApiConstants.tenantAccountSummary,
          httpRequestType: HttpRequestType.get,
          cacheKey: TenantAccountSummaryContent.cacheKey,
          mapper: (json) =>
              TenantAccountSummaryContent.fromJson(_profileJsonMap(json)),
          fromCacheJson: TenantAccountSummaryContent.fromJson,
          toJson: (summary) => summary.toJson(),
        ),
      ),
      withInternetInterceptor: true,
    );
  }
}
