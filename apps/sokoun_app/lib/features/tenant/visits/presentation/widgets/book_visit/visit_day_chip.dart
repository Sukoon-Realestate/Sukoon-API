part of '../../../imports.dart';

class VisitDayChip extends StatelessWidget {
  const VisitDayChip({
    super.key,
    required this.day,
    required this.isSelected,
    required this.onPressed,
  });

  final VisitDayContent day;
  final bool isSelected;
  final VoidCallback onPressed;

  @override
  Widget build(BuildContext context) {
    return Semantics(
      button: true,
      selected: isSelected,
      child: GestureDetector(
        onTap: onPressed,
        behavior: HitTestBehavior.opaque,
        child: AnimatedContainer(
          duration: SokounMotion.duration(context, milliseconds: 180),
          width:
              76.w *
              (MediaQuery.textScalerOf(context).scale(14) / 14).clamp(1, 2),
          padding: EdgeInsets.symmetric(horizontal: 8.w, vertical: 10.h),
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
                day.weekdayLabel,
                color: isSelected ? AppColors.white : AppColors.sokoonGray,
                fontSize: 12.sp,
                fontWeight: FontWeight.w700,
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
              ),
              2.szH,
              AppText(
                day.day,
                color: isSelected ? AppColors.white : AppColors.sokoonNavy,
                fontSize: 19.sp,
                fontWeight: FontWeight.w700,
              ),
            ],
          ),
        ),
      ),
    );
  }
}
