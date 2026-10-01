part of '../../imports.dart';

class OwnerVisitStatusCubit extends AsyncCubit<bool> {
  OwnerVisitStatusCubit() : super(false);

  Future<void> acceptVisitRequest({
    required String requestId,
    required void Function() onSuccess,
    void Function(String message)? onError,
  }) async {
    if (isClosed || isLoading) return;
    await _updateVisitRequest(
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
      api: ApiConstants.rejectOwnerVisitRequest(requestId),
      body: const {'reason': 'timing_not_suitable', 'custom_reason': ''},
      onSuccess: onSuccess,
      onError: onError,
    );
  }

  Future<void> _updateVisitRequest({
    required String api,
    Map<String, dynamic>? body,
    required void Function() onSuccess,
    void Function(String message)? onError,
  }) async {
    if (isClosed || isLoading) return;
    await executeAsyncWithBaseModel(
      operation: () => baseCrudUseCase.call(
        CrudBaseParmas<bool>(
          api: api,
          body: body,
          httpRequestType: HttpRequestType.post,
          mapper: (_) => true,
        ),
      ),
      onSuccess: (_) {
        WorkspaceCountsRefreshBus.refresh();
        onSuccess();
      },
      onError: onError,
    );
  }
}
