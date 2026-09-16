import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/align_helper.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:melos_core/core/widgets/buttons/app_loading_button.dart';
import 'package:sokoun_app/features/shared/auth/data/models/otp.dart';
import 'package:sokoun_app/features/shared/auth/presentation/cubits/otp.dart';

import '../widgets/auth_scaffold.dart';
import '../widgets/otp/otp_code_field.dart';
import '../widgets/otp/otp_header.dart';
import '../widgets/otp/otp_resend_timer.dart';

class OtpScreen extends StatefulWidget {
  const OtpScreen({super.key, required this.email, required this.onVerified});

  final String email;
  final VoidCallback onVerified;

  @override
  State<OtpScreen> createState() => _OtpScreenState();
}

class _OtpScreenState extends State<OtpScreen> {
  final TextEditingController _otpController = TextEditingController();
  late final OtpCubit _otpCubit;
  int _timerResetKey = 0;
  bool _canResend = false;
  bool _isResending = false;

  @override
  void initState() {
    super.initState();
    _otpCubit = OtpCubit();
  }

  @override
  void dispose() {
    _otpController.dispose();
    unawaited(_otpCubit.close());
    super.dispose();
  }

  bool get _isCodeComplete => _otpController.text.length == 6;

  String get _maskedEmail {
    final List<String> parts = widget.email.trim().split('@');
    if (parts.length != 2 || parts.first.isEmpty) {
      return widget.email;
    }

    final String localPart = parts.first;
    final String visiblePart = localPart.length > 1
        ? localPart.substring(0, 2)
        : localPart;
    return '$visiblePart****@${parts.last}';
  }

  Future<void> _confirm(BuildContext _) async {
    if (!_isCodeComplete) {
      return;
    }

    await _otpCubit.verifyOtp(
      body: VerifyOtpBody(email: widget.email.trim(), otp: _otpController.text),
      onSuccess: widget.onVerified,
    );
  }

  Future<void> _resend() async {
    if (!_canResend || _isResending) {
      return;
    }

    setState(() => _isResending = true);
    try {
      await _otpCubit.resendOtp(
        body: ResendOtpBody(email: widget.email.trim()),
        onSuccess: () {
          if (!mounted) {
            return;
          }

          _otpController.clear();
          setState(() {
            _canResend = false;
            _timerResetKey++;
          });
        },
      );
    } finally {
      if (mounted) {
        setState(() => _isResending = false);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return AuthScaffold(
      showBackButton: false,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          const OtpHeader(),
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
            _maskedEmail,
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
          IgnorePointer(
            ignoring: !_isCodeComplete,
            child: AppLoadingButton(
              asyncCall: _confirm,
              title: LocaleKeys.confirmLogin,
              buttonColor: _isCodeComplete
                  ? AppColors.tealOrGoldBasedRole
                  : AppColors.sokoonMuted,
              textColor: AppColors.white,
              borderRadius: 14.r,
              height: 52.h,
              width: double.infinity,
              fontSize: 16.sp,
              fontWeight: FontWeight.w700,
            ),
          ),
          14.szH,
          TextButton(
            onPressed: _canResend && !_isResending ? _resend : null,
            style: TextButton.styleFrom(
              minimumSize: Size.zero,
              padding: EdgeInsets.symmetric(horizontal: 8.w, vertical: 4.h),
              tapTargetSize: MaterialTapTargetSize.shrinkWrap,
            ),
            child: _isResending
                ? SizedBox.square(
                    dimension: 16.r,
                    child: CircularProgressIndicator(
                      strokeWidth: 2.r,
                      color: AppColors.tealOrGoldBasedRole,
                    ),
                  )
                : AppText(
                    LocaleKeys.resendCode,
                    color: _canResend
                        ? AppColors.tealOrGoldBasedRole
                        : AppColors.sokoonMuted,
                    fontSize: 13.sp,
                    fontWeight: FontWeight.w700,
                  ),
          ).centerWidget,
        ],
      ),
    );
  }
}
