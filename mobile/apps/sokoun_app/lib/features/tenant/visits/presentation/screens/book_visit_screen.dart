part of '../../imports.dart';

class BookVisitScreen extends StatefulWidget {
  const BookVisitScreen({super.key, required this.property});
  final VisitPropertyContent property;
  @override
  State<BookVisitScreen> createState() => _BookVisitScreenState();
}

class _BookVisitScreenState extends State<BookVisitScreen> {
  late final BookVisitCubit _bookVisitCubit;
  late final VisitAvailabilityCubit _daysCubit;
  late final VisitAvailabilityCubit _timesCubit;
  late final Future<void> _daysRequest;
  final TextEditingController _noteController = TextEditingController();
  final ValueNotifier<Future<void>> _timesRequest = ValueNotifier(
    Future.value(),
  );
  final ValueNotifier<({int dayIndex, TimeOfDay? time})> _selection =
      ValueNotifier((dayIndex: 0, time: null));
  bool _submitted = false;
  bool _confirming = false;

  List<VisitDayContent> get _days => _daysCubit.data.days
      .where((day) => VisitScheduleRules.isTodayOrLater(day.visitDate))
      .toList(growable: false);

  @override
  void initState() {
    super.initState();
    _bookVisitCubit = BookVisitCubit();
    _daysCubit = VisitAvailabilityCubit();
    _timesCubit = VisitAvailabilityCubit();
    _daysRequest = _loadDays();
  }

  Future<void> _loadDays() async {
    await _daysCubit.load(widget.property.id);
    if (!mounted || !_daysCubit.state.isSuccess) return;
    _selection.value = (dayIndex: 0, time: null);
    if (_days.isNotEmpty) {
      _timesRequest.value = _timesCubit.load(
        widget.property.id,
        date: _days.first.visitDate,
      );
    }
  }

  void _selectDay(int index) {
    if (index < 0 || index >= _days.length || _confirming) return;
    _selection.value = (dayIndex: index, time: null);
    _timesRequest.value = _timesCubit.load(
      widget.property.id,
      date: _days[index].visitDate,
    );
  }

  @override
  void dispose() {
    _noteController.dispose();
    _selection.dispose();
    _timesRequest.dispose();
    _bookVisitCubit.close();
    _daysCubit.close();
    _timesCubit.close();
    super.dispose();
  }

  Future<void> _confirmVisit(BuildContext context) async {
    if (_confirming || _bookVisitCubit.isLoading) return;
    if (!WorkspaceNavigation.isAuthenticated) {
      await WorkspaceNavigation.open(
        workspace: AppWorkspace.tenant,
        showLoginSheet: true,
        detail: () => Go.to(BookVisitScreen(property: widget.property)),
      );
      return;
    }
    final selection = _selection.value;
    final time = selection.time;
    if (time == null ||
        selection.dayIndex < 0 ||
        selection.dayIndex >= _days.length) {
      return;
    }
    final day = _days[selection.dayIndex];
    final apiTime = BookVisitBody.formatApiTime(
      hour: time.hour,
      minute: time.minute,
    );
    _confirming = true;
    try {
      // Recheck on the server. Cached availability never authorizes a booking.
      final request = _timesCubit.load(widget.property.id, date: day.visitDate);
      _timesRequest.value = request;
      await request;
      if (!mounted || !context.mounted) return;
      final slotIsAvailable =
          _timesCubit.state.isSuccess &&
          !_timesCubit.data.isCached &&
          _timesCubit.data.times.any(
            (slot) =>
                slot.isAvailable &&
                Validators.normalizeVisitTime(slot.visitTime) == apiTime,
          );
      if (!slotIsAvailable ||
          !VisitScheduleRules.isFuture(day.visitDate, apiTime)) {
        _selection.value = (dayIndex: selection.dayIndex, time: null);
        return;
      }
      final confirmed = await showModalBottomSheet<bool>(
        context: context,
        useSafeArea: true,
        isScrollControlled: true,
        showDragHandle: true,
        builder: (_) => VisitRequestReviewSheet(
          property: widget.property,
          day: day,
          time: time,
          note: _noteController.text,
        ),
      );
      if (confirmed != true ||
          !mounted ||
          !VisitScheduleRules.isFuture(day.visitDate, apiTime)) {
        return;
      }
      await _bookVisitCubit.bookVisit(
        propertyId: widget.property.id,
        ownerId: widget.property.ownerId,
        visitDate: day.visitDate,
        visitHour: time.hour,
        visitMinute: time.minute,
        note: _noteController.text.trim(),
        onSuccess: () {
          if (!mounted) return;
          _submitted = true;
          Go.off(
            VisitConfirmedScreen(
              message: _bookVisitCubit.state.msg ?? '',
              property: widget.property,
              selectedDay: day,
              selectedTime: VisitTimeSlotContent(
                label: time.format(context),
                visitTime: apiTime,
              ),
            ),
          );
        },
        onError: (_) {
          if (!mounted) return;
          _selection.value = (dayIndex: selection.dayIndex, time: null);
          _timesRequest.value = _timesCubit.load(
            widget.property.id,
            date: day.visitDate,
          );
        },
      );
    } finally {
      _confirming = false;
    }
  }

