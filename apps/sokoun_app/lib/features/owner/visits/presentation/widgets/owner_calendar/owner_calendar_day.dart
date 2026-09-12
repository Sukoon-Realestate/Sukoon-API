part of '../../../imports.dart';

class OwnerCalendarDay extends StatelessWidget {
  const OwnerCalendarDay({
    super.key,
    required this.day,
    required this.isSelected,
    required this.hasVisit,
    required this.onPressed,
  });

  final int? day;
  final bool isSelected;
  final bool hasVisit;
  final VoidCallback? onPressed;

  @override
  Widget build(BuildContext context) {
    if (day == null) {
      return const SizedBox.shrink();
    }

    return Material(
      color: AppColors.transparent,
      child: InkWell(
        onTap: onPressed,
        borderRadius: BorderRadius.circular(10.r),
        child: Container(
          decoration: BoxDecoration(
            color: isSelected ? AppColors.gold : AppColors.transparent,
            borderRadius: BorderRadius.circular(10.r),
          ),
          child: Stack(
            alignment: Alignment.center,
            children: [
              AppText(
                '$day',
                color: isSelected ? AppColors.white : AppColors.sokoonNavy,
                fontSize: 13.sp,
                fontWeight: isSelected ? FontWeight.w900 : FontWeight.w500,
              ),
              if (hasVisit)
                Positioned(
                  bottom: 3.h,
                  child: Container(
                    width: 5.r,
                    height: 5.r,
                    decoration: BoxDecoration(
                      color: isSelected
                          ? AppColors.white
                          : AppColors.sokoonTeal,
                      shape: BoxShape.circle,
                    ),
                  ),
                ),
            ],
          ),
        ),
      ),
    );
  }
}
