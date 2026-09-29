part of '../../../imports.dart';

class OwnerAvailabilityContent extends StatelessWidget {
  const OwnerAvailabilityContent({
    super.key,
    required this.days,
    required this.slots,
    required this.slotStates,
    required this.selectedDayIndex,
    required this.onDaySelected,
    required this.onTimePressed,
    required this.onSavePressed,
  });

  final List<OwnerAvailabilityDayContent> days;
  final List<OwnerAvailabilitySlotBody> slots;
  final List<OwnerAvailabilitySlotState> slotStates;
  final int selectedDayIndex;
  final ValueChanged<int> onDaySelected;
  final ValueChanged<int> onTimePressed;
  final Future<void> Function() onSavePressed;

  @override
  Widget build(BuildContext context) {
    final OwnerAvailabilityDayContent selectedDay = days[selectedDayIndex];

    return SingleChildScrollView(
      padding: EdgeInsets.fromLTRB(20.w, 2.h, 20.w, 24.h),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          AppText(
            LocaleKeys.ownerAvailabilityDescription,
            color: AppColors.sokoonGray,
            fontSize: 14.sp,
            fontWeight: FontWeight.w400,
          ),
          16.szH,
          SingleChildScrollView(
            scrollDirection: Axis.horizontal,
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                for (int index = 0; index < days.length; index++) ...[
                  if (index > 0) 6.szW,
                  OwnerAvailabilityDayChip(
                    day: days[index],
                    isSelected: selectedDayIndex == index,
                    onPressed: () => onDaySelected(index),
                  ),
                ],
              ],
            ),
          ),
          18.szH,
          AppText(
            _ownerAvailabilityDateLabel(context, selectedDay),
            color: AppColors.sokoonNavy,
            fontSize: 14.sp,
            fontWeight: FontWeight.w700,
          ),
          12.szH,
          LayoutBuilder(
            builder: (context, constraints) {
              final int columns = SokounLayout.columns(
                context,
                constraints.maxWidth,
                minimumWidth: 76,
                maximum: 6,
                gap: 8,
              );
              final double chipWidth =
                  (constraints.maxWidth - (columns - 1) * 8) / columns;
              return Wrap(
                spacing: 8.w,
                runSpacing: 8.h,
                children: [
                  for (int index = 0; index < slots.length; index++)
                    SizedBox(
                      width: chipWidth,
                      child: OwnerAvailabilityTimeChip(
                        label: _ownerAvailabilityTimeLabel(
                          context,
                          slots[index].time,
                        ),
                        state: slotStates[index],
                        onPressed: () => onTimePressed(index),
                      ),
                    ),
                ],
              );
            },
          ),
          18.szH,
          const OwnerAvailabilityLegend(),
          18.szH,
          AppLoadingButton(
            asyncCall: (_) => onSavePressed(),
            title: LocaleKeys.ownerAvailabilitySave,
            buttonColor: AppColors.sokoonTeal,
            textColor: AppColors.white,
            borderRadius: 14.r,
            height: 52.h,
            fontSize: 14.sp,
            fontWeight: FontWeight.w700,
          ),
        ],
      ),
    );
  }
}

String _ownerAvailabilityDateLabel(
  BuildContext context,
  OwnerAvailabilityDayContent day,
) {
  final DateTime? date = day.dateValue;
  if (date == null) {
    return day.localizedWeekday;
  }
  final MaterialLocalizations localizations = MaterialLocalizations.of(context);
  return '${day.localizedWeekday} ${localizations.formatDecimal(date.day)} '
      '${localizations.formatMonthYear(date)}';
}

String _ownerAvailabilityTimeLabel(BuildContext context, String value) {
  final List<String> parts = value.split(':');
  if (parts.length < 2) {
    return value;
  }
  final int? hour = int.tryParse(parts[0]);
  final int? minute = int.tryParse(parts[1]);
  if (hour == null || minute == null) {
    return value;
  }
  return MaterialLocalizations.of(
    context,
  ).formatTimeOfDay(TimeOfDay(hour: hour, minute: minute));
}
