import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/widgets/app_text.dart';

class AddPropertyPrimaryButton extends StatelessWidget {
  const AddPropertyPrimaryButton({
    super.key,
    required this.label,
    required this.onTap,
    this.isOutline = false,
  });

  final String label;
  final VoidCallback onTap;
  final bool isOutline;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      behavior: HitTestBehavior.opaque,
      child: Container(
        height: 48.h,
        alignment: Alignment.center,
        decoration: BoxDecoration(
          color: isOutline ? AppColors.white : AppColors.sokoonTeal,
          borderRadius: BorderRadius.circular(14.r),
          border: Border.all(
            color: isOutline ? AppColors.sokoonBorder : AppColors.sokoonTeal,
          ),
        ),
        child: AppText(
          label,
          color: isOutline ? AppColors.sokoonNavy : AppColors.white,
          fontSize: 15.sp,
          fontWeight: FontWeight.w900,
          textAlign: TextAlign.center,
        ),
      ),
    );
  }
}
