part of '../../imports.dart';

class OwnerAvailabilityScreen extends StatefulWidget {
  const OwnerAvailabilityScreen({
    super.key,
    required this.ownerPropertyId,
    required this.availabilityStartDate,
  });

  final String ownerPropertyId;
  final DateTime availabilityStartDate;

  @override
  State<OwnerAvailabilityScreen> createState() =>
      _OwnerAvailabilityScreenState();
}

class _OwnerAvailabilityScreenState extends State<OwnerAvailabilityScreen> {
  // Day and slot changes intentionally recompose the complete schedule grid.
  final Map<String, OwnerAvailabilitySlotState> _slotStates = {};
  late final OwnerAvailabilityCubit _availabilityCubit;
  late final List<OwnerAvailabilityDayContent> _days;
  final List<OwnerAvailabilitySlotBody> _slots =
      OwnerAvailabilityDefaults.slots;
  late int _selectedDayIndex;

  @override
  void initState() {
    super.initState();
    _availabilityCubit = OwnerAvailabilityCubit();
    final DateTime selectedDate = DateUtils.dateOnly(
      widget.availabilityStartDate,
    );
    final DateTime weekStart = selectedDate.subtract(
      Duration(days: selectedDate.weekday - DateTime.monday),
    );
    _days = List<OwnerAvailabilityDayContent>.generate(
      DateTime.daysPerWeek,
      (index) => OwnerAvailabilityDayContent.fromDate(
        weekStart.add(Duration(days: index)),
      ),
      growable: false,
    );
    _selectedDayIndex = selectedDate.difference(weekStart).inDays;
    _initializeSlots();
  }

  @override
  void dispose() {
    _availabilityCubit.close();
    super.dispose();
  }

  void _initializeSlots() {
    for (int dayIndex = 0; dayIndex < _days.length; dayIndex++) {
      for (int timeIndex = 0; timeIndex < _slots.length; timeIndex++) {
        _slotStates[_slotKey(dayIndex, timeIndex)] =
            OwnerAvailabilitySlotState.unspecified;
      }
    }
  }

  String _slotKey(int dayIndex, int timeIndex) => '$dayIndex-$timeIndex';

  OwnerAvailabilitySlotState _slotState(int timeIndex) {
    return _slotStates[_slotKey(_selectedDayIndex, timeIndex)] ??
        OwnerAvailabilitySlotState.unspecified;
  }

  List<OwnerAvailabilitySlotState> get _selectedSlotStates {
    return List<OwnerAvailabilitySlotState>.generate(
      _slots.length,
      _slotState,
      growable: false,
    );
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

  Future<void> _saveAvailability() async {
    final OwnerAvailabilitySaveBody body = OwnerAvailabilitySaveBody(
      availabilityDate: _days[_selectedDayIndex].date,
      slots: List<OwnerAvailabilitySlotBody>.generate(
        _slots.length,
        (index) =>
            _slots[index].copyWith(isEnabled: _slotState(index).isAvailable),
        growable: false,
      ),
    );
    final bool saved = await _availabilityCubit.saveAvailability(
      ownerPropertyId: widget.ownerPropertyId,
      body: body,
    );
    if (saved && mounted) {
      Go.back(true);
    }
  }

  @override
  Widget build(BuildContext context) {
    return BlocProvider<OwnerAvailabilityCubit>.value(
      value: _availabilityCubit,
      child: Scaffold(
        backgroundColor: AppColors.scaffoldBackground,
        body: SafeArea(
          child: Column(
            children: [
              VisitHeader(title: LocaleKeys.ownerAvailabilityTitle),
              Expanded(
                child: OwnerAvailabilityContent(
                  days: _days,
                  slots: _slots,
                  slotStates: _selectedSlotStates,
                  selectedDayIndex: _selectedDayIndex,
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
