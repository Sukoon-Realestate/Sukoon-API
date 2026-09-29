import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/widgets/buttons/default_button.dart';

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

    return DefaultButton(
      onTap: onTap,
      title: label,
      disabled: !isEnabled,
      color: isOutline ? AppColors.white : AppColors.sokoonTeal,
      textColor: isOutline ? AppColors.sokoonNavy : AppColors.white,
      borderColor: isOutline ? AppColors.sokoonBorder : null,
      borderRadius: BorderRadius.circular(12.r),
      width: double.infinity,
      minHeight: 48.h,
      isFitted: false,
      padding: EdgeInsets.symmetric(horizontal: 16.w, vertical: 12.h),
      fontSize: 15.sp,
      fontWeight: FontWeight.w700,
    );
  }
}
