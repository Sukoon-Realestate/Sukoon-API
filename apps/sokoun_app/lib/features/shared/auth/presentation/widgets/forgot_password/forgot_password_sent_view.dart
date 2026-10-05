import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/align_helper.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/helpers/text_style_manager.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:melos_core/core/widgets/buttons/app_loading_button.dart';
import 'package:melos_core/core/widgets/buttons/default_button.dart';

import '../shared/auth_resend_timer.dart';

class ForgotPasswordSentView extends StatefulWidget {
  const ForgotPasswordSentView({
    super.key,
    this.message = '',
    required this.maskedEmail,
    required this.onResend,
    required this.onChangeEmail,
  });

  final String message;
  final String maskedEmail;
  final Future<void> Function(VoidCallback onSuccess) onResend;
  final VoidCallback onChangeEmail;

  @override
  State<ForgotPasswordSentView> createState() => _ForgotPasswordSentViewState();
}

class _ForgotPasswordSentViewState extends State<ForgotPasswordSentView> {
  final ValueNotifier<bool> _canResend = ValueNotifier<bool>(false);

  Future<void> _resend(BuildContext _) async {
    if (!_canResend.value) {
      return;
    }

    await widget.onResend(() {
      if (!mounted) {
        return;
      }

      _canResend.value = false;
    });
  }

  @override
  void dispose() {
    _canResend.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final Color accentColor = AppColors.sokoonTeal;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Container(
          width: 96.r,
          height: 96.r,
          decoration: BoxDecoration(
            color: AppColors.mintLight,
            borderRadius: BorderRadius.circular(28.r),
          ),
          child: Stack(
            alignment: Alignment.center,
            children: [
              Icon(
                Icons.mark_email_read_outlined,
                color: accentColor,
                size: 44.r,
              ),
              PositionedDirectional(
                end: 13.w,
                bottom: 13.h,
                child: Container(
                  width: 22.r,
                  height: 22.r,
                  decoration: const BoxDecoration(
                    color: AppColors.green,
                    shape: BoxShape.circle,
                  ),
                  child: Icon(
                    Icons.check_rounded,
                    color: AppColors.white,
                    size: 15.r,
                  ),
                ),
              ),
            ],
          ),
        ).centerWidget,
        20.szH,
        AppText(
          widget.message,
          style: AppTextStyles.bold.copyWith(
            color: AppColors.sokoonNavy,
            fontSize: 20.sp,
          ),
          textAlign: TextAlign.center,
        ),
        8.szH,
        AppText(
          LocaleKeys.resetLinkSentDescription,
          style: AppTextStyles.medium13.copyWith(
            color: AppColors.sokoonGray,
            fontSize: 13.sp,
            height: 1.45,
          ),
          textAlign: TextAlign.center,
        ),
        5.szH,
        AppText(
          widget.maskedEmail,
          style: AppTextStyles.extraBold.copyWith(
            color: accentColor,
            fontSize: 14.sp,
          ),
          textAlign: TextAlign.center,
        ),
        30.szH,
        _RecoveryStep(
          number: 1,
          title: LocaleKeys.openYourEmail,
          description: LocaleKeys.lookForSokoonEmail,
        ),
        14.szH,
        _RecoveryStep(
          number: 2,
          title: LocaleKeys.tapTheLink,
          description: LocaleKeys.recoveryLinkValidFor24Hours,
        ),
        14.szH,
        _RecoveryStep(
          number: 3,
          title: LocaleKeys.createNewPassword,
          description: LocaleKeys.minimumEightCharacters,
        ),
        28.szH,
        Container(
          padding: EdgeInsets.all(16.r),
          decoration: BoxDecoration(
            color: AppColors.white,
            borderRadius: BorderRadius.circular(14.r),
            border: Border.all(color: AppColors.grayPale),
          ),
          child: Column(
            children: [
              AppText(
                LocaleKeys.emailNotReceived,
                style: AppTextStyles.extraBold13.copyWith(
                  color: AppColors.sokoonNavy,
                  fontSize: 13.sp,
                  height: 1.45,
                ),
                textAlign: TextAlign.center,
              ),
              4.szH,
              AppText(
                LocaleKeys.checkSpamFirst,
                style: AppTextStyles.medium11.copyWith(
                  color: AppColors.sokoonGray,
                  fontSize: 11.sp,
                  height: 1.45,
                ),
                textAlign: TextAlign.center,
              ),
              12.szH,
              ValueListenableBuilder<bool>(
                valueListenable: _canResend,
                builder: (context, canResend, _) => Column(
                  spacing: 14.h,
                  children: [
                    AuthResendTimer(
                      canResend: canResend,
                      onTimerEnds: () {
                        if (mounted) {
                          _canResend.value = true;
                        }
                      },
                    ),
                    IgnorePointer(
                      ignoring: !canResend,
                      child: AppLoadingButton(
                        asyncCall: _resend,
                        title: LocaleKeys.resend,
                        buttonColor: canResend
                            ? accentColor
                            : AppColors.sokoonMuted,
                        textColor: AppColors.white,
                        borderRadius: 12.r,
                        height: 46.h,
                        textStyle: AppTextStyles.bold14.copyWith(
                          fontSize: 14.sp,
                          height: 1.45,
                        ),
                        icon: Icon(
                          Icons.refresh_rounded,
                          color: AppColors.white,
                          size: 18.r,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
        12.szH,
        DefaultButton(
          onTap: widget.onChangeEmail,
          height: 50.h,
          width: double.infinity,
          color: AppColors.white,
          borderColor: accentColor,
          borderRadius: BorderRadius.circular(14.r),
          customChild: AppText(
            LocaleKeys.changeEmail,
            style: AppTextStyles.extraBold.copyWith(
              color: accentColor,
              fontSize: 14.sp,
            ),
          ),
          textStyle: AppTextStyles.medium13.copyWith(
            fontSize: FontSize.s13,
            height: 1.45,
          ),
        ),
      ],
    );
  }
}

class _RecoveryStep extends StatelessWidget {
  const _RecoveryStep({
    required this.number,
    required this.title,
    required this.description,
  });

  final int number;
  final String title;
  final String description;

  @override
  Widget build(BuildContext context) {
    final Color accentColor = AppColors.sokoonTeal;

    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      spacing: 12.w,
      children: [
        Container(
          width: 34.r,
          height: 34.r,
          alignment: Alignment.center,
          decoration: BoxDecoration(
            color: AppColors.mintLight,
            shape: BoxShape.circle,
          ),
          child: AppText(
            '$number',
            style: AppTextStyles.bold13.copyWith(
              color: accentColor,
              fontSize: 13.sp,
              height: 1.45,
            ),
          ),
        ),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            spacing: 3.h,
            children: [
              AppText(
                title,
                style: AppTextStyles.extraBold13.copyWith(
                  color: AppColors.sokoonNavy,
                  fontSize: 13.sp,
                  height: 1.45,
                ),
              ),
              AppText(
                description,
                style: AppTextStyles.medium11.copyWith(
                  color: AppColors.sokoonGray,
                  fontSize: 11.sp,
                  height: 1.45,
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }
}
