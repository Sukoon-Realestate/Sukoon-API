import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/padding_extension.dart';
import 'package:melos_core/core/helpers/text_style_manager.dart';
import 'package:melos_core/core/widgets/app_text.dart';

class LoginDivider extends StatelessWidget {
  const LoginDivider({super.key});

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Expanded(
          child: Divider(
            color: context.appColor(AppColors.grayPale),
            height: 1,
          ),
        ),
        AppText(
          LocaleKeys.or,
          style: AppTextStyles.medium12.copyWith(
            color: context.appColor(AppColors.sokoonGray),
            fontSize: 12.sp,
            height: 1.45,
          ),
        ).paddingSymmetric(horizontal: 12.w),
        Expanded(
          child: Divider(
            color: context.appColor(AppColors.grayPale),
            height: 1,
          ),
        ),
      ],
    );
  }
}
