import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';

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
        ? AppColors.sokoonTeal
        : AppColors.sokoonGray;

    return TextField(
      controller: controller,
      readOnly: readOnly,
      autofocus: autofocus,
      onTap: onTap,
      onChanged: onChanged,
      textDirection: TextDirection.rtl,
      textInputAction: TextInputAction.search,
      style: TextStyle(
        color: AppColors.sokoonNavy,
        fontSize: 14.sp,
        fontFamily: ConstantManager.fontFamily,
      ),
      decoration: InputDecoration(
        hintText: LocaleKeys.chatSearchHint,
        hintStyle: TextStyle(
          color: AppColors.sokoonMuted,
          fontSize: 14.sp,
          fontFamily: ConstantManager.fontFamily,
        ),
        filled: true,
        fillColor: isActive ? AppColors.scaffoldBackground : AppColors.white,
        prefixIcon: Icon(Icons.search_rounded, color: iconColor, size: 18.r),
        suffixIcon: onClearPressed == null
            ? null
            : IconButton(
                onPressed: onClearPressed,
                icon: Icon(
                  Icons.close_rounded,
                  color: AppColors.sokoonGray,
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
