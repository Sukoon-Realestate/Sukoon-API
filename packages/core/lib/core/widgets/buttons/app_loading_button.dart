import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';

import '../../../config/res/config_imports.dart';
import '../../extensions/padding_extension.dart';
import '../app_text.dart';
import 'custom_app_buttons/loading_button.dart';
import 'app_control_theme.dart';

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
  final TextStyle? textStyle;
  final Widget? icon;

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
    this.textStyle,
    this.icon,
  });

  @override
  Widget build(BuildContext context) {
    final AppControlTheme? controls = Theme.of(
      context,
    ).extension<AppControlTheme>();
    final Widget label = Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        if (icon != null) ...[icon!, SizedBox(width: 8.w)],
        Flexible(
          child: AppText(
            title,
            textAlign: TextAlign.center,
            style: textStyle,
            fontSize: fontSize ?? textStyle?.fontSize ?? 14.sp,
            fontWeight: fontWeight ?? textStyle?.fontWeight ?? FontWeight.bold,
            color: textColor ?? textStyle?.color ?? Colors.white,
          ),
        ),
      ],
    );
    return LoadingButton(
      borderRadius:
          borderRadius ??
          controls?.radius ??
          ConstantManager.buttonBorderRadiusNumber,
      height: height ?? controls?.minimumHeight ?? 45.h,
      width: width ?? double.infinity,
      btnColor: buttonColor ?? AppColors.primary,
      loadingWidget: SizedBox.square(
        dimension: 15.sp,
        child: const CircularProgressIndicator(
          color: Colors.white,
        ).paddingAll(3.r),
      ),
      idleWidget: controls == null ? FittedBox(child: label) : label,
      call: asyncCall,
    );
  }
}
