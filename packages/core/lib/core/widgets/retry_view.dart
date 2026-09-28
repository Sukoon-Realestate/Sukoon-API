import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:melos_core/core/widgets/buttons/default_button.dart';

class AppRetryView extends StatefulWidget {
  const AppRetryView({super.key, required this.onRetry});

  final Future<void> Function() onRetry;

  @override
  State<AppRetryView> createState() => _AppRetryViewState();
}

class _AppRetryViewState extends State<AppRetryView> {
  final ValueNotifier<bool> _isRetrying = ValueNotifier<bool>(false);

  Future<void> _retry() async {
    if (_isRetrying.value) return;
    _isRetrying.value = true;
    try {
      await widget.onRetry();
    } finally {
      if (mounted) _isRetrying.value = false;
    }
  }

  @override
  void dispose() {
    _isRetrying.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: EdgeInsets.all(24.w),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(
              Icons.cloud_off_outlined,
              color: AppColors.sokoonMuted,
              size: 44.r,
            ),
            12.szH,
            AppText(
              LocaleKeys.exceptionError,
              color: AppColors.sokoonNavy,
              fontSize: 18.sp,
              fontWeight: FontWeight.w900,
              textAlign: TextAlign.center,
            ),
            6.szH,
            AppText(
              LocaleKeys.checkInternet,
              color: AppColors.sokoonGray,
              fontSize: 13.sp,
              textAlign: TextAlign.center,
            ),
            18.szH,
            ValueListenableBuilder<bool>(
              valueListenable: _isRetrying,
              builder: (context, isRetrying, _) => DefaultButton(
                onTap: isRetrying ? null : _retry,
                title: LocaleKeys.ownerRetryAction,
                width: 160.w,
                color: AppColors.sokoonTeal,
                textColor: AppColors.white,
                borderRadius: BorderRadius.circular(12.r),
                customChild: isRetrying
                    ? SizedBox.square(
                        dimension: 18.r,
                        child: const CircularProgressIndicator(
                          strokeWidth: 2,
                          color: AppColors.white,
                        ),
                      )
                    : null,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
