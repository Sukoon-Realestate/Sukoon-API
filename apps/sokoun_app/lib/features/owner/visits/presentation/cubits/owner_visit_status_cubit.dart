part of '../../imports.dart';

class OwnerVisitStatusCubit extends AsyncCubit<bool> {
  OwnerVisitStatusCubit() : super(false);

  Future<void> updateVisitStatus({
    required String visitId,
    required OwnerVisitUpdateStatus status,
    required void Function() onSuccess,
    void Function(String message)? onError,
  }) async {
    await executeAsyncWithBaseModel(
      operation: () => baseCrudUseCase.call(
        CrudBaseParmas<bool>(
          api: ApiConstants.propertyVisitDetails(visitId),
          httpRequestType: HttpRequestType.patch,
          body: {'status': status.name},
          mapper: (_) => true,
        ),
      ),
      onSuccess: (_) => onSuccess(),
      onError: onError,
    );
  }
}
