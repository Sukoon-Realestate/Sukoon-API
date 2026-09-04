part of '../../imports.dart';

class OwnerCalendarCubit extends AsyncCubit<OwnerVisitCalendarContent> {
  OwnerCalendarCubit({required DateTime initialDate})
    : _selectedDate = DateUtils.dateOnly(initialDate),
      super(OwnerVisitCalendarContent.initial(initialDate));

  DateTime _selectedDate;
  bool _hasInternetInterceptor = false;

  Future<void> getCalendar({required DateTime date}) async {
    _selectedDate = DateUtils.dateOnly(date);
    final bool shouldAttachInternetInterceptor = !_hasInternetInterceptor;
    _hasInternetInterceptor = true;
    await executeAsyncWithBaseModel(
      operation: () {
        final DateTime selectedDate = _selectedDate;
        final String formattedDate = OwnerVisitCalendarContent.formatDate(
          selectedDate,
        );
        return baseCrudUseCase.call(
          CrudBaseParmas<OwnerVisitCalendarContent>(
            api: ApiConstants.ownerCalendar,
            httpRequestType: HttpRequestType.get,
            queryParameters: {
              'year': selectedDate.year,
              'month': selectedDate.month,
              'date': formattedDate,
            },
            cacheKey:
                'owner_calendar_${selectedDate.year}_${selectedDate.month}_$formattedDate',
            mapper: (json) => OwnerVisitCalendarContent.fromJson(
              json is Map<String, dynamic> ? json : const {},
              fallbackDate: selectedDate,
            ),
            fromCacheJson: (json) => OwnerVisitCalendarContent.fromJson(
              json,
              fallbackDate: selectedDate,
            ),
            toJson: (calendar) => calendar.toJson(),
          ),
        );
      },
      withInternetInterceptor: shouldAttachInternetInterceptor,
    );
  }
}
