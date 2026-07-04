import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';

import '../../../../config/res/config_imports.dart';
import '../default_button.dart';

enum ShapeType{withBorderColor, withBackGroundColor}
class AppDefaultButton extends StatelessWidget {
  final ShapeType shapeType;
  final Color? backgroundColor;
  final Color? textColor;
  final String title;
  final Color? borderColor;
  final FutureOr<void> Function()? onTap;
  const AppDefaultButton.withBorderColor({super.key,
    required this.title,
    required this.onTap,
    this.borderColor,
  }) : shapeType = ShapeType.withBorderColor,
        backgroundColor = null,
        textColor = null;

  const AppDefaultButton.withBackGroundColor({super.key,
    required this.title,
    required this.onTap,
    this.backgroundColor,
    this.textColor,
    this.borderColor,
  }) : shapeType = ShapeType.withBackGroundColor;

  @override
  Widget build(BuildContext context) {
    return DefaultButton(
      color: shapeType == ShapeType.withBorderColor?
      AppColors.white : backgroundColor?? AppColors.primary,
      title: title,
      fontSize: 16.sp,
      fontWeight: FontWeight.w400,
      borderRadius: ConstantManager.buttonBorderRadius,
      borderColor: borderColor?? AppColors.primary,
      textColor: shapeType == ShapeType.withBorderColor?
      AppColors.primary : textColor?? AppColors.white,
      onTap: onTap,
    );
  }
}
