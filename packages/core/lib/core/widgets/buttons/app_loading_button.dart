import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';

import '../../../config/res/config_imports.dart';
import '../../extensions/padding_extension.dart';
import '../app_text.dart';
import 'custom_app_buttons/loading_button.dart';

class AppLoadingButton extends StatelessWidget {
  final Future<void> Function(BuildContext context) asyncCall;
  final String title;
  final double? width;
  final double? height;
  final double? borderRadius;
  final double? fontSize;
  final Color? textColor;
  final Color? buttonColor;
  final FontWeight? fontWeight;

  const AppLoadingButton({
    super.key,
    required this.asyncCall,
    required this.title,
    this.width,
    this.height,
    this.borderRadius,
    this.fontSize,
    this.textColor,
    this.buttonColor,
    this.fontWeight,
  });

  @override
  Widget build(BuildContext context) {
    return LoadingButton(
      borderRadius: borderRadius ?? ConstantManager.buttonBorderRadiusNumber,
      height: height ?? 45.h,
      width: width ?? double.infinity,
      btnColor: buttonColor ?? AppColors.primary,
      loadingWidget: SizedBox.square(
        dimension: 15.sp,
        child: const CircularProgressIndicator(
          color: Colors.white,
        ).paddingAll(3.r),
      ),
      idleWidget: FittedBox(
        child: AppText(
          title,
          fontSize: fontSize ?? 14.sp,
          fontWeight: fontWeight ?? FontWeight.bold,
          color: textColor ?? Colors.white,
        ),
      ),
      call: asyncCall
    );
  }
}
