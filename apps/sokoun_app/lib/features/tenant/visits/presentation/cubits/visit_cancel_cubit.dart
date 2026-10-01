part of '../../imports.dart';

class VisitCancelCubit extends AsyncCubit<bool> {
  VisitCancelCubit() : super(false);
  Future<bool> cancel(String visitId) async {
    if (isClosed || isLoading || visitId.isEmpty) return false;
    bool succeeded = false;
    await executeAsyncWithBaseModel(
      operation: () => baseCrudUseCase.call(
        CrudBaseParmas<bool>(
          api: ApiConstants.updatePropertyVisit(visitId),
          httpRequestType: HttpRequestType.patch,
          body: {'status': 'canceled'},
          mapper: (_) => true,
        ),
      ),
      onSuccess: (_) {
        succeeded = true;
        WorkspaceCountsRefreshBus.refresh();
      },
    );
    return succeeded;
  }
}
