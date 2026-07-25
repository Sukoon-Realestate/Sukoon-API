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
          width: 47.w,
          padding: EdgeInsets.symmetric(horizontal: 6.w, vertical: 7.h),
          decoration: BoxDecoration(
            color: isSelected ? AppColors.sokoonTeal : AppColors.white,
            borderRadius: BorderRadius.circular(16.r),
            border: Border.all(
              color: isSelected ? AppColors.sokoonTeal : AppColors.sokoonBorder,
            ),
          ),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              AppText(
                day.shortWeekday,
                color: isSelected ? AppColors.white : AppColors.sokoonGray,
                fontSize: 9.sp,
                fontWeight: FontWeight.w500,
                maxLines: 1,
              ),
              3.szH,
              AppText(
                day.day,
                color: isSelected ? AppColors.white : AppColors.sokoonNavy,
                fontSize: 14.sp,
                fontWeight: FontWeight.w900,
              ),
            ],
          ),
        ),
      ),
    );
  }
}
