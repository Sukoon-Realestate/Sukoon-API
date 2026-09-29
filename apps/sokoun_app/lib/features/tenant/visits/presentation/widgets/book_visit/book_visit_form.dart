part of '../../../imports.dart';

class BookVisitForm extends StatelessWidget {
  const BookVisitForm({
    super.key,
    required this.property,
    required this.days,
    required this.selectedDayIndex,
    required this.selectedTime,
    required this.noteController,
    required this.onDaySelected,
    required this.onTimeSelected,
    required this.onConfirmPressed,
  });

  final VisitPropertyContent property;
  final List<VisitDayContent> days;
  final int selectedDayIndex;
  final TimeOfDay? selectedTime;
  final TextEditingController noteController;
  final ValueChanged<int> onDaySelected;
  final ValueChanged<TimeOfDay> onTimeSelected;
  final Future<void> Function(BuildContext context) onConfirmPressed;

  @override
  Widget build(BuildContext context) {
    final bool canConfirm = days.isNotEmpty && selectedTime != null;
    return SingleChildScrollView(
      padding: EdgeInsets.fromLTRB(20.w, 0, 20.w, 24.h),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          VisitPropertySummaryCard(property: property),
          18.szH,
          _BookVisitSectionTitle(LocaleKeys.tenantVisitChooseDay),
          10.szH,
          if (days.isEmpty)
            AppText(
              LocaleKeys.tenantVisitNoAvailableDays,
              color: AppColors.sokoonMuted,
              fontSize: 12.sp,
            )
          else
            SingleChildScrollView(
              scrollDirection: Axis.horizontal,
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  for (int index = 0; index < days.length; index++) ...[
                    if (index > 0) 8.szW,
                    VisitDayChip(
                      day: days[index],
                      isSelected: selectedDayIndex == index,
                      onPressed: () => onDaySelected(index),
                    ),
                  ],
                ],
              ),
            ),
          20.szH,
          _BookVisitSectionTitle(LocaleKeys.tenantVisitChooseTime),
          10.szH,
          VisitTimePickerField(
            selectedTime: selectedTime,
            onTimeSelected: days.isEmpty ? null : onTimeSelected,
          ),
          22.szH,
          _BookVisitSectionTitle(LocaleKeys.tenantVisitNoteLabel),
          10.szH,
          Container(
            constraints: BoxConstraints(minHeight: 80.h),
            padding: EdgeInsets.symmetric(horizontal: 14.w),
            decoration: BoxDecoration(
              color: AppColors.white,
              borderRadius: BorderRadius.circular(16.r),
              border: Border.all(color: AppColors.sokoonBorder),
            ),
            child: TextField(
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
          IgnorePointer(
            ignoring: !canConfirm,
            child: Opacity(
              opacity: canConfirm ? 1 : .45,
              child: AppLoadingButton(
                asyncCall: onConfirmPressed,
                title: LocaleKeys.tenantVisitConfirmRequest,
                buttonColor: AppColors.sokoonTeal,
                textColor: AppColors.white,
                borderRadius: 14.r,
                height: 50.h,
                fontSize: 15.sp,
                fontWeight: FontWeight.w700,
              ),
            ),
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
      fontWeight: FontWeight.w700,
      maxLines: 1,
    );
  }
}
