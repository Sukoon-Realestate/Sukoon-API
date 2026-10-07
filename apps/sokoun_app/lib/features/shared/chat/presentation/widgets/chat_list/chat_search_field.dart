import 'package:melos_core/core/widgets/text_fields/default_text_field.dart';
import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/helpers/text_style_manager.dart';

class ChatSearchField extends StatelessWidget {
  const ChatSearchField({
    super.key,
    this.controller,
    this.readOnly = false,
    this.autofocus = false,
    this.isActive = false,
    this.onTap,
    this.onChanged,
    this.onClearPressed,
  });

  final TextEditingController? controller;
  final bool readOnly;
  final bool autofocus;
  final bool isActive;
  final VoidCallback? onTap;
  final ValueChanged<String>? onChanged;
  final VoidCallback? onClearPressed;

  @override
  Widget build(BuildContext context) {
    final Color iconColor = isActive
        ? context.appColor(AppColors.sokoonTeal)
        : context.appColor(AppColors.sokoonGray);

    return DefaultTextField(
      controller: controller,
      readOnly: readOnly,
      autoFocus: autofocus,
      onTap: onTap,
      onChanged: (value) => onChanged?.call(value ?? ''),
      action: TextInputAction.search,
      style: AppTextStyles.base.copyWith(
        color: context.appColor(AppColors.sokoonNavy),
        fontSize: 14.sp,
      ),
      decoration: InputDecoration(
        hintText: LocaleKeys.chatSearchHint,
        hintStyle: AppTextStyles.base.copyWith(
          color: context.appColor(AppColors.sokoonMuted),
          fontSize: 14.sp,
        ),
        filled: true,
        fillColor: isActive
            ? context.appColor(AppColors.scaffoldBackground, surface: true)
            : context.appColor(AppColors.white, surface: true),
        prefixIcon: Icon(
          Icons.search_rounded,
          color: context.appColor(iconColor),
          size: 18.r,
        ),
        suffixIcon: onClearPressed == null
            ? null
            : IconButton(
                onPressed: onClearPressed,
                icon: Icon(
                  Icons.close_rounded,
                  color: context.appColor(AppColors.sokoonGray),
                  size: 18.r,
                ),
              ),
        contentPadding: EdgeInsets.symmetric(horizontal: 14.w, vertical: 12.h),
        enabledBorder: _border,
        focusedBorder: _border,
      ),
    );
  }

  OutlineInputBorder get _border {
    return OutlineInputBorder(
      borderRadius: BorderRadius.circular(16.r),
      borderSide: BorderSide(
        color: isActive ? AppColors.sokoonTeal : AppColors.sokoonBorder,
        width: isActive ? 2.w : 1.w,
      ),
    );
  }
}
