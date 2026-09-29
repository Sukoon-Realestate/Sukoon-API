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
            color: isSelected ? AppColors.sokoonTeal : AppColors.white,
            borderRadius: BorderRadius.circular(999.r),
            border: Border.all(
              color: isSelected ? AppColors.sokoonTeal : AppColors.sokoonBorder,
            ),
          ),
          child: AppText(
            label,
            color: isSelected ? AppColors.white : AppColors.sokoonNavy,
            fontSize: 12.sp,
            fontWeight: FontWeight.w800,
            maxLines: 1,
          ),
        ),
      ),
    );
  }
}
