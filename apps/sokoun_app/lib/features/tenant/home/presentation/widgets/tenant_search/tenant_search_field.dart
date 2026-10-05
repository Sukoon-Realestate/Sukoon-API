import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/padding_extension.dart';
import 'package:melos_core/core/helpers/text_style_manager.dart';
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
      borderColor: context.appColor(AppColors.sokoonTeal),
      fillColor: context.appColor(AppColors.white, surface: true),
      contentPadding: EdgeInsets.symmetric(vertical: 15.h),
      style: AppTextStyles.semiBold.copyWith(
        color: context.appColor(AppColors.sokoonNavy),
        fontSize: 14.sp,
      ),
      prefixIcon: GestureDetector(
        onTap: onSearchTap,
        behavior: HitTestBehavior.opaque,
        child: Container(
          padding: EdgeInsets.symmetric(horizontal: 12.w, vertical: 6.h),
          decoration: BoxDecoration(
            color: context.appColor(AppColors.mintLight, surface: true),
            borderRadius: BorderRadius.circular(12.r),
          ),
          child: AppText(
            LocaleKeys.search,
            style: AppTextStyles.extraBold.copyWith(
              color: context.appColor(AppColors.sokoonTeal),
              fontSize: 12.sp,
            ),
          ),
        ),
      ).paddingOnlyDirectional(start: 8.w),
      suffixIcon: controller == null
          ? Icon(
              Icons.search_rounded,
              color: context.appColor(AppColors.sokoonMuted),
              size: 20.r,
            )
          : ValueListenableBuilder<TextEditingValue>(
              valueListenable: controller!,
              builder: (context, value, _) => value.text.isEmpty
                  ? Icon(
                      Icons.search_rounded,
                      color: context.appColor(AppColors.sokoonMuted),
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
                        color: context.appColor(AppColors.sokoonGray),
                        size: 20.r,
                      ),
                    ),
            ),
    );
  }
}
