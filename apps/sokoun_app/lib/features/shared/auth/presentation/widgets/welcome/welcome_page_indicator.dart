import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';

class WelcomePageIndicator extends StatelessWidget {
  const WelcomePageIndicator({
    super.key,
    this.activeIndex = 0,
    this.itemCount = 3,
  });

  final int activeIndex;
  final int itemCount;

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.center,
      children: List.generate(itemCount, (index) {
        final isActive = index == activeIndex;

        return AnimatedContainer(
          duration: const Duration(milliseconds: 180),
          margin: EdgeInsets.symmetric(horizontal: 3.w),
          width: isActive ? 18.w : 7.r,
          height: 7.r,
          decoration: BoxDecoration(
            color: isActive ? AppColors.sokoonTeal : AppColors.sokoonBorder,
            borderRadius: BorderRadius.circular(999.r),
          ),
        );
      }),
    );
  }
}
