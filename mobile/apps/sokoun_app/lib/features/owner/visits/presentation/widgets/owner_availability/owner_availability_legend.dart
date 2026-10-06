part of '../../../imports.dart';

class OwnerAvailabilityLegend extends StatelessWidget {
  const OwnerAvailabilityLegend({super.key});

  @override
  Widget build(BuildContext context) {
    return Wrap(
      spacing: 14.w,
      runSpacing: 8.h,
      children: const [
        _OwnerAvailabilityLegendItem(
          state: OwnerAvailabilitySlotState.available,
        ),
        _OwnerAvailabilityLegendItem(state: OwnerAvailabilitySlotState.booked),
        _OwnerAvailabilityLegendItem(
          state: OwnerAvailabilitySlotState.unspecified,
        ),
      ],
    );
  }
}

class _OwnerAvailabilityLegendItem extends StatelessWidget {
  const _OwnerAvailabilityLegendItem({required this.state});

  final OwnerAvailabilitySlotState state;

  Color get _backgroundColor {
    if (state.isAvailable) {
      return AppColors.mintLight;
    }
    if (state.isBooked) {
      return AppColors.redPale;
    }
    return AppColors.white;
  }

  Color get _borderColor {
    if (state.isAvailable) {
      return AppColors.sokoonTeal;
    }
    if (state.isBooked) {
      return AppColors.red;
    }
    return AppColors.sokoonGray;
  }

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      spacing: 6.w,
      children: [
        Container(
          width: 16.r,
          height: 16.r,
          decoration: BoxDecoration(
            color: context.appColor(_backgroundColor, surface: true),
            borderRadius: BorderRadius.circular(4.r),
            border: Border.all(color: context.appColor(_borderColor)),
          ),
        ),
        AppText(
          state.label,
          style: AppTextStyles.medium11.copyWith(
            color: context.appColor(AppColors.sokoonGray),
            fontSize: 11.sp,
            height: 1.45,
          ),
        ),
      ],
    );
  }
}
