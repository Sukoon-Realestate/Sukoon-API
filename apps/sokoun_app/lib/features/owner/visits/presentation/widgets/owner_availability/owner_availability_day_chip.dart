part of '../../../imports.dart';

class OwnerAvailabilityDayChip extends StatelessWidget {
  const OwnerAvailabilityDayChip({
    super.key,
    required this.day,
    required this.isSelected,
    required this.onPressed,
  });

  final OwnerAvailabilityDayContent day;
  final bool isSelected;
  final VoidCallback onPressed;

  @override
  Widget build(BuildContext context) {
    return Material(
      color: AppColors.transparent,
      child: InkWell(
        onTap: onPressed,
        borderRadius: BorderRadius.circular(16.r),
        child: Container(
          width:
              64.w *
              (MediaQuery.textScalerOf(context).scale(14) / 14).clamp(1, 2),
          padding: EdgeInsets.symmetric(horizontal: 6.w, vertical: 7.h),
          decoration: BoxDecoration(
            color: isSelected ? AppColors.sokoonTeal : AppColors.white,
            borderRadius: BorderRadius.circular(16.r),
            border: Border.all(
              color: isSelected ? AppColors.sokoonTeal : AppColors.sokoonBorder,
            ),
          ),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              AppText(
                day.localizedShortWeekday,
                color: isSelected ? AppColors.white : AppColors.sokoonGray,
                fontSize: 12.sp,
                fontWeight: FontWeight.w500,
                maxLines: 1,
              ),
              3.szH,
              AppText(
                '${day.dateValue?.day ?? ''}',
                color: isSelected ? AppColors.white : AppColors.sokoonNavy,
                fontSize: 14.sp,
                fontWeight: FontWeight.w700,
              ),
            ],
          ),
        ),
      ),
    );
  }
}

extension OwnerAvailabilityDayPresentation on OwnerAvailabilityDayContent {
  String get localizedWeekday {
    return switch (dayName) {
      'monday' => LocaleKeys.ownerAvailabilityMonday,
      'tuesday' => LocaleKeys.ownerAvailabilityTuesday,
      'wednesday' => LocaleKeys.ownerAvailabilityWednesday,
      'thursday' => LocaleKeys.ownerAvailabilityThursday,
      'friday' => LocaleKeys.ownerAvailabilityFriday,
      'saturday' => LocaleKeys.ownerAvailabilitySaturday,
      'sunday' => LocaleKeys.ownerAvailabilitySunday,
      _ => dayName,
    };
  }

  String get localizedShortWeekday {
    return switch (dayName) {
      'monday' => LocaleKeys.ownerAvailabilityMondayShort,
      'tuesday' => LocaleKeys.ownerAvailabilityTuesdayShort,
      'wednesday' => LocaleKeys.ownerAvailabilityWednesdayShort,
      'thursday' => LocaleKeys.ownerAvailabilityThursdayShort,
      'friday' => LocaleKeys.ownerAvailabilityFridayShort,
      'saturday' => LocaleKeys.ownerAvailabilitySaturdayShort,
      'sunday' => LocaleKeys.ownerAvailabilitySundayShort,
      _ => dayName,
    };
  }
}
