import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/padding_extension.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/helpers/text_style_manager.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:melos_core/generated/assets.dart';

class TenantSuggestedPropertiesEmptyState extends StatelessWidget {
  const TenantSuggestedPropertiesEmptyState({super.key});

  @override
  Widget build(BuildContext context) {
    final bool reduceMotion = MediaQuery.of(context).disableAnimations;
    return Semantics(
      label: LocaleKeys.tenantHomeEmptyTitle,
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          ExcludeSemantics(
            child: Assets.lottie.emptyBox.lottie(
              width: 112.r,
              height: 96.r,
              animate: !reduceMotion,
              repeat: false,
              fit: BoxFit.contain,
              package: 'melos_core',
            ),
          ),
          8.szH,
          AppText(
            LocaleKeys.tenantHomeEmptyTitle,
            style: AppTextStyles.bold16.copyWith(
              color: AppColors.sokoonNavy,
              fontSize: 16.sp,
              height: 1.45,
            ),
            textAlign: TextAlign.center,
            maxLines: 2,
          ),
          6.szH,
          AppText(
            LocaleKeys.tenantHomeEmptyDescription,
            style: AppTextStyles.medium13.copyWith(
              color: AppColors.sokoonGray,
              fontSize: 13.sp,
              height: 1.45,
            ),
            textAlign: TextAlign.center,
            maxLines: 3,
          ),
        ],
      ).paddingSymmetric(horizontal: 24.w, vertical: 12.h),
    );
  }
}
