part of '../../imports.dart';

class OwnerRequestDetailsCubit
    extends AsyncCubit<OwnerVisitRequestDetailsContent> {
  OwnerRequestDetailsCubit()
    : super(const OwnerVisitRequestDetailsContent.initial());

  Future<void> getRequestDetails(String requestId) async {
    await executeAsyncWithBaseModel(
      operation: () => baseCrudUseCase.call(
        CrudBaseParmas<OwnerVisitRequestDetailsContent>(
          api: ApiConstants.ownerVisitRequestDetails(requestId),
          httpRequestType: HttpRequestType.get,
          cacheKey: 'owner_visit_request_details_$requestId',
          mapper: (json) => OwnerVisitRequestDetailsContent.fromJson(
            _ownerVisitJsonMap(json),
          ),
          fromCacheJson: OwnerVisitRequestDetailsContent.fromJson,
          toJson: (request) => request.toJson(),
        ),
      ),
      withInternetInterceptor: true,
    );
  }
}
