import 'package:easy_timer_count/easy_timer_count.dart';
import 'package:easy_timer_count/helpers/time.dart';
import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/helpers/text_style_manager.dart';
import 'package:melos_core/core/widgets/app_text.dart';

class AuthResendTimer extends StatelessWidget {
  const AuthResendTimer({
    super.key,
    required this.canResend,
    required this.onTimerEnds,
  });

  final bool canResend;
  final VoidCallback onTimerEnds;

  @override
  Widget build(BuildContext context) {
    if (canResend) {
      return AppText(
        LocaleKeys.youCanResendCodeNow,
        style: AppTextStyles.medium13.copyWith(
          color: AppColors.sokoonGray,
          fontSize: 13.sp,
          height: 1.45,
        ),
        textAlign: TextAlign.center,
      );
    }

    return EasyTimerCount.builder(
      duration: EasyTime(minutes: 1),
      onTimerStarts: (_) {},
      onTimerEnds: (_) => onTimerEnds(),
      builder: (timeString) {
        return Text.rich(
          TextSpan(
            text: '${LocaleKeys.resendAfter} ',
            style: AppTextStyles.medium13.copyWith(
              color: AppColors.sokoonGray,
              fontSize: 13.sp,
              height: 1.45,
            ),
            children: [
              TextSpan(
                text: timeString,
                style: AppTextStyles.extraBold.copyWith(
                  color: AppColors.sokoonTeal,
                ),
              ),
            ],
          ),
          textAlign: TextAlign.center,
        );
      },
    );
  }
}
