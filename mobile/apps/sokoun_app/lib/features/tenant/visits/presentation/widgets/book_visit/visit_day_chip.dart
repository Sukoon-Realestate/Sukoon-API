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
            spacing: 2.h,
            children: [
              AppText(
                day.weekdayLabel,
                style: AppTextStyles.bold12.copyWith(
                  color: isSelected
                      ? AppColors.white
                      : context.appColor(AppColors.sokoonGray),
                  fontSize: 12.sp,
                  height: 1.45,
                ),
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
              ),
              AppText(
                day.day,
                style: AppTextStyles.bold.copyWith(
                  color: isSelected
                      ? AppColors.white
                      : context.appColor(AppColors.sokoonNavy),
                  fontSize: 19.sp,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
