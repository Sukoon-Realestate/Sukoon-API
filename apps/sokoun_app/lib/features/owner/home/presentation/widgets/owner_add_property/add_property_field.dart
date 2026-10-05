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
    this.isRequired = true,
    this.showLabel = true,
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
  final bool isRequired;
  final bool showLabel;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      spacing: 6.h,
      children: [
        if (showLabel)
          AddPropertyFieldLabel(label: field.label, isRequired: isRequired),
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
                validator ??
                (value) =>
                    isRequired ? Validators.validateRequired(value) : null,
            style: AppTextStyles.medium.copyWith(
              color: context.appColor(AppColors.sokoonNavy),
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

class AddPropertyFieldLabel extends StatelessWidget {
  const AddPropertyFieldLabel({
    super.key,
    required this.label,
    this.isRequired = true,
  });

  final String label;
  final bool isRequired;

  @override
  Widget build(BuildContext context) => AppText(
    isRequired ? '$label *' : label,
    style: AppTextStyles.medium13.copyWith(
      color: context.appColor(AppColors.sokoonGray),
    ),
  );
}
