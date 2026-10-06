import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/align_helper.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/helpers/text_style_manager.dart';
import 'package:melos_core/core/widgets/app_text.dart';

class ForgotPasswordIntro extends StatelessWidget {
  const ForgotPasswordIntro({super.key});

  @override
  Widget build(BuildContext context) {
    final Color accentColor = context.appColor(AppColors.sokoonTeal);

    return Column(
      children: [
        Container(
          width: 80.r,
          height: 80.r,
          decoration: BoxDecoration(
            color: context.appColor(AppColors.mintLight, surface: true),
            borderRadius: BorderRadius.circular(24.r),
          ),
          child: Icon(
            Icons.lock_reset_rounded,
            color: context.appColor(accentColor),
            size: 38.r,
          ),
        ).centerWidget,
        20.szH,
        AppText(
          LocaleKeys.forgotPassword,
          style: AppTextStyles.bold.copyWith(
            color: context.appColor(AppColors.sokoonNavy),
            fontSize: 20.sp,
          ),
          textAlign: TextAlign.center,
        ),
        8.szH,
        AppText(
          LocaleKeys.forgotPasswordDescription,
          style: AppTextStyles.medium13.copyWith(
            color: context.appColor(AppColors.sokoonGray),
            fontSize: 13.sp,
            height: 1.7,
          ),
          textAlign: TextAlign.center,
        ),
      ],
    );
  }
}
