part of '../../imports.dart';

class BookVisitScreen extends StatefulWidget {
  const BookVisitScreen({super.key, this.property});

  final VisitPropertyContent? property;

  @override
  State<BookVisitScreen> createState() => _BookVisitScreenState();
}

class _BookVisitScreenState extends State<BookVisitScreen> {
  late final VisitPropertyContent _property;
  late final TextEditingController _noteController;
  late final BookVisitCubit _bookVisitCubit;
  late final VisitScheduleCubit _scheduleCubit;
  late Future<void> _scheduleRequest;
  int _selectedDayIndex = 0;
  int? _selectedTimeIndex;

  bool get _usesPrototypeSchedule => _property.id.isEmpty;

  @override
  void initState() {
    super.initState();
    _property = widget.property ?? VisitPropertyContent.prototype();
    _noteController = TextEditingController();
    _bookVisitCubit = BookVisitCubit();
    _scheduleCubit = VisitScheduleCubit();
    if (_usesPrototypeSchedule) {
      _selectedDayIndex = 1;
      _selectedTimeIndex = 3;
      _scheduleRequest = _scheduleCubit.useLocalSchedule(
        VisitScheduleContent(
          days: TenantVisitsContent.days,
          times: TenantVisitsContent.timeSlots,
        ),
      );
    } else {
      _scheduleRequest = _loadSchedule();
    }
  }

  @override
  void dispose() {
    _noteController.dispose();
    _bookVisitCubit.close();
    _scheduleCubit.close();
    super.dispose();
  }

  Future<void> _loadSchedule({String? selectedDate}) async {
    await _scheduleCubit.getAvailableDates(
      propertyId: _property.id,
      date: selectedDate,
    );
    if (!mounted || !_scheduleCubit.state.status.isSuccess) return;

    final VisitScheduleContent schedule = _scheduleCubit.data;
    int selectedDayIndex = 0;
    if (selectedDate != null) {
      final int matchingIndex = schedule.days.indexWhere(
        (day) => day.visitDate == selectedDate,
      );
      if (matchingIndex >= 0) selectedDayIndex = matchingIndex;
    }

    final int firstAvailableTime = schedule.times.indexWhere(
      (time) => time.isAvailable,
    );
    setState(() {
      _selectedDayIndex = selectedDayIndex;
      _selectedTimeIndex = firstAvailableTime < 0 ? null : firstAvailableTime;
    });
  }

  void _selectDay(VisitScheduleContent schedule, int index) {
    if (_usesPrototypeSchedule) {
      setState(() => _selectedDayIndex = index);
      return;
    }

    final String selectedDate = schedule.days[index].visitDate;
    final Future<void> request = _loadSchedule(selectedDate: selectedDate);
    setState(() {
      _selectedDayIndex = index;
      _selectedTimeIndex = null;
      _scheduleRequest = request;
    });
  }

  void _refreshScheduleAfterConflict(String selectedDate) {
    if (!mounted) return;
    final Future<void> request = _loadSchedule(selectedDate: selectedDate);
    setState(() {
      _selectedTimeIndex = null;
      _scheduleRequest = request;
    });
  }

  Future<void> _confirmVisit(BuildContext context) async {
    final VisitScheduleContent schedule = _scheduleCubit.data;
    final int? timeIndex = _selectedTimeIndex;
    if (schedule.days.isEmpty ||
        timeIndex == null ||
        _selectedDayIndex >= schedule.days.length ||
        timeIndex >= schedule.times.length ||
        !schedule.times[timeIndex].isAvailable) {
      return;
    }

    final VisitDayContent selectedDay = schedule.days[_selectedDayIndex];
    final VisitTimeSlotContent selectedTime = schedule.times[timeIndex];

    await context.read<BookVisitCubit>().bookVisit(
      propertyId: _property.id,
      visitDate: selectedDay.visitDate,
      visitTime: selectedTime.visitTime,
      note: _noteController.text.trim(),
      onSuccess: () => Go.to(
        VisitConfirmedScreen(
          property: _property,
          selectedDay: selectedDay,
          selectedTime: selectedTime,
        ),
      ),
      onError: (message) {
        if (BookVisitCubit.isUnavailableSlotError(message)) {
          _refreshScheduleAfterConflict(selectedDay.visitDate);
        }
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    return MultiBlocProvider(
      providers: [
        BlocProvider<BookVisitCubit>.value(value: _bookVisitCubit),
        BlocProvider<VisitScheduleCubit>.value(value: _scheduleCubit),
      ],
      child: Directionality(
        textDirection: TextDirection.rtl,
        child: Scaffold(
          backgroundColor: AppColors.scaffoldBackground,
          body: SafeArea(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                VisitHeader(
                  title: LocaleKeys.tenantVisitBookTitle,
                  backKey: const ValueKey('book-visit-back'),
                  onBackPressed: () => Go.back(),
                ),
                Expanded(
                  child:
                      StatusBuilder<
                        VisitScheduleCubit,
                        VisitScheduleContent
                      >.withShimmer(
                        initialDataForShimmer:
                            const VisitScheduleContent.initial(),
                        requestToTryAgainWhenError: _scheduleRequest,
                        errorType: ErrorType.defaultView,
                        builder: (schedule) => BookVisitForm(
                          property: _property,
                          days: schedule.days,
                          timeSlots: schedule.times,
                          selectedDayIndex: _selectedDayIndex,
                          selectedTimeIndex: _selectedTimeIndex,
                          noteController: _noteController,
                          onDaySelected: (index) => _selectDay(schedule, index),
                          onTimeSelected: (index) {
                            setState(() => _selectedTimeIndex = index);
                          },
                          onConfirmPressed: _confirmVisit,
                        ),
                      ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
