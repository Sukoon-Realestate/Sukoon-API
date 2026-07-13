import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/widgets/app_text.dart';

class LoginDivider extends StatelessWidget {
  const LoginDivider({super.key});

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        const Expanded(child: Divider(color: AppColors.grayPale, height: 1)),
        Padding(
          padding: EdgeInsets.symmetric(horizontal: 12.w),
          child: AppText(
            LocaleKeys.or,
            color: AppColors.sokoonGray,
            fontSize: 12.sp,
            fontWeight: FontWeight.w500,
          ),
        ),
        const Expanded(child: Divider(color: AppColors.grayPale, height: 1)),
      ],
    );
  }
}
