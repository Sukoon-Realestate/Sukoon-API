import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';

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
      decoration: const BoxDecoration(
        color: AppColors.white,
        border: Border(bottom: BorderSide(color: AppColors.grayPale)),
      ),
      child: Row(
        textDirection: TextDirection.ltr,
        children: [
          Expanded(
            child: Container(
              height: 44.h,
              padding: EdgeInsets.symmetric(horizontal: 14.w),
              decoration: BoxDecoration(
                color: AppColors.grayBackground,
                borderRadius: BorderRadius.circular(22.r),
              ),
              child: Row(
                textDirection: TextDirection.ltr,
                children: [
                  Icon(
                    Icons.search_rounded,
                    color: AppColors.sokoonGray,
                    size: 20.r,
                  ),
                  8.szW,
                  Expanded(
                    child: TextField(
                      controller: controller,
                      onChanged: onChanged,
                      onSubmitted: onSubmitted,
                      textInputAction: TextInputAction.search,
                      textAlign: TextAlign.right,
                      style: TextStyle(
                        color: AppColors.sokoonNavy,
                        fontSize: 14.sp,
                        fontWeight: FontWeight.w600,
                      ),
                      decoration: InputDecoration(
                        isCollapsed: true,
                        border: InputBorder.none,
                        hintText: 'شقة مفروشة مدينة نصر…',
                        hintStyle: TextStyle(
                          color: AppColors.sokoonGray,
                          fontSize: 14.sp,
                          fontWeight: FontWeight.w400,
                        ),
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
          10.szW,
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
                color: AppColors.sokoonTeal,
                size: 21.r,
              ),
            ),
          ),
        ],
      ),
    );
  }
}
