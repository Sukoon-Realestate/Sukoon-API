part of '../../../imports.dart';

class OwnerAvailabilityContent extends StatelessWidget {
  const OwnerAvailabilityContent({
    super.key,
    required this.days,
    required this.times,
    required this.selectedDayIndex,
    required this.slotState,
    required this.onDaySelected,
    required this.onTimePressed,
    required this.onSavePressed,
  });

  final List<OwnerAvailabilityDayContent> days;
  final List<String> times;
  final int selectedDayIndex;
  final OwnerAvailabilitySlotState Function(int index) slotState;
  final ValueChanged<int> onDaySelected;
  final ValueChanged<int> onTimePressed;
  final VoidCallback onSavePressed;

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
          SizedBox(
            height: 60.h,
            child: ListView.separated(
              scrollDirection: Axis.horizontal,
              itemBuilder: (context, index) {
                return OwnerAvailabilityDayChip(
                  key: ValueKey('owner-availability-day-$index'),
                  day: days[index],
                  isSelected: index == selectedDayIndex,
                  onPressed: () => onDaySelected(index),
                );
              },
              separatorBuilder: (context, index) => 6.szW,
              itemCount: days.length,
            ),
          ),
          18.szH,
          AppText(
            '${selectedDay.weekday} ${selectedDay.day} ${LocaleKeys.ownerAvailabilityMonthJune}',
            color: AppColors.sokoonNavy,
            fontSize: 14.sp,
            fontWeight: FontWeight.w900,
          ),
          12.szH,
          LayoutBuilder(
            builder: (context, constraints) {
              final double chipWidth = (constraints.maxWidth - 24.w) / 4;
              return Wrap(
                spacing: 8.w,
                runSpacing: 8.h,
                children: [
                  for (int index = 0; index < times.length; index++)
                    SizedBox(
                      width: chipWidth,
                      child: OwnerAvailabilityTimeChip(
                        key: ValueKey('owner-availability-time-$index'),
                        label: times[index],
                        state: slotState(index),
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
          DefaultButton(
            key: const ValueKey('owner-availability-save'),
            onTap: onSavePressed,
            title: LocaleKeys.ownerAvailabilitySave,
            color: AppColors.sokoonTeal,
            textColor: AppColors.white,
            borderRadius: BorderRadius.circular(14.r),
            height: 52.h,
            fontSize: 14.sp,
            fontWeight: FontWeight.w900,
          ),
        ],
      ),
    );
  }
}
