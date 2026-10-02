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
  late final OwnerAvailabilityCubit _availabilityCubit, _saveCubit;
  late DateTime _weekStart, _requestedDate;
  // Selecting a date or editing slots intentionally recomposes the schedule grid.
  final Map<String, List<OwnerAvailabilitySlotContent>> _drafts = {};
  final ValueNotifier<bool> _isSaving = ValueNotifier(false);
  int _selectedDayIndex = 0;
  bool _saved = false;

  List<OwnerAvailabilityDayContent> get _days => _availabilityCubit.data.days;
  String get _selectedDate => _days[_selectedDayIndex].date;
  List<OwnerAvailabilitySlotContent> get _slots =>
      _drafts[_selectedDate] ?? _days[_selectedDayIndex].slots;

  @override
  void initState() {
    super.initState();
    _requestedDate = widget.availabilityStartDate;
    _weekStart = OwnerAvailabilityScheduleContent.startOfWeek(_requestedDate);
    _availabilityCubit = OwnerAvailabilityCubit();
    _saveCubit = OwnerAvailabilityCubit();
    _loadAvailability();
  }

  Future<void> _loadAvailability() => _availabilityCubit.loadAvailability(
    ownerPropertyId: widget.ownerPropertyId,
    weekStart: _weekStart,
    onLoaded: (schedule) {
      if (!mounted) return;
      final requested = OwnerVisitCalendarContent.formatDate(_requestedDate);
      final index = schedule.days.indexWhere((day) => day.date == requested);
      _selectedDayIndex = index < 0 ? 0 : index;
    },
  );
  @override
  void dispose() {
    _availabilityCubit.close();
    _saveCubit.close();
    _isSaving.dispose();
    super.dispose();
  }

  void _selectDay(int index) {
    if (_isSaving.value) return;
    setState(() => _selectedDayIndex = index);
  }

  void _changeWeek(int offset) {
    if (_availabilityCubit.isLoading || _isSaving.value) return;
    _weekStart = DateTime(
      _weekStart.year,
      _weekStart.month,
      _weekStart.day + offset * 7,
    );
    _requestedDate = _weekStart;
    _loadAvailability();
  }

  void _toggleSlot(int index) {
    if (_isSaving.value || _slots[index].slotState.isBooked) return;
    final slots = List<OwnerAvailabilitySlotContent>.of(_slots);
    slots[index] = slots[index].copyWith(
      isEnabled: !slots[index].isEnabled,
      state: slots[index].isEnabled ? 'unspecified' : 'available',
    );
    setState(() => _drafts[_selectedDate] = slots);
  }

  Future<void> _addTime() async {
    if (_isSaving.value || _days.isEmpty) return;
    final date = _selectedDate;
    final selected = await showTimePicker(
      context: context,
      initialTime: const TimeOfDay(hour: 12, minute: 0),
    );
    if (selected == null ||
        !mounted ||
        _isSaving.value ||
        date != _selectedDate) {
      return;
    }
    final time =
        '${selected.hour.toString().padLeft(2, '0')}:'
        '${selected.minute.toString().padLeft(2, '0')}:00';
    if (_slots.any(
      (slot) => Validators.normalizeVisitTime(slot.time) == time,
    )) {
      MessageUtils.showSnackBar(
        LocaleKeys.ownerAvailabilityTimeAlreadyExists,
        context: context,
      );
      return;
    }
    final slots = [
      ..._slots,
      OwnerAvailabilitySlotContent(
        id: '',
        time: time,
        isEnabled: true,
        state: 'available',
        visit: null,
      ),
    ]..sort((a, b) => a.time.compareTo(b.time));
    setState(() => _drafts[date] = slots);
  }

  Future<void> _saveAvailability() async {
    if (_isSaving.value || _days.isEmpty) return;
    _isSaving.value = true;
    try {
      final entries = _drafts.entries.toList();
      if (entries.isEmpty && _slots.isNotEmpty) {
        entries.add(MapEntry(_selectedDate, _slots));
      }
      for (final entry in entries) {
        final saved = await _saveCubit.saveAvailability(
          ownerPropertyId: widget.ownerPropertyId,
          body: OwnerAvailabilitySaveBody(
            availabilityDate: entry.key,
            slots: entry.value
                .map(
                  (slot) => OwnerAvailabilitySlotBody(
                    time: Validators.normalizeVisitTime(slot.time),
                    isEnabled: slot.isEnabled,
                  ),
                )
                .toList(growable: false),
          ),
        );
        if (!mounted) return;
        if (!saved) return;
        _drafts.remove(entry.key);
        _availabilityCubit.updateData(
          _availabilityCubit.data.copyWith(
            days: _days
                .map(
                  (day) => day.date == entry.key
                      ? day.copyWith(slots: entry.value)
                      : day,
                )
                .toList(growable: false),
          ),
        );
      }
      if (entries.isNotEmpty && mounted) {
        _saved = true;
        Go.back(true);
      }
    } finally {
      if (mounted) _isSaving.value = false;
    }
  }

  @override
  Widget build(BuildContext context) => BlocProvider.value(
    value: _availabilityCubit,
    child: UnsavedChangesGuard(
      hasChanges: () => !_saved && _drafts.isNotEmpty,
      isSaving: () => _isSaving.value,
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
                shimmerBuilder: (_) => const SizedBox.expand(),
                builder: (schedule) => schedule.days.isEmpty
                    ? const OwnerAvailabilityEmptyState()
                    : ValueListenableBuilder<bool>(
                        valueListenable: _isSaving,
                        builder: (context, saving, _) =>
                            OwnerAvailabilityContent(
                              days: _days,
                              slots: _slots
                                  .map(
                                    (slot) => OwnerAvailabilitySlotBody(
                                      time: slot.time,
                                      isEnabled: slot.isEnabled,
                                    ),
                                  )
                                  .toList(growable: false),
                              slotStates: _slots
                                  .map((slot) => slot.slotState)
                                  .toList(growable: false),
                              selectedDayIndex: _selectedDayIndex,
                              onDaySelected: _selectDay,
                              onTimePressed: _toggleSlot,
                              onSavePressed: _saveAvailability,
                              onAddTimePressed: _addTime,
                              onPreviousWeek: () => _changeWeek(-1),
                              onNextWeek: () => _changeWeek(1),
                              isSaving: saving,
                              canSave: _drafts.isNotEmpty || _slots.isNotEmpty,
                            ),
                      ),
              ),
        ),
      ),
    ),
  );
}
