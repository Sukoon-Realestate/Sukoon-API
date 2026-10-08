part of '../../imports.dart';

class OwnerRequestDetailsCubit
    extends VerifiedActionCubit<OwnerVisitRequestDetailsContent> {
  OwnerRequestDetailsCubit({this.useVisitEndpoint = false})
    : super(const OwnerVisitRequestDetailsContent.initial());

  final bool useVisitEndpoint;

  Future<void> getRequestDetails(String requestId) async {
    if (isClosed || isLoading) return;
    await executeAsyncWithBaseModel(
      operation: () => baseCrudUseCase.call(
        CrudBaseParmas<OwnerVisitRequestDetailsContent>(
          api: useVisitEndpoint
              ? ApiConstants.propertyVisitDetails(requestId)
              : ApiConstants.ownerVisitRequestDetails(requestId),
          httpRequestType: HttpRequestType.get,
          cacheKey:
              '${useVisitEndpoint ? 'received_visit_details' : 'owner_visit_request_details'}_$requestId',
          mapper: (json) =>
              OwnerVisitRequestDetailsContent.fromJson(ownerVisitJsonMap(json)),
          fromCacheJson: OwnerVisitRequestDetailsContent.fromJson,
          toJson: (request) => request.toJson(),
        ),
      ),
      withInternetInterceptor: true,
    );
  }
}
