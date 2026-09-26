import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
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
        color: AppColors.white,
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
                  color: AppColors.grayPale,
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
                  color: AppColors.sokoonTeal,
                ),
              ),
            ),
            16.szH,
            AppText(
              LocaleKeys.unauthenticatedSheetTitle,
              color: AppColors.sokoonNavy,
              fontSize: 18.sp,
              fontWeight: FontWeight.w800,
              textAlign: TextAlign.center,
            ),
            8.szH,
            Align(
              alignment: Alignment.center,
              child: ConstrainedBox(
                constraints: BoxConstraints(maxWidth: 280.w),
                child: AppText(
                  LocaleKeys.unauthenticatedSheetDescription,
                  color: AppColors.sokoonGray,
                  fontSize: 13.sp,
                  fontWeight: FontWeight.w400,
                  textAlign: TextAlign.center,
                  height: 1.6,
                ),
              ),
            ),
            28.szH,
            DefaultButton(
              onTap: () => Go.back(UnauthenticatedSheetAction.login),
              title: LocaleKeys.login,
              color: AppColors.sokoonTeal,
              textColor: AppColors.white,
              borderRadius: BorderRadius.circular(14.r),
              height: 52.h,
              width: double.infinity,
              fontSize: 16.sp,
              fontWeight: FontWeight.w700,
              isFitted: false,
            ),
            10.szH,
            SizedBox(
              height: 48.h,
              child: OutlinedButton(
                onPressed: () =>
                    Go.back(UnauthenticatedSheetAction.createAccount),
                style: OutlinedButton.styleFrom(
                  foregroundColor: AppColors.sokoonNavy,
                  side: BorderSide(color: AppColors.grayPale, width: 1.5.w),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12.r),
                  ),
                ),
                child: AppText(
                  LocaleKeys.createAccount,
                  color: AppColors.sokoonNavy,
                  fontSize: 15.sp,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
