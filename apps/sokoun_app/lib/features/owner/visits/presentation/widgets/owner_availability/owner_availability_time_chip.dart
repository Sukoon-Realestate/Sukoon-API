part of '../../../imports.dart';

class OwnerAvailabilityTimeChip extends StatelessWidget {
  const OwnerAvailabilityTimeChip({
    super.key,
    required this.label,
    required this.state,
    required this.onPressed,
  });

  final String label;
  final OwnerAvailabilitySlotState state;
  final VoidCallback onPressed;

  Color get _backgroundColor {
    if (state.isBooked) {
      return AppColors.redPale;
    }
    if (state.isAvailable) {
      return AppColors.mintLight;
    }
    return AppColors.white;
  }

  Color get _foregroundColor {
    if (state.isBooked) {
      return AppColors.red;
    }
    if (state.isAvailable) {
      return AppColors.sokoonTeal;
    }
    return AppColors.sokoonGray;
  }

  @override
  Widget build(BuildContext context) {
    return Material(
      color: AppColors.transparent,
      child: InkWell(
        onTap: onPressed,
        borderRadius: BorderRadius.circular(16.r),
        child: Container(
          height: 40.h,
          alignment: Alignment.center,
          decoration: BoxDecoration(
            color: _backgroundColor,
            borderRadius: BorderRadius.circular(16.r),
            border: Border.all(color: _foregroundColor),
          ),
          child: FittedBox(
            fit: BoxFit.scaleDown,
            child: AppText(
              state.isBooked ? '$label ×' : label,
              style: AppTextStyles.bold12.copyWith(
                color: _foregroundColor,
                fontSize: 12.sp,
                height: 1.45,
              ),
            ),
          ),
        ),
      ),
    );
  }
}
