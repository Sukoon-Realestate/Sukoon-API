import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/helpers/text_style_manager.dart';
import 'package:melos_core/core/helpers/validators.dart';
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
          spacing: 4.h,
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
              style: AppTextStyles.semiBold.copyWith(
                color: AppColors.sokoonNavy,
                fontSize: 15.sp,
              ),
              onChanged: onChanged,
              validator:
                  validator ??
                  (value) => Validators.validatePasswordConfirmation(
                    value,
                    password: passwordController?.text,
                  ),
            ),
            if (errorText != null && errorText!.isNotEmpty)
              AppText(
                errorText!,
                style: AppTextStyles.bold12.copyWith(
                  color: AppColors.sokoonRose,
                  fontSize: 12.sp,
                  height: 1.45,
                ),
              ),
          ],
        );
      },
    );
  }
}
