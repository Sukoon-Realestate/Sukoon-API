import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/navigation/navigator.dart';

class SokoonBackButton extends StatelessWidget {
  const SokoonBackButton({super.key});

  @override
  Widget build(BuildContext context) {
    return SizedBox.square(
      dimension: 36.r,
      child: DecoratedBox(
        decoration: BoxDecoration(
          color: AppColors.white,
          borderRadius: BorderRadius.circular(12.r),
          border: Border.all(color: AppColors.sokoonBorder),
        ),
        child: IconButton(
          onPressed: () => Go.back(),
          padding: EdgeInsets.zero,
          icon: Icon(
            Icons.arrow_back_ios_new_rounded,
            color: AppColors.sokoonNavy,
            size: 16.r,
          ),
        ),
      ),
    );
  }
}
