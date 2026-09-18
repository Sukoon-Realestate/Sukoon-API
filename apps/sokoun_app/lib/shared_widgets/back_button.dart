import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/navigation/navigator.dart';

class SokoonBackButton extends StatelessWidget {
  const SokoonBackButton({
    super.key,
    this.onTap,
    this.backgroundColor = AppColors.white,
    this.borderColor = AppColors.sokoonBorder,
    this.icon = Icons.arrow_back_ios_new_rounded,
  });

  final VoidCallback? onTap;
  final Color backgroundColor;
  final Color borderColor;
  final IconData icon;

  @override
  Widget build(BuildContext context) {
    return Visibility(
      visible: Navigator.canPop(context),
      child: SizedBox.square(
        dimension: 36.r,
        child: DecoratedBox(
          decoration: BoxDecoration(
            color: backgroundColor,
            borderRadius: BorderRadius.circular(12.r),
            border: Border.all(color: borderColor),
          ),
          child: IconButton(
            onPressed: onTap ?? () => Go.back(),
            padding: EdgeInsets.zero,
            icon: Icon(icon, color: AppColors.sokoonNavy, size: 16.r),
          ),
        ),
      ),
    );
  }
}
