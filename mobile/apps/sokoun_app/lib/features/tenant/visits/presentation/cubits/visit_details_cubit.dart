part of '../../imports.dart';

class VisitDetailsCubit extends AsyncCubit<TenantVisitDetailsContent> {
  VisitDetailsCubit() : super(const TenantVisitDetailsContent.initial());
  Future<void> load(String visitId) async {
    if (isClosed || isLoading || visitId.isEmpty) return;
    await executeAsyncWithBaseModel(
      operation: () => baseCrudUseCase.call(
        CrudBaseParmas<TenantVisitDetailsContent>(
          api: ApiConstants.tenantVisitRequestDetails(visitId),
          httpRequestType: HttpRequestType.get,
          cacheKey: 'tenant_visit_details_$visitId',
          mapper: (json) =>
              TenantVisitDetailsContent.fromJson(visitJsonMap(json)),
          fromCacheJson: TenantVisitDetailsContent.fromJson,
          toJson: (data) => data.toJson(),
        ),
      ),
      withInternetInterceptor: true,
    );
  }
}
