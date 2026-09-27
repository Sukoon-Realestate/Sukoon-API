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
  final ValueNotifier<({int dayIndex, TimeOfDay? time})> _selection =
      ValueNotifier<({int dayIndex, TimeOfDay? time})>((
        dayIndex: 0,
        time: null,
      ));

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
    _selection.dispose();
    _bookVisitCubit.close();
    super.dispose();
  }

  void _clearTimeAfterConflict() {
    if (!mounted) return;
    _selection.value = (dayIndex: _selection.value.dayIndex, time: null);
  }

  Future<void> _confirmVisit(BuildContext context) async {
    if (!WorkspaceNavigation.isAuthenticated) {
      await WorkspaceNavigation.open(
        workspace: AppWorkspace.tenant,
        showLoginSheet: true,
        detail: () => Go.to(BookVisitScreen(property: _property)),
      );
      return;
    }
    final ({int dayIndex, TimeOfDay? time}) selection = _selection.value;
    final TimeOfDay? selectedTimeOfDay = selection.time;
    if (_days.isEmpty ||
        selectedTimeOfDay == null ||
        selection.dayIndex >= _days.length) {
      return;
    }

    final VisitDayContent selectedDay = _days[selection.dayIndex];
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
      ownerId: _property.ownerId,
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
      child: Scaffold(
        backgroundColor: AppColors.scaffoldBackground,
        body: SafeArea(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              VisitHeader(title: LocaleKeys.tenantVisitBookTitle),
              Expanded(
                child:
                    ValueListenableBuilder<({int dayIndex, TimeOfDay? time})>(
                      valueListenable: _selection,
                      builder: (context, selection, _) => BookVisitForm(
                        property: _property,
                        days: _days,
                        selectedDayIndex: selection.dayIndex,
                        selectedTime: selection.time,
                        noteController: _noteController,
                        onDaySelected: (index) => _selection.value = (
                          dayIndex: index,
                          time: selection.time,
                        ),
                        onTimeSelected: (time) => _selection.value = (
                          dayIndex: selection.dayIndex,
                          time: time,
                        ),
                        onConfirmPressed: _confirmVisit,
                      ),
                    ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
