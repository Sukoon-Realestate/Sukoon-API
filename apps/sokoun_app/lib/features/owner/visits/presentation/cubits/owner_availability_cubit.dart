part of '../../imports.dart';

class OwnerAvailabilityCubit
    extends AsyncCubit<OwnerAvailabilityScheduleContent> {
  OwnerAvailabilityCubit()
    : super(const OwnerAvailabilityScheduleContent.initial());

  Future<bool> saveAvailability({
    required String ownerPropertyId,
    required OwnerAvailabilitySaveBody body,
  }) async {
    await executeAsyncWithBaseModel(
      operation: () => baseCrudUseCase.call(
        CrudBaseParmas<OwnerAvailabilityScheduleContent>(
          api: ApiConstants.ownerPropertyAvailability(ownerPropertyId),
          httpRequestType: HttpRequestType.post,
          body: body.toJson(),
          mapper: (json) => OwnerAvailabilityScheduleContent.fromJson(
            json is Map<String, dynamic> ? json : const {},
          ),
        ),
      ),
    );
    return state.isSuccess;
  }
}
