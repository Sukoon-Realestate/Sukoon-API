import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
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
      color: AppColors.white,
      borderColor: AppColors.sokoonBorder,
      borderRadius: BorderRadius.circular(12.r),
      height: 48.h,
      width: double.infinity,
      customChild: Row(
        mainAxisAlignment: MainAxisAlignment.center,
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(Icons.apple, color: AppColors.sokoonNavy, size: 20.r),
          SizedBox(width: 10.w),
          Flexible(
            child: AppText(
              label ?? LocaleKeys.continueWithApple,
              color: AppColors.sokoonNavy,
              fontSize: 14.sp,
              fontWeight: FontWeight.w700,
              overflow: TextOverflow.ellipsis,
            ),
          ),
        ],
      ),
    );
  }
}
