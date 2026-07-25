part of '../../../imports.dart';

class OwnerCalendarContent extends StatelessWidget {
  const OwnerCalendarContent({
    super.key,
    required this.selectedDay,
    required this.onDaySelected,
    required this.onAvailabilityPressed,
  });

  final int selectedDay;
  final ValueChanged<int> onDaySelected;
  final VoidCallback onAvailabilityPressed;

  @override
  Widget build(BuildContext context) {
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
                    final int? day = OwnerVisitCalendarContent.monthDays[index];
                    return OwnerCalendarDay(
                      day: day,
                      isSelected: day == selectedDay,
                      hasVisit:
                          day != null &&
                          OwnerVisitCalendarContent.daysWithVisits.contains(
                            day,
                          ),
                      onPressed: day == null ? null : () => onDaySelected(day),
                    );
                  },
                  itemCount: OwnerVisitCalendarContent.monthDays.length,
                ),
              ],
            ),
          ),
          18.szH,
          AppText(
            '${LocaleKeys.ownerCalendarVisitsOnDay} $selectedDay',
            color: AppColors.sokoonGray,
            fontSize: 13.sp,
            fontWeight: FontWeight.w800,
          ),
          12.szH,
          for (final OwnerCalendarVisitContent visit
              in OwnerVisitCalendarContent.visits) ...[
            OwnerCalendarVisitCard(visit: visit),
            10.szH,
          ],
          10.szH,
          DefaultButton(
            key: const ValueKey('owner-open-availability'),
            onTap: onAvailabilityPressed,
            title: LocaleKeys.ownerCalendarManageAvailability,
            color: AppColors.gold,
            textColor: AppColors.white,
            borderRadius: BorderRadius.circular(14.r),
            height: 50.h,
            fontSize: 14.sp,
            fontWeight: FontWeight.w900,
          ),
        ],
      ),
    );
  }
}
