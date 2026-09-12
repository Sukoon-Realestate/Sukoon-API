part of '../../imports.dart';

class BookVisitCubit extends AsyncCubit<Map<String, dynamic>> {
  BookVisitCubit() : super(const {});

  Future<void> bookVisit({
    required String propertyId,
    required String visitDate,
    required int visitHour,
    required int visitMinute,
    required String note,
    required void Function() onSuccess,
    void Function(String message)? onError,
  }) async {
    final BookVisitBody body = BookVisitBody.fromTime(
      visitDate: visitDate,
      hour: visitHour,
      minute: visitMinute,
      note: note,
    );
    await executeAsyncWithBaseModel(
      operation: () => baseCrudUseCase.call(
        CrudBaseParmas<Map<String, dynamic>>(
          api: ApiConstants.propertyVisits(propertyId),
          httpRequestType: HttpRequestType.post,
          body: body.toJson(),
          mapper: (json) =>
              json is Map<String, dynamic> ? json : <String, dynamic>{},
        ),
      ),
      onSuccess: (_) => onSuccess(),
      onError: onError,
    );
  }

  static bool isUnavailableSlotError(String message) {
    final String normalized = message.toLowerCase();
    return normalized.contains('already booked') ||
        normalized.contains('not available');
  }
}
