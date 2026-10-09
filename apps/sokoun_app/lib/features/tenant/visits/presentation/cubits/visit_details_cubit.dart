part of '../../imports.dart';

class VisitDetailsCubit extends VerifiedActionCubit<TenantVisitDetailsContent> {
  VisitDetailsCubit() : super(const TenantVisitDetailsContent.initial());
  Future<void>? _loadRequest;

  Future<void> load(String visitId) =>
      _loadRequest ??= _load(visitId).whenComplete(() => _loadRequest = null);

  Future<void> refresh(String visitId) async {
    await _loadRequest;
    if (!isClosed) await load(visitId);
  }

  Future<void> _load(String visitId) async {
    if (isClosed || isLoading || visitId.isEmpty) return;
    await executeAsyncWithBaseModel(
      operation: () => baseCrudUseCase.call(
        CrudBaseParmas<TenantVisitDetailsContent>(
          api: ApiConstants.tenantVisitRequestDetails(visitId),
          httpRequestType: HttpRequestType.get,
          cachePolicy: ReadCachePolicy.privateMemory,
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
