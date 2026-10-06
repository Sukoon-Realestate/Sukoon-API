part of '../../imports.dart';

class OwnerAvailabilityCubit
    extends AsyncCubit<OwnerAvailabilityScheduleContent> {
  OwnerAvailabilityCubit()
    : super(const OwnerAvailabilityScheduleContent.initial());

  Future<void> loadAvailability({
    required String ownerPropertyId,
    required DateTime weekStart,
    required void Function(OwnerAvailabilityScheduleContent) onLoaded,
  }) async {
    if (isClosed || isLoading) return;
    await executeAsyncWithBaseModel(
      operation: () => baseCrudUseCase.call(
        CrudBaseParmas<OwnerAvailabilityScheduleContent>(
          api: ApiConstants.ownerPropertyAvailability(ownerPropertyId),
          httpRequestType: HttpRequestType.get,
          queryParameters: {
            'week_start': OwnerVisitCalendarContent.formatDate(weekStart),
          },
          cacheKey: cacheKey(ownerPropertyId, weekStart),
          mapper: (json) => OwnerAvailabilityScheduleContent.fromJson(
            json is Map<String, dynamic> ? json : const {},
          ).withEditableDays(),
          fromCacheJson: OwnerAvailabilityScheduleContent.fromJson,
          toJson: (schedule) => schedule.toJson(),
        ),
      ),
      onSuccess: (model) => onLoaded(model.data),
      withInternetInterceptor: true,
    );
  }

  static String cacheKey(String propertyId, DateTime weekStart) =>
      'owner_property_availability_${propertyId}_${OwnerVisitCalendarContent.formatDate(weekStart)}';

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
      onSuccess: (_) {
        final date = DateTime.tryParse(body.availabilityDate);
        if (date != null) {
          ObjectBoxCacheService.remove(
            cacheKey(
              ownerPropertyId,
              OwnerAvailabilityScheduleContent.startOfWeek(date),
            ),
          );
        }
      },
    );
    return state.isSuccess;
  }
}
