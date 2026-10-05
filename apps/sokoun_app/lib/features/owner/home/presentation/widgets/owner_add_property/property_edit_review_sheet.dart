import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/helpers/text_style_manager.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:melos_core/core/widgets/buttons/default_button.dart';

class PropertyEditReviewSheet extends StatelessWidget {
  const PropertyEditReviewSheet({super.key});

  @override
  Widget build(BuildContext context) => SafeArea(
    child: SingleChildScrollView(
      padding: EdgeInsets.all(24.w),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.stretch,
        spacing: 16.h,
        children: [
          Icon(Icons.schedule_rounded, color: AppColors.amber, size: 48.r),
          AppText(
            LocaleKeys.ownerPropertyEditReviewTitle,
            style: AppTextStyles.bold.copyWith(fontSize: 20.sp),
            textAlign: TextAlign.center,
          ),
          AppText(
            LocaleKeys.ownerPropertyEditReviewDescription,
            textAlign: TextAlign.center,
          ),
          DefaultButton(
            title: LocaleKeys.ownerPropertyEditReviewDone,
            onTap: Go.back,
          ),
        ],
      ),
    ),
  );
}
