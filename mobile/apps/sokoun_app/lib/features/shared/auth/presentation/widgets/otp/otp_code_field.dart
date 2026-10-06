import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/helpers/text_style_manager.dart';
import 'package:melos_core/core/helpers/validators.dart';
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
        color: context.appColor(AppColors.sokoonNavy),
        fontSize: 22.sp,
      ),
      decoration: BoxDecoration(
        color: context.appColor(AppColors.white, surface: true),
        borderRadius: BorderRadius.circular(12.r),
        border: Border.all(color: context.appColor(AppColors.grayPale)),
      ),
    );

    final activeTheme = defaultTheme.copyDecorationWith(
      color: context.appColor(AppColors.mintLight, surface: true),
      border: Border.all(
        color: context.appColor(AppColors.sokoonTeal),
        width: 1.5,
      ),
      borderRadius: BorderRadius.circular(12.r),
    );

    return Directionality(
      textDirection: TextDirection.ltr,
      child: Pinput(
        length: Validators.otpLength,
        controller: controller,
        validator: Validators.validateOtpCode,
        keyboardType: TextInputType.number,
        inputFormatters: [Validators.asciiDigitsOnly],
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
