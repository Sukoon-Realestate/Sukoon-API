import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/widgets/app_text.dart';

class HomeSearchBox extends StatelessWidget {
  const HomeSearchBox({required this.onPressed, super.key});

  final VoidCallback onPressed;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onPressed,
      child: Container(
        height: 52.h,
        padding: EdgeInsetsDirectional.only(start: 16.w, end: 8.w),
        decoration: BoxDecoration(
          color: AppColors.white,
          borderRadius: BorderRadius.circular(16.r),
          border: Border.all(color: AppColors.sokoonBorder),
        ),
        child: Row(
          spacing: 12.w,
          children: [
            Icon(
              Icons.search_rounded,
              color: AppColors.sokoonMuted,
              size: 20.r,
            ),
            Expanded(
              child: AppText(
                LocaleKeys.tenantHomeSearchAreaHint,
                color: AppColors.sokoonMuted,
                fontSize: 14.sp,
                fontWeight: FontWeight.w400,
                overflow: TextOverflow.ellipsis,
              ),
            ),
            Container(
              width: 34.r,
              height: 34.r,
              decoration: BoxDecoration(
                color: AppColors.sokoonTeal,
                borderRadius: BorderRadius.circular(12.r),
              ),
              child: Icon(
                Icons.tune_rounded,
                color: AppColors.white,
                size: 17.r,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