  Widget _form(VisitAvailabilityContent availability) =>
      ValueListenableBuilder<({int dayIndex, TimeOfDay? time})>(
        valueListenable: _selection,
        builder: (context, selection, _) {
          final days = _days;
          return BookVisitForm(
            property: widget.property,
            days: days,
            selectedDayIndex: selection.dayIndex,
            selectedTime: selection.time,
            noteController: _noteController,
            onDaySelected: _selectDay,
            onTimeSelected: (time) {
              if (!_confirming) {
                _selection.value = (dayIndex: selection.dayIndex, time: time);
              }
            },
            onConfirmPressed: _confirmVisit,
            timeSelector: days.isEmpty
                ? const SizedBox.shrink()
                : BlocProvider.value(
                    value: _timesCubit,
                    child: ValueListenableBuilder<Future<void>>(
                      valueListenable: _timesRequest,
                      builder: (context, request, _) => FutureBuilder<void>(
                        future: request,
                        builder: (context, snapshot) =>
                            StatusBuilder<
                              VisitAvailabilityCubit,
                              VisitAvailabilityContent
                            >.withShimmer(
                              initialDataForShimmer:
                                  const VisitAvailabilityContent.initial(),
                              shimmerBuilder: (_) => const SizedBox(height: 80),
                              onRetry: () => _timesCubit.load(
                                widget.property.id,
                                date: days[selection.dayIndex].visitDate,
                              ),
                              builder: (content) => VisitAvailableTimes(
                                date: days[selection.dayIndex].visitDate,
                                slots: content.times,
                                isCached: content.isCached,
                                selectedTime: selection.time,
                                onSelected: (time) {
                                  if (!_confirming) {
                                    _selection.value = (
                                      dayIndex: selection.dayIndex,
                                      time: time,
                                    );
                                  }
                                },
                              ),
                            ),
                      ),
                    ),
                  ),
          );
        },
      );

  @override
  Widget build(BuildContext context) => MultiBlocProvider(
    providers: [
      BlocProvider.value(value: _bookVisitCubit),
      BlocProvider.value(value: _daysCubit),
    ],
    child: UnsavedChangesGuard(
      hasChanges: () =>
          !_submitted &&
          (_selection.value.time != null ||
              _noteController.text.trim().isNotEmpty),
      isSaving: () => _confirming || _bookVisitCubit.isLoading,
      child: AppScaffold(
        title: LocaleKeys.tenantVisitBookTitle,
        showBackButton: true,
        body: SafeArea(
          child: FutureBuilder<void>(
            future: _daysRequest,
            builder: (context, snapshot) =>
                StatusBuilder<
                  VisitAvailabilityCubit,
                  VisitAvailabilityContent
                >.withShimmer(
                  initialDataForShimmer:
                      const VisitAvailabilityContent.initial(),
                  shimmerBuilder: (_) => const SizedBox(height: 240),
                  onRetry: _loadDays,
                  builder: _form,
                ),
          ),
        ),
      ),
    ),
  );
}
