part of '../../imports.dart';

class VisitReviewCubit extends AsyncCubit<bool> {
  VisitReviewCubit() : super(false);
  Future<bool> submit({
    required String visitId,
    required VisitReviewBody body,
  }) async {
    if (isClosed ||
        isLoading ||
        !Validators.isNonBlank(visitId) ||
        !body.isValid) {
      return false;
    }
    bool succeeded = false;
    await executeAsyncWithBaseModel(
      showMsgOnSuccess: true,
      operation: () => baseCrudUseCase.call(
        CrudBaseParmas<bool>(
          api: ApiConstants.reviewPropertyVisit(visitId),
          httpRequestType: HttpRequestType.post,
          body: body.toJson(),
          mapper: (_) => true,
        ),
      ),
      onSuccess: (_) => succeeded = true,
    );
    return succeeded;
  }
}
