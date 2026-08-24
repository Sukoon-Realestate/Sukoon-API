part of '../../../imports.dart';

class BookVisitForm extends StatelessWidget {
  const BookVisitForm({
    super.key,
    required this.property,
    required this.days,
    required this.timeSlots,
    required this.selectedDayIndex,
    required this.selectedTimeIndex,
    required this.noteController,
    required this.onDaySelected,
    required this.onTimeSelected,
    required this.onConfirmPressed,
  });

  final VisitPropertyContent property;
  final List<VisitDayContent> days;
  final List<VisitTimeSlotContent> timeSlots;
  final int selectedDayIndex;
  final int selectedTimeIndex;
  final TextEditingController noteController;
  final ValueChanged<int> onDaySelected;
  final ValueChanged<int> onTimeSelected;
  final Future<void> Function(BuildContext context) onConfirmPressed;

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      padding: EdgeInsets.fromLTRB(20.w, 0, 20.w, 24.h),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          VisitPropertySummaryCard(property: property),
          18.szH,
          _BookVisitSectionTitle(LocaleKeys.tenantVisitChooseDay),
          10.szH,
          SizedBox(
            height: 74.h,
            child: ListView.separated(
              scrollDirection: Axis.horizontal,
              itemBuilder: (context, index) {
                return VisitDayChip(
                  day: days[index],
                  isSelected: selectedDayIndex == index,
                  onPressed: () => onDaySelected(index),
                );
              },
              separatorBuilder: (context, index) => 8.szW,
              itemCount: days.length,
            ),
          ),
          20.szH,
          _BookVisitSectionTitle(LocaleKeys.tenantVisitChooseTime),
          10.szH,
          GridView.builder(
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
              crossAxisCount: 3,
              childAspectRatio: 2.55,
              crossAxisSpacing: 8.w,
              mainAxisSpacing: 8.h,
            ),
            itemCount: timeSlots.length,
            itemBuilder: (context, index) {
              final VisitTimeSlotContent slot = timeSlots[index];
              return VisitTimeChip(
                slot: slot,
                isSelected: selectedTimeIndex == index,
                onPressed: slot.isAvailable
                    ? () => onTimeSelected(index)
                    : null,
              );
            },
          ),
          22.szH,
          _BookVisitSectionTitle(LocaleKeys.tenantVisitNoteLabel),
          10.szH,
          Container(
            height: 80.h,
            padding: EdgeInsets.symmetric(horizontal: 14.w),
            decoration: BoxDecoration(
              color: AppColors.white,
              borderRadius: BorderRadius.circular(16.r),
              border: Border.all(color: AppColors.sokoonBorder),
            ),
            child: TextField(
              key: const ValueKey('visit-note-field'),
              controller: noteController,
              maxLines: 3,
              textAlign: TextAlign.start,
              style: TextStyle(
                color: AppColors.sokoonNavy,
                fontSize: 13.sp,
                fontWeight: FontWeight.w500,
                fontFamily: ConstantManager.fontFamily,
              ),
              decoration: InputDecoration(
                hintText: LocaleKeys.tenantVisitNoteHint,
                hintStyle: TextStyle(
                  color: AppColors.navyAlpha50,
                  fontSize: 13.sp,
                  fontFamily: ConstantManager.fontFamily,
                ),
                border: InputBorder.none,
              ),
            ),
          ),
          16.szH,
          const VisitPrivacyBanner(),
          16.szH,
          AppLoadingButton(
            key: const ValueKey('visit-confirm-request'),
            asyncCall: onConfirmPressed,
            title: LocaleKeys.tenantVisitConfirmRequest,
            buttonColor: AppColors.sokoonTeal,
            textColor: AppColors.white,
            borderRadius: 14.r,
            height: 50.h,
            fontSize: 15.sp,
            fontWeight: FontWeight.w900,
          ),
        ],
      ),
    );
  }
}

class _BookVisitSectionTitle extends StatelessWidget {
  const _BookVisitSectionTitle(this.title);

  final String title;

  @override
  Widget build(BuildContext context) {
    return AppText(
      title,
      color: AppColors.sokoonNavy,
      fontSize: 14.sp,
      fontWeight: FontWeight.w900,
      maxLines: 1,
    );
  }
}
