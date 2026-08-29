part of '../../imports.dart';

class VisitScheduleCubit extends AsyncCubit<VisitScheduleContent> {
  VisitScheduleCubit() : super(const VisitScheduleContent.initial());

  Future<void> getAvailableDates({
    required String propertyId,
    String? date,
  }) async {
    await executeAsyncWithBaseModel(
      operation: () => baseCrudUseCase.call(
        CrudBaseParmas<VisitScheduleContent>(
          api: ApiConstants.propertyAvailableDates(propertyId),
          httpRequestType: HttpRequestType.get,
          queryParameters: date == null || date.isEmpty ? null : {'date': date},
          mapper: (json) => VisitScheduleContent.fromJson(
            json is Map<String, dynamic> ? json : const {},
          ),
        ),
      ),
    );
  }

  Future<void> useLocalSchedule(VisitScheduleContent schedule) async {
    emit(state.success(data: schedule));
  }
}
