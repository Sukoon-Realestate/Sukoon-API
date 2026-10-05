part of '../../../imports.dart';

class VisitFilterChip extends StatelessWidget {
  const VisitFilterChip({
    super.key,
    required this.label,
    required this.isSelected,
    required this.onPressed,
  });

  final String label;
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
          padding: EdgeInsets.symmetric(horizontal: 13.w, vertical: 7.h),
          decoration: BoxDecoration(
            color: isSelected
                ? context.appColor(AppColors.sokoonTeal, surface: true)
                : context.appColor(AppColors.white, surface: true),
            borderRadius: BorderRadius.circular(999.r),
            border: Border.all(
              color: isSelected
                  ? context.appColor(AppColors.sokoonTeal)
                  : context.appColor(AppColors.sokoonBorder),
            ),
          ),
          child: AppText(
            label,
            style: AppTextStyles.extraBold.copyWith(
              color: isSelected
                  ? AppColors.white
                  : context.appColor(AppColors.sokoonNavy),
              fontSize: 12.sp,
            ),
            maxLines: 1,
          ),
        ),
      ),
    );
  }
}
