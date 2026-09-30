part of '../../imports.dart';

class OwnerVisitStatusCubit extends AsyncCubit<bool> {
  OwnerVisitStatusCubit() : super(false);

  Future<void> acceptVisitRequest({
    required String requestId,
    required void Function() onSuccess,
    void Function(String message)? onError,
  }) async {
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
    await _updateVisitRequest(
      api: ApiConstants.rejectOwnerVisitRequest(requestId),
      onSuccess: onSuccess,
      onError: onError,
    );
  }

  Future<void> _updateVisitRequest({
    required String api,
    required void Function() onSuccess,
    void Function(String message)? onError,
  }) async {
    await executeAsyncWithBaseModel(
      operation: () => baseCrudUseCase.call(
        CrudBaseParmas<bool>(
          api: api,
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
