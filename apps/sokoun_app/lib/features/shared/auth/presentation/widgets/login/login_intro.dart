import 'package:melos_core/core/helpers/text_style_manager.dart';
import 'package:melos_core/core/widgets/app_logo_widget.dart';
import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/widgets/app_text.dart';

class LoginIntro extends StatelessWidget {
  const LoginIntro({super.key});

  @override
  Widget build(BuildContext context) {
    return Column(
      spacing: 12.h,
      children: [
        AppLogoWidget(),
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
