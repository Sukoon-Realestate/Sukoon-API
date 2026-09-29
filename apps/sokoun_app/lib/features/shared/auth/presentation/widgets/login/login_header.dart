import 'package:melos_core/core/helpers/text_style_manager.dart';
import 'package:melos_core/core/widgets/app_logo_widget.dart';
import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/widgets/app_text.dart';

class LoginHeader extends StatelessWidget {
  const LoginHeader({super.key});

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Container(
          width: 60.r,
          height: 60.r,
          decoration: BoxDecoration(
            color: AppColors.sokoonTeal,
            borderRadius: BorderRadius.circular(16.r),
          ),
          child: AppLogoWidget(color: AppColors.white, size: 32.r),
        ),
        12.szH,
        AppText(
          LocaleKeys.login,
          style: AppTextStyles.bold.copyWith(
            color: AppColors.sokoonNavy,
            fontSize: 22.sp,
          ),
          textAlign: TextAlign.center,
        ),
        4.szH,
        AppText(
          LocaleKeys.welcomeBackToSokoon,
          style: AppTextStyles.medium12.copyWith(
            color: AppColors.sokoonGray,
            fontSize: 12.sp,
            height: 1.45,
          ),
          textAlign: TextAlign.center,
        ),
      ],
    );
  }
}
