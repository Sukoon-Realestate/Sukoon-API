import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
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

  @override
  Widget build(BuildContext context) {
    final hasInput = controller != null;
    final fieldTextColor = field.isFocused || hasInput
        ? AppColors.sokoonNavy
        : AppColors.navyAlpha50;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        AppText(
          field.label,
          color: AppColors.sokoonGray,
          fontSize: 12.sp,
          fontWeight: FontWeight.w600,
          textAlign: TextAlign.right,
        ),
        6.szH,
        Container(
          height: maxLines == 1 ? 46.h : null,
          constraints: maxLines > 1 ? BoxConstraints(minHeight: 86.h) : null,
          padding: EdgeInsets.symmetric(horizontal: 14.w),
          decoration: BoxDecoration(
            color: field.isFocused || hasInput
                ? AppColors.white
                : AppColors.grayOffWhite,
            borderRadius: BorderRadius.circular(12.r),
            border: Border.all(
              color: field.isFocused || hasInput
                  ? AppColors.sokoonTeal
                  : AppColors.grayPale,
              width: field.isFocused || hasInput ? 1.2 : 1,
            ),
          ),
          child: Row(
            textDirection: TextDirection.ltr,
            crossAxisAlignment: maxLines == 1
                ? CrossAxisAlignment.center
                : CrossAxisAlignment.start,
            children: [
              if (suffix != null) ...[
                Padding(
                  padding: EdgeInsets.only(top: maxLines == 1 ? 0 : 14.h),
                  child: suffix!,
                ),
                8.szW,
              ],
              Expanded(
                child: hasInput
                    ? TextField(
                        controller: controller,
                        onChanged: onChanged,
                        readOnly: readOnly,
                        onTap: onTap,
                        keyboardType: keyboardType,
                        inputFormatters: inputFormatters,
                        maxLines: maxLines,
                        minLines: minLines,
                        textAlign: field.textAlign,
                        style: TextStyle(
                          color: fieldTextColor,
                          fontSize: field.isFocused ? 16.sp : 13.sp,
                          fontWeight: field.isFocused
                              ? FontWeight.w900
                              : FontWeight.w500,
                        ),
                        decoration: InputDecoration(
                          isCollapsed: true,
                          border: InputBorder.none,
                          hintText: hint ?? field.value,
                          hintStyle: TextStyle(
                            color: AppColors.navyAlpha50,
                            fontSize: 12.sp,
                            fontWeight: FontWeight.w400,
                          ),
                          contentPadding: EdgeInsets.symmetric(
                            vertical: maxLines == 1 ? 0 : 14.h,
                          ),
                        ),
                      )
                    : AppText(
                        field.value,
                        color: fieldTextColor,
                        fontSize: field.isFocused ? 16.sp : 13.sp,
                        fontWeight: field.isFocused
                            ? FontWeight.w900
                            : FontWeight.w400,
                        textAlign: field.textAlign,
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                      ),
              ),
            ],
          ),
        ),
      ],
    );
  }
}
