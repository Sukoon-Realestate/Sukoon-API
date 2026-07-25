part of '../../imports.dart';

class OwnerAvailabilityScreen extends StatefulWidget {
  const OwnerAvailabilityScreen({super.key});

  @override
  State<OwnerAvailabilityScreen> createState() =>
      _OwnerAvailabilityScreenState();
}

class _OwnerAvailabilityScreenState extends State<OwnerAvailabilityScreen> {
  final Map<String, OwnerAvailabilitySlotState> _slotStates = {};
  int _selectedDayIndex = 1;

  List<OwnerAvailabilityDayContent> get _days =>
      OwnerVisitCalendarContent.availabilityDays;

  List<String> get _times => OwnerVisitCalendarContent.availabilityTimes;

  @override
  void initState() {
    super.initState();
    _initializeSlots();
  }

  void _initializeSlots() {
    for (int dayIndex = 0; dayIndex < _days.length; dayIndex++) {
      for (int timeIndex = 0; timeIndex < _times.length; timeIndex++) {
        final bool isBooked =
            (dayIndex == 0 && timeIndex == 0) ||
            (dayIndex == 1 && timeIndex == 5) ||
            (dayIndex == 2 && timeIndex == 1);
        final bool isAvailable = timeIndex % 3 == 0;
        _slotStates[_slotKey(dayIndex, timeIndex)] = isBooked
            ? OwnerAvailabilitySlotState.booked
            : isAvailable
            ? OwnerAvailabilitySlotState.available
            : OwnerAvailabilitySlotState.unspecified;
      }
    }
  }

  String _slotKey(int dayIndex, int timeIndex) => '$dayIndex-$timeIndex';

  OwnerAvailabilitySlotState _slotState(int timeIndex) {
    return _slotStates[_slotKey(_selectedDayIndex, timeIndex)] ??
        OwnerAvailabilitySlotState.unspecified;
  }

  void _selectDay(int index) => setState(() => _selectedDayIndex = index);

  void _toggleSlot(int timeIndex) {
    final String key = _slotKey(_selectedDayIndex, timeIndex);
    final OwnerAvailabilitySlotState state =
        _slotStates[key] ?? OwnerAvailabilitySlotState.unspecified;
    if (state.isBooked) {
      return;
    }

    setState(() {
      _slotStates[key] = state.isAvailable
          ? OwnerAvailabilitySlotState.unspecified
          : OwnerAvailabilitySlotState.available;
    });
  }

  void _saveAvailability() => Go.back(true);

  @override
  Widget build(BuildContext context) {
    return Directionality(
      textDirection: TextDirection.rtl,
      child: Scaffold(
        backgroundColor: AppColors.scaffoldBackground,
        body: SafeArea(
          child: Column(
            children: [
              VisitHeader(
                title: LocaleKeys.ownerAvailabilityTitle,
                backKey: const ValueKey('owner-availability-back'),
                onBackPressed: () => Go.back(),
              ),
              Expanded(
                child: OwnerAvailabilityContent(
                  days: _days,
                  times: _times,
                  selectedDayIndex: _selectedDayIndex,
                  slotState: _slotState,
                  onDaySelected: _selectDay,
                  onTimePressed: _toggleSlot,
                  onSavePressed: _saveAvailability,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
