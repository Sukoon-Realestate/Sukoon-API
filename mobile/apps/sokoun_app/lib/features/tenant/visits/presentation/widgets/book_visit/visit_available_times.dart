part of '../../../imports.dart';

class VisitAvailableTimes extends StatelessWidget {
  const VisitAvailableTimes({
    super.key,
    required this.date,
    required this.slots,
    required this.selectedTime,
    required this.onSelected,
    this.isCached = false,
  });
  final String date;
  final List<VisitTimeSlotContent> slots;
  final TimeOfDay? selectedTime;
  final ValueChanged<TimeOfDay> onSelected;
  final bool isCached;

  @override
  Widget build(BuildContext context) {
    final available = slots
        .where(
          (slot) =>
              slot.isAvailable &&
              VisitScheduleRules.isFuture(date, slot.visitTime),
        )
        .toList(growable: false);
    if (available.isEmpty || isCached) {
      return Column(
        children: [
          Assets.lottie.noData.lottie(
            package: 'melos_core',
            width: 100,
            height: 90,
            repeat: false,
            animate: !MediaQuery.of(context).disableAnimations,
          ),
          AppText(
            isCached
                ? LocaleKeys.freeAvailabilityOffline
                : LocaleKeys.freeNoVisitTimes,
            textAlign: TextAlign.center,
          ),
        ],
      );
    }
    return Wrap(
      spacing: 8,
      runSpacing: 8,
      children: [
        for (final slot in available)
          Builder(
            builder: (context) {
              final time = VisitScheduleRules.time(slot.visitTime)!;
              final value = TimeOfDay(hour: time.hour, minute: time.minute);
              return ChoiceChip(
                label: AppText(value.format(context)),
                selected: selectedTime == value,
                onSelected: (_) => onSelected(value),
              );
            },
          ),
      ],
    );
  }
}
