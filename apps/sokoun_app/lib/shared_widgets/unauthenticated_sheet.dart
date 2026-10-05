import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/helpers/text_style_manager.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:melos_core/core/widgets/buttons/default_button.dart';

enum UnauthenticatedSheetAction { login, createAccount }

class UnauthenticatedSheet extends StatelessWidget {
  const UnauthenticatedSheet({super.key});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: EdgeInsets.fromLTRB(24.w, 24.h, 24.w, 0),
      decoration: BoxDecoration(
        color: context.appColor(AppColors.white, surface: true),
        borderRadius: BorderRadius.vertical(top: Radius.circular(24.r)),
      ),
      child: SafeArea(
        top: false,
        minimum: EdgeInsets.only(bottom: 40.h),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Align(
              alignment: Alignment.center,
              child: Container(
                width: 40.w,
                height: 4.h,
                decoration: BoxDecoration(
                  color: context.appColor(AppColors.grayPale, surface: true),
                  borderRadius: BorderRadius.circular(2.r),
                ),
              ),
            ),
            24.szH,
            Align(
              alignment: Alignment.center,
              child: Container(
                width: 64.r,
                height: 64.r,
                decoration: BoxDecoration(
                  color: AppColors.tealAlpha07,
                  borderRadius: BorderRadius.circular(20.r),
                ),
                alignment: Alignment.center,
                child: Icon(
                  Icons.lock_outline_rounded,
                  size: 30.r,
                  color: context.appColor(AppColors.sokoonTeal),
                ),
              ),
            ),
            16.szH,
            AppText(
              LocaleKeys.unauthenticatedSheetTitle,
              style: AppTextStyles.extraBold.copyWith(
                color: context.appColor(AppColors.sokoonNavy),
                fontSize: 18.sp,
              ),
              textAlign: TextAlign.center,
            ),
            8.szH,
            Align(
              alignment: Alignment.center,
              child: ConstrainedBox(
                constraints: BoxConstraints(maxWidth: 280.w),
                child: AppText(
                  LocaleKeys.unauthenticatedSheetDescription,
                  style: AppTextStyles.regular13.copyWith(
                    color: context.appColor(AppColors.sokoonGray),
                    fontSize: 13.sp,
                    height: 1.6,
                  ),
                  textAlign: TextAlign.center,
                ),
              ),
            ),
            28.szH,
            DefaultButton(
              onTap: () => Go.back(UnauthenticatedSheetAction.login),
              title: LocaleKeys.login,
              color: context.appColor(AppColors.sokoonTeal, surface: true),
              textColor: AppColors.white,
              borderRadius: BorderRadius.circular(14.r),
              height: 52.h,
              width: double.infinity,
              textStyle: AppTextStyles.bold16.copyWith(
                fontSize: 16.sp,
                height: 1.45,
              ),
              isFitted: false,
            ),
            10.szH,
            SizedBox(
              height: 48.h,
              child: OutlinedButton(
                onPressed: () =>
                    Go.back(UnauthenticatedSheetAction.createAccount),
                style: OutlinedButton.styleFrom(
                  foregroundColor: context.appColor(AppColors.sokoonNavy),
                  side: BorderSide(
                    color: context.appColor(AppColors.grayPale),
                    width: 1.5.w,
                  ),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12.r),
                  ),
                ),
                child: AppText(
                  LocaleKeys.createAccount,
                  style: AppTextStyles.semiBold.copyWith(
                    color: context.appColor(AppColors.sokoonNavy),
                    fontSize: 15.sp,
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
