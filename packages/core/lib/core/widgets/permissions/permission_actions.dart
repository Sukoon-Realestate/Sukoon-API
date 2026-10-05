import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';

import '../../../config/language/locale_keys.g.dart';
import '../../../config/res/config_imports.dart';
import '../../extensions/sized_box_helper.dart';
import '../app_text.dart';
import '../buttons/default_button.dart';

class PermissionActions extends StatelessWidget {
  const PermissionActions({
    super.key,
    required this.allowLabel,
    required this.color,
    required this.shadowColor,
    required this.onAllowPressed,
    required this.onNotNowPressed,
  });

  final String allowLabel;
  final Color color;
  final Color shadowColor;
  final VoidCallback onAllowPressed;
  final VoidCallback onNotNowPressed;

  @override
  Widget build(BuildContext context) {
    final BorderRadius radius = BorderRadius.circular(12.r);

    return Column(
      mainAxisSize: MainAxisSize.min,
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        DecoratedBox(
          decoration: BoxDecoration(
            borderRadius: radius,
            boxShadow: [
              BoxShadow(
                color: shadowColor,
                blurRadius: 16.r,
                offset: Offset(0, 4.h),
              ),
            ],
          ),
          child: DefaultButton(
            onTap: onAllowPressed,
            color: color,
            borderRadius: radius,
            width: double.infinity,
            minHeight: 48.h,
            padding: EdgeInsets.symmetric(horizontal: 16.w, vertical: 12.h),
            isFitted: false,
            customChild: AppText(
              allowLabel,
              color: AppColors.white,
              fontSize: 15.sp,
              fontWeight: FontWeight.w700,
              textAlign: TextAlign.center,
              height: 1.5,
            ),
          ),
        ),
        10.szH,
        DefaultButton(
          onTap: onNotNowPressed,
          color: context.appColor(AppColors.white, surface: true),
          borderRadius: radius,
          borderColor: context.appColor(AppColors.sokoonBorder),
          borderWidth: 1.5,
          width: double.infinity,
          minHeight: 44.h,
          padding: EdgeInsets.symmetric(horizontal: 16.w, vertical: 11.h),
          isFitted: false,
          customChild: AppText(
            LocaleKeys.permissionNotNow,
            color: context.appColor(AppColors.sokoonNavy),
            fontSize: 14.sp,
            fontWeight: FontWeight.w500,
            textAlign: TextAlign.center,
            height: 1.5,
          ),
        ),
      ],
    );
  }
}
