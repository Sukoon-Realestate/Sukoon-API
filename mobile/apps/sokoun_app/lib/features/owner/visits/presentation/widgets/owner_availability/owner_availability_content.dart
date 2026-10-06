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
    this.onAddTimePressed,
    this.onPreviousWeek,
    this.onNextWeek,
    this.isSaving = false,
    this.canSave,
    this.dayFieldKey,
  });

  final List<OwnerAvailabilityDayContent> days;
  final List<OwnerAvailabilitySlotBody> slots;
  final List<OwnerAvailabilitySlotState> slotStates;
  final int selectedDayIndex;
  final ValueChanged<int> onDaySelected;
  final ValueChanged<int> onTimePressed;
  final Future<void> Function() onSavePressed;
  final VoidCallback? onAddTimePressed, onPreviousWeek, onNextWeek;
  final bool isSaving;
  final bool? canSave;
  final GlobalKey? dayFieldKey;

  @override
  Widget build(BuildContext context) {
    final OwnerAvailabilityDayContent selectedDay = days[selectedDayIndex];

    return SingleChildScrollView(
      padding: EdgeInsets.fromLTRB(20.w, 2.h, 20.w, 24.h),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          if (onPreviousWeek != null || onNextWeek != null)
            Row(
              children: [
                IconButton(
                  tooltip: LocaleKeys.ownerAvailabilityPreviousWeek,
                  onPressed: isSaving ? null : onPreviousWeek,
                  icon: Icon(
                    Directionality.of(context) == TextDirection.rtl
                        ? Icons.chevron_right_rounded
                        : Icons.chevron_left_rounded,
                  ),
                ),
                Expanded(
                  child: AppText(
                    '${days.first.date} – ${days.last.date}',
                    textAlign: TextAlign.center,
                    style: AppTextStyles.bold13,
                  ),
                ),
                IconButton(
                  tooltip: LocaleKeys.ownerAvailabilityNextWeek,
                  onPressed: isSaving ? null : onNextWeek,
                  icon: Icon(
                    Directionality.of(context) == TextDirection.rtl
                        ? Icons.chevron_left_rounded
                        : Icons.chevron_right_rounded,
                  ),
                ),
              ],
            ),
          AppText(
            LocaleKeys.ownerAvailabilityCairoTime,
            style: AppTextStyles.regular12,
            textAlign: TextAlign.center,
          ),
          12.szH,
          AppText(
            LocaleKeys.ownerAvailabilityDescription,
            style: AppTextStyles.regular14.copyWith(
              color: context.appColor(AppColors.sokoonGray),
              fontSize: 14.sp,
              height: 1.45,
            ),
          ),
          16.szH,
          SingleChildScrollView(
            key: dayFieldKey,
            scrollDirection: Axis.horizontal,
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              spacing: 6.w,
              children: [
                for (int index = 0; index < days.length; index++)
                  OwnerAvailabilityDayChip(
                    day: days[index],
                    isSelected: selectedDayIndex == index,
                    onPressed: () => onDaySelected(index),
                  ),
              ],
            ),
          ),
          18.szH,
          SokounContentTransition(
            identity: selectedDay.dateValue,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                AppText(
                  _ownerAvailabilityDateLabel(context, selectedDay),
                  style: AppTextStyles.bold14.copyWith(
                    color: context.appColor(AppColors.sokoonNavy),
                    fontSize: 14.sp,
                    height: 1.45,
                  ),
                ),
                12.szH,
                if (slots.isEmpty)
                  const OwnerAvailabilityEmptyState()
                else
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
              ],
            ),
          ),
          const OwnerAvailabilityLegend(),
          if (onAddTimePressed != null)
            TextButton.icon(
              onPressed: isSaving ? null : onAddTimePressed,
              icon: const Icon(Icons.add_rounded),
              label: AppText(LocaleKeys.ownerAvailabilityAddTime),
            ),
          18.szH,
          if (canSave ?? slots.isNotEmpty)
            AppLoadingButton(
              asyncCall: (_) => onSavePressed(),
              title: LocaleKeys.ownerAvailabilitySave,
              buttonColor: context.appColor(
                AppColors.sokoonTeal,
                surface: true,
              ),
              textColor: AppColors.white,
              borderRadius: 14.r,
              height: 52.h,
              textStyle: AppTextStyles.bold14.copyWith(
                fontSize: 14.sp,
                height: 1.45,
              ),
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
