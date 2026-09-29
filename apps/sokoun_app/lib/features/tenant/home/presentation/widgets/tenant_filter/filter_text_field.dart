import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/helpers/text_style_manager.dart';
import 'package:melos_core/core/widgets/app_text.dart';

class FilterTextField extends StatelessWidget {
  const FilterTextField({
    super.key,
    required this.label,
    required this.hint,
    required this.controller,
    required this.onChanged,
    this.keyboardType,
    this.inputFormatters,
    this.textAlign = TextAlign.start,
  });

  final String label;
  final String hint;
  final TextEditingController controller;
  final ValueChanged<String> onChanged;
  final TextInputType? keyboardType;
  final List<TextInputFormatter>? inputFormatters;
  final TextAlign textAlign;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        AppText(
          label,
          style: AppTextStyles.semiBold.copyWith(
            color: AppColors.sokoonGray,
            fontSize: 12.sp,
          ),
          textAlign: TextAlign.start,
        ),
        6.szH,
        Container(
          constraints: BoxConstraints(minHeight: 48.h),
          padding: EdgeInsets.symmetric(horizontal: 12.w),
          decoration: BoxDecoration(
            color: AppColors.grayOffWhite,
            borderRadius: BorderRadius.circular(12.r),
            border: Border.all(color: AppColors.grayPale),
          ),
          child: TextField(
            controller: controller,
            onChanged: onChanged,
            keyboardType: keyboardType,
            inputFormatters: inputFormatters,
            textAlign: textAlign,
            style: AppTextStyles.semiBold.copyWith(
              color: AppColors.sokoonNavy,
              fontSize: 13.sp,
            ),
            decoration: InputDecoration(
              isCollapsed: true,
              border: InputBorder.none,
              hintText: hint,
              hintStyle: AppTextStyles.regular12.copyWith(
                color: AppColors.navyAlpha50,
                fontSize: 12.sp,
                height: 1.45,
              ),
              contentPadding: EdgeInsets.symmetric(vertical: 14.h),
            ),
          ),
        ),
      ],
    );
  }
}
