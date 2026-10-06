import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:melos_core/core/widgets/buttons/retry_button.dart';

class AppRetryView extends StatelessWidget {
  const AppRetryView({
    super.key,
    required this.onRetry,
    this.isConnectionError = true,
  });

  final Future<void> Function() onRetry;
  final bool isConnectionError;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: SingleChildScrollView(
        padding: EdgeInsets.all(24.w),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(
              isConnectionError
                  ? Icons.cloud_off_outlined
                  : Icons.error_outline,
              color: context.appColor(AppColors.sokoonMuted),
              size: 44.r,
            ),
            12.szH,
            AppText(
              LocaleKeys.exceptionError,
              color: context.appColor(AppColors.sokoonNavy),
              fontSize: 18.sp,
              fontWeight: FontWeight.w900,
              textAlign: TextAlign.center,
            ),
            if (isConnectionError) ...[
              6.szH,
              AppText(
                LocaleKeys.checkInternet,
                color: context.appColor(AppColors.sokoonGray),
                fontSize: 13.sp,
                textAlign: TextAlign.center,
              ),
            ],
            18.szH,
            RetryButton(onRetry: onRetry),
          ],
        ),
      ),
    );
  }
}
