import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';

import '../../../config/language/locale_keys.g.dart';
import '../../../config/res/config_imports.dart';
import 'default_button.dart';

class RetryButton extends StatefulWidget {
  const RetryButton({super.key, required this.onRetry});

  final Future<void> Function() onRetry;

  @override
  State<RetryButton> createState() => _RetryButtonState();
}

class _RetryButtonState extends State<RetryButton> {
  bool _isRetrying = false;

  Future<void> _retry() async {
    if (_isRetrying) return;
    setState(() => _isRetrying = true);
    try {
      await widget.onRetry();
    } finally {
      if (mounted) setState(() => _isRetrying = false);
    }
  }

  @override
  Widget build(BuildContext context) => DefaultButton(
    onTap: _isRetrying ? null : _retry,
    title: LocaleKeys.ownerRetryAction,
    width: 160.w,
    color: AppColors.sokoonTeal,
    textColor: AppColors.white,
    borderRadius: BorderRadius.circular(12.r),
    customChild: _isRetrying
        ? SizedBox.square(
            dimension: 18.r,
            child: const CircularProgressIndicator(
              strokeWidth: 2,
              color: AppColors.white,
            ),
          )
        : null,
  );
}
