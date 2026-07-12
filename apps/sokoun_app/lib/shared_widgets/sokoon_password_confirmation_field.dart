import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:melos_core/core/widgets/text_fields/default_text_field.dart';

class SokoonPasswordConfirmationField extends StatelessWidget {
  const SokoonPasswordConfirmationField({
    super.key,
    required this.controller,
    this.passwordController,
    this.label,
    this.hintText = '••••••••',
    this.accentColor = AppColors.sokoonTeal,
    this.hasError = false,
    this.errorText,
    this.onChanged,
    this.validator,
    this.action = TextInputAction.done,
  });

  final TextEditingController controller;
  final TextEditingController? passwordController;
  final String? label;
  final String hintText;
  final Color accentColor;
  final bool hasError;
  final String? errorText;
  final ValueChanged<String?>? onChanged;
  final FormFieldValidator<String?>? validator;
  final TextInputAction action;

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

        return Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            DefaultTextField.withTitle(
              controller: controller,
              upperTitle: label ?? LocaleKeys.confirmPassword,
              title: hintText,
              isPassword: true,
              action: action,
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
              validator: validator ?? _validatePasswordConfirmation,
            ),
            if (errorText != null && errorText!.isNotEmpty) ...[
              SizedBox(height: 4.h),
              AppText(
                errorText!,
                color: AppColors.sokoonRose,
                fontSize: 12.sp,
                fontWeight: FontWeight.w700,
              ),
            ],
          ],
        );
      },
    );
  }

  String? _validatePasswordConfirmation(String? value) {
    if (passwordController == null) {
      return null;
    }

    if (value == null || value.isEmpty) {
      return LocaleKeys.passRequiredValidation;
    }

    if (value != passwordController!.text) {
      return LocaleKeys.confirmValidation;
    }

    return null;
  }
}
