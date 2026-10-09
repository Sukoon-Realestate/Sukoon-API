part of '../../imports.dart';

class VisitAvailabilityCubit extends AsyncCubit<VisitAvailabilityContent> {
  VisitAvailabilityCubit() : super(const VisitAvailabilityContent.initial());
  int _revision = 0;

  Future<void> load(String propertyId, {String date = ''}) async {
    if (isClosed || propertyId.isEmpty) return;
    final revision = ++_revision;
    await executeAsyncWithBaseModel(
      operation: () => baseCrudUseCase.call(
        CrudBaseParmas<VisitAvailabilityContent>(
          api: ApiConstants.propertyAvailableDates(propertyId),
          httpRequestType: HttpRequestType.get,
          cachePolicy: ReadCachePolicy.privateMemory,
          queryParameters: {if (date.isNotEmpty) 'date': date},
          cacheKey:
              'visit_availability_${UserModel.currentUser?.id ?? 'guest'}_${propertyId}_$date',
          mapper: (json) =>
              VisitAvailabilityContent.fromJson(visitJsonMap(json)),
          fromCacheJson: VisitAvailabilityContent.fromJson,
          toJson: (content) => content.toJson(),
        ),
      ),
      withInternetInterceptor: true,
      shouldApplyResult: () => revision == _revision,
      onSuccess: (response) {
        if (response.key == 'fromCache') {
          updateData(data.copyWith(isCached: true));
        }
      },
    );
  }
}
