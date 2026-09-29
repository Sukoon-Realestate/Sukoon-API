import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/helpers/text_style_manager.dart';
import 'package:pinput/pinput.dart';

class OtpCodeField extends StatelessWidget {
  const OtpCodeField({
    super.key,
    required this.controller,
    this.onChanged,
    this.onCompleted,
  });

  final TextEditingController controller;
  final ValueChanged<String>? onChanged;
  final ValueChanged<String>? onCompleted;

  @override
  Widget build(BuildContext context) {
    final defaultTheme = PinTheme(
      width: 45.w,
      height: 58.h,
      textStyle: AppTextStyles.extraBold.copyWith(
        color: AppColors.sokoonNavy,
        fontSize: 22.sp,
      ),
      decoration: BoxDecoration(
        color: AppColors.white,
        borderRadius: BorderRadius.circular(12.r),
        border: Border.all(color: AppColors.grayPale),
      ),
    );

    final activeTheme = defaultTheme.copyDecorationWith(
      color: AppColors.mintLight,
      border: Border.all(color: AppColors.sokoonTeal, width: 1.5),
      borderRadius: BorderRadius.circular(12.r),
    );

    return Directionality(
      textDirection: TextDirection.ltr,
      child: Pinput(
        length: 6,
        controller: controller,
        keyboardType: TextInputType.number,
        inputFormatters: [FilteringTextInputFormatter.digitsOnly],
        defaultPinTheme: defaultTheme,
        focusedPinTheme: activeTheme,
        submittedPinTheme: activeTheme,
        closeKeyboardWhenCompleted: true,
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        pinAnimationType: PinAnimationType.scale,
        onChanged: onChanged,
        onCompleted: onCompleted,
      ),
    );
  }
}
