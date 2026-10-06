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
        onTap: state.isBooked ? null : onPressed,
        borderRadius: BorderRadius.circular(16.r),
        child: AnimatedContainer(
          duration: SokounMotion.duration(context, milliseconds: 180),
          curve: SokounMotion.curve,
          constraints: BoxConstraints(minHeight: 48.h),
          padding: EdgeInsets.symmetric(horizontal: 6.w, vertical: 10.h),
          alignment: Alignment.center,
          decoration: BoxDecoration(
            color: context.appColor(_backgroundColor, surface: true),
            borderRadius: BorderRadius.circular(16.r),
            border: Border.all(color: context.appColor(_foregroundColor)),
          ),
          child: AppText(
            state.isBooked ? '$label ×' : label,
            textAlign: TextAlign.center,
            style: AppTextStyles.bold12.copyWith(
              color: context.appColor(_foregroundColor),
              fontSize: 12.sp,
              height: 1.45,
            ),
          ),
        ),
      ),
    );
  }
}
