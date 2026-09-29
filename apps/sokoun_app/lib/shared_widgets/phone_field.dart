import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/helpers/text_style_manager.dart';
import 'package:melos_core/core/widgets/text_fields/default_text_field.dart';

class SokoonPhoneField extends StatelessWidget {
  const SokoonPhoneField({
    super.key,
    required this.controller,
    this.label,
    this.hintText = '01xxxxxxxxx',
    this.accentColor = AppColors.sokoonTeal,
    this.hasError = false,
    this.onChanged,
    this.validator,
    this.action = TextInputAction.next,
    this.maxLength,
  });

  final TextEditingController controller;
  final String? label;
  final String hintText;
  final Color accentColor;
  final bool hasError;
  final ValueChanged<String?>? onChanged;
  final FormFieldValidator<String?>? validator;
  final TextInputAction action;
  final int? maxLength;

  @override
  Widget build(BuildContext context) {
    return ValueListenableBuilder<TextEditingValue>(
      valueListenable: controller,
      builder: (context, value, child) {
        final borderColor = hasError
            ? AppColors.sokoonRose
            : value.text.isNotEmpty
            ? accentColor
            : AppColors.sokoonBorder;

        return DefaultTextField.withTitle(
          controller: controller,
          upperTitle: label ?? LocaleKeys.phoneNumber,
          title: hintText,
          inputType: TextInputType.phone,
          action: action,
          borderRadius: 12.r,
          borderColor: borderColor,
          fillColor: AppColors.white,
          maxLength: maxLength,
          inputFormatters: [FilteringTextInputFormatter.digitsOnly],
          contentPadding: EdgeInsets.symmetric(
            horizontal: 16.w,
            vertical: 14.h,
          ),
          style: AppTextStyles.semiBold.copyWith(
            color: AppColors.sokoonNavy,
            fontSize: 15.sp,
          ),
          onChanged: onChanged,
          validator: validator,
        );
      },
    );
  }
}
