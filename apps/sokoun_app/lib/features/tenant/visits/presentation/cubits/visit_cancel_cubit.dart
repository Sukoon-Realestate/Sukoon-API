part of '../../imports.dart';

class VisitCancelCubit extends VerifiedActionCubit<bool> {
  VisitCancelCubit() : super(false);
  Future<bool> cancel(String visitId) async {
    if (isClosed || isLoading || visitId.isEmpty) return false;
    bool succeeded = false;
    await executeAsyncWithBaseModel(
      showMsgOnSuccess: true,
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
