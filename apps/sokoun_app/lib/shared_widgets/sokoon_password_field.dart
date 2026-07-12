import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:melos_core/core/widgets/text_fields/default_text_field.dart';
import 'package:melos_core/core/helpers/validators.dart';

class SokoonPasswordField extends StatelessWidget {
  const SokoonPasswordField({
    super.key,
    required this.controller,
    this.label,
    this.hintText = '••••••••',
    this.accentColor = AppColors.sokoonTeal,
    this.hasError = false,
    this.errorText,
    this.onChanged,
  });

  final TextEditingController controller;
  final String? label;
  final String hintText;
  final Color accentColor;
  final bool hasError;
  final String? errorText;
  final ValueChanged<String?>? onChanged;

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
              upperTitle: label ?? LocaleKeys.password,
              title: hintText,
              isPassword: true,
              action: TextInputAction.done,
              textAlign: TextAlign.left,
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
              validator: Validators.validateEmail,
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
}
