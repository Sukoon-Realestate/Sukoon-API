import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:melos_core/core/helpers/text_style_manager.dart';

class SearchRefreshNotice extends StatelessWidget {
  const SearchRefreshNotice({
    super.key,
    required this.isLoading,
    this.errorMessage,
    required this.onRetry,
  });

  final bool isLoading;
  final String? errorMessage;
  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) => Semantics(
    liveRegion: true,
    child: Padding(
      padding: EdgeInsets.fromLTRB(16.w, 0, 16.w, 16.h),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        spacing: 8.h,
        children: [
          AppText(
            isLoading
                ? LocaleKeys.searchUpdatingPreviousResults
                : errorMessage ?? '',
            style: AppTextStyles.regular13.copyWith(
              color: AppColors.sokoonGray,
            ),
          ),
          if (isLoading)
            const LinearProgressIndicator()
          else
            Align(
              alignment: AlignmentDirectional.centerStart,
              child: TextButton(
                onPressed: onRetry,
                child: AppText(LocaleKeys.searchRetry),
              ),
            ),
        ],
      ),
    ),
  );
}
