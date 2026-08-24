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
  late final List<VisitTimeSlotContent> _timeSlots;
  late final TextEditingController _noteController;
  late final BookVisitCubit _bookVisitCubit;
  int _selectedDayIndex = 1;
  int _selectedTimeIndex = 3;

  @override
  void initState() {
    super.initState();
    _property = widget.property ?? VisitPropertyContent.prototype();
    _days = TenantVisitsContent.days;
    _timeSlots = TenantVisitsContent.timeSlots;
    _noteController = TextEditingController();
    _bookVisitCubit = BookVisitCubit();
  }

  @override
  void dispose() {
    _noteController.dispose();
    _bookVisitCubit.close();
    super.dispose();
  }

  Future<void> _confirmVisit(BuildContext context) async {
    final VisitDayContent selectedDay = _days[_selectedDayIndex];
    final VisitTimeSlotContent selectedTime = _timeSlots[_selectedTimeIndex];

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
    );
  }

  @override
  Widget build(BuildContext context) {
    return BlocProvider.value(
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
                  onBackPressed: () => Go.back(),
                ),
                Expanded(
                  child: BookVisitForm(
                    property: _property,
                    days: _days,
                    timeSlots: _timeSlots,
                    selectedDayIndex: _selectedDayIndex,
                    selectedTimeIndex: _selectedTimeIndex,
                    noteController: _noteController,
                    onDaySelected: (index) {
                      setState(() => _selectedDayIndex = index);
                    },
                    onTimeSelected: (index) {
                      setState(() => _selectedTimeIndex = index);
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
