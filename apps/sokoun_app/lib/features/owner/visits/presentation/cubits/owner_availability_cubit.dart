part of '../../imports.dart';

class OwnerAvailabilityCubit
    extends AsyncCubit<OwnerAvailabilityScheduleContent> {
  OwnerAvailabilityCubit()
    : super(const OwnerAvailabilityScheduleContent.initial());

  Future<void> loadAvailability({
    required String ownerPropertyId,
    required void Function(OwnerAvailabilityScheduleContent) onLoaded,
  }) async {
    if (isClosed || isLoading) return;
    await executeAsyncWithBaseModel(
      operation: () => baseCrudUseCase.call(
        CrudBaseParmas<OwnerAvailabilityScheduleContent>(
          api: ApiConstants.ownerPropertyAvailability(ownerPropertyId),
          httpRequestType: HttpRequestType.get,
          cacheKey: 'owner_property_availability_$ownerPropertyId',
          mapper: (json) => OwnerAvailabilityScheduleContent.fromJson(
            json is Map<String, dynamic> ? json : const {},
          ),
          fromCacheJson: OwnerAvailabilityScheduleContent.fromJson,
          toJson: (schedule) => schedule.toJson(),
        ),
      ),
      onSuccess: (model) => onLoaded(model.data),
      withInternetInterceptor: true,
    );
  }

  Future<bool> saveAvailability({
    required String ownerPropertyId,
    required OwnerAvailabilitySaveBody body,
  }) async {
    if (isClosed || isLoading) return false;
    await executeAsyncWithBaseModel(
      operation: () => baseCrudUseCase.call(
        CrudBaseParmas<OwnerAvailabilityScheduleContent>(
          api: ApiConstants.ownerPropertyAvailability(ownerPropertyId),
          httpRequestType: HttpRequestType.put,
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
