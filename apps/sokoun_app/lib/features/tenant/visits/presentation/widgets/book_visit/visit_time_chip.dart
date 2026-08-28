part of '../../../imports.dart';

class VisitTimeChip extends StatelessWidget {
  const VisitTimeChip({
    super.key,
    required this.slot,
    required this.isSelected,
    required this.onPressed,
  });

  final VisitTimeSlotContent slot;
  final bool isSelected;
  final VoidCallback? onPressed;

  @override
  Widget build(BuildContext context) {
    final bool isEnabled = onPressed != null;

    return Semantics(
      button: true,
      enabled: isEnabled,
      selected: isSelected,
      child: GestureDetector(
        key: ValueKey('visit-time-${slot.label}'),
        onTap: onPressed,
        behavior: HitTestBehavior.opaque,
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 180),
          alignment: Alignment.center,
          decoration: BoxDecoration(
            color: isSelected
                ? AppColors.sokoonTeal
                : isEnabled
                ? AppColors.white
                : AppColors.grayBackground,
            borderRadius: BorderRadius.circular(14.r),
            border: Border.all(
              color: isSelected ? AppColors.sokoonTeal : AppColors.sokoonBorder,
            ),
          ),
          child: FittedBox(
            fit: BoxFit.scaleDown,
            child: Row(
              mainAxisAlignment: MainAxisAlignment.center,
              mainAxisSize: MainAxisSize.min,
              children: [
                AppText(
                  slot.label,
                  color: isSelected
                      ? AppColors.white
                      : isEnabled
                      ? AppColors.sokoonNavy
                      : AppColors.sokoonMuted,
                  fontSize: 13.sp,
                  fontWeight: FontWeight.w800,
                  maxLines: 1,
                ),
                if (!isEnabled) ...[
                  3.szW,
                  Icon(
                    Icons.close_rounded,
                    color: AppColors.sokoonMuted,
                    size: 12.r,
                  ),
                ],
              ],
            ),
          ),
        ),
      ),
    );
  }
}
