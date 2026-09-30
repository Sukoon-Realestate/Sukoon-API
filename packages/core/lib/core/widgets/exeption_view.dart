import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';

import '../../config/language/locale_keys.g.dart';
import '../../config/res/config_imports.dart';
import '../../../generated/assets.dart';
import 'app_text.dart';
import 'buttons/retry_button.dart';
import 'retry_view.dart';

class ExceptionView extends StatelessWidget {
  final Size? size;
  final String? msg;
  final Future<void> Function()? onRetry;

  const ExceptionView({super.key, this.size, this.msg, this.onRetry});

  @override
  Widget build(BuildContext context) {
    final Future<void> Function()? retry = onRetry;
    if (msg?.trim() == LocaleKeys.checkInternet.trim() && retry != null) {
      return AppRetryView(onRetry: retry);
    }

    if (msg == null && retry == null) {
      return FittedBox(
        child: Assets.lottie.error2.lottie(
          package: 'melos_core',
          width: size?.width,
          height: size?.height,
          fit: BoxFit.contain,
        ),
      );
    }

    final String message = msg?.trim() ?? '';
    return Center(
      child: SingleChildScrollView(
        padding: EdgeInsets.all(24.w),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Assets.lottie.error2.lottie(
              package: 'melos_core',
              width: size?.width ?? 220.w,
              height: size?.height ?? 180.h,
              fit: BoxFit.contain,
              repeat: false,
              animate: !MediaQuery.disableAnimationsOf(context),
            ),
            SizedBox(height: 12.h),
            AppText(
              message.isEmpty ? LocaleKeys.exceptionError : message,
              color: AppColors.sokoonNavy,
              fontSize: 16.sp,
              textAlign: TextAlign.center,
            ),
            if (retry != null) ...[
              SizedBox(height: 18.h),
              RetryButton(onRetry: retry),
            ],
          ],
        ),
      ),
    );
  }
}
