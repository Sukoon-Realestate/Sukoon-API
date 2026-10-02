part of '../../../imports.dart';

class OwnerCalendarDay extends StatelessWidget {
  const OwnerCalendarDay({
    super.key,
    required this.day,
    required this.isSelected,
    required this.hasVisit,
    required this.onPressed,
    this.visitCount = 0,
  });

  final int? day;
  final bool isSelected;
  final bool hasVisit;
  final VoidCallback? onPressed;
  final int visitCount;

  @override
  Widget build(BuildContext context) {
    if (day == null) {
      return const SizedBox.shrink();
    }

    return Semantics(
      label: LocaleKeys.ownerCalendarDayVisitCount
          .replaceAll('{day}', '$day')
          .replaceAll('{count}', '$visitCount'),
      selected: isSelected,
      button: true,
      onTap: onPressed,
      excludeSemantics: true,
      child: Material(
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
                  style: AppTextStyles.regular13.copyWith(
                    color: isSelected ? AppColors.white : AppColors.sokoonNavy,
                    fontSize: 13.sp,
                    fontWeight: isSelected ? FontWeight.w700 : FontWeight.w500,
                    height: 1.45,
                  ),
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
      ),
    );
  }
}
