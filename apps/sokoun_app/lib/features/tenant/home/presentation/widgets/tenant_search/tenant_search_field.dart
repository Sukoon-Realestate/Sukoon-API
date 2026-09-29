import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/padding_extension.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:melos_core/core/widgets/text_fields/default_text_field.dart';

class TenantSearchField extends StatelessWidget {
  const TenantSearchField({
    super.key,
    this.controller,
    this.onChanged,
    this.onSubmitted,
    this.onSearchTap,
  });

  final TextEditingController? controller;
  final ValueChanged<String>? onChanged;
  final ValueChanged<String>? onSubmitted;
  final VoidCallback? onSearchTap;

  @override
  Widget build(BuildContext context) {
    return DefaultTextField(
      controller: controller,
      onChanged: (value) => onChanged?.call(value ?? ''),
      onSubmitted: (value) => onSubmitted?.call(value ?? ''),
      action: TextInputAction.search,
      textAlign: TextAlign.start,
      title: LocaleKeys.tenantSearchFieldHint,
      borderRadius: 16.r,
      borderColor: AppColors.sokoonTeal,
      fillColor: AppColors.white,
      contentPadding: EdgeInsets.symmetric(vertical: 15.h),
      style: TextStyle(
        color: AppColors.sokoonNavy,
        fontSize: 14.sp,
        fontWeight: FontWeight.w600,
      ),
      prefixIcon: GestureDetector(
        onTap: onSearchTap,
        behavior: HitTestBehavior.opaque,
        child: Container(
          padding: EdgeInsets.symmetric(horizontal: 12.w, vertical: 6.h),
          decoration: BoxDecoration(
            color: AppColors.mintLight,
            borderRadius: BorderRadius.circular(12.r),
          ),
          child: AppText(
            LocaleKeys.search,
            color: AppColors.sokoonTeal,
            fontSize: 12.sp,
            fontWeight: FontWeight.w800,
          ),
        ),
      ).paddingOnlyDirectional(start: 8.w),
      suffixIcon: controller == null
          ? Icon(Icons.search_rounded, color: AppColors.sokoonMuted, size: 20.r)
          : ValueListenableBuilder<TextEditingValue>(
              valueListenable: controller!,
              builder: (context, value, _) => value.text.isEmpty
                  ? Icon(
                      Icons.search_rounded,
                      color: AppColors.sokoonMuted,
                      size: 20.r,
                    )
                  : IconButton(
                      tooltip: LocaleKeys.clearSearchQuery,
                      onPressed: () {
                        controller!.clear();
                        onChanged?.call('');
                      },
                      icon: Icon(
                        Icons.close_rounded,
                        color: AppColors.sokoonGray,
                        size: 20.r,
                      ),
                    ),
            ),
    );
  }
}
