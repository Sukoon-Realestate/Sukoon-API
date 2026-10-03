import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/helpers/validators.dart';
import 'package:melos_core/core/helpers/text_style_manager.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/features/owner/home/data/models/owner_add_property_content.dart';

class AddPropertyField extends StatelessWidget {
  const AddPropertyField({
    super.key,
    required this.field,
    this.suffix,
    this.controller,
    this.onChanged,
    this.keyboardType = TextInputType.text,
    this.inputFormatters,
    this.hint,
    this.readOnly = false,
    this.onTap,
    this.maxLines = 1,
    this.minLines,
    this.validator,
  });

  final AddPropertyFieldContent field;
  final Widget? suffix;
  final TextEditingController? controller;
  final ValueChanged<String>? onChanged;
  final TextInputType keyboardType;
  final List<TextInputFormatter>? inputFormatters;
  final String? hint;
  final bool readOnly;
  final VoidCallback? onTap;
  final int maxLines;
  final int? minLines;
  final FormFieldValidator<String>? validator;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      spacing: 6.h,
      children: [
        AppText(
          '${field.label} *',
          style: AppTextStyles.medium13.copyWith(color: AppColors.sokoonGray),
        ),
        if (controller != null)
          TextFormField(
            controller: controller,
            onChanged: onChanged,
            readOnly: readOnly,
            onTap: onTap,
            keyboardType: keyboardType,
            inputFormatters: inputFormatters,
            maxLines: maxLines,
            minLines: minLines,
            textAlign: field.textAlign,
            textInputAction: maxLines == 1
                ? TextInputAction.next
                : TextInputAction.newline,
            validator:
                validator ?? (value) => Validators.validateRequired(value),
            style: AppTextStyles.medium.copyWith(
              color: AppColors.sokoonNavy,
              fontSize: 15.sp,
            ),
            decoration: InputDecoration(
              errorMaxLines: 3,
              hintText: hint ?? field.value,
              suffixIcon: suffix == null
                  ? null
                  : Padding(
                      padding: EdgeInsets.symmetric(horizontal: 12.w),
                      child: Center(widthFactor: 1, child: suffix),
                    ),
              contentPadding: EdgeInsets.symmetric(
                horizontal: 14.w,
                vertical: 14.h,
              ),
            ),
          )
        else
          AppText(field.value, style: AppTextStyles.regular14),
      ],
    );
  }
}
