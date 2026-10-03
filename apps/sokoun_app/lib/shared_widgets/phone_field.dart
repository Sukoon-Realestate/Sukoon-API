import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/padding_extension.dart';
import 'package:melos_core/core/helpers/text_style_manager.dart';
import 'package:melos_core/core/helpers/validators.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:melos_core/core/widgets/text_fields/default_text_field.dart';

class SokoonPhoneField extends StatelessWidget {
  static const String _countryCode = '+20';

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

  static TextEditingValue _addCountryCode(
    TextEditingValue oldValue,
    TextEditingValue newValue,
  ) {
    final String text = newValue.text.trimLeft();
    if (text.isEmpty ||
        text.startsWith('+') ||
        !newValue.composing.isCollapsed) {
      return newValue;
    }

    final String phone =
        '$_countryCode${text.startsWith('0') ? text.substring(1) : text}';
    final int offset = phone.length - newValue.text.length;
    return newValue.copyWith(
      text: phone,
      selection: newValue.selection.isValid
          ? newValue.selection.copyWith(
              baseOffset: (newValue.selection.baseOffset + offset).clamp(
                0,
                phone.length,
              ),
              extentOffset: (newValue.selection.extentOffset + offset).clamp(
                0,
                phone.length,
              ),
            )
          : newValue.selection,
      composing: TextRange.empty,
    );
  }

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
          inputFormatters: [TextInputFormatter.withFunction(_addCountryCode)],
          suffixIcon: Directionality(
            textDirection: TextDirection.ltr,
            child: Row(
              mainAxisSize: MainAxisSize.min,
              spacing: 8.w,
              children: [
                AppText('🇪🇬', fontSize: 20.sp),
                AppText(
                  _countryCode,
                  style: AppTextStyles.semiBold.copyWith(
                    color: AppColors.sokoonGray,
                    fontSize: 15.sp,
                  ),
                ),
              ],
            ).paddingSymmetric(horizontal: 12.w),
          ),
          action: action,
          borderRadius: 12.r,
          borderColor: borderColor,
          fillColor: AppColors.white,
          maxLength: maxLength,
          contentPadding: EdgeInsets.symmetric(
            horizontal: 16.w,
            vertical: 14.h,
          ),
          style: AppTextStyles.semiBold.copyWith(
            color: AppColors.sokoonNavy,
            fontSize: 15.sp,
          ),
          onChanged: onChanged,
          validator: validator ?? Validators.validateEgyptianMobile,
        );
      },
    );
  }
}
