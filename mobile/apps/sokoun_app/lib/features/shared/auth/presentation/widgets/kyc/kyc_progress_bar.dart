import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';

class KycProgressBar extends StatelessWidget {
  const KycProgressBar({
    super.key,
    required this.currentStep,
    this.totalSteps = 3,
  });

  final int currentStep;
  final int totalSteps;

  @override
  Widget build(BuildContext context) {
    return Row(
      children: List.generate(totalSteps, (index) {
        final isActive = index < currentStep;

        return Expanded(
          child: Container(
            height: 4.h,
            margin: EdgeInsetsDirectional.only(
              end: index == totalSteps - 1 ? 0 : 6.w,
            ),
            decoration: BoxDecoration(
              color: isActive
                  ? context.appColor(AppColors.sokoonTeal, surface: true)
                  : context.appColor(AppColors.grayPale, surface: true),
              borderRadius: BorderRadius.circular(999.r),
            ),
          ),
        );
      }),
    );
  }
}
