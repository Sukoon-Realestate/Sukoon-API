import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/widgets/app_text.dart';

class AddPropertyPrimaryButton extends StatelessWidget {
  const AddPropertyPrimaryButton({
    super.key,
    required this.label,
    this.onTap,
    this.isOutline = false,
  });

  final String label;
  final VoidCallback? onTap;
  final bool isOutline;

  @override
  Widget build(BuildContext context) {
    final isEnabled = onTap != null;

    return GestureDetector(
      onTap: onTap,
      behavior: HitTestBehavior.opaque,
      child: Container(
        height: 48.h,
        alignment: Alignment.center,
        decoration: BoxDecoration(
          color: isOutline
              ? AppColors.white
              : isEnabled
              ? AppColors.sokoonTeal
              : AppColors.graySoft,
          borderRadius: BorderRadius.circular(14.r),
          border: Border.all(
            color: isOutline
                ? isEnabled
                      ? AppColors.sokoonBorder
                      : AppColors.grayPale
                : isEnabled
                ? AppColors.sokoonTeal
                : AppColors.graySoft,
          ),
        ),
        child: AppText(
          label,
          color: isOutline
              ? isEnabled
                    ? AppColors.sokoonNavy
                    : AppColors.sokoonMuted
              : AppColors.white,
          fontSize: 15.sp,
          fontWeight: FontWeight.w900,
          textAlign: TextAlign.center,
        ),
      ),
    );
  }
}
