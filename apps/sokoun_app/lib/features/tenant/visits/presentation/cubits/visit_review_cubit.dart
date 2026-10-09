part of '../../imports.dart';

class VisitReviewCubit extends VerifiedActionCubit<bool> {
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
    bool eligible = false;
    await executeAsyncWithBaseModel(
      operation: () async {
        final fresh = await baseCrudUseCase.call(
          CrudBaseParmas<TenantVisitDetailsContent>(
            api: ApiConstants.tenantVisitRequestDetails(visitId),
            httpRequestType: HttpRequestType.get,
            cachePolicy: ReadCachePolicy.privateMemory,
            cacheKey: 'review_eligibility_$visitId',
            mapper: (json) =>
                TenantVisitDetailsContent.fromJson(visitJsonMap(json)),
            fromCacheJson: TenantVisitDetailsContent.fromJson,
            toJson: (value) => value.toJson(),
          ),
        );
        final details = fresh.tryGetSuccess()?.data;
        eligible =
            details != null &&
            details.visit.id == visitId &&
            details.visit.canReview &&
            details.review == null;
        return eligible
            ? Success(BaseModel(key: '', msg: '', data: false))
            : Error(
                fresh.tryGetError() ??
                    ServerFailure(
                      LocaleKeys.professionalUnavailableDestination,
                    ),
              );
      },
    );
    if (!eligible || isClosed) return false;
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
