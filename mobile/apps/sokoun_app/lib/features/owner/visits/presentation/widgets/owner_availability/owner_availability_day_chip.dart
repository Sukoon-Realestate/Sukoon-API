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
        child: AnimatedContainer(
          duration: SokounMotion.duration(context, milliseconds: 180),
          curve: SokounMotion.curve,
          width:
              64.w *
              (MediaQuery.textScalerOf(context).scale(14) / 14).clamp(1, 2),
          padding: EdgeInsets.symmetric(horizontal: 6.w, vertical: 7.h),
          decoration: BoxDecoration(
            color: isSelected
                ? context.appColor(AppColors.sokoonTeal, surface: true)
                : context.appColor(AppColors.white, surface: true),
            borderRadius: BorderRadius.circular(16.r),
            border: Border.all(
              color: isSelected
                  ? context.appColor(AppColors.sokoonTeal)
                  : context.appColor(AppColors.sokoonBorder),
            ),
          ),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            mainAxisAlignment: MainAxisAlignment.center,
            spacing: 3.h,
            children: [
              AppText(
                day.localizedShortWeekday,
                style: AppTextStyles.medium12.copyWith(
                  color: isSelected
                      ? AppColors.white
                      : context.appColor(AppColors.sokoonGray),
                  fontSize: 12.sp,
                  height: 1.45,
                ),
                maxLines: 1,
              ),
              AppText(
                '${day.dateValue?.day ?? ''}',
                style: AppTextStyles.bold14.copyWith(
                  color: isSelected
                      ? AppColors.white
                      : context.appColor(AppColors.sokoonNavy),
                  fontSize: 14.sp,
                  height: 1.45,
                ),
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
