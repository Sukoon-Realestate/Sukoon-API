import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/helpers/text_style_manager.dart';
import 'package:melos_core/core/helpers/validators.dart';
import 'package:melos_core/core/widgets/text_fields/default_text_field.dart';

class SokoonNameField extends StatelessWidget {
  const SokoonNameField({
    super.key,
    required this.controller,
    this.label,
    this.hintText,
    this.accentColor = AppColors.sokoonTeal,
    this.hasError = false,
    this.onChanged,
    this.validator,
    this.action = TextInputAction.next,
  });

  final TextEditingController controller;
  final String? label;
  final String? hintText;
  final Color accentColor;
  final bool hasError;
  final ValueChanged<String?>? onChanged;
  final FormFieldValidator<String?>? validator;
  final TextInputAction action;

  @override
  Widget build(BuildContext context) {
    return ValueListenableBuilder<TextEditingValue>(
      valueListenable: controller,
      builder: (context, value, child) {
        final borderColor = hasError
            ? context.appColor(AppColors.sokoonRose)
            : value.text.isNotEmpty
            ? accentColor
            : context.appColor(AppColors.sokoonBorder);

        return DefaultTextField.withTitle(
          controller: controller,
          upperTitle: label ?? LocaleKeys.fullName,
          title: hintText ?? LocaleKeys.fullNameHint,
          action: action,
          textAlign: TextAlign.right,
          borderRadius: 12.r,
          borderColor: context.appColor(borderColor),
          fillColor: context.appColor(AppColors.white, surface: true),
          contentPadding: EdgeInsets.symmetric(
            horizontal: 16.w,
            vertical: 14.h,
          ),
          style: AppTextStyles.semiBold.copyWith(
            color: context.appColor(AppColors.sokoonNavy),
            fontSize: 15.sp,
          ),
          onChanged: onChanged,
          validator: validator ?? Validators.validateName,
        );
      },
    );
  }
}
