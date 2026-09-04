part of '../../imports.dart';

class BookVisitScreen extends StatefulWidget {
  const BookVisitScreen({super.key, this.property});

  final VisitPropertyContent? property;

  @override
  State<BookVisitScreen> createState() => _BookVisitScreenState();
}

class _BookVisitScreenState extends State<BookVisitScreen> {
  late final VisitPropertyContent _property;
  late final List<VisitDayContent> _days;
  late final TextEditingController _noteController;
  late final BookVisitCubit _bookVisitCubit;
  int _selectedDayIndex = 0;
  TimeOfDay? _selectedTime;

  @override
  void initState() {
    super.initState();
    _property = widget.property ?? VisitPropertyContent.prototype();
    _days = _createUpcomingDays();
    _noteController = TextEditingController();
    _bookVisitCubit = BookVisitCubit();
  }

  List<VisitDayContent> _createUpcomingDays() {
    final DateTime today = DateUtils.dateOnly(DateTime.now());
    return List<VisitDayContent>.generate(7, (index) {
      final DateTime date = DateTime(
        today.year,
        today.month,
        today.day + index,
      );
      return VisitDayContent(
        weekday: _getWeekdayLabel(date.weekday),
        day: date.day.toString(),
        month: date.month.toString(),
        visitDate: _formatVisitDate(date),
      );
    }, growable: false);
  }

  String _getWeekdayLabel(int weekday) {
    return switch (weekday) {
      DateTime.monday => LocaleKeys.tenantVisitDayMonday,
      DateTime.tuesday => LocaleKeys.tenantVisitDayTuesday,
      DateTime.wednesday => LocaleKeys.tenantVisitDayWednesday,
      DateTime.thursday => LocaleKeys.tenantVisitDayThursday,
      DateTime.friday => LocaleKeys.tenantVisitDayFriday,
      DateTime.saturday => LocaleKeys.tenantVisitDaySaturday,
      DateTime.sunday => LocaleKeys.tenantVisitDaySunday,
      _ => '',
    };
  }

  String _formatVisitDate(DateTime date) {
    final String month = date.month.toString().padLeft(2, '0');
    final String day = date.day.toString().padLeft(2, '0');
    return '${date.year}-$month-$day';
  }

  @override
  void dispose() {
    _noteController.dispose();
    _bookVisitCubit.close();
    super.dispose();
  }

  void _clearTimeAfterConflict() {
    if (!mounted) return;
    setState(() => _selectedTime = null);
  }

  Future<void> _confirmVisit(BuildContext context) async {
    final TimeOfDay? selectedTimeOfDay = _selectedTime;
    if (_days.isEmpty ||
        selectedTimeOfDay == null ||
        _selectedDayIndex >= _days.length) {
      return;
    }

    final VisitDayContent selectedDay = _days[_selectedDayIndex];
    final String displayTime = BookVisitBody.formatDisplayTime(
      hour: selectedTimeOfDay.hour,
      minute: selectedTimeOfDay.minute,
    );
    final VisitTimeSlotContent selectedTime = VisitTimeSlotContent(
      label: displayTime,
      visitTime: BookVisitBody.formatApiTime(
        hour: selectedTimeOfDay.hour,
        minute: selectedTimeOfDay.minute,
      ),
    );

    await context.read<BookVisitCubit>().bookVisit(
      propertyId: _property.id,
      visitDate: selectedDay.visitDate,
      visitHour: selectedTimeOfDay.hour,
      visitMinute: selectedTimeOfDay.minute,
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
          _clearTimeAfterConflict();
        }
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    return BlocProvider<BookVisitCubit>.value(
      value: _bookVisitCubit,
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
                ),
                Expanded(
                  child: BookVisitForm(
                    property: _property,
                    days: _days,
                    selectedDayIndex: _selectedDayIndex,
                    selectedTime: _selectedTime,
                    noteController: _noteController,
                    onDaySelected: (index) {
                      setState(() => _selectedDayIndex = index);
                    },
                    onTimeSelected: (time) {
                      setState(() => _selectedTime = time);
                    },
                    onConfirmPressed: _confirmVisit,
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
