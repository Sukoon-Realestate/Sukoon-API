import 'package:melos_core/core/widgets/text_fields/default_text_field.dart';
import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/helpers/text_style_manager.dart';

class ResultsSearchHeader extends StatelessWidget {
  const ResultsSearchHeader({
    super.key,
    this.controller,
    this.onChanged,
    this.onSubmitted,
    this.onFiltersTap,
  });

  final TextEditingController? controller;
  final ValueChanged<String>? onChanged;
  final ValueChanged<String>? onSubmitted;
  final VoidCallback? onFiltersTap;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: EdgeInsets.symmetric(horizontal: 14.w, vertical: 10.h),
      decoration: BoxDecoration(
        color: context.appColor(AppColors.white, surface: true),
        border: Border(
          bottom: BorderSide(color: context.appColor(AppColors.grayPale)),
        ),
      ),
      child: Row(
        spacing: 10.w,
        children: [
          Expanded(
            child: Container(
              height: 44.h,
              padding: EdgeInsets.symmetric(horizontal: 14.w),
              decoration: BoxDecoration(
                color: context.appColor(
                  AppColors.grayBackground,
                  surface: true,
                ),
                borderRadius: BorderRadius.circular(22.r),
              ),
              child: Row(
                spacing: 8.w,
                children: [
                  Icon(
                    Icons.search_rounded,
                    color: context.appColor(AppColors.sokoonGray),
                    size: 20.r,
                  ),
                  Expanded(
                    child: DefaultTextField(
                      controller: controller,
                      onChanged: (value) => onChanged?.call(value ?? ''),
                      onSubmitted: (value) => onSubmitted?.call(value ?? ''),
                      action: TextInputAction.search,
                      textAlign: TextAlign.start,
                      style: AppTextStyles.semiBold.copyWith(
                        color: context.appColor(AppColors.sokoonNavy),
                        fontSize: 14.sp,
                      ),
                      decoration: InputDecoration(
                        isCollapsed: true,
                        border: InputBorder.none,
                        hintText: LocaleKeys.tenantSearchResultsHint,
                        hintStyle: AppTextStyles.regular14.copyWith(
                          color: context.appColor(AppColors.sokoonGray),
                          fontSize: 14.sp,
                          height: 1.45,
                        ),
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
          GestureDetector(
            onTap: onFiltersTap,
            behavior: HitTestBehavior.opaque,
            child: Container(
              width: 44.r,
              height: 44.r,
              decoration: BoxDecoration(
                color: AppColors.tealAlpha07,
                borderRadius: BorderRadius.circular(14.r),
                border: Border.all(color: AppColors.tealAlpha19),
              ),
              child: Icon(
                Icons.tune_rounded,
                color: context.appColor(AppColors.sokoonTeal),
                size: 21.r,
              ),
            ),
          ),
        ],
      ),
    );
  }
}
