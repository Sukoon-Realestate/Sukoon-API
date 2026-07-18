import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:melos_core/core/widgets/buttons/default_button.dart';
import 'package:sokoun_app/features/auth/data/social_auth_service/facebook_sign_in.dart';

class AppFacebookSignInButton extends StatelessWidget {
  const AppFacebookSignInButton({super.key, required this.onSuccess});

  final Future<void> Function(String userToken) onSuccess;

  @override
  Widget build(BuildContext context) {
    return DefaultButton(
      onTap: () async {
        final String userToken = await FacebookSignService.instance.authorize();
        if (userToken.isNotEmpty) {
          await onSuccess.call(userToken);
        }
      },
      color: AppColors.white,
      borderColor: AppColors.sokoonBorder,
      borderRadius: BorderRadius.circular(12.r),
      height: 48.h,
      width: double.infinity,
      customChild: Row(
        mainAxisAlignment: MainAxisAlignment.center,
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(Icons.facebook, color: AppColors.facebookBlue, size: 20.r),
          SizedBox(width: 10.w),
          Flexible(
            child: AppText(
              LocaleKeys.continueWithFacebook,
              color: AppColors.facebookBlue,
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
