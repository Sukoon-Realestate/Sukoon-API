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
  late final OwnerAvailabilityCubit _saveCubit;
  int _selectedDayIndex = 0;

  List<OwnerAvailabilityDayContent> get _days => _availabilityCubit.data.days;
  List<OwnerAvailabilitySlotContent> get _slots =>
      _days[_selectedDayIndex].slots;

  @override
  void initState() {
    super.initState();
    _availabilityCubit = OwnerAvailabilityCubit();
    _saveCubit = OwnerAvailabilityCubit();
    _loadAvailability();
  }

  Future<void> _loadAvailability() => _availabilityCubit.loadAvailability(
    ownerPropertyId: widget.ownerPropertyId,
    onLoaded: (schedule) {
      if (!mounted) return;
      _slotStates.clear();
      final String requestedDate = OwnerVisitCalendarContent.formatDate(
        widget.availabilityStartDate,
      );
      final int requestedIndex = schedule.days.indexWhere(
        (day) => day.date == requestedDate,
      );
      _selectedDayIndex = requestedIndex < 0 ? 0 : requestedIndex;
    },
  );

  @override
  void dispose() {
    _availabilityCubit.close();
    _saveCubit.close();
    super.dispose();
  }

  String _slotKey(int timeIndex) =>
      '${_days[_selectedDayIndex].date}_${_slots[timeIndex].time}';

  OwnerAvailabilitySlotState _slotState(int timeIndex) =>
      _slotStates[_slotKey(timeIndex)] ?? _slots[timeIndex].slotState;

  void _selectDay(int index) {
    if (_saveCubit.isLoading) return;
    setState(() => _selectedDayIndex = index);
  }

  void _toggleSlot(int timeIndex) {
    if (_saveCubit.isLoading || _slotState(timeIndex).isBooked) return;
    final String key = _slotKey(timeIndex);
    final OwnerAvailabilitySlotState state = _slotState(timeIndex);
    setState(() {
      _slotStates[key] = state.isAvailable
          ? OwnerAvailabilitySlotState.unspecified
          : OwnerAvailabilitySlotState.available;
    });
  }

  Future<void> _saveAvailability() async {
    if (_days.isEmpty || _slots.isEmpty || _saveCubit.isLoading) return;
    final OwnerAvailabilitySaveBody body = OwnerAvailabilitySaveBody(
      availabilityDate: _days[_selectedDayIndex].date,
      slots: List<OwnerAvailabilitySlotBody>.generate(
        _slots.length,
        (index) => OwnerAvailabilitySlotBody(
          time: _slots[index].time,
          isEnabled: _slotState(index).isBooked
              ? _slots[index].isEnabled
              : _slotState(index).isAvailable,
        ),
        growable: false,
      ),
    );
    final bool saved = await _saveCubit.saveAvailability(
      ownerPropertyId: widget.ownerPropertyId,
      body: body,
    );
    if (saved && mounted) Go.back(true);
  }

  @override
  Widget build(BuildContext context) =>
      BlocProvider<OwnerAvailabilityCubit>.value(
        value: _availabilityCubit,
        child: AppScaffold(
          title: LocaleKeys.ownerAvailabilityTitle,
          showBackButton: true,
          backgroundColor: AppColors.scaffoldBackground,
          body: SafeArea(
            child:
                StatusBuilder<
                  OwnerAvailabilityCubit,
                  OwnerAvailabilityScheduleContent
                >.withShimmer(
                  initialDataForShimmer:
                      const OwnerAvailabilityScheduleContent.initial(),
                  onRetry: _loadAvailability,
                  shimmerBuilder: (_) => const OwnerAvailabilityEmptyState(),
                  builder: (schedule) => schedule.days.isEmpty
                      ? const OwnerAvailabilityEmptyState()
                      : OwnerAvailabilityContent(
                          days: _days,
                          slots: [
                            for (final slot in _slots)
                              OwnerAvailabilitySlotBody(
                                time: slot.time,
                                isEnabled: slot.isEnabled,
                              ),
                          ],
                          slotStates: List<OwnerAvailabilitySlotState>.generate(
                            _slots.length,
                            _slotState,
                            growable: false,
                          ),
                          selectedDayIndex: _selectedDayIndex,
                          onDaySelected: _selectDay,
                          onTimePressed: _toggleSlot,
                          onSavePressed: _saveAvailability,
                        ),
                ),
          ),
        ),
      );
}
