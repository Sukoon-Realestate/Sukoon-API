part of '../../../imports.dart';

class OwnerCalendarContent extends StatelessWidget {
  const OwnerCalendarContent({
    super.key,
    required this.calendar,
    required this.selectedDate,
    required this.onDaySelected,
    required this.onAvailabilityPressed,
  });

  final OwnerVisitCalendarContent calendar;
  final DateTime selectedDate;
  final ValueChanged<DateTime> onDaySelected;
  final VoidCallback? onAvailabilityPressed;

  @override
  Widget build(BuildContext context) {
    final List<int?> monthDays = calendar.monthDays;
    return SingleChildScrollView(
      padding: EdgeInsets.fromLTRB(16.w, 16.h, 16.w, 24.h),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Container(
            padding: EdgeInsets.all(12.r),
            decoration: BoxDecoration(
              color: AppColors.white,
              borderRadius: BorderRadius.circular(18.r),
              border: Border.all(color: AppColors.sokoonBorder),
            ),
            child: Column(
              children: [
                Row(
                  children: [
                    for (final String day
                        in OwnerVisitCalendarContent.weekdayHeaders)
                      Expanded(
                        child: AppText(
                          day,
                          color: AppColors.sokoonGray,
                          fontSize: 11.sp,
                          fontWeight: FontWeight.w700,
                          textAlign: TextAlign.center,
                        ),
                      ),
                  ],
                ),
                8.szH,
                GridView.builder(
                  shrinkWrap: true,
                  physics: const NeverScrollableScrollPhysics(),
                  gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
                    crossAxisCount: 7,
                    mainAxisSpacing: 4.h,
                    crossAxisSpacing: 4.w,
                    childAspectRatio: 1.02,
                  ),
                  itemBuilder: (context, index) {
                    final int? day = monthDays[index];
                    return OwnerCalendarDay(
                      day: day,
                      isSelected: day == selectedDate.day,
                      hasVisit: day != null && calendar.hasVisitsOn(day),
                      onPressed: day == null
                          ? null
                          : () => onDaySelected(
                              DateTime(calendar.year, calendar.month, day),
                            ),
                    );
                  },
                  itemCount: monthDays.length,
                ),
              ],
            ),
          ),
          18.szH,
          AppText(
            '${LocaleKeys.ownerCalendarVisitsOnDay} ${selectedDate.day}',
            color: AppColors.sokoonGray,
            fontSize: 13.sp,
            fontWeight: FontWeight.w800,
          ),
          12.szH,
          for (final OwnerCalendarVisitContent visit in calendar.visits) ...[
            OwnerCalendarVisitCard(visit: visit),
            10.szH,
          ],
          10.szH,
          DefaultButton(
            onTap: onAvailabilityPressed,
            title: LocaleKeys.ownerCalendarManageAvailability,
            color: AppColors.gold,
            textColor: AppColors.white,
            borderRadius: BorderRadius.circular(14.r),
            height: 50.h,
            fontSize: 14.sp,
            fontWeight: FontWeight.w700,
          ),
        ],
      ),
    );
  }
}
