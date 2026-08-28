import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/align_helper.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:melos_core/core/widgets/buttons/default_button.dart';

import '../widgets/auth_scaffold.dart';
import '../widgets/otp/otp_code_field.dart';
import '../widgets/otp/otp_header.dart';
import '../widgets/otp/otp_resend_timer.dart';

class OtpScreen extends StatefulWidget {
  const OtpScreen({
    super.key,
    this.maskedEmail = 'ah****@gmail.com',
    this.onConfirm,
    this.onResend,
  });

  final String maskedEmail;
  final ValueChanged<String>? onConfirm;
  final VoidCallback? onResend;

  @override
  State<OtpScreen> createState() => _OtpScreenState();
}

class _OtpScreenState extends State<OtpScreen> {
  final _otpController = TextEditingController();
  int _timerResetKey = 0;
  bool _canResend = false;

  @override
  void dispose() {
    _otpController.dispose();
    super.dispose();
  }

  bool get _isCodeComplete => _otpController.text.length == 6;

  void _confirm() {
    if (!_isCodeComplete) {
      return;
    }

    widget.onConfirm?.call(_otpController.text);
  }

  void _resend() {
    widget.onResend?.call();
    setState(() {
      _canResend = false;
      _timerResetKey++;
    });
  }

  @override
  Widget build(BuildContext context) {
    return AuthScaffold(
      showBackButton: false,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          OtpHeader(),
          36.szH,
          Container(
            width: 64.r,
            height: 64.r,
            decoration: BoxDecoration(
              color: AppColors.tealOrGoldAlphaBasedRole,
              borderRadius: BorderRadius.circular(18.r),
            ),
            child: Icon(
              Icons.mail_outline_rounded,
              color: AppColors.tealOrGoldBasedRole,
              size: 30.r,
            ),
          ).centerWidget,
          18.szH,
          AppText(
            LocaleKeys.otpSentToEmail,
            color: AppColors.sokoonNavy,
            fontSize: 18.sp,
            fontWeight: FontWeight.w800,
            textAlign: TextAlign.center,
          ),
          8.szH,
          AppText(
            widget.maskedEmail,
            color: AppColors.tealOrGoldBasedRole,
            fontSize: 14.sp,
            fontWeight: FontWeight.w700,
            textAlign: TextAlign.center,
          ),
          6.szH,
          TextButton(
            onPressed: () => Go.back(),
            style: TextButton.styleFrom(
              minimumSize: Size.zero,
              padding: EdgeInsets.zero,
              tapTargetSize: MaterialTapTargetSize.shrinkWrap,
            ),
            child: AppText(
              LocaleKeys.changeEmail,
              color: AppColors.sokoonGray,
              fontSize: 12.sp,
              fontWeight: FontWeight.w700,
              decoration: TextDecoration.underline,
            ),
          ),
          26.szH,
          OtpCodeField(
            controller: _otpController,
            onChanged: (_) => setState(() {}),
            onCompleted: (_) => _confirm(),
          ),
          20.szH,
          OtpResendTimer(
            timerResetKey: _timerResetKey,
            canResend: _canResend,
            onTimerEnds: () {
              if (mounted) {
                setState(() {
                  _canResend = true;
                });
              }
            },
          ),
          18.szH,
          DefaultButton(
            onTap: _isCodeComplete ? _confirm : null,
            title: LocaleKeys.confirmLogin,
            color: _isCodeComplete
                ? AppColors.tealOrGoldBasedRole
                : AppColors.sokoonMuted,
            textColor: AppColors.white,
            borderRadius: BorderRadius.circular(14.r),
            height: 52.h,
            width: double.infinity,
            fontSize: 16.sp,
            fontWeight: FontWeight.w700,
          ),
          14.szH,
          Center(
            child: TextButton(
              onPressed: _canResend ? _resend : null,
              style: TextButton.styleFrom(
                minimumSize: Size.zero,
                padding: EdgeInsets.symmetric(horizontal: 8.w, vertical: 4.h),
                tapTargetSize: MaterialTapTargetSize.shrinkWrap,
              ),
              child: AppText(
                LocaleKeys.resendCode,
                color: _canResend
                    ? AppColors.tealOrGoldBasedRole
                    : AppColors.sokoonMuted,
                fontSize: 13.sp,
                fontWeight: FontWeight.w700,
              ),
            ),
          ),
        ],
      ),
    );
  }
}
