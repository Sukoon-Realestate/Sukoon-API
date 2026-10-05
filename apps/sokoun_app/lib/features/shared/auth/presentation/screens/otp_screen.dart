import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/align_helper.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/helpers/text_style_manager.dart';
import 'package:melos_core/core/helpers/validators.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:melos_core/core/widgets/buttons/app_loading_button.dart';
import 'package:melos_core/core/widgets/custom_loading.dart';
import 'package:melos_core/core/widgets/first_validation_error_form.dart';
import 'package:sokoun_app/features/shared/auth/data/models/otp.dart';
import 'package:sokoun_app/features/shared/auth/presentation/cubits/otp.dart';

import '../widgets/auth_scaffold.dart';
import '../widgets/otp/otp_code_field.dart';
import '../widgets/shared/auth_resend_timer.dart';

class OtpScreen extends StatefulWidget {
  const OtpScreen({super.key, required this.email, required this.onVerified});

  final String email;
  final VoidCallback onVerified;

  @override
  State<OtpScreen> createState() => _OtpScreenState();
}

class _OtpScreenState extends State<OtpScreen> {
  final GlobalKey _otpFieldKey = GlobalKey();
  final TextEditingController _otpController = TextEditingController();
  late final OtpCubit _otpCubit;
  final ValueNotifier<({bool canResend, bool isResending})> _uiState =
      ValueNotifier<({bool canResend, bool isResending})>((
        canResend: false,
        isResending: false,
      ));

  @override
  void initState() {
    super.initState();
    _otpCubit = OtpCubit();
  }

  @override
  void dispose() {
    _otpController.dispose();
    _uiState.dispose();
    _otpCubit.close();
    super.dispose();
  }

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
    await _otpCubit.verifyOtp(
      body: VerifyOtpBody(email: widget.email, otp: _otpController.text),
      onSuccess: widget.onVerified,
    );
  }

  List<FirstValidationErrorField> _validationFields() => [
    FirstValidationErrorField(
      fieldKey: _otpFieldKey,
      title: LocaleKeys.verificationCode,
      value: _otpController.text,
      validator: Validators.validateOtpCode,
    ),
  ];

  Future<void> _resend() async {
    if (!_uiState.value.canResend || _uiState.value.isResending) {
      return;
    }

    _uiState.value = (canResend: _uiState.value.canResend, isResending: true);
    try {
      await _otpCubit.resendOtp(
        body: ResendOtpBody(email: widget.email.trim()),
        onSuccess: () {
          if (!mounted) {
            return;
          }

          _otpController.clear();
          _uiState.value = (
            canResend: false,
            isResending: _uiState.value.isResending,
          );
        },
      );
    } finally {
      if (mounted) {
        _uiState.value = (
          canResend: _uiState.value.canResend,
          isResending: false,
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return AuthScaffold(
      showBackButton: true,
      title: LocaleKeys.verificationCode,
      child: FirstValidationErrorForm(
        validationFields: _validationFields,
        onValid: () => _confirm(context),
        builder: (context, submit) => Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            36.szH,
            Container(
              width: 64.r,
              height: 64.r,
              decoration: BoxDecoration(
                color: AppColors.mintLight,
                borderRadius: BorderRadius.circular(18.r),
              ),
              child: Icon(
                Icons.mail_outline_rounded,
                color: AppColors.sokoonTeal,
                size: 30.r,
              ),
            ).centerWidget,
            18.szH,
            AppText(
              LocaleKeys.otpSentToEmail,
              style: AppTextStyles.extraBold.copyWith(
                color: AppColors.sokoonNavy,
                fontSize: 18.sp,
              ),
              textAlign: TextAlign.center,
            ),
            8.szH,
            AppText(
              _maskedEmail,
              style: AppTextStyles.bold14.copyWith(
                color: AppColors.sokoonTeal,
                fontSize: 14.sp,
                height: 1.45,
              ),
              textAlign: TextAlign.center,
            ),
            26.szH,
            AppText(
              LocaleKeys.otpCodeExpiresInTenMinutes,
              style: AppTextStyles.regular12.copyWith(
                color: AppColors.sokoonGray,
              ),
              textAlign: TextAlign.center,
            ),
            12.szH,
            ValueListenableBuilder<({bool canResend, bool isResending})>(
              valueListenable: _uiState,
              builder: (context, uiState, _) => Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  OtpCodeField(key: _otpFieldKey, controller: _otpController),
                  20.szH,
                  AuthResendTimer(
                    canResend: uiState.canResend,
                    onTimerEnds: () {
                      if (mounted) {
                        _uiState.value = (
                          canResend: true,
                          isResending: _uiState.value.isResending,
                        );
                      }
                    },
                  ),
                  18.szH,
                  AppLoadingButton(
                    asyncCall: (_) => submit(),
                    title: LocaleKeys.confirmLogin,
                    buttonColor: AppColors.sokoonTeal,
                    textColor: AppColors.white,
                    borderRadius: 14.r,
                    height: 52.h,
                    width: double.infinity,
                    textStyle: AppTextStyles.bold16.copyWith(
                      fontSize: 16.sp,
                      height: 1.45,
                    ),
                  ),
                  14.szH,
                  TextButton(
                    onPressed: uiState.canResend && !uiState.isResending
                        ? _resend
                        : null,
                    style: TextButton.styleFrom(
                      minimumSize: Size.zero,
                      padding: EdgeInsets.symmetric(
                        horizontal: 8.w,
                        vertical: 4.h,
                      ),
                      tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                    ),
                    child: uiState.isResending
                        ? SizedBox.square(
                            dimension: 16.r,
                            child: CustomLoading.showLoadingView(
                              color: AppColors.sokoonTeal,
                              size: 16.r,
                            ),
                          )
                        : AppText(
                            LocaleKeys.resendCode,
                            style: AppTextStyles.bold13.copyWith(
                              color: uiState.canResend
                                  ? AppColors.sokoonTeal
                                  : AppColors.sokoonMuted,
                              fontSize: 13.sp,
                              height: 1.45,
                            ),
                          ),
                  ).centerWidget,
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
