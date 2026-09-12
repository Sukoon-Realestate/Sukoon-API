import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/helpers/validators.dart';
import 'package:melos_core/core/widgets/text_fields/default_text_field.dart';

class SokoonEmailField extends StatelessWidget {
  const SokoonEmailField({
    super.key,
    required this.controller,
    this.label,
    this.hintText = 'example@email.com',
    this.accentColor = AppColors.sokoonTeal,
    this.hasError = false,
    this.onChanged,
    this.validator,
    this.action = TextInputAction.next,
    this.readOnly = false,
  });

  final TextEditingController controller;
  final String? label;
  final String hintText;
  final Color accentColor;
  final bool hasError;
  final ValueChanged<String?>? onChanged;
  final FormFieldValidator<String?>? validator;
  final TextInputAction action;
  final bool readOnly;

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
          upperTitle: label ?? LocaleKeys.email,
          title: hintText,
          inputType: TextInputType.emailAddress,
          action: action,
          readOnly: readOnly,
          borderRadius: 12.r,
          borderColor: borderColor,
          fillColor: AppColors.white,
          contentPadding: EdgeInsets.symmetric(
            horizontal: 16.w,
            vertical: 14.h,
          ),
          style: TextStyle(
            color: AppColors.sokoonNavy,
            fontFamily: ConstantManager.fontFamily,
            fontSize: 15.sp,
            fontWeight: FontWeight.w600,
          ),
          onChanged: onChanged,
          validator: validator ?? Validators.validateEmail,
        );
      },
    );
  }
}
