import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/helpers/text_style_manager.dart';
import 'package:melos_core/core/helpers/validators.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:melos_core/core/widgets/buttons/app_loading_button.dart';
import 'package:sokoun_app/shared_widgets/email_field.dart';

import 'forgot_password_intro.dart';
import 'forgot_password_security_hint.dart';

class ForgotPasswordForm extends StatelessWidget {
  const ForgotPasswordForm({
    super.key,
    required this.formKey,
    required this.emailController,
    required this.hasSubmittedInvalidEmail,
    required this.isEmailValid,
    required this.onEmailChanged,
    required this.onSubmit,
    required this.onBackToLogin,
  });

  final GlobalKey<FormState> formKey;
  final TextEditingController emailController;
  final bool hasSubmittedInvalidEmail;
  final bool isEmailValid;
  final VoidCallback onEmailChanged;
  final Future<void> Function(BuildContext context) onSubmit;
  final VoidCallback onBackToLogin;

  @override
  Widget build(BuildContext context) {
    final Color accentColor = AppColors.sokoonTeal;

    return Form(
      key: formKey,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          const ForgotPasswordIntro(),
          30.szH,
          SokoonEmailField(
            controller: emailController,
            hintText: 'ahmed@gmail.com',
            accentColor: accentColor,
            hasError: hasSubmittedInvalidEmail,
            action: TextInputAction.done,
            prefixIcon: Icon(
              Icons.mail_outline_rounded,
              color: AppColors.sokoonMuted,
              size: 20.r,
            ),
            suffixIcon: isEmailValid
                ? Icon(
                    Icons.check_circle_rounded,
                    color: accentColor,
                    size: 20.r,
                  )
                : null,
            validator: Validators.validateEmail,
            onChanged: (_) => onEmailChanged(),
            onSubmitted: (_) => onSubmit(context),
          ),
          7.szH,
          AppText(
            LocaleKeys.forgotPasswordEmailHint,
            style: AppTextStyles.medium11.copyWith(
              color: AppColors.sokoonGray,
              fontSize: 11.sp,
              height: 1.45,
            ),
          ),
          22.szH,
          AppLoadingButton(
            asyncCall: onSubmit,
            title: LocaleKeys.sendRecoveryLink,
            buttonColor: accentColor,
            textColor: AppColors.white,
            borderRadius: 14.r,
            height: 52.h,
            textStyle: AppTextStyles.extraBold.copyWith(fontSize: 16.sp),
            icon: Icon(Icons.send_rounded, color: AppColors.white, size: 18.r),
          ),
          18.szH,
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Flexible(
                child: AppText(
                  LocaleKeys.rememberedPassword,
                  style: AppTextStyles.medium12.copyWith(
                    color: AppColors.sokoonGray,
                    fontSize: 12.sp,
                    height: 1.45,
                  ),
                ),
              ),
              4.szW,
              TextButton(
                onPressed: onBackToLogin,
                style: TextButton.styleFrom(
                  minimumSize: Size.zero,
                  padding: EdgeInsets.zero,
                  tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                ),
                child: AppText(
                  LocaleKeys.login,
                  style: AppTextStyles.extraBold.copyWith(
                    color: accentColor,
                    fontSize: 12.sp,
                    decoration: TextDecoration.underline,
                  ),
                ),
              ),
            ],
          ),
          28.szH,
          const ForgotPasswordSecurityHint(),
        ],
      ),
    );
  }
}
