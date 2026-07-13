import 'package:easy_timer_count/easy_timer_count.dart';
import 'package:easy_timer_count/helpers/separator.dart';
import 'package:easy_timer_count/helpers/time.dart';
import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/widgets/app_text.dart';

class OtpResendTimer extends StatelessWidget {
  const OtpResendTimer({
    super.key,
    required this.timerResetKey,
    required this.canResend,
    required this.onTimerEnds,
  });

  final int timerResetKey;
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
      key: ValueKey(timerResetKey),
      duration: EasyTime(seconds: 45),
      separatorType: SeparatorType.none,
      onTimerStarts: (_) {},
      onTimerEnds: (_) => onTimerEnds(),
      builder: (timeString) {
        final seconds = _secondsFromTimer(timeString);

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
                text: '$seconds ${LocaleKeys.seconds}',
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

  String _secondsFromTimer(String timeString) {
    final digits = RegExp(r'\d+').allMatches(timeString).map((match) {
      return int.tryParse(match.group(0) ?? '') ?? 0;
    }).toList();

    if (digits.isEmpty) {
      return '0';
    }

    return digits.last.toString().padLeft(2, '0');
  }
}
