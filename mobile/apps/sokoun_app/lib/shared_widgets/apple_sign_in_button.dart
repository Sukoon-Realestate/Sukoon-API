import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/helpers/text_style_manager.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:melos_core/core/widgets/buttons/default_button.dart';

class SokoonAppleSignInButton extends StatelessWidget {
  const SokoonAppleSignInButton({super.key, this.onTap, this.label});

  final VoidCallback? onTap;
  final String? label;

  @override
  Widget build(BuildContext context) {
    return DefaultButton(
      onTap: onTap,
      color: context.appColor(AppColors.white, surface: true),
      borderColor: context.appColor(AppColors.sokoonBorder),
      borderRadius: BorderRadius.circular(12.r),
      height: 48.h,
      width: double.infinity,
      customChild: Row(
        mainAxisAlignment: MainAxisAlignment.center,
        mainAxisSize: MainAxisSize.min,
        spacing: 10.w,
        children: [
          Icon(
            Icons.apple,
            color: context.appColor(AppColors.sokoonNavy),
            size: 20.r,
          ),
          Flexible(
            child: AppText(
              label ?? LocaleKeys.continueWithApple,
              style: AppTextStyles.bold14.copyWith(
                color: context.appColor(AppColors.sokoonNavy),
                fontSize: 14.sp,
                height: 1.45,
              ),
              overflow: TextOverflow.ellipsis,
            ),
          ),
        ],
      ),
      textStyle: AppTextStyles.medium13.copyWith(
        fontSize: FontSize.s13,
        height: 1.45,
      ),
    );
  }
}
