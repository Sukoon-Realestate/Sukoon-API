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
  late final ValueNotifier<VisitPropertyContent> _currentProperty =
      ValueNotifier(widget.property);
  late final TextDraftBinding _draft;
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
    _draft = TextDraftBinding(
      flow: 'viewing',
      entityId: widget.property.id,
      workspace: 'tenant',
      fields: [_noteController, _selection],
      context: () => context,
      mounted: () => mounted,
      capture: () => TextFormDraft({
        'note': _noteController.text,
        'date': _days.isNotEmpty && _selection.value.dayIndex < _days.length
            ? _days[_selection.value.dayIndex].visitDate
            : '',
        'time': _selection.value.time == null
            ? ''
            : BookVisitBody.formatApiTime(
                hour: _selection.value.time!.hour,
                minute: _selection.value.time!.minute,
              ),
        'offer_id': widget.property.selection?.offerId ?? '',
      }),
      restore: (draft) {
        unawaited(_restoreViewing(draft));
      },
    );
    unawaited(_draft.start());
  }

  Future<void> _restoreViewing(TextFormDraft draft) async {
    _noteController.text = draft['note'];
    await _daysRequest;
    if (!mounted) return;
    final int index = _days.indexWhere((day) => day.visitDate == draft['date']);
    if (index < 0 ||
        draft['offer_id'] != (widget.property.selection?.offerId ?? '')) {
      return;
    }
    _selectDay(index);
    await _timesRequest.value;
    if (!mounted) return;
    final String time = draft['time'];
    final parts = time.split(':');
    final int? hour = parts.isEmpty ? null : int.tryParse(parts[0]);
    final int? minute = parts.length < 2 ? null : int.tryParse(parts[1]);
    if (hour == null ||
        minute == null ||
        !VisitScheduleRules.isFuture(draft['date'], time) ||
        !_timesCubit.data.times.any(
          (slot) =>
              slot.isAvailable &&
              Validators.normalizeVisitTime(slot.visitTime) == time,
        )) {
      return;
    }
    _selection.value = (
      dayIndex: index,
      time: TimeOfDay(hour: hour, minute: minute),
    );
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
    unawaited(_draft.close());
    _noteController.dispose();
    _currentProperty.dispose();
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
        detail: () => Go.to(BookVisitScreen(property: _currentProperty.value)),
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
      final rental = _currentProperty.value.selection;
      if (_currentProperty.value.hasRentalOffers &&
          (!RentalOfferCapabilities.configured.canRequestViewing ||
              rental == null)) {
        Messages.showToast(
          msg: LocaleKeys.rentalUnavailableCapability,
          status: BaseStatus.error,
        );
        return;
      }
      if (rental != null) {
        try {
          final fresh = await RentalOfferReadData(
            _bookVisitCubit.baseCrudUseCase,
          ).freshSelection(rental);
          if (!mounted) return;
          _currentProperty.value = _currentProperty.value.copyWith(
            selection: fresh,
            meta: RentalOfferLabels.price(fresh),
          );
          if (!rental.sameTermsAs(fresh)) {
            Messages.showToast(
              msg: LocaleKeys.rentalTermsChanged,
              status: BaseStatus.error,
            );
            return;
          }
        } catch (error) {
          if (mounted) {
            Messages.showToast(
              msg: error is StateError ? error.message : error.toString(),
              status: BaseStatus.error,
            );
          }
          return;
        }
      }
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
          property: _currentProperty.value,
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
      if (!await _draft.beginSubmission()) return;
      await _bookVisitCubit.bookVisit(
        propertyId: widget.property.id,
        ownerId: widget.property.ownerId,
        selection: _currentProperty.value.selection,
        hasRentalOffers: _currentProperty.value.hasRentalOffers,
        visitDate: day.visitDate,
        visitHour: time.hour,
        visitMinute: time.minute,
        note: _noteController.text.trim(),
        onSuccess: () {
          if (!mounted) return;
          _submitted = true;
          unawaited(_draft.clear());
          Go.off(
            VisitConfirmedScreen(
              message: _bookVisitCubit.state.msg ?? '',
              property: _currentProperty.value,
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
      await _draft.finishSubmission(
        confirmed: _submitted,
        unknown: _bookVisitCubit.lastFailure?.outcomeUnknown ?? false,
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
          return ValueListenableBuilder<VisitPropertyContent>(
            valueListenable: _currentProperty,
            builder: (_, property, _) => BookVisitForm(
              property: _currentProperty.value,
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
                                shimmerBuilder: (_) =>
                                    const SizedBox(height: 80),
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
