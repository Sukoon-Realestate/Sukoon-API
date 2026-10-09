part of '../../imports.dart';

class OwnerCalendarCubit
    extends VerifiedActionCubit<OwnerVisitCalendarContent> {
  OwnerCalendarCubit({required DateTime initialDate})
    : _selectedDate = DateUtils.dateOnly(initialDate),
      super(OwnerVisitCalendarContent.initial(initialDate));

  DateTime _selectedDate;
  Future<void>? _request;
  int _requestVersion = 0;
  CancelToken? _cancelToken;

  Future<void> getCalendar({required DateTime date}) {
    if (isClosed) return Future<void>.value();
    final DateTime selectedDate = DateUtils.dateOnly(date);
    if (selectedDate == _selectedDate && _request != null) return _request!;
    _selectedDate = selectedDate;
    _cancelToken?.cancel();
    final CancelToken cancelToken = _cancelToken = CancelToken();
    final int version = ++_requestVersion;
    return _request = _load(selectedDate, version, cancelToken).whenComplete(
      () {
        if (version == _requestVersion) _request = null;
      },
    );
  }

  Future<void> _load(
    DateTime selectedDate,
    int version,
    CancelToken cancelToken,
  ) async {
    await executeAsyncWithBaseModel(
      shouldApplyResult: () => version == _requestVersion,
      operation: () {
        final String formattedDate = OwnerVisitCalendarContent.formatDate(
          selectedDate,
        );
        return baseCrudUseCase.call(
          CrudBaseParmas<OwnerVisitCalendarContent>(
            api: ApiConstants.ownerCalendar,
            httpRequestType: HttpRequestType.get,
            cachePolicy: ReadCachePolicy.privateMemory,
            cancelToken: cancelToken,
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
      withInternetInterceptor: true,
    );
  }

  @override
  Future<void> close() {
    _requestVersion++;
    _cancelToken?.cancel();
    return super.close();
  }
}
