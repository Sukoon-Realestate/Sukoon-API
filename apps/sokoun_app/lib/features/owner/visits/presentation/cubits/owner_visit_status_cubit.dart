part of '../../imports.dart';

class OwnerVisitStatusCubit extends VerifiedActionCubit<bool> {
  OwnerVisitStatusCubit() : super(false);

  Future<void> acceptVisitRequest({
    required String requestId,
    required void Function() onSuccess,
    void Function(String message)? onError,
  }) async {
    if (isClosed || isLoading) return;
    await _updateVisitRequest(
      requestId: requestId,
      api: ApiConstants.acceptOwnerVisitRequest(requestId),
      onSuccess: onSuccess,
      onError: onError,
    );
  }

  Future<void> rejectVisitRequest({
    required String requestId,
    required void Function() onSuccess,
    void Function(String message)? onError,
  }) async {
    if (isClosed || isLoading) return;
    await _updateVisitRequest(
      requestId: requestId,
      api: ApiConstants.rejectOwnerVisitRequest(requestId),
      body: const {'reason': 'timing_not_suitable', 'custom_reason': ''},
      onSuccess: onSuccess,
      onError: onError,
    );
  }

  Future<void> _updateVisitRequest({
    required String requestId,
    required String api,
    Map<String, dynamic>? body,
    required void Function() onSuccess,
    void Function(String message)? onError,
  }) async {
    if (isClosed || isLoading) return;
    await executeAsyncWithBaseModel(
      showMsgOnSuccess: true,
      operation: () => baseCrudUseCase.call(
        CrudBaseParmas<bool>(
          api: api,
          body: body,
          httpRequestType: HttpRequestType.post,
          mapper: (_) => true,
        ),
      ),
      onSuccess: (_) {
        // The pre-decision snapshot must not return after accepting/rejecting.
        ObjectBoxCacheService.remove('owner_visit_request_details_$requestId');
        ObjectBoxCacheService.remove('received_visit_details_$requestId');
        WorkspaceCountsRefreshBus.refresh();
        onSuccess();
      },
      onError: onError,
    );
  }
}
