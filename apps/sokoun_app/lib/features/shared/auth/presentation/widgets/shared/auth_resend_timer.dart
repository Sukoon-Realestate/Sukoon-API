import 'package:easy_timer_count/easy_timer_count.dart';
import 'package:easy_timer_count/helpers/time.dart';
import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
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
        color: AppColors.sokoonGray,
        fontSize: 13.sp,
        fontWeight: FontWeight.w500,
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
            style: TextStyle(
              color: AppColors.sokoonGray,
              fontFamily: ConstantManager.fontFamily,
              fontSize: 13.sp,
              fontWeight: FontWeight.w500,
            ),
            children: [
              TextSpan(
                text: timeString,
                style: TextStyle(
                  color: AppColors.tealOrGoldBasedRole,
                  fontWeight: FontWeight.w800,
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
